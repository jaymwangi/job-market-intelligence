"""Unit tests for the technology category taxonomy."""

from app.etl.enrichment.classification_config import CategoryConfig, CategoryRole
from app.etl.enrichment.taxonomy import CategoryTaxonomy


def make_category(
    category_id: str,
    *,
    parent: str | None = None,
    role: CategoryRole = CategoryRole.STANDALONE,
) -> CategoryConfig:
    return CategoryConfig(
        id=category_id,
        display_name=category_id.title(),
        icon="test",
        color="#000000",
        description=f"Test category: {category_id}",
        family="test",
        is_tech=True,
        weight=1.0,
        parent=parent,
        role=role,
    )


def make_taxonomy() -> CategoryTaxonomy:
    categories = {
        "software": make_category(
            "software",
            role=CategoryRole.PARENT,
        ),
        "backend": make_category(
            "backend",
            parent="software",
            role=CategoryRole.SPECIALIZATION,
        ),
        "frontend": make_category(
            "frontend",
            parent="software",
            role=CategoryRole.SPECIALIZATION,
        ),
        "data": make_category(
            "data",
            role=CategoryRole.PARENT,
        ),
        "analytics": make_category(
            "analytics",
            parent="data",
            role=CategoryRole.SPECIALIZATION,
        ),
        "design": make_category(
            "design",
            role=CategoryRole.STANDALONE,
        ),
    }
    return CategoryTaxonomy(categories)


class TestCategoryTaxonomy:
    def test_builds_parent_child_relationships(self):
        taxonomy = make_taxonomy()

        assert taxonomy.get_parent("backend") == "software"
        assert taxonomy.get_parent("frontend") == "software"
        assert taxonomy.get_parent("analytics") == "data"

        assert set(taxonomy.get_children("software")) == {
            "backend",
            "frontend",
        }
        assert taxonomy.get_children("data") == ["analytics"]

    def test_get_parent_returns_none_for_parent_category(self):
        taxonomy = make_taxonomy()

        assert taxonomy.get_parent("software") is None
        assert taxonomy.get_parent("design") is None

    def test_get_parent_returns_none_for_unknown_category(self):
        taxonomy = make_taxonomy()

        assert taxonomy.get_parent("unknown") is None

    def test_get_children_returns_empty_for_leaf_category(self):
        taxonomy = make_taxonomy()

        assert taxonomy.get_children("backend") == []

    def test_get_children_returns_empty_for_unknown_category(self):
        taxonomy = make_taxonomy()

        assert taxonomy.get_children("unknown") == []

    def test_competes_returns_false_for_same_category(self):
        taxonomy = make_taxonomy()

        assert taxonomy.competes("backend", "backend") is False

    def test_competes_returns_false_for_parent_child_relationship(self):
        taxonomy = make_taxonomy()

        assert taxonomy.competes("software", "backend") is False
        assert taxonomy.competes("backend", "software") is False

    def test_competes_returns_true_for_unrelated_categories(self):
        taxonomy = make_taxonomy()

        assert taxonomy.competes("backend", "frontend") is True
        assert taxonomy.competes("backend", "analytics") is True
        assert taxonomy.competes("software", "data") is True

    def test_competing_categories_filters_parent_child_relationships(self):
        taxonomy = make_taxonomy()

        sorted_categories = [
            ("backend", 10.0),
            ("software", 9.0),
            ("frontend", 8.0),
            ("analytics", 7.0),
            ("design", 6.0),
        ]

        result = taxonomy.competing_categories("backend", sorted_categories)

        assert result == [
            ("frontend", 8.0),
            ("analytics", 7.0),
            ("design", 6.0),
        ]

    def test_competing_categories_unknown_primary_excludes_first_result(self):
        taxonomy = make_taxonomy()

        sorted_categories = [
            ("unknown", 10.0),
            ("backend", 9.0),
            ("frontend", 8.0),
        ]

        result = taxonomy.competing_categories("unknown", sorted_categories)

        assert result == [
            ("backend", 9.0),
            ("frontend", 8.0),
        ]

    def test_is_parent(self):
        taxonomy = make_taxonomy()

        assert taxonomy.is_parent("software") is True
        assert taxonomy.is_parent("data") is True
        assert taxonomy.is_parent("backend") is False
        assert taxonomy.is_parent("design") is False
        assert taxonomy.is_parent("unknown") is False

    def test_is_specialization(self):
        taxonomy = make_taxonomy()

        assert taxonomy.is_specialization("backend") is True
        assert taxonomy.is_specialization("frontend") is True
        assert taxonomy.is_specialization("analytics") is True
        assert taxonomy.is_specialization("software") is False
        assert taxonomy.is_specialization("design") is False
        assert taxonomy.is_specialization("unknown") is False
