"""Country normalization - business logic, not configuration."""

from typing import Optional
from app.etl.enrichment.data.country_map import COUNTRY_MAP, COUNTRY_NAMES


class CountryNormalizer:
    """Normalize country codes and names."""

    def __init__(self):
        # Data loaded from data module
        self.country_map = COUNTRY_MAP
        self.country_names = COUNTRY_NAMES

    def normalize(self, country_str: Optional[str]) -> Optional[str]:
        """
        Normalize country to ISO 2-letter format.

        Args:
            country_str: Country name, code, or location string

        Returns:
            ISO 2-letter code or None if not found
        """
        if not country_str:
            return None

        # Clean input
        normalized = country_str.strip().lower()

        # Try direct match
        if normalized in self.country_map:
            return self.country_map[normalized]

        # Try to extract country from location string
        # e.g., "London, UK" -> "UK"
        parts = [p.strip().lower() for p in normalized.split(",")]
        for part in parts:
            if part in self.country_map:
                return self.country_map[part]

        # Try to extract from common patterns
        # e.g., "London (UK)" -> "UK"
        import re
        patterns = [
            r"\(([a-z]{2})\)",  # (GB)
            r"\[([a-z]{2})\]",  # [GB]
            r",\s*([a-z]{2})$",  # , GB
        ]
        for pattern in patterns:
            match = re.search(pattern, normalized)
            if match:
                code = match.group(1)
                if code in self.country_map:
                    return self.country_map[code]

        return None

    def get_country_name(self, country_code: str) -> str:
        """Get full country name from ISO code."""
        return self.country_names.get(country_code.upper(), country_code)