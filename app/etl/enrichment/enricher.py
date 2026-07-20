"""Enrichment orchestrator - coordinates all enrichment components."""

from typing import List, Optional
from config.settings import settings
from app.etl.schemas.transformed import JobTransformed
from app.etl.schemas.enriched import JobEnriched
from app.etl.enrichment.skill_extractor import SkillExtractor
from app.etl.enrichment.technology_classifier import TechnologyClassifier
from app.etl.enrichment.country_normalizer import CountryNormalizer
from app.etl.enrichment.currency_normalizer import CurrencyNormalizer
import logging

logger = logging.getLogger(__name__)


class Enricher:
    """Orchestrates the enrichment pipeline."""

    def __init__(self):
        self.skill_extractor = SkillExtractor(
            keywords=None,  # Uses TECH_KEYWORDS from data
            data_path=settings.skills_data_path,
        )
        self.tech_classifier = TechnologyClassifier()
        self.country_normalizer = CountryNormalizer()
        self.currency_normalizer = CurrencyNormalizer()
        self.normalize_salaries = settings.normalize_salaries

    def enrich(self, job: JobTransformed) -> JobEnriched:
        """Enrich a single job with intelligence data."""
        # Extract skills
        skills = self.skill_extractor.extract_skills(job.title, job.description)

        # Classify technology
        tech_category = self.tech_classifier.classify(job.title, skills)
        is_tech = self.tech_classifier.is_tech_role_with_category(tech_category)

        # Normalize country
        country_code = self._normalize_country(job)

        # Normalize currency - try multiple sources
        currency = self._normalize_currency(job, country_code)

        # Optional salary normalization
        normalized_min = None
        normalized_max = None

        if self.normalize_salaries and currency:
            if job.salary_min is not None:
                normalized_min = self.currency_normalizer.convert(
                    amount=job.salary_min,
                    from_currency=currency,
                    to_currency="USD",
                )
            if job.salary_max is not None:
                normalized_max = self.currency_normalizer.convert(
                    amount=job.salary_max,
                    from_currency=currency,
                    to_currency="USD",
                )

        return JobEnriched(
            source_id=job.source_id,
            source=job.source,
            title=job.title,
            company=job.company,
            location=job.location,
            description=job.description,
            salary_min=job.salary_min,
            salary_max=job.salary_max,
            salary_currency=job.salary_currency,
            employment_type=job.employment_type,
            category=job.category,
            posted_date=job.posted_date,
            scraped_date=job.scraped_date,
            url=job.url,
            source_country=job.source_country,
            skills=skills,
            technology_category=tech_category.value,
            is_tech_role=is_tech,
            country_code=country_code,
            currency=currency,
            normalized_salary_min=normalized_min,
            normalized_salary_max=normalized_max,
        )

    def _normalize_country(self, job: JobTransformed) -> Optional[str]:
        """Normalize country from source_country or location."""
        if job.source_country:
            normalized = self.country_normalizer.normalize(job.source_country)
            if normalized:
                return normalized

        if job.location:
            return self.country_normalizer.normalize(job.location)

        return None

    def _normalize_currency(self, job: JobTransformed, country_code: Optional[str]) -> Optional[str]:
        """
        Normalize currency from multiple sources.
        
        Priority:
        1. Use salary_currency from the job data
        2. Infer from country_code
        3. Default to USD
        """
        # Try 1: Use salary_currency from job data
        if job.salary_currency:
            currency = self.currency_normalizer.normalize(job.salary_currency)
            if currency:
                logger.debug(f"Currency from salary_currency: {currency}")
                return currency
        
        # Try 2: Infer from country_code
        if country_code:
            currency = self.currency_normalizer.infer_currency_from_country(country_code)
            if currency:
                logger.debug(f"Currency inferred from country {country_code}: {currency}")
                return currency
        
        # Try 3: Default to USD
        logger.debug(f"Using default currency USD for job {job.source_id}")
        return "USD"

    def enrich_batch(self, jobs: List[JobTransformed]) -> List[JobEnriched]:
        """Enrich a batch of jobs."""
        return [self.enrich(job) for job in jobs]