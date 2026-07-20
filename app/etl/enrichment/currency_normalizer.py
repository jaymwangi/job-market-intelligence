"""Currency normalization - business logic, not configuration."""

from typing import Optional
from app.etl.enrichment.data.currency_map import CURRENCY_MAP, REFERENCE_RATES


class CurrencyNormalizer:
    """
    Normalize currency codes and convert between currencies.

    All rates are relative to USD (base currency).
    Conversion: amount * (rate[from_currency] / rate[to_currency])
    """

    # Base currency for all conversions
    BASE_CURRENCY = "USD"

    def __init__(self):
        self.currency_map = CURRENCY_MAP
        self.reference_rates = REFERENCE_RATES

    def normalize(self, currency: Optional[str]) -> Optional[str]:
        """Normalize currency to ISO 3-letter format."""
        if not currency:
            return None

        normalized = currency.strip().upper()
        return self.currency_map.get(normalized, normalized)

    def infer_currency_from_country(self, country_code: str) -> Optional[str]:
        """
        Infer currency from country code.
        
        Args:
            country_code: ISO 2-letter country code
            
        Returns:
            ISO 3-letter currency code or None if unknown
        """
        country_currency_map = {
            "GB": "GBP",
            "US": "USD",
            "DE": "EUR",
            "FR": "EUR",
            "CA": "CAD",
            "AU": "AUD",
            "IN": "INR",
            "SG": "SGD",
            "NL": "EUR",
            "ES": "EUR",
            "IT": "EUR",
            "SE": "SEK",
            "CH": "CHF",
            "IE": "EUR",
            "NZ": "NZD",
        }
        return country_currency_map.get(country_code.upper())

    def convert(
        self,
        amount: float,
        from_currency: str,
        to_currency: str = "USD",
    ) -> Optional[float]:
        """
        Convert currency using reference rates.

        Args:
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code (default: USD)

        Returns:
            Converted amount or None if conversion fails

        Note: These are static reference rates for normalization purposes.
        For production use, consider integrating a live currency API.
        """
        if amount is None:
            return None

        # Normalize currencies
        from_curr = self.normalize(from_currency)
        to_curr = self.normalize(to_currency)

        if not from_curr or not to_curr:
            return amount

        # If same currency, return original
        if from_curr == to_curr:
            return amount

        # Get rates (all relative to USD)
        from_rate = self.reference_rates.get(from_curr)
        to_rate = self.reference_rates.get(to_curr)

        if from_rate is None or to_rate is None:
            # No rate available, return original
            return amount

        # Convert: amount * (from_rate / to_rate)
        return amount * (from_rate / to_rate)

    def to_usd(self, amount: float, from_currency: str) -> Optional[float]:
        """Convenience method - convert to USD."""
        return self.convert(amount, from_currency, "USD")