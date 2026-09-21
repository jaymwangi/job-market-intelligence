import pytest

from app.etl.enrichment.country_normalizer import CountryNormalizer


class TestCountryNormalizer:
    @pytest.fixture
    def normalizer(self):
        return CountryNormalizer()

    def test_initializes_with_country_data(self, normalizer):
        assert normalizer.country_map
        assert normalizer.country_names

    @pytest.mark.parametrize("value", [None, "", "   "])
    def test_normalize_empty_values_returns_none(self, normalizer, value):
        assert normalizer.normalize(value) is None

    def test_normalize_direct_country_code(self, normalizer):
        assert normalizer.normalize("GB") == "GB"

    def test_normalize_direct_country_name(self, normalizer):
        assert normalizer.normalize("United Kingdom") == "GB"

    def test_normalize_strips_and_lowercases_input(self, normalizer):
        assert normalizer.normalize("  UNITED KINGDOM  ") == "GB"

    def test_normalize_country_from_comma_separated_location(self, normalizer):
        assert normalizer.normalize("London, UK") == "GB"

    def test_normalize_country_from_comma_separated_location_case_insensitive(
        self, normalizer
    ):
        assert normalizer.normalize("London, uK") == "GB"

    def test_normalize_country_from_parentheses(self, normalizer):
        assert normalizer.normalize("London (GB)") == "GB"

    def test_normalize_country_from_square_brackets(self, normalizer):
        assert normalizer.normalize("London [GB]") == "GB"

    def test_normalize_country_from_trailing_comma_code(self, normalizer):
        assert normalizer.normalize("London, GB") == "GB"

    def test_normalize_unknown_country_returns_none(self, normalizer):
        assert normalizer.normalize("Atlantis") is None

    @pytest.mark.parametrize(
        ("code", "expected"),
        [
            ("gb", "United Kingdom"),
            ("GB", "United Kingdom"),
            ("xx", "xx"),
        ],
    )
    def test_get_country_name(self, normalizer, code, expected):
        assert normalizer.get_country_name(code) == expected
