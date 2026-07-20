"""Currency mapping data - static reference data."""

CURRENCY_MAP = {
    # British Pound
    "GBP": "GBP",
    "£": "GBP",
    "GB": "GBP",
    "POUND": "GBP",
    "POUNDS": "GBP",
    # US Dollar
    "USD": "USD",
    "$": "USD",
    "US": "USD",
    "DOLLAR": "USD",
    "DOLLARS": "USD",
    # Euro
    "EUR": "EUR",
    "€": "EUR",
    "EU": "EUR",
    "EURO": "EUR",
    "EUROS": "EUR",
    # Canadian Dollar
    "CAD": "CAD",
    "CA": "CAD",
    "C$": "CAD",
    # Australian Dollar
    "AUD": "AUD",
    "AU": "AUD",
    "A$": "AUD",
    # Indian Rupee
    "INR": "INR",
    "₹": "INR",
    "RUPEES": "INR",
    # Singapore Dollar
    "SGD": "SGD",
    "S$": "SGD",
    # Swiss Franc
    "CHF": "CHF",
    "SWISS FRANC": "CHF",
    # Swedish Krona
    "SEK": "SEK",
    "SWEDISH KRONA": "SEK",
    # Norwegian Krone
    "NOK": "NOK",
    "NORWEGIAN KRONE": "NOK",
    # Danish Krone
    "DKK": "DKK",
    "DANISH KRONE": "DKK",
    # New Zealand Dollar
    "NZD": "NZD",
    "NZ": "NZD",
}

# Static reference rates (relative to USD)
# These are NOT live rates - they're for normalization only
# Last updated: 2026-07-20
REFERENCE_RATES = {
    "GBP": 1.27,  # 1 GBP = 1.27 USD
    "EUR": 1.09,  # 1 EUR = 1.09 USD
    "CAD": 0.73,  # 1 CAD = 0.73 USD
    "AUD": 0.67,  # 1 AUD = 0.67 USD
    "INR": 0.012,  # 1 INR = 0.012 USD
    "SGD": 0.74,  # 1 SGD = 0.74 USD
    "CHF": 1.12,  # 1 CHF = 1.12 USD
    "SEK": 0.095,  # 1 SEK = 0.095 USD
    "NOK": 0.095,  # 1 NOK = 0.095 USD
    "DKK": 0.146,  # 1 DKK = 0.146 USD
    "NZD": 0.61,  # 1 NZD = 0.61 USD
}