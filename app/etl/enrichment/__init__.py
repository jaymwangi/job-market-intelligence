"""Enrichment package - exposes public API.

This package provides all enrichment components for the ETL pipeline:
- Language detection
- Skill extraction
- Technology classification and scoring
- Country normalization
- Currency normalization
- Enrichment orchestration

Sprint 6.6 adds:
- Language detection (LanguageDetector, detect_language)
- Technology scoring (TechnologyScorer, TechScoreResult, score_job)
- Evidence tracking (Evidence, MatchSource)
- Enhanced enricher with timing metrics and step-based architecture

Version: 2.0.0
Author: James Mwangi
License: MIT

Public API:
    Primary entry points (intended for most users):
        - Enricher: Orchestrates the enrichment pipeline
        - TechnologyScorer: Scores job postings for technology roles
        - LanguageDetector: Detects language from text
        - SkillExtractor: Extracts skills from job postings
        - CountryNormalizer: Normalizes country codes
        - CurrencyNormalizer: Normalizes currency codes
        - enrich_job: Convenience function to enrich a single job
        - enrich_jobs: Convenience function to enrich a batch of jobs
        - score_job: Convenience function to score a job
        - detect_language: Convenience function to detect language

    Advanced/Internal (used primarily for configuration):
        - get_config: Gets the loaded configuration
        - reload_config: Reloads configuration
        - get_scorer: Gets the singleton scorer
        - get_detector: Gets the singleton language detector
        - get_enricher: Gets the singleton enricher

    Sprint 6.6 Rich Types:
        - TechScoreResult: Detailed scoring result with explanations
        - Evidence: Individual piece of evidence for classification
        - MatchSource: Source of a match (title, description, skills)

    Deprecated (will be removed in a future version):
        - TechnologyClassifier: Use TechnologyScorer instead
        - TechnologyCategory: Use TechScoreResult.primary_category_str instead
"""

import warnings

# ============================================================
# Version & Metadata
# ============================================================

__version__ = "2.0.0"
__author__ = "James Mwangi"
__license__ = "MIT"


# ============================================================
# Primary Entry Points
# ============================================================

# Enrichment Orchestrator
from app.etl.enrichment.enricher import (
    Enricher,
    get_enricher,
    enrich_job,
    enrich_jobs,
)

# Technology Scoring (Sprint 6.6 - Primary)
from app.etl.enrichment.tech_scorer import (
    TechnologyScorer,
    TechScoreResult,
    MatchSource,
    Evidence,
    get_scorer,
    score_job,
)

# Language Detection (Sprint 6.6)
from app.etl.enrichment.language_detector import (
    LanguageDetector,
    get_detector,
    detect_language,
    is_english,
    detect_language_with_confidence,
    clear_language_cache,
    get_language_cache_stats,
)

# Skill Extraction
from app.etl.enrichment.skill_extractor import SkillExtractor

# Geographic Enrichment
from app.etl.enrichment.country_normalizer import CountryNormalizer
from app.etl.enrichment.currency_normalizer import CurrencyNormalizer


# ============================================================
# Advanced/Internal
# ============================================================

# Configuration - only expose the functions users need
from app.etl.enrichment.classification_config import (
    get_config,
    reload_config,
    ConfigurationError,
)


# ============================================================
# Deprecated (Legacy) - with warnings
# ============================================================

def TechnologyClassifier(*args, **kwargs):
    """Legacy technology classifier - deprecated.

    Deprecated:
        Use TechnologyScorer instead. TechnologyScorer provides
        richer results including confidence scores, evidence,
        explanations, and top categories.

    Migration:
        from app.etl.enrichment import TechnologyScorer, score_job
        result = TechnologyScorer().score(title, description, skills)
        # Or use the convenience function:
        result = score_job(title, description, skills)
    """
    warnings.warn(
        "TechnologyClassifier is deprecated. "
        "Use TechnologyScorer instead for richer results with "
        "confidence scores, evidence, and explanations.",
        DeprecationWarning,
        stacklevel=2,
    )
    from app.etl.enrichment.technology_classifier import (
        TechnologyClassifier as _TechnologyClassifier,
    )
    return _TechnologyClassifier(*args, **kwargs)


# TechnologyCategory is re-exported directly from the legacy module
# without wrapping, to preserve Enum semantics.
# Deprecated: Use TechScoreResult.primary_category_str instead.
from app.etl.enrichment.technology_classifier import (
    TechnologyCategory,
)


# ============================================================
# __all__ - Public API (Fully Alphabetized)
# ============================================================

__all__ = [
    # Primary Entry Points
    "clear_language_cache",
    "ConfigurationError",
    "CountryNormalizer",
    "CurrencyNormalizer",
    "detect_language",
    "detect_language_with_confidence",
    "Enricher",
    "enrich_job",
    "enrich_jobs",
    "Evidence",
    "get_config",
    "get_detector",
    "get_enricher",
    "get_language_cache_stats",
    "get_scorer",
    "is_english",
    "LanguageDetector",
    "MatchSource",
    "reload_config",
    "score_job",
    "SkillExtractor",
    "TechnologyScorer",
    "TechScoreResult",
    
    # Deprecated
    "TechnologyCategory",
    "TechnologyClassifier",
]