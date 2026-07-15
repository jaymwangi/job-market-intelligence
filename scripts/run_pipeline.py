"""Run the Job Market Intelligence ETL pipeline."""

import sys
import logging
from datetime import UTC, datetime

from app.database.session import get_db
from app.etl.extractors.jobs_api import JobsExtractor
from app.etl.loaders import JobLoader
from app.etl.transformers.jobs_transformer import JobsTransformer
from app.etl.validators import validate_jobs
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

    if not settings.adzuna_app_id or not settings.adzuna_app_key:
        logger.error("❌ Adzuna credentials not configured.")
        return 1

    db_gen = get_db()
    session = next(db_gen)
    pipeline_run_repo = PipelineRunRepository(session)
    
    # Initialize pipeline_run to None so it exists in the except block
    pipeline_run = None

    try:
        # Create pipeline run record at the orchestration level
        pipeline_run = pipeline_run_repo.create(
            source_site="adzuna",
            started_at=datetime.now(UTC)
        )

        # ------------------------------------------------------------------
        # STEP 1: EXTRACT (multiple pages)
        # ------------------------------------------------------------------
        logger.info("\n📡 STEP 1: EXTRACT")
        logger.info(f"   App ID:  {mask_sensitive(settings.adzuna_app_id)}")

        extractor = JobsExtractor(
            api_url=settings.adzuna_base_url,
            app_id=settings.adzuna_app_id,
            api_key=settings.adzuna_app_key,
            debug=False,
        )

        all_raw_jobs = []
        for page in range(1, settings.pipeline_max_pages + 1):
            logger.info(f"   Fetching page {page}/{settings.pipeline_max_pages}...")
            data = extractor.fetch_page(
                page=page,
                results_per_page=settings.pipeline_results_per_page
            )
            raw_jobs = data.get("results", [])
            all_raw_jobs.extend(raw_jobs)
            logger.info(f"   Page {page}: {len(raw_jobs)} jobs")

        logger.info(f"✅ Extracted {len(all_raw_jobs)} total jobs")

        # ------------------------------------------------------------------
        # STEP 2: TRANSFORM
        # ------------------------------------------------------------------
        logger.info("\n🔄 STEP 2: TRANSFORM")

        transformer = JobsTransformer()
        transformed = transformer.transform(all_raw_jobs)

        logger.info(f"✅ Transformed {len(transformed)} jobs")

        # ------------------------------------------------------------------
        # STEP 3: VALIDATE
        # ------------------------------------------------------------------
        logger.info("\n✅ STEP 3: VALIDATE")

        validated = validate_jobs(transformed)

        logger.info(f"✅ Validated {len(validated)} jobs")

        # ------------------------------------------------------------------
        # STEP 4: UPSERT (Insert or Update)
        # ------------------------------------------------------------------
        logger.info("\n💾 STEP 4: UPSERT")

        loader = JobLoader(session, source_site="adzuna")
        result = loader.upsert(validated)

        logger.info("\n📊 Upsert Summary")
        logger.info("-" * 40)
        logger.info(f"Processed : {result.processed}")
        logger.info(f"Inserted  : {result.inserted}")
        logger.info(f"Updated   : {result.updated}")
        logger.info(f"Failed    : {result.failed}")

        if result.errors:
            logger.warning("\n⚠ Errors")
            for error in result.errors:
                logger.warning(f" - {error}")

        # ------------------------------------------------------------------
        # STEP 5: DELETE OLD JOBS (Retention based on scraped_date)
        # ------------------------------------------------------------------
        logger.info(f"\n🗑️ STEP 5: DELETE JOBS OLDER THAN {settings.pipeline_retention_days} DAYS")

        deleted_count = loader.purge_older_than(settings.pipeline_retention_days)
        result.deleted = deleted_count
        logger.info(f"✅ Deleted {deleted_count} jobs")

        # ------------------------------------------------------------------
        # STEP 6: FINISH PIPELINE RUN
        # ------------------------------------------------------------------
        pipeline_run_repo.finish(
            pipeline_run,
            status="completed",
            records_processed=result.processed,
        )

        # ------------------------------------------------------------------
        # COMMIT TRANSACTION (caller owns this)
        # ------------------------------------------------------------------
        session.commit()
        logger.info("✅ Transaction committed successfully")

        # ------------------------------------------------------------------
        # FINAL SUMMARY
        # ------------------------------------------------------------------
        logger.info("\n📝 Pipeline Summary")
        logger.info("-" * 40)
        logger.info(f"Run ID    : {pipeline_run.id}")
        logger.info(f"Extracted : {len(all_raw_jobs)}")
        logger.info(f"Validated : {len(validated)}")
        logger.info(f"Processed : {result.processed}")
        logger.info(f"Inserted  : {result.inserted}")
        logger.info(f"Updated   : {result.updated}")
        logger.info(f"Deleted   : {result.deleted}")
        logger.info(f"Failed    : {result.failed}")
        logger.info(f"Retention : {settings.pipeline_retention_days} days (based on scraped_date)")

        logger.info("\n" + "=" * 60)
        logger.info("🎉 ETL PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}", exc_info=True)
        
        # Rollback transaction (caller owns this)
        session.rollback()
        logger.warning("⚠️ Transaction rolled back")
        
        # Record failure only if pipeline_run was created
        if pipeline_run is not None:
            try:
                pipeline_run_repo.finish(
                    pipeline_run,
                    status="failed",
                    records_processed=0,
                    error_message=str(e),
                )
                session.commit()
            except Exception as finish_error:
                logger.error(f"❌ Failed to record pipeline failure: {finish_error}")
        
        return 1

    finally:
        # Advance the generator so its finally block closes the session
        try:
            next(db_gen)
        except StopIteration:
            pass


def main():
    """Entry point."""
    sys.exit(run_pipeline())


if __name__ == "__main__":
    main()