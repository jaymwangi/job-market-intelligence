"""Technology classification - business logic."""

import re

from app.etl.enrichment.data.technology_categories import (
    CATEGORY_KEYWORDS,
    TechnologyCategory,
)


class TechnologyClassifier:
    """Classify jobs into technology categories."""

    def __init__(self):
        self.categories = CATEGORY_KEYWORDS

    @staticmethod
    def _keyword_matches(text: str, keyword: str) -> bool:
        """Check whether a keyword appears as a standalone term."""
        keyword = keyword.strip().lower()

        if not keyword:
            return False

        if " " in keyword:
            return keyword in text

        return bool(
            re.search(
                rf"(?<!\w){re.escape(keyword)}(?!\w)",
                text,
            )
        )

    def classify(self, title: str, skills: list[str]) -> TechnologyCategory:
        """Classify job into technology category."""
        text = f"{title.lower()} {' '.join(skills).lower()}"

        for category, keywords in self.categories.items():
            for keyword in keywords:
                if self._keyword_matches(text, keyword):
                    return category

        return TechnologyCategory.OTHER

    def is_tech_role(self, title: str, skills: list[str]) -> bool:
        """Determine if this is a technology role."""
        category = self.classify(title, skills)
        return category != TechnologyCategory.OTHER

    def is_tech_role_with_category(self, category: TechnologyCategory) -> bool:
        """
        Determine if a category is a technology role.

        This avoids double classification when you already have the category.
        """
        return category != TechnologyCategory.OTHER
