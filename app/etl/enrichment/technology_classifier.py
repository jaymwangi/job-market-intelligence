"""Technology classification - business logic."""

from typing import List
from app.etl.enrichment.data.technology_categories import (
    TechnologyCategory,
    CATEGORY_KEYWORDS,
)


class TechnologyClassifier:
    """Classify jobs into technology categories."""

    def __init__(self):
        self.categories = CATEGORY_KEYWORDS

    def classify(self, title: str, skills: List[str]) -> TechnologyCategory:
        """Classify job into technology category."""
        text = f"{title.lower()} {' '.join(skills).lower()}"

        for category, keywords in self.categories.items():
            for keyword in keywords:
                if keyword in text:
                    return category

        return TechnologyCategory.OTHER

    def is_tech_role(self, title: str, skills: List[str]) -> bool:
        """Determine if this is a technology role."""
        category = self.classify(title, skills)
        return category != TechnologyCategory.OTHER

    def is_tech_role_with_category(self, category: TechnologyCategory) -> bool:
        """
        Determine if a category is a technology role.

        This avoids double classification when you already have the category.
        """
        return category != TechnologyCategory.OTHER