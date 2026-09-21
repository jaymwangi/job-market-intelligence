import re

import pytest

from app.etl.enrichment.title_pattern import TitlePattern


class TestTitlePattern:
    def test_initializes_and_compiles_pattern(self):
        pattern = TitlePattern(r"data\s+scientist")

        assert pattern.pattern == r"data\s+scientist"
        assert pattern.compiled is not None
        assert pattern.categories == ()
        assert pattern.weight == 8.0
        assert pattern.strength == "potential"
        assert pattern.specificity == "medium"

    def test_converts_categories_list_to_tuple(self):
        pattern = TitlePattern(
            "developer",
            categories=["backend", "software"],
        )

        assert pattern.categories == ("backend", "software")

    def test_preserves_tuple_categories(self):
        categories = ("backend", "software")
        pattern = TitlePattern("developer", categories=categories)

        assert pattern.categories is categories

    def test_accepts_precompiled_pattern(self):
        compiled = re.compile("python", re.IGNORECASE)

        pattern = TitlePattern("python", compiled=compiled)

        assert pattern.compiled is compiled

    def test_rejects_non_string_pattern(self):
        with pytest.raises(ValueError, match="Pattern must be a string"):
            TitlePattern(123)  # type: ignore[arg-type]

    def test_rejects_invalid_regex(self):
        with pytest.raises(ValueError, match="Invalid regex pattern"):
            TitlePattern("[")

    def test_matches_matching_title(self):
        pattern = TitlePattern(r"data\s+scientist")

        assert pattern.matches("Senior Data Scientist") is True

    def test_matches_case_insensitively(self):
        pattern = TitlePattern("python developer")

        assert pattern.matches("Senior PYTHON DEVELOPER") is True

    def test_returns_false_for_non_matching_title(self):
        pattern = TitlePattern("python developer")

        assert pattern.matches("Senior Data Scientist") is False

    def test_returns_false_for_empty_title(self):
        pattern = TitlePattern("python")

        assert pattern.matches("") is False

    def test_returns_false_when_pattern_is_not_compiled(self):
        pattern = TitlePattern("python")

        object.__setattr__(pattern, "compiled", None)

        assert pattern.matches("Python Developer") is False

    def test_strength_properties(self):
        assert TitlePattern("x", strength="strong").is_strong is True
        assert TitlePattern("x", strength="potential").is_potential is True
        assert TitlePattern("x", strength="adjacent").is_adjacent is True
        assert TitlePattern("x", strength="ambiguous").is_ambiguous is True

    def test_strength_properties_return_false_for_other_strength(self):
        pattern = TitlePattern("x", strength="strong")

        assert pattern.is_potential is False
        assert pattern.is_adjacent is False
        assert pattern.is_ambiguous is False

    def test_strength_priority_for_known_strengths(self):
        assert TitlePattern("x", strength="strong").strength_priority == 4
        assert TitlePattern("x", strength="potential").strength_priority == 3
        assert TitlePattern("x", strength="adjacent").strength_priority == 2
        assert TitlePattern("x", strength="ambiguous").strength_priority == 1

    def test_strength_priority_for_unknown_strength(self):
        pattern = TitlePattern("x", strength="unknown")

        assert pattern.strength_priority == 0
