import pytest

from app.etl.enrichment.currency_normalizer import CurrencyNormalizer


class TestCurrencyNormalizer:
    @pytest.fixture
    def normalizer(self):
        return CurrencyNormalizer()

    def test_initializes_with_currency_data(self, normalizer):
        assert normalizer.currency_map
        assert normalizer.reference_rates
        assert normalizer.BASE_CURRENCY == "USD"

    @pytest.mark.parametrize("value", [None, ""])
    def test_normalize_empty_values_returns_none(self, normalizer, value):
        assert normalizer.normalize(value) is None

    def test_normalize_strips_and_uppercases_currency(self, normalizer):
        assert normalizer.normalize("  usd  ") == "USD"

    def test_normalize_uses_currency_alias_map(self, normalizer):
        # Pick an alias that actually exists in the configured map.
        alias, expected = next(
            (key, value)
            for key, value in normalizer.currency_map.items()
            if key != value
        )
        assert normalizer.normalize(alias) == expected

    def test_normalize_unknown_currency_returns_normalized_value(self, normalizer):
        assert normalizer.normalize(" xyz ") == "XYZ"

    @pytest.mark.parametrize(
        ("country", "currency"),
        [
            ("GB", "GBP"),
            ("US", "USD"),
            ("DE", "EUR"),
            ("FR", "EUR"),
            ("CA", "CAD"),
            ("AU", "AUD"),
            ("IN", "INR"),
            ("SG", "SGD"),
            ("NL", "EUR"),
            ("ES", "EUR"),
            ("IT", "EUR"),
            ("SE", "SEK"),
            ("CH", "CHF"),
            ("IE", "EUR"),
            ("NZ", "NZD"),
        ],
    )
    def test_infer_currency_from_country(self, normalizer, country, currency):
        assert normalizer.infer_currency_from_country(country) == currency

    def test_infer_currency_from_country_is_case_insensitive(self, normalizer):
        assert normalizer.infer_currency_from_country("gb") == "GBP"

    def test_infer_currency_from_unknown_country_returns_none(self, normalizer):
        assert normalizer.infer_currency_from_country("XX") is None

    def test_convert_returns_amount_when_currency_is_missing(self, normalizer):
        assert normalizer.convert(100.0, "", "USD") == 100.0

    def test_convert_returns_amount_for_same_currency(self, normalizer):
        assert normalizer.convert(100.0, "USD", "USD") == 100.0

    def test_convert_returns_amount_when_source_rate_is_missing(self, normalizer):
        assert normalizer.convert(100.0, "XYZ", "USD") == 100.0

    def test_convert_returns_amount_when_target_rate_is_missing(self, normalizer):
        assert normalizer.convert(100.0, "USD", "XYZ") == 100.0

    def test_convert_converts_between_known_currencies(self, normalizer):
        result = normalizer.convert(100.0, "GBP", "EUR")

        expected = 100.0 * (
            normalizer.reference_rates["GBP"]
            / normalizer.reference_rates["EUR"]
        )

        assert result == pytest.approx(expected)


    def test_to_usd_delegates_to_convert(self, normalizer):
        result = normalizer.to_usd(100.0, "GBP")

        expected = normalizer.convert(100.0, "GBP", "USD")

        assert result == pytest.approx(expected)
