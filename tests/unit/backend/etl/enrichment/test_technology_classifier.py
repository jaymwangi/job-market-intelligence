"""Unit tests for the technology classifier."""

from app.etl.enrichment.data.technology_categories import TechnologyCategory
from app.etl.enrichment.technology_classifier import TechnologyClassifier


class TestTechnologyClassifier:
    def test_initializes_with_category_keywords(self):
        classifier = TechnologyClassifier()

        assert classifier.categories
        assert TechnologyCategory.BACKEND in classifier.categories

    def test_keyword_matches_single_word(self):
        classifier = TechnologyClassifier()

        assert classifier._keyword_matches("python developer", "python") is True
        assert classifier._keyword_matches("python developer", "PYTHON") is True

    def test_keyword_matches_rejects_partial_word(self):
        classifier = TechnologyClassifier()

        assert classifier._keyword_matches("typescript developer", "script") is False
        assert classifier._keyword_matches("developer", "dev") is False

    def test_keyword_matches_multi_word_keyword(self):
        classifier = TechnologyClassifier()

        assert (
            classifier._keyword_matches(
                "senior software engineer with machine learning experience",
                "machine learning",
            )
            is True
        )

    def test_keyword_matches_empty_keyword(self):
        classifier = TechnologyClassifier()

        assert classifier._keyword_matches("python developer", "") is False
        assert classifier._keyword_matches("python developer", "   ") is False

    def test_classify_backend_role(self):
        classifier = TechnologyClassifier()

        result = classifier.classify(
            "Senior Backend Developer",
            ["Python", "Django"],
        )

        assert result == TechnologyCategory.BACKEND

    def test_classify_frontend_role(self):
        classifier = TechnologyClassifier()

        result = classifier.classify(
            "Frontend Developer",
            ["React", "TypeScript"],
        )

        assert result == TechnologyCategory.FRONTEND

    def test_classify_full_stack_role(self):
        classifier = TechnologyClassifier()

        result = classifier.classify(
            "Full Stack Developer",
            [],
        )

        assert result == TechnologyCategory.FULL_STACK

    def test_classify_data_engineering_role(self):
        classifier = TechnologyClassifier()

        result = classifier.classify(
            "Data Engineer",
            ["Airflow", "Spark"],
        )

        assert result == TechnologyCategory.DATA_ENGINEERING

    def test_classify_unknown_role_as_other(self):
        classifier = TechnologyClassifier()

        result = classifier.classify(
            "Administrative Assistant",
            ["Microsoft Office"],
        )

        assert result == TechnologyCategory.OTHER

    def test_classify_uses_skills_when_title_has_no_match(self):
        classifier = TechnologyClassifier()

        result = classifier.classify(
            "Engineer",
            ["React", "TypeScript"],
        )

        assert result == TechnologyCategory.FRONTEND

    def test_is_tech_role_returns_true_for_technology_category(self):
        classifier = TechnologyClassifier()

        assert (
            classifier.is_tech_role(
                "Backend Developer",
                ["Python"],
            )
            is True
        )

    def test_is_tech_role_returns_false_for_other(self):
        classifier = TechnologyClassifier()

        assert (
            classifier.is_tech_role(
                "Office Administrator",
                ["Microsoft Office"],
            )
            is False
        )

    def test_is_tech_role_with_category(self):
        classifier = TechnologyClassifier()

        assert classifier.is_tech_role_with_category(TechnologyCategory.BACKEND) is True

        assert classifier.is_tech_role_with_category(TechnologyCategory.OTHER) is False
