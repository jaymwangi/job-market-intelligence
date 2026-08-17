# app/etl/enrichment/taxonomy.py

from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple
from app.etl.enrichment.classification_config import CategoryConfig, CategoryRole


class CategoryTaxonomy:
    """Manages category hierarchy and relationships."""

    def __init__(self, categories: Dict[str, CategoryConfig]):
        self.categories = categories
        
        # Build lookup structures
        self.children: Dict[str, Set[str]] = defaultdict(set)
        self.parents: Dict[str, Optional[str]] = {}
        self.roles: Dict[str, CategoryRole] = {}
        
        for name, cfg in categories.items():
            self.parents[name] = cfg.parent
            self.roles[name] = cfg.role
            if cfg.parent:
                self.children[cfg.parent].add(name)

    def competes(self, first: str, second: str) -> bool:
        """
        Determine if two categories should compete.

        Rules:
        - A category does not compete with its parent
        - A category does not compete with its children
        - Sibling categories DO compete
        """
        if first == second:
            return False

        # Check if second is the parent of first
        if self.parents.get(first) == second:
            return False

        # Check if first is the parent of second
        if self.parents.get(second) == first:
            return False

        return True

    def competing_categories(
        self,
        primary_category: str,
        sorted_categories: List[Tuple[str, float]],
    ) -> List[Tuple[str, float]]:
        """
        Get categories that should legitimately compete with the primary.
        """
        if primary_category not in self.categories:
            return sorted_categories[1:]

        return [
            (cat, score)
            for cat, score in sorted_categories[1:]
            if self.competes(primary_category, cat)
        ]

    def is_parent(self, category: str) -> bool:
        """Check if a category is a parent category."""
        return self.roles.get(category) == CategoryRole.PARENT

    def is_specialization(self, category: str) -> bool:
        """Check if a category is a specialization."""
        return self.roles.get(category) == CategoryRole.SPECIALIZATION

    def get_children(self, category: str) -> List[str]:
        """Get all children of a category."""
        return list(self.children.get(category, set()))

    def get_parent(self, category: str) -> Optional[str]:
        """Get the parent of a category."""
        return self.parents.get(category)