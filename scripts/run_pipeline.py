"""Run the Job Market Intelligence ETL pipeline."""

import sys
import logging
from datetime import UTC, datetime

from sqlalchemy import text
from app.etl import ETLPipeline
from app.database.session import get_db
from app.repositories.pipeline_run_repository import PipelineRunRepository
from config.settings import settings

# Setup logging
from config.logging_config import setup_logging
setup_logging()
logger = logging.getLogger(__name__)


def mask_sensitive(value: str, show: int = 4) -> str:
    """Mask sensitive strings, showing only first few characters."""
    if not value:
        return "None"
    if len(value) <= show:
        return "*" * len(value)
    return f"{value[:show]}..."


def print_summary(metrics, pipeline_run_id=None) -> None:
    """Print a formatted summary of pipeline results."""
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
    print("=" * 70)


def run_pipeline() -> int:
    """
    Run the full ETL pipeline using settings from configuration.
    
    Owns the transaction: commit on success, rollback on failure.
    Pipeline execution tracking is managed here, not in the loader.
    
    Returns:
        0 for success, 1 for failure
    """
    logger.info("🚀 Job Market Intelligence ETL Pipeline")
    logger.info("=" * 60)
    logger.info(f"Started: {datetime.now(UTC).isoformat()}")
    logger.info(f"Pages: {settings.pipeline_max_pages}, "
                f"Results/page: {settings.pipeline_results_per_page}, "
                f"Retention: {settings.pipeline_retention_days} days")
    logger.info(f"Countries: {', '.join(settings.default_countries)}")

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
        print_summary(metrics, pipeline_run.id)

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
    """Entry point."""
    return run_pipeline()


if __name__ == "__main__":
    sys.exit(main())