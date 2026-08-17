"""Run the Job Market Intelligence ETL pipeline."""

import sys
import logging
import signal
from datetime import UTC, datetime
from typing import Optional, Dict, Any
from uuid import UUID

from sqlalchemy import text
from app.etl import ETLPipeline
from app.database.session import get_db
from app.repositories.pipeline_run_repository import PipelineRunRepository
from config.settings import settings

# Setup logging
from config.logging_config import setup_logging
setup_logging()
logger = logging.getLogger(__name__)


class ETLTimeoutError(Exception):
    """Raised when ETL pipeline times out."""
    pass


def timeout_handler(signum, frame):
    """Handle timeout signal."""
    timeout_minutes = getattr(settings, 'etl_timeout_minutes', 25)
    raise ETLTimeoutError(f"ETL pipeline exceeded {timeout_minutes} minutes")


def mask_sensitive(value: str, show: int = 4) -> str:
    """Mask sensitive strings, showing only first few characters."""
    if not value:
        return "None"
    if len(value) <= show:
        return "*" * len(value)
    return f"{value[:show]}..."


def print_summary(
    metrics,
    pipeline_run_id: Optional[str] = None,
    acquisition_metrics: Optional[Dict[str, Any]] = None
) -> None:
    """
    Print a formatted summary of pipeline results.
    
    Args:
        metrics: PipelineMetrics object with pipeline statistics
        pipeline_run_id: Optional pipeline run ID (string)
        acquisition_metrics: Optional aggregated acquisition metrics
    """
    print("\n" + "=" * 70)
    print("📊 ETL Pipeline Summary")
    print("=" * 70)
    if pipeline_run_id:
        print(f"  Run ID:              {pipeline_run_id}")
    print(f"  Duration:            {metrics.duration_seconds:.2f}s")
    print("-" * 70)
    print(f"  Extracted:           {metrics.extracted}")
    print(f"  Transformed:         {metrics.transformed}")
    print(f"  Enriched:            {metrics.enriched}")
    print(f"  Validated:           {metrics.validated}")
    print(f"  Inserted:            {metrics.inserted}")
    print(f"  Updated:             {metrics.updated}")
    print(f"  Purged:              {metrics.purged}")
    print(f"  Skills Added:        {metrics.skills_added}")
    print(f"  Relationships Added: {metrics.relationships_added}")
    print("=" * 70)

    if metrics.validated > 0 and metrics.extracted > 0:
        success_rate = (metrics.validated / metrics.extracted) * 100
        print(f"  Success Rate:        {success_rate:.1f}%")
    else:
        print("  Success Rate:        N/A")
    
    # Add acquisition metrics if available
    if acquisition_metrics:
        print("-" * 70)
        print("🎯 Acquisition Strategy (Adaptive)")
        print(f"  Unique jobs acquired: {acquisition_metrics.get('unique_count', 0)}")
        print(f"  Tech classified:      {acquisition_metrics.get('tech_classified_count', 0)}")
        print(f"  Non-tech classified:  {acquisition_metrics.get('non_tech_classified_count', 0)}")
        print(f"  Unclassified:         {acquisition_metrics.get('unclassified_count', 0)}")
        print(f"  Target tech ratio:    {acquisition_metrics.get('target_tech_ratio', 0):.1%}")
        print(f"  Actual tech ratio:    {acquisition_metrics.get('actual_tech_ratio', 0):.1%}")
        print(f"  Duplicates:           {acquisition_metrics.get('duplicate_count', 0)}")
        print(f"  Broad queries used:   {acquisition_metrics.get('broad_queries_used', 0)}")
        print(f"  Tech queries used:    {acquisition_metrics.get('tech_queries_used', 0)}")
        print(f"  Total batches:        {acquisition_metrics.get('total_batches', 0)}")
        
        reached_parity = acquisition_metrics.get('reached_parity_all', False)
        parity_status = "✅ Yes (all countries)" if reached_parity else "❌ No (some countries still have deficit)"
        print(f"  Parity reached:       {parity_status}")
        
        countries = acquisition_metrics.get('countries', [])
        if countries:
            print(f"  Countries:            {', '.join(c.upper() for c in countries)}")
    
    print("=" * 70)


def run_pipeline_with_timeout(timeout_minutes: int = 25) -> int:
    """
    Run the ETL pipeline with timeout protection (Unix only).
    
    Args:
        timeout_minutes: Maximum runtime in minutes before timeout
        
    Returns:
        0 for success, 1 for failure, 2 for timeout
    """
    # Set timeout alarm only if SIGALRM is available (Unix)
    sigalrm = getattr(signal, 'SIGALRM', None)
    alarm_func = getattr(signal, 'alarm', None)
    
    if sigalrm is not None and alarm_func is not None:
        signal.signal(sigalrm, timeout_handler)
        alarm_func(timeout_minutes * 60)
        has_timeout = True
    else:
        logger.warning("⚠️ Signal-based timeout not supported on this platform; skipping timeout")
        has_timeout = False
    
    try:
        return run_pipeline()
    except ETLTimeoutError as e:
        logger.error(f"⏰ {str(e)}")
        return 2
    finally:
        # Cancel alarm if available
        if has_timeout and alarm_func is not None:
            alarm_func(0)


def run_pipeline() -> int:
    """
    Run the full ETL pipeline using settings from configuration.
    
    Owns the transaction: commit on success, rollback on failure.
    Pipeline execution tracking is managed here, not in the loader.
    
    Returns:
        0 for success, 1 for failure
    """
    timeout_minutes = getattr(settings, 'etl_timeout_minutes', 25)
    
    logger.info("🚀 Job Market Intelligence ETL Pipeline")
    logger.info("=" * 60)
    logger.info(f"Started: {datetime.now(UTC).isoformat()}")
    logger.info(f"Timeout: {timeout_minutes} minutes")
    logger.info(f"Pages: {settings.pipeline_max_pages}, "
                f"Results/page: {settings.pipeline_results_per_page}, "
                f"Retention: {settings.pipeline_retention_days} days")
    logger.info(f"Countries: {', '.join(settings.default_countries)}")
    logger.info(f"Acquisition: {'Enabled' if settings.acquisition_enabled else 'Disabled'}")

    if not settings.adzuna_app_id or not settings.adzuna_app_key:
        logger.error("❌ Adzuna credentials not configured.")
        return 1

    db_gen = get_db()
    session = next(db_gen)
    
    # ============================================================
    # Set database timeouts to prevent idle-in-transaction timeout
    # ============================================================
    try:
        logger.info("⏱️ Setting database timeouts...")
        session.execute(text("SET idle_in_transaction_session_timeout = '15min'"))
        session.execute(text("SET statement_timeout = '10min'"))
        session.commit()
        logger.info("✅ Database timeouts set successfully")
    except Exception as e:
        logger.warning(f"⚠️ Could not set timeouts: {e}")
        # Continue anyway - the pipeline will try to run
    
    pipeline_run_repo = PipelineRunRepository(session)
    
    pipeline_run = None

    try:
        # Create pipeline run record at the orchestration level
        pipeline_run = pipeline_run_repo.create(
            source_site="adzuna",
            started_at=datetime.now(UTC)
        )

        # ------------------------------------------------------------------
        # Initialize and run the ETL pipeline
        # ------------------------------------------------------------------
        logger.info("\n" + "=" * 60)
        logger.info("📡 STEP 1-5: EXTRACT → TRANSFORM → ENRICH → VALIDATE → LOAD")
        logger.info("=" * 60)

        # Create and run pipeline (database already initialized via Alembic)
        pipeline = ETLPipeline()
        metrics = pipeline.run(countries=settings.default_countries)

        # Get acquisition metrics if available
        acquisition_metrics = pipeline.get_acquisition_metrics()

        # ------------------------------------------------------------------
        # FINISH PIPELINE RUN
        # ------------------------------------------------------------------
        pipeline_run_repo.finish(
            pipeline_run,
            status="completed",
            records_processed=metrics.validated,
        )

        # ------------------------------------------------------------------
        # COMMIT TRANSACTION
        # ------------------------------------------------------------------
        session.commit()
        logger.info("✅ Transaction committed successfully")

        # ------------------------------------------------------------------
        # FINAL SUMMARY
        # ------------------------------------------------------------------
        # Convert UUID to string if needed
        run_id_str = str(pipeline_run.id) if pipeline_run and hasattr(pipeline_run, 'id') else None
        print_summary(metrics, run_id_str, acquisition_metrics)

        logger.info("\n" + "=" * 60)
        logger.info("🎉 ETL PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)

        return 0

    except KeyboardInterrupt:
        logger.warning("⚠️ Pipeline interrupted by user")
        return 130

    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}", exc_info=True)
        
        # Rollback the transaction
        session.rollback()
        logger.warning("⚠️ Transaction rolled back")
        
        # Record failure
        if pipeline_run is not None:
            try:
                pipeline_run_repo.finish(
                    pipeline_run,
                    status="failed",
                    records_processed=0,
                    error_message=str(e),
                )
                session.commit()
                logger.info("✅ Pipeline failure recorded")
            except Exception as finish_error:
                logger.error(f"❌ Failed to record pipeline failure: {finish_error}")
                try:
                    session.rollback()
                except Exception:
                    pass
        
        return 1

    finally:
        # Advance the generator so its finally block closes the session
        try:
            next(db_gen)
        except StopIteration:
            pass


def main() -> int:
    """Entry point with timeout protection."""
    timeout_minutes = getattr(settings, 'etl_timeout_minutes', 25)
    result = run_pipeline_with_timeout(timeout_minutes)
    
    if result == 2:
        logger.error("⏰ ETL pipeline timed out!")
        logger.error(f"   Timeout was set to {timeout_minutes} minutes")
        logger.error("   Consider increasing ETL_TIMEOUT_MINUTES in settings")
        return 1
    
    return result


if __name__ == "__main__":
    sys.exit(main())