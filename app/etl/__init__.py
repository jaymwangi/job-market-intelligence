# app/etl/__init__.py

"""ETL Pipeline - orchestrates the complete extract-transform-enrich-validate-load flow."""

from typing import Optional, List, Dict, Any
import logging
from datetime import datetime, UTC

from sqlalchemy.orm import Session

from app.etl.extractors.jobs_api import JobsExtractor
from app.etl.transformers.jobs_transformer import JobsTransformer
from app.etl.enrichment import Enricher
from app.etl.validators.job_schema import JobValidator
from app.etl.loaders.job_loader import JobLoader
from app.etl.schemas.metrics import PipelineMetrics
from app.etl.schemas.validated import JobValidated
from app.database.session import SessionLocal
from config.settings import settings


logger = logging.getLogger(__name__)


class ETLPipeline:
    """
    Complete ETL pipeline with adaptive acquisition support.

    In adaptive mode, the pipeline processes jobs in batches:
        1. Get next query from controller
        2. Extract raw jobs
        3. Limit to batch_size
        4. Transform
        5. Enrich (including classification)
        6. Update controller with classification results
        7. Repeat until target reached

    In legacy mode, it follows the standard extract-all → transform → enrich → validate → load.
    """

    def __init__(self, db_session: Session | None = None):
        """Initialize pipeline components."""
        self.db_session = db_session

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

        self._acquisition_controllers: Dict[str, Any] = {}
        self._acquisition_metrics: Dict[str, Any] = {}

    def run(
        self,
        countries: Optional[list[str]] = None,
        use_acquisition: Optional[bool] = None,
    ) -> PipelineMetrics:
        """
        Run the full ETL pipeline with optional adaptive acquisition.

        Args:
            countries: List of country codes to extract from.
                If None, defaults to settings.default_countries.
            use_acquisition: Whether to use acquisition strategy.
                If None, uses settings.acquisition_enabled.

        Returns:
            PipelineMetrics with detailed counts and status.

        Raises:
            Exception: If any stage fails (all-or-nothing semantics).
        """
        if countries is None:
            countries = settings.default_countries

        if use_acquisition is None:
            use_acquisition = settings.acquisition_enabled

        start_time = datetime.now(UTC)

        logger.info(
            "Starting ETL pipeline for countries: %s (acquisition=%s)",
            ", ".join(countries) if countries else "none",
            use_acquisition,
        )

        metrics = PipelineMetrics()

        # ------------------------------------------------------------
        # Phase 1: Extract (adaptive or legacy)
        # ------------------------------------------------------------
        if use_acquisition:
            # Adaptive acquisition: processes batches with classification feedback
            validated_jobs = self._run_adaptive_acquisition(
                countries,
                metrics,
            )
        else:
            # Legacy: extract all, then transform/enrich/validate in one go
            raw_jobs = self._extract_legacy(countries)

            metrics.extracted = len(raw_jobs)

            if not raw_jobs:
                logger.warning("No jobs extracted - pipeline complete")
                return metrics

            # Transform, enrich, validate (standard flow)
            validated_jobs = self._process_jobs(
                raw_jobs,
                metrics,
            )

        # ------------------------------------------------------------
        # Phase 5: Load (common for both paths)
        # ------------------------------------------------------------
        if validated_jobs:
            metrics = self._load_jobs(
                validated_jobs,
                metrics,
            )
        else:
            logger.warning("No validated jobs to load")

        # ------------------------------------------------------------
        # Pipeline Complete
        # ------------------------------------------------------------
        duration = (
            datetime.now(UTC) - start_time
        ).total_seconds()

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

    # ------------------------------------------------------------------
    # Adaptive Acquisition (Batch-Level)
    # ------------------------------------------------------------------

    def _run_adaptive_acquisition(
        self,
        countries: List[str],
        metrics: PipelineMetrics,
    ) -> List[JobValidated]:
        """
        Run adaptive acquisition with batch-level classification feedback.

        For each country, the controller decides which queries to run.
        After each batch, the controller is updated with actual classifications.
        This allows real-time adaptation to reach the target tech ratio.

        Returns:
            List of validated job objects (JobValidated).
        """
        from app.etl.acquisition import AcquisitionController

        all_validated_jobs: List[JobValidated] = []

        session = SessionLocal()

        try:
            for country in countries:
                logger.info(f"\n{'=' * 60}")
                logger.info(f"🌍 Processing country: {country.upper()}")
                logger.info(f"{'=' * 60}")

                # Initialize controller for this country
                controller = AcquisitionController(
                    db_session=session,
                    target_tech_ratio=settings.acquisition_target_tech_ratio,
                    max_jobs_per_run=settings.acquisition_max_jobs_per_run,
                    batch_size=settings.acquisition_batch_size,
                    broad_queries=settings.acquisition_broad_queries,
                    tech_queries=settings.acquisition_tech_queries,
                    use_category_filter=settings.acquisition_use_category_filter,
                    country=country,
                    parity_tolerance=settings.acquisition_parity_tolerance,
                )

                self._acquisition_controllers[country] = controller

                # Log initial state
                progress = controller.get_progress()

                logger.info(
                    f"Initial state: mode={progress['mode']}, "
                    f"tech={progress['db_tech']}, "
                    f"non_tech={progress['db_non_tech']}, "
                    f"deficit={progress['tech_deficit']}"
                )

                batch_number = 0
                max_batches = settings.acquisition_max_queries_per_country

                while batch_number < max_batches:
                    # 1. Get next query from controller
                    query = controller.get_next_query()

                    if not query:
                        logger.info("No more queries available")
                        break

                    logger.info(f"\n{'─' * 40}")
                    logger.info(
                        f"Batch {batch_number + 1}: {query.get('what')}"
                    )
                    logger.info(f"{'─' * 40}")

                    # 2. Extract raw jobs from Adzuna (may return many)
                    raw_jobs = self.extractor.extract_with_params(
                        country=country,
                        search_params=query,
                    )

                    if not raw_jobs:
                        logger.warning(
                            f"No jobs found for query: {query.get('what')}"
                        )
                        batch_number += 1
                        continue

                    logger.info(
                        f"Extracted {len(raw_jobs)} raw jobs from query"
                    )

                    # 3. CRITICAL: Limit to batch_size
                    # Calculate how many jobs we can still acquire this run
                    current_total = (
                        controller.get_stats().jobs_acquired_this_run
                    )

                    remaining_capacity = (
                        controller.max_jobs_per_run - current_total
                    )

                    # Take only up to batch_size, but don't exceed remaining capacity
                    batch_limit = min(
                        settings.acquisition_batch_size,
                        remaining_capacity,
                        len(raw_jobs),
                    )

                    if batch_limit <= 0:
                        logger.info("No remaining capacity for this batch")
                        break

                    # Slice the raw jobs to batch_limit
                    batch_raw_jobs = raw_jobs[:batch_limit]

                    logger.info(
                        f"Processing {len(batch_raw_jobs)} jobs "
                        f"(batch limit: {batch_limit})"
                    )

                    # 4. Add to controller (tracking intent)
                    added, duplicates = controller.add_jobs(
                        batch_raw_jobs,
                        query,
                        country,
                    )

                    logger.info(
                        f"Added {added} new jobs, {duplicates} duplicates"
                    )

                    metrics.extracted += added

                    if added == 0:
                        batch_number += 1
                        continue

                    # 5. Transform
                    logger.info("Transforming jobs...")

                    transformed_jobs = self.transformer.transform(
                        batch_raw_jobs
                    )

                    metrics.transformed += len(transformed_jobs)

                    if not transformed_jobs:
                        batch_number += 1
                        continue

                    # 6. Enrich (including classification)
                    logger.info("Enriching and classifying jobs...")

                    enriched_jobs = self.enricher.enrich_batch(
                        transformed_jobs
                    )

                    metrics.enriched += len(enriched_jobs)

                    if not enriched_jobs:
                        batch_number += 1
                        continue

                    # 7. Update controller with classification results
                    logger.info(
                        "Updating controller with classification results..."
                    )

                    controller.update_classification(
                        enriched_jobs
                    )

                    # 8. Validate
                    logger.info("Validating jobs...")

                    validated_jobs = self.validator.validate_batch(
                        enriched_jobs
                    )

                    metrics.validated += len(validated_jobs)

                    all_validated_jobs.extend(validated_jobs)

                    # 9. Log progress
                    progress = controller.get_progress()

                    logger.info(
                        f"Batch {batch_number + 1} complete: "
                        f"mode={progress['mode']}, "
                        f"tech_classified="
                        f"{progress['tech_classified_acquired']}, "
                        f"remaining_needed="
                        f"{progress['remaining_tech_needed']}, "
                        f"projected_has_parity="
                        f"{progress['projected_has_parity']}"
                    )

                    # 10. Check if we've reached max jobs
                    if (
                        controller.get_stats().jobs_acquired_this_run
                        >= controller.max_jobs_per_run
                    ):
                        logger.info(
                            f"Reached max jobs per run for {country}"
                        )
                        break

                    batch_number += 1

                # Log final state for country
                result = controller.get_result()

                logger.info(
                    f"\n✅ Country {country.upper()} complete:\n"
                    f"  Mode: {result.mode.value}\n"
                    f"  Mode changed: {result.mode_changed}\n"
                    f"  Unique jobs: {result.unique_count}\n"
                    f"  Tech intent: {result.tech_intent_count}\n"
                    f"  Broad intent: {result.broad_intent_count}\n"
                    f"  Tech classified: {result.tech_classified_count}\n"
                    f"  Non-tech classified: "
                    f"{result.non_tech_classified_count}\n"
                    f"  Unclassified: {result.unclassified_count}\n"
                    f"  Actual tech ratio: "
                    f"{result.actual_classified_tech_ratio:.2%}\n"
                    f"  Reached parity: {result.reached_parity}\n"
                    f"  Batches processed: {batch_number + 1}"
                )

            # Store aggregated metrics for reporting
            self._acquisition_metrics = (
                self._aggregate_acquisition_metrics()
            )

            return all_validated_jobs

        finally:
            session.close()

    def _aggregate_acquisition_metrics(
        self,
    ) -> Dict[str, Any]:
        """Aggregate metrics from all country controllers."""
        if not self._acquisition_controllers:
            return {}

        total_unique = 0
        total_tech_classified = 0
        total_non_tech_classified = 0
        total_unclassified = 0
        total_duplicates = 0
        total_broad_queries = 0
        total_tech_queries = 0
        total_batches = 0
        reached_parity_all = True

        for country, controller in (
            self._acquisition_controllers.items()
        ):
            result = controller.get_result()

            total_unique += result.unique_count
            total_tech_classified += result.tech_classified_count
            total_non_tech_classified += (
                result.non_tech_classified_count
            )
            total_unclassified += result.unclassified_count
            total_duplicates += result.duplicate_count
            total_broad_queries += result.broad_queries_used
            total_tech_queries += result.tech_queries_used

            total_batches += (
                result.batch_count
                if hasattr(result, "batch_count")
                else 0
            )

            if not result.reached_parity:
                reached_parity_all = False

        total_classified = (
            total_tech_classified + total_non_tech_classified
        )

        actual_tech_ratio = (
            total_tech_classified / total_classified
            if total_classified > 0
            else 0.0
        )

        return {
            "unique_count": total_unique,
            "tech_classified_count": total_tech_classified,
            "non_tech_classified_count": total_non_tech_classified,
            "unclassified_count": total_unclassified,
            "actual_tech_ratio": actual_tech_ratio,
            "target_tech_ratio": settings.acquisition_target_tech_ratio,
            "duplicate_count": total_duplicates,
            "broad_queries_used": total_broad_queries,
            "tech_queries_used": total_tech_queries,
            "total_batches": total_batches,
            "reached_parity_all": reached_parity_all,
            "countries": list(
                self._acquisition_controllers.keys()
            ),
        }

    # ------------------------------------------------------------------
    # Legacy Extraction (No Acquisition)
    # ------------------------------------------------------------------

    def _extract_legacy(
        self,
        countries: List[str],
    ) -> List[Dict]:
        """Legacy extraction without acquisition strategy."""
        all_jobs = []

        for country in countries:
            try:
                country_jobs = self.extractor.extract(
                    country=country
                )

                all_jobs.extend(country_jobs)

                logger.info(
                    "Extracted %d jobs from %s",
                    len(country_jobs),
                    country,
                )

            except Exception as e:
                logger.exception(
                    "Failed to extract from %s: %s",
                    country,
                    str(e),
                )
                raise

        return all_jobs

    # ------------------------------------------------------------------
    # Common Processing Pipeline (Transform → Enrich → Validate)
    # ------------------------------------------------------------------

    def _process_jobs(
        self,
        raw_jobs: List[Dict],
        metrics: PipelineMetrics,
    ) -> List[JobValidated]:
        """Apply transform, enrich, and validate to a batch of raw jobs."""

        # Transform
        logger.info("Transforming jobs...")

        transformed_jobs = self.transformer.transform(
            raw_jobs
        )

        metrics.transformed = len(transformed_jobs)

        if not transformed_jobs:
            logger.warning("No jobs transformed")
            return []

        # Enrich
        logger.info("Enriching jobs...")

        enriched_jobs = self.enricher.enrich_batch(
            transformed_jobs
        )

        metrics.enriched = len(enriched_jobs)

        if not enriched_jobs:
            logger.warning("No jobs enriched")
            return []

        # Validate
        logger.info("Validating jobs...")

        validated_jobs = self.validator.validate_batch(
            enriched_jobs
        )

        metrics.validated = len(validated_jobs)

        return validated_jobs

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------

    def _load_jobs(
        self,
        jobs: List[JobValidated],
        metrics: PipelineMetrics,
    ) -> PipelineMetrics:
        """Load validated jobs to database using bounded batches."""
        if not jobs:
            return metrics

        try:
            if self.db_session is not None:
                return self._load_jobs_with_session(
                    self.db_session,
                    jobs,
                    metrics,
                    commit=False,
                )

            with SessionLocal() as session:
                return self._load_jobs_with_session(
                    session,
                    jobs,
                    metrics,
                    commit=True,
                )

        except Exception:
            logger.exception("Load failed")
            raise

    def _load_jobs_with_session(
        self,
        session: Session,
        jobs: List[JobValidated],
        metrics: PipelineMetrics,
        commit: bool,
    ) -> PipelineMetrics:
        """Load jobs using the supplied database session."""
        loader = JobLoader(db_session=session)

        load_result = loader.upsert_in_batches(
            jobs,
            batch_size=100,
        )

        load_metrics = loader.to_metrics(
            load_result
        )

        metrics.inserted = load_metrics.inserted
        metrics.updated = load_metrics.updated
        metrics.purged = load_metrics.purged
        metrics.skills_added = load_metrics.skills_added
        metrics.relationships_added = (
            load_metrics.relationships_added
        )

        if commit:
            session.commit()

        logger.info(
            "Load complete: inserted=%d, updated=%d, "
            "skills=%d, relationships=%d",
            metrics.inserted,
            metrics.updated,
            metrics.skills_added,
            metrics.relationships_added,
        )

        return metrics

    # ------------------------------------------------------------------
    # Metrics Accessors
    # ------------------------------------------------------------------

    def get_acquisition_metrics(
        self,
    ) -> Optional[Dict[str, Any]]:
        """Get aggregated acquisition metrics from the last pipeline run."""
        return (
            self._acquisition_metrics
            if self._acquisition_metrics
            else None
        )

    def get_acquisition_controllers(
        self,
    ) -> Dict[str, Any]:
        """Get the acquisition controllers for each country."""
        return self._acquisition_controllers