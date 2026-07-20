"""ETL Pipeline - orchestrates the complete extract-transform-enrich-validate-load flow."""

from typing import Optional
import logging
from datetime import datetime, UTC

from app.etl.extractors.jobs_api import JobsExtractor
from app.etl.transformers.jobs_transformer import JobsTransformer
from app.etl.enrichment import Enricher
from app.etl.validators.job_schema import JobValidator
from app.etl.loaders.job_loader import JobLoader
from app.etl.schemas.metrics import PipelineMetrics
from app.database.session import SessionLocal
from config.settings import settings

logger = logging.getLogger(__name__)


class ETLPipeline:
    """
    Complete ETL pipeline with typed stages.

    Flow:
        Extract (Raw) → Transform (JobTransformed)
        → Enrich (JobEnriched)
        → Validate (JobValidated)
        → Load (Database)

    Each stage has a clear data contract, making the pipeline
    easy to test, extend, and maintain.
    """

    def __init__(self):
        """Initialize pipeline components."""
        self.extractor = JobsExtractor(
            api_url=settings.adzuna_base_url,
            app_id=settings.adzuna_app_id,
            api_key=settings.adzuna_app_key,
            debug=settings.debug,
            results_per_page=settings.pipeline_results_per_page,
            max_pages=settings.pipeline_max_pages,
        )
        self.transformer = JobsTransformer()
        self.enricher = Enricher()
        self.validator = JobValidator()

    def run(self, countries: Optional[list[str]] = None) -> PipelineMetrics:
        """
        Run the full ETL pipeline.

        Args:
            countries: List of country codes to extract from.
                      If None, defaults to settings.default_countries.
                      If empty list, runs zero countries.

        Returns:
            PipelineMetrics with detailed counts and status.

        Raises:
            Exception: If any stage fails (all-or-nothing semantics).
        """
        if countries is None:
            countries = settings.default_countries

        start_time = datetime.now(UTC)
        logger.info(
            "Starting ETL pipeline for countries: %s",
            ", ".join(countries) if countries else "none",
        )

        metrics = PipelineMetrics()

        # ============================================================
        # Phase 1: Extract
        # ============================================================
        logger.info("Phase 1: Extracting jobs...")
        raw_jobs: list = []

        for country in countries:
            try:
                country_jobs = self.extractor.extract(country=country)
                raw_jobs.extend(country_jobs)
                logger.info(
                    "Extracted %d jobs from %s",
                    len(country_jobs),
                    country,
                )
            except Exception as e:
                logger.exception("Failed to extract from %s: %s", country, str(e))
                raise

        metrics.extracted = len(raw_jobs)
        logger.info("Extracted %d total raw jobs", metrics.extracted)

        if not raw_jobs:
            logger.warning("No jobs extracted - pipeline complete")
            return metrics

        # ============================================================
        # Phase 2: Transform
        # ============================================================
        logger.info("Phase 2: Transforming jobs...")
        try:
            transformed_jobs = self.transformer.transform(raw_jobs)
            metrics.transformed = len(transformed_jobs)
            logger.info(
                "Transformed %d/%d jobs",
                metrics.transformed,
                metrics.extracted,
            )
        except Exception as e:
            logger.exception("Transformation failed: %s", str(e))
            raise

        if not transformed_jobs:
            logger.warning("No jobs transformed - pipeline complete")
            return metrics

        # ============================================================
        # Phase 3: Enrich
        # ============================================================
        logger.info("Phase 3: Enriching jobs...")
        try:
            enriched_jobs = self.enricher.enrich_batch(transformed_jobs)
            metrics.enriched = len(enriched_jobs)
            logger.info(
                "Enriched %d/%d jobs",
                metrics.enriched,
                metrics.transformed,
            )
        except Exception as e:
            logger.exception("Enrichment failed: %s", str(e))
            raise

        if not enriched_jobs:
            logger.warning("No jobs enriched - pipeline complete")
            return metrics

        # ============================================================
        # Phase 4: Validate
        # ============================================================
        logger.info("Phase 4: Validating jobs...")
        try:
            validated_jobs = self.validator.validate_batch(enriched_jobs)
            metrics.validated = len(validated_jobs)
            logger.info(
                "Validated %d/%d jobs",
                metrics.validated,
                metrics.enriched,
            )
        except Exception as e:
            logger.exception("Validation failed: %s", str(e))
            raise

        if not validated_jobs:
            logger.warning("No jobs validated - pipeline complete")
            return metrics

        # ============================================================
        # Phase 5: Load
        # ============================================================
        logger.info("Phase 5: Loading jobs...")
        session = SessionLocal()

        try:
            loader = JobLoader(db_session=session)

            load_result = loader.upsert(validated_jobs)

            load_metrics = loader.to_metrics(load_result)

            metrics.inserted = load_metrics.inserted
            metrics.updated = load_metrics.updated
            metrics.purged = load_metrics.purged
            metrics.skills_added = load_metrics.skills_added
            metrics.relationships_added = load_metrics.relationships_added

            session.commit()

            logger.info(
                "Load complete: inserted=%d, updated=%d, skills=%d, relationships=%d",
                metrics.inserted,
                metrics.updated,
                metrics.skills_added,
                metrics.relationships_added,
            )

        except Exception as e:
            session.rollback()
            logger.exception("Load failed: %s", str(e))
            raise
        finally:
            session.close()

        # ============================================================
        # Pipeline Complete
        # ============================================================
        duration = (datetime.now(UTC) - start_time).total_seconds()
        metrics.duration_seconds = duration

        logger.info(
            "ETL pipeline complete in %.2fs: extracted=%d, transformed=%d, "
            "enriched=%d, validated=%d, inserted=%d, updated=%d, purged=%d",
            duration,
            metrics.extracted,
            metrics.transformed,
            metrics.enriched,
            metrics.validated,
            metrics.inserted,
            metrics.updated,
            metrics.purged,
        )

        return metrics