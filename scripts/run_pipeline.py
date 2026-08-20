"""Run the Job Market Intelligence ETL pipeline."""

import logging
import signal
import sys
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.database.session import SessionLocal
from app.etl import ETLPipeline
from app.models.pipeline_run import PipelineRun
from app.repositories.pipeline_run_repository import PipelineRunRepository

# Setup logging
from config.logging_config import setup_logging
from config.settings import settings

setup_logging()
logger = logging.getLogger(__name__)


class ETLTimeoutError(Exception):
    """Raised when ETL pipeline times out."""

    pass


def timeout_handler(signum, frame):
    """Handle timeout signal."""
    timeout_minutes = settings.etl_timeout_minutes
    raise ETLTimeoutError(f"ETL pipeline exceeded {timeout_minutes} minutes")


def mask_sensitive(value: str, show: int = 4) -> str:
    """Mask sensitive strings, showing only first few characters."""
    if not value:
        return "None"
    if len(value) <= show:
        return "*" * len(value)
    return f"{value[:show]}..."


def print_summary(
    metrics, pipeline_run_id: str | None = None, acquisition_metrics: dict[str, Any] | None = None
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

        reached_parity = acquisition_metrics.get("reached_parity_all", False)
        parity_status = (
            "✅ Yes (all countries)"
            if reached_parity
            else "❌ No (some countries still have deficit)"
        )
        print(f"  Parity reached:       {parity_status}")

        countries = acquisition_metrics.get("countries", [])
        if countries:
            print(f"  Countries:            {', '.join(c.upper() for c in countries)}")

    print("=" * 70)


def mark_pipeline_run_failed(pipeline_run_id: UUID | None, error_message: str) -> None:
    """
    Record ETL failure using a short-lived database transaction.

    Args:
        pipeline_run_id: UUID of the pipeline run to mark as failed
        error_message: Error message to record
    """
    if pipeline_run_id is None:
        return

    try:
        with SessionLocal() as session:
            repo = PipelineRunRepository(session)
            pipeline_run = session.get(PipelineRun, pipeline_run_id)

            if pipeline_run is None:
                logger.error("❌ Could not find pipeline run %s", pipeline_run_id)
                return

            repo.finish(
                pipeline_run,
                status="failed",
                records_processed=0,
                error_message=error_message,
            )
            session.commit()
            logger.info("✅ Pipeline failure recorded")

    except Exception as e:
        logger.error("❌ Failed to record pipeline failure: %s", e, exc_info=True)


def run_pipeline_with_timeout(timeout_minutes: int | None = None) -> int:
    """
    Run the ETL pipeline with timeout protection (Unix only).

    Args:
        timeout_minutes: Maximum runtime in minutes before timeout.
            If None, uses settings.etl_timeout_minutes.

    Returns:
        0 for success, 1 for failure, 2 for timeout.
    """
    if timeout_minutes is None:
        timeout_minutes = settings.etl_timeout_minutes

    # Set timeout alarm only if SIGALRM is available (Unix)
    sigalrm = getattr(signal, "SIGALRM", None)
    alarm_func = getattr(signal, "alarm", None)

    if sigalrm is not None and alarm_func is not None:
        signal.signal(sigalrm, timeout_handler)
        alarm_func(timeout_minutes * 60)
        has_timeout = True
    else:
        logger.warning(
            "⚠️ Signal-based timeout not supported on this platform; " "skipping timeout"
        )
        has_timeout = False

    try:
        return run_pipeline()
    except ETLTimeoutError as e:
        logger.error("⏰ %s", str(e))
        return 2
    finally:
        if has_timeout and alarm_func is not None:
            alarm_func(0)


def run_pipeline() -> int:
    """
    Run the full ETL pipeline using settings from configuration.

    Database transactions are deliberately kept short:
    - Transaction 1: create pipeline_run (commit immediately)
    - ETL execution: no orchestration transaction
    - Transaction 2: finish pipeline_run (commit immediately)
    - Failure handling: fresh short transaction

    Returns:
        0 for success, 1 for failure
    """
    timeout_minutes = settings.etl_timeout_minutes

    logger.info("🚀 Job Market Intelligence ETL Pipeline")
    logger.info("=" * 60)
    logger.info(f"Started: {datetime.now(UTC).isoformat()}")
    logger.info(f"Timeout: {timeout_minutes} minutes")
    logger.info(
        f"Pages: {settings.pipeline_max_pages}, "
        f"Results/page: {settings.pipeline_results_per_page}, "
        f"Retention: {settings.pipeline_retention_days} days"
    )
    logger.info(f"Countries: {', '.join(settings.default_countries)}")
    logger.info(f"Acquisition: {'Enabled' if settings.acquisition_enabled else 'Disabled'}")

    if not settings.adzuna_app_id or not settings.adzuna_app_key:
        logger.error("❌ Adzuna credentials not configured.")
        return 1

    pipeline_run_id = None

    # ============================================================
    # 1. CREATE PIPELINE RUN - Short transaction only
    # ============================================================
    try:
        with SessionLocal() as session:
            logger.info("📝 Creating pipeline run...")
            repo = PipelineRunRepository(session)
            pipeline_run = repo.create(
                source_site="adzuna",
                started_at=datetime.now(UTC),
            )
            # ✅ Commit immediately - end the transaction
            session.commit()
            pipeline_run_id = pipeline_run.id
            logger.info(f"✅ Pipeline run created: {pipeline_run_id}")

    except Exception as e:
        logger.error(f"❌ Failed to create pipeline run: {e}", exc_info=True)
        return 1

    # ============================================================
    # 2. RUN ETL - NO database transaction open here
    # ============================================================
    try:
        logger.info("\n" + "=" * 60)
        logger.info("📡 STEP 1-5: EXTRACT → TRANSFORM → ENRICH → VALIDATE → LOAD")
        logger.info("=" * 60)

        pipeline = ETLPipeline()
        metrics = pipeline.run(countries=settings.default_countries)
        acquisition_metrics = pipeline.get_acquisition_metrics()

    except ETLTimeoutError as e:
        # ✅ Record timeout failure and re-raise for timeout handler
        logger.error(f"⏰ {str(e)}")
        mark_pipeline_run_failed(pipeline_run_id, str(e))
        raise

    except KeyboardInterrupt:
        logger.warning("⚠️ Pipeline interrupted by user")
        mark_pipeline_run_failed(pipeline_run_id, "Interrupted by user")
        return 130

    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}", exc_info=True)
        mark_pipeline_run_failed(pipeline_run_id, str(e))
        return 1

    # ============================================================
    # 3. FINISH PIPELINE RUN - Short transaction only
    # ============================================================
    try:
        with SessionLocal() as session:
            logger.info("📝 Finishing pipeline run...")
            repo = PipelineRunRepository(session)

            pipeline_run = session.get(PipelineRun, pipeline_run_id)
            if pipeline_run is None:
                raise RuntimeError(f"Pipeline run {pipeline_run_id} could not be found")

            repo.finish(
                pipeline_run,
                status="completed",
                records_processed=metrics.validated,
            )
            session.commit()
            logger.info("✅ Pipeline run marked as completed")

    except Exception as e:
        logger.error(f"❌ Failed to finish pipeline run: {e}", exc_info=True)
        return 1

    # ============================================================
    # 4. FINAL SUMMARY
    # ============================================================
    run_id_str = str(pipeline_run_id) if pipeline_run_id else None
    print_summary(metrics, run_id_str, acquisition_metrics)

    logger.info("\n" + "=" * 60)
    logger.info("🎉 ETL PIPELINE COMPLETED SUCCESSFULLY")
    logger.info("=" * 60)

    return 0


def main() -> int:
    """Entry point with timeout protection."""
    result = run_pipeline_with_timeout()

    if result == 2:
        logger.error("⏰ ETL pipeline timed out!")
        logger.error(
            "   Timeout was set to %s minutes",
            settings.etl_timeout_minutes,
        )
        logger.error("   Consider increasing ETL_TIMEOUT_MINUTES in settings")
        return 1

    return result


if __name__ == "__main__":
    sys.exit(main())
