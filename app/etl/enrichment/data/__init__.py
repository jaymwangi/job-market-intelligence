"""Static reference data for enrichment."""

from app.etl.enrichment.data.country_map import COUNTRY_MAP, COUNTRY_NAMES
from app.etl.enrichment.data.currency_map import CURRENCY_MAP, REFERENCE_RATES
from app.etl.enrichment.data.technology_categories import (
    TechnologyCategory,
    CATEGORY_KEYWORDS,
)
from app.etl.enrichment.data.skills import TECH_KEYWORDS

__all__ = [
    "COUNTRY_MAP",
    "COUNTRY_NAMES",
    "CURRENCY_MAP",
    "REFERENCE_RATES",
    "TechnologyCategory",
    "CATEGORY_KEYWORDS",
    "TECH_KEYWORDS",
]