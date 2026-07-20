"""Job validator - ensures data quality, pure validation."""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from pydantic import ValidationError
from app.etl.schemas.enriched import JobEnriched
from app.etl.schemas.validated import JobValidated

logger = logging.getLogger(__name__)


class JobValidator:
    """
    Validate enriched job data - pure validation, no mutation.

    This validator takes JobEnriched objects and returns JobValidated objects.
    Invalid jobs are logged and dropped.

    Validation rules:
        - Required fields: source_id, title, company
        - Salary: non-negative, min <= max (with swap and warning)
        - Country code: 2 characters if present
        - Currency: 3 characters if present
    """

    def validate(self, job: JobEnriched) -> Optional[JobValidated]:
        """
        Validate a single job.

        Args:
            job: Enriched job data

        Returns:
            Validated job or None if invalid

        Note: This is pure validation - the original job is not mutated.
        """
        warnings = []

        # Extract data for validation
        data = job.model_dump()

        # 1. Check required fields
        if not data.get("source_id"):
            logger.warning("Missing source_id")
            return None

        if not data.get("title"):
            logger.warning("Missing title for job: %s", data.get("source_id"))
            return None

        if not data.get("company"):
            logger.warning("Missing company for job: %s", data.get("source_id"))
            return None

        # 2. Validate salary ranges
        salary_min = data.get("salary_min")
        salary_max = data.get("salary_max")

        if salary_min is not None and salary_max is not None:
            if salary_min < 0 or salary_max < 0:
                logger.warning(
                    "Negative salary for job %s: min=%s, max=%s",
                    data.get("source_id"),
                    salary_min,
                    salary_max,
                )
                return None

            if salary_min > salary_max:
                logger.warning(
                    "Min salary > max salary for job %s: min=%s, max=%s",
                    data.get("source_id"),
                    salary_min,
                    salary_max,
                )
                warnings.append("Min salary > max salary - values swapped")
                # Create new data dict with swapped values (no mutation)
                data = dict(data)
                data["salary_min"] = salary_max
                data["salary_max"] = salary_min

        # 3. Ensure scraped_date is set (should be set by transformer, but defensive)
        if not data.get("scraped_date"):
            logger.warning(
                "Missing scraped_date for job %s - using current time",
                data.get("source_id"),
            )
            data["scraped_date"] = datetime.utcnow()

        # 4. Build validated job (Pydantic handles field-level validation)
        try:
            return JobValidated(
                **data,
                validation_timestamp=datetime.utcnow(),
                validation_warnings=warnings,
            )
        except ValidationError as e:
            logger.warning(
                "Pydantic validation failed for job %s: %s",
                data.get("source_id"),
                str(e),
            )
            return None

    def validate_batch(self, jobs: List[JobEnriched]) -> List[JobValidated]:
        """
        Validate a batch of jobs.

        Args:
            jobs: List of enriched jobs

        Returns:
            List of validated jobs (invalid ones are dropped)
        """
        if not jobs:
            return []

        valid = []
        for job in jobs:
            validated = self.validate(job)
            if validated:
                valid.append(validated)

        logger.info(
            "Validation complete: %d/%d jobs passed",
            len(valid),
            len(jobs),
        )
        return valid