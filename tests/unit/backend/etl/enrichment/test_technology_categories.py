import pytest

from app.etl.enrichment.data.technology_categories import (
    ALL_CATEGORY_KEYWORDS,
    CATEGORY_DISPLAY_NAMES,
    CATEGORY_KEYWORDS,
    CATEGORY_WEIGHTS,
    SKILL_DISPLAY_NAMES,
    TechnologyCategory,
    find_category_for_keyword,
    get_category_display_name,
    get_category_keywords,
    get_category_weight,
    get_skill_display_name,
    is_tech_keyword,
    normalize_skills_list,
)


class TestTechnologyCategory:
    def test_contains_expected_categories(self):
        assert TechnologyCategory.BACKEND.value == "backend"
        assert TechnologyCategory.ML_AI.value == "ml_ai"
        assert TechnologyCategory.SYSTEMS.value == "systems"
        assert TechnologyCategory.SOLUTIONS.value == "solutions"
        assert TechnologyCategory.SUPPORT.value == "support"
        assert TechnologyCategory.MANAGEMENT.value == "management"

    def test_display_names_exist_for_all_categories(self):
        assert set(CATEGORY_DISPLAY_NAMES) == set(TechnologyCategory)

    def test_weights_exist_for_all_categories(self):
        assert set(CATEGORY_WEIGHTS) == set(TechnologyCategory)

    def test_keywords_exist_for_all_categories(self):
        assert set(CATEGORY_KEYWORDS) == set(TechnologyCategory)

    def test_all_category_keywords_contains_known_keywords(self):
        assert "python" in ALL_CATEGORY_KEYWORDS
        assert "kubernetes" in ALL_CATEGORY_KEYWORDS
        assert "technical support" in ALL_CATEGORY_KEYWORDS


class TestCategoryHelpers:
    def test_get_category_display_name_with_enum(self):
        assert (
            get_category_display_name(TechnologyCategory.BACKEND)
            == "Backend Development"
        )

    def test_get_category_display_name_with_valid_string(self):
        assert get_category_display_name("backend") == "Backend Development"

    def test_get_category_display_name_with_unknown_string(self):
        assert get_category_display_name("custom_category") == "Custom_Category"

    def test_get_category_weight_with_enum(self):
        assert get_category_weight(TechnologyCategory.FULL_STACK) == 1.2

    def test_get_category_weight_with_valid_string(self):
        assert get_category_weight("data_science") == 1.2

    def test_get_category_weight_with_unknown_string(self):
        assert get_category_weight("custom_category") == 1.0

    def test_get_category_keywords_with_enum(self):
        keywords = get_category_keywords(TechnologyCategory.BACKEND)

        assert "python" in keywords
        assert "django" in keywords
        assert isinstance(keywords, list)

    def test_get_category_keywords_with_valid_string(self):
        keywords = get_category_keywords("frontend")

        assert "react" in keywords
        assert "typescript" in keywords

    def test_get_category_keywords_with_unknown_string(self):
        assert get_category_keywords("custom_category") == []


class TestKeywordHelpers:
    def test_is_tech_keyword_is_case_insensitive(self):
        assert is_tech_keyword("python") is True
        assert is_tech_keyword("PYTHON") is True
        assert is_tech_keyword("Kubernetes") is True

    def test_is_tech_keyword_returns_false_for_unknown_keyword(self):
        assert is_tech_keyword("not-a-real-technology") is False

    def test_find_category_for_keyword_is_case_insensitive(self):
        assert find_category_for_keyword("Python") == TechnologyCategory.BACKEND
        assert find_category_for_keyword("PYTHON") == TechnologyCategory.BACKEND

    def test_find_category_for_keyword_returns_none_for_unknown(self):
        assert find_category_for_keyword("not-a-real-technology") is None


class TestSkillDisplayHelpers:
    def test_get_skill_display_name_known_skill(self):
        assert get_skill_display_name("python") == "Python"
        assert get_skill_display_name("aws") == "AWS"
        assert get_skill_display_name("sql") == "SQL"

    def test_get_skill_display_name_strips_whitespace(self):
        assert get_skill_display_name("  python  ") == "Python"

    def test_get_skill_display_name_is_case_insensitive(self):
        assert get_skill_display_name("PYTHON") == "Python"

    def test_get_skill_display_name_unknown_skill(self):
        assert get_skill_display_name("some_new_skill") == "Some_New_Skill"

    def test_normalize_skills_list_handles_empty_list(self):
        assert normalize_skills_list([]) == []

    def test_normalize_skills_list_removes_empty_values(self):
        assert normalize_skills_list(
            ["python", "", "   ", "sql"]
        ) == ["Python", "SQL"]

    def test_normalize_skills_list_normalizes_and_sorts(self):
        result = normalize_skills_list(
            [" python ", "AWS", "sql", "docker"]
        )

        assert result == ["AWS", "Docker", "Python", "SQL"]

    def test_normalize_skills_list_removes_duplicates(self):
        result = normalize_skills_list(
            ["python", "Python", " PYTHON ", "aws", "AWS"]
        )

        assert result == ["AWS", "Python"]

    def test_normalize_skills_list_handles_unknown_skills(self):
        result = normalize_skills_list(
            ["python", "my_custom_skill"]
        )

        assert result == ["My_Custom_Skill", "Python"]
