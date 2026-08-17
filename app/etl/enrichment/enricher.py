"""Enrichment orchestrator - coordinates all enrichment components.

This module orchestrates the enrichment pipeline for job postings:
1. Language detection
2. Skill extraction
3. Technology scoring (with evidence and confidence)
4. Country normalization
5. Currency normalization
6. Optional salary normalization

The enricher uses:
- LanguageDetector for language detection
- SkillExtractor for skill extraction
- TechnologyScorer for tech role classification
- CountryNormalizer for country codes
- CurrencyNormalizer for currency codes

Design decisions:
- Dependency injection for testability
- Running statistics for performance monitoring (constant memory)
- time.perf_counter() for high-resolution timing
- Modular step-based architecture with EnrichmentStep protocol
- Metadata for version tracking and auditing
- Batch processing continues on individual failures
"""

import time
from datetime import datetime
from typing import List, Optional, Dict, Any, Protocol, Tuple, Callable

from config.settings import settings

# 👇 IMPORTANT: Don't import JobEnriched at the top level
# from app.etl.schemas.enriched import JobEnriched  # ❌ REMOVE THIS

from app.etl.schemas.transformed import JobTransformed

from app.etl.enrichment.country_normalizer import CountryNormalizer
from app.etl.enrichment.currency_normalizer import CurrencyNormalizer
from app.etl.enrichment.language_detector import LanguageDetector, get_detector
from app.etl.enrichment.skill_extractor import SkillExtractor
from app.etl.enrichment.tech_scorer import TechnologyScorer, TechScoreResult, get_scorer
from app.shared.languages import LanguageCode

import logging

logger = logging.getLogger(__name__)


class EnrichmentStep(Protocol):
    """
    Protocol for enrichment steps.
    
    Each step must implement an `enrich` method that takes
    a job and a context dict, and modifies the context.
    """
    
    def enrich(self, job: JobTransformed, context: dict) -> None:
        """Enrich the job and update the context."""
        ...


class Enricher:
    """
    Orchestrates the enrichment pipeline for job postings.

    Coordinates all enrichment components in the correct order.
    The pipeline is designed to be idempotent and deterministic.

    Args:
        language_detector: Optional LanguageDetector instance
        skill_extractor: Optional SkillExtractor instance
        tech_scorer: Optional TechnologyScorer instance
        country_normalizer: Optional CountryNormalizer instance
        currency_normalizer: Optional CurrencyNormalizer instance
        normalize_salaries: Whether to normalize salaries to USD
        language_detection_enabled: Whether to detect language
    """

    def __init__(
        self,
        language_detector: Optional[LanguageDetector] = None,
        skill_extractor: Optional[SkillExtractor] = None,
        tech_scorer: Optional[TechnologyScorer] = None,
        country_normalizer: Optional[CountryNormalizer] = None,
        currency_normalizer: Optional[CurrencyNormalizer] = None,
        normalize_salaries: Optional[bool] = None,
        language_detection_enabled: Optional[bool] = None,
    ):
        """Initialize the enricher with optional dependency injection."""

        # Language detection
        self.language_detector = language_detector or get_detector()
        self.language_detection_enabled = (
            language_detection_enabled
            if language_detection_enabled is not None
            else getattr(settings, 'language_detection_enabled', True)
        )

        # Skill extraction - handle missing settings gracefully
        try:
            skills_data_path = getattr(settings, 'skills_data_path', None)
            self.skill_extractor = skill_extractor or SkillExtractor(
                keywords=None,
                data_path=skills_data_path,
            )
        except Exception as e:
            logger.warning("Failed to initialize SkillExtractor with settings: %s", e)
            self.skill_extractor = skill_extractor or SkillExtractor()

        # Technology scoring
        self.tech_scorer = tech_scorer or get_scorer()

        # Normalizers
        self.country_normalizer = country_normalizer or CountryNormalizer()
        self.currency_normalizer = currency_normalizer or CurrencyNormalizer()

        # Settings - handle missing gracefully
        self.normalize_salaries = (
            normalize_salaries
            if normalize_salaries is not None
            else getattr(settings, 'normalize_salaries', False)
        )

        # Timing statistics (running stats - constant memory)
        self._timing_stats: Dict[str, Dict[str, float]] = {
            "language": {"count": 0, "total_ms": 0, "min_ms": float("inf"), "max_ms": 0},
            "skills": {"count": 0, "total_ms": 0, "min_ms": float("inf"), "max_ms": 0},
            "tech_scoring": {"count": 0, "total_ms": 0, "min_ms": float("inf"), "max_ms": 0},
            "country": {"count": 0, "total_ms": 0, "min_ms": float("inf"), "max_ms": 0},
            "currency": {"count": 0, "total_ms": 0, "min_ms": float("inf"), "max_ms": 0},
            "salary": {"count": 0, "total_ms": 0, "min_ms": float("inf"), "max_ms": 0},
            "total": {"count": 0, "total_ms": 0, "min_ms": float("inf"), "max_ms": 0},
        }
        
        # Enrichment steps (ordered)
        self._steps = self._build_steps()

        logger.info(
            "Enricher initialized: language_detection=%s, normalize_salaries=%s",
            self.language_detection_enabled,
            self.normalize_salaries,
        )

    def _build_steps(self) -> List[Tuple[str, Callable[[JobTransformed, dict], None]]]:
        """
        Build the ordered list of enrichment steps.
        
        Returns:
            List of (step_name, step_function) tuples
        """
        return [
            ("language", self._enrich_language),
            ("skills", self._enrich_skills),
            ("tech_scoring", self._enrich_tech_scoring),
            ("country", self._enrich_country),
            ("currency", self._enrich_currency),
            ("salary", self._enrich_salary),
            ("build", self._enrich_build_job),
        ]

    def enrich(self, job: JobTransformed) -> Any:
        """
        Enrich a single job with intelligence data.

        Args:
            job: Transformed job data

        Returns:
            JobEnriched: Enriched job with all metadata

        Raises:
            Exception: If enrichment fails (caller should handle)
        """
        start_time = time.perf_counter()
        context: Dict[str, Any] = {
            "job": job,
            "timings": {},
        }

        # Run each enrichment step
        for step_name, step_func in self._steps:
            step_start = time.perf_counter()
            try:
                step_func(job, context)
            except Exception as e:
                logger.error("Step '%s' failed for job %s: %s", step_name, job.source_id, e)
                raise
            
            # Record timing
            elapsed_ms = (time.perf_counter() - step_start) * 1000
            context["timings"][step_name] = elapsed_ms
            self._record_timing(step_name, elapsed_ms)

        # Record total timing
        total_ms = (time.perf_counter() - start_time) * 1000
        self._record_timing("total", total_ms)

        # Return the enriched job
        return context["enriched_job"]

    def _enrich_language(self, job: JobTransformed, context: dict) -> None:
        """Step 1: Detect language."""
        if not self.language_detection_enabled:
            context["language"] = LanguageCode.ENGLISH
            return

        text = f"{job.title} {job.description or ''}"
        context["language"] = self.language_detector.detect(text)

    def _enrich_skills(self, job: JobTransformed, context: dict) -> None:
        """Step 2: Extract skills."""
        context["skills"] = self.skill_extractor.extract_skills(
            job.title, job.description or ""
        )

    def _enrich_tech_scoring(self, job: JobTransformed, context: dict) -> None:
        """Step 3: Score technology role."""
        skills = context.get("skills", [])
        context["tech_decision"] = self.tech_scorer.classify(
            title=job.title,
            description=job.description or "",
            skills=skills,
        )

    def _enrich_country(self, job: JobTransformed, context: dict) -> None:
        """Step 4: Normalize country."""
        country_code = None
        
        if job.source_country:
            normalized = self.country_normalizer.normalize(job.source_country)
            if normalized:
                country_code = normalized

        if not country_code and job.location:
            country_code = self.country_normalizer.normalize(job.location)

        context["country_code"] = country_code

    def _enrich_currency(self, job: JobTransformed, context: dict) -> None:
        """Step 5: Normalize currency."""
        country_code = context.get("country_code")
        currency = None

        # Try salary_currency first
        if job.salary_currency:
            currency = self.currency_normalizer.normalize(job.salary_currency)

        # Try country inference
        if not currency and country_code:
            currency = self.currency_normalizer.infer_currency_from_country(country_code)

        # Default to USD
        context["currency"] = currency or "USD"

    def _enrich_salary(self, job: JobTransformed, context: dict) -> None:
        """Step 6: Normalize salaries (optional)."""
        if not self.normalize_salaries:
            context["normalized_min"] = None
            context["normalized_max"] = None
            return

        currency = context.get("currency")
        if not currency:
            context["normalized_min"] = None
            context["normalized_max"] = None
            return

        normalized_min = None
        normalized_max = None

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

        context["normalized_min"] = normalized_min
        context["normalized_max"] = normalized_max
     

    def _enrich_build_job(self, job: JobTransformed, context: dict) -> None:
        """
        Step 7: Build the enriched job.
        
        Uses model_dump() to avoid manually copying fields.
        Only adds new fields that exist in JobEnriched.
        """
        from app.etl.schemas.enriched import JobEnriched
        
        tech_decision = context.get("tech_decision")
        if tech_decision is None:
            # Create a default decision if tech scoring didn't run
            from app.etl.enrichment.classifier import ClassificationDecision, DecisionReason
            tech_decision = ClassificationDecision(
                is_tech=False,
                primary_category="other",
                primary_score=0.0,
                margin=0.0,
                score=0.0,
                confidence=0.0,
                reason=DecisionReason.NO_CATEGORIES,
                second_best_category=None,
                second_best_score=None,
                ambiguity_score=0.0,
                explanations=["No tech scoring performed"],
                thresholds=None
            )

        # Start with transformed job data
        job_data = job.model_dump()
        
        # Add enrichment fields
        job_data.update({
            # Sprint 6.6: Language detection
            "language": context.get("language", LanguageCode.ENGLISH).value,
            
            # Sprint 6.6: Skill extraction
            "skills": context.get("skills", []),
            
            # Sprint 6.6: Technology classification
            "technology_category": (
                tech_decision.primary_category 
                if tech_decision and tech_decision.is_tech 
                else None
            ),
            "is_tech_role": tech_decision.is_tech if tech_decision else False,
            
            # ✅ FIX: tech_confidence must be None for non-tech jobs
            "tech_confidence": (
                tech_decision.confidence 
                if tech_decision and tech_decision.is_tech 
                else None
            ),
            
            "matched_tech_terms": context.get("matched_tech_terms", []),
            
            # Sprint 6.6: Geographic enrichment
            "country_code": context.get("country_code"),
            "currency": context.get("currency"),
            "normalized_salary_min": context.get("normalized_min"),
            "normalized_salary_max": context.get("normalized_max"),
        })
        
        # Create enriched job
        context["enriched_job"] = JobEnriched(**job_data)
    
    
    def _record_timing(self, key: str, elapsed_ms: float) -> None:
        """Record a timing measurement (running statistics)."""
        if key not in self._timing_stats:
            return

        stats = self._timing_stats[key]
        stats["count"] += 1
        stats["total_ms"] += elapsed_ms
        stats["min_ms"] = min(stats["min_ms"], elapsed_ms)
        stats["max_ms"] = max(stats["max_ms"], elapsed_ms)

    def enrich_batch(self, jobs: List[JobTransformed]) -> List[Any]:
        """
        Enrich a batch of jobs.

        Args:
            jobs: List of transformed jobs

        Returns:
            List[JobEnriched]: List of enriched jobs (failed jobs are skipped)
        """
        enriched = []
        total = len(jobs)

        for i, job in enumerate(jobs):
            try:
                enriched.append(self.enrich(job))
            except Exception as e:
                logger.error(
                    "Failed to enrich job %s (%d/%d): %s",
                    job.source_id,
                    i + 1,
                    total,
                    e,
                    exc_info=True,
                )

        logger.info("Enriched %d/%d jobs successfully", len(enriched), total)
        return enriched

    def get_timing_stats(self) -> Dict[str, Dict[str, float]]:
        """
        Get timing statistics.

        Returns:
            Dict with avg_ms, min_ms, max_ms, count for each step
        """
        stats = {}
        for key, data in self._timing_stats.items():
            count = data["count"]
            if count > 0:
                stats[key] = {
                    "avg_ms": data["total_ms"] / count,
                    "min_ms": data["min_ms"],
                    "max_ms": data["max_ms"],
                    "count": count,
                }
            else:
                stats[key] = {"avg_ms": 0, "min_ms": 0, "max_ms": 0, "count": 0}
        return stats

    def get_pipeline_stats(self) -> dict:
        """
        Get comprehensive pipeline statistics.

        Returns:
            dict: Pipeline statistics including cache stats and timing
        """
        from app.etl.enrichment.language_detector import get_language_cache_stats

        return {
            "language_cache": get_language_cache_stats(),
            "timing_stats": self.get_timing_stats(),
            "normalize_salaries": self.normalize_salaries,
            "language_detection_enabled": self.language_detection_enabled,
        }

    def reset_timing_stats(self) -> None:
        """Reset all timing statistics."""
        for key in self._timing_stats:
            self._timing_stats[key] = {
                "count": 0,
                "total_ms": 0,
                "min_ms": float("inf"),
                "max_ms": 0,
            }


# ============================================================
# Convenience Functions
# ============================================================

_enricher: Optional[Enricher] = None


def get_enricher() -> Enricher:
    """Get a singleton instance of the enricher."""
    global _enricher
    if _enricher is None:
        _enricher = Enricher()
    return _enricher


def enrich_job(job: JobTransformed) -> Any:
    """Convenience function to enrich a single job."""
    return get_enricher().enrich(job)


def enrich_jobs(jobs: List[JobTransformed]) -> List[Any]:
    """Convenience function to enrich a batch of jobs."""
    return get_enricher().enrich_batch(jobs)


# ============================================================
# Export
# ============================================================

__all__ = [
    "EnrichmentStep",
    "Enricher",
    "get_enricher",
    "enrich_job",
    "enrich_jobs",
]