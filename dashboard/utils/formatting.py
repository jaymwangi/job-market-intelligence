# dashboard/utils/formatting.py
"""Formatting utilities."""

import re
from typing import Optional


def format_currency(
    amount: Optional[float], currency: str = "USD", locale: str = "en_US"
) -> str:
    """Format currency values."""
    if amount is None:
        return "N/A"

    # Simple formatting without locale dependency
    if currency.upper() in ["USD", "CAD", "AUD", "NZD", "SGD"]:
        symbol = "$"
    elif currency.upper() == "EUR":
        symbol = "€"
    elif currency.upper() == "GBP":
        symbol = "£"
    else:
        symbol = currency

    return f"{symbol}{amount:,.0f}"


def format_number(num: Optional[float], decimals: int = 0) -> str:
    """Format numbers with commas."""
    if num is None:
        return "N/A"

    if decimals == 0:
        return f"{num:,.0f}"
    else:
        return f"{num:,.{decimals}f}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format percentage."""
    return f"{value:.{decimals}f}%"


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def to_snake_case(text: str) -> str:
    """Convert text to snake_case."""
    text = re.sub(r"([A-Z])", r"_\1", text).lower()
    text = re.sub(r"[^a-z0-9_]", "_", text)
    text = re.sub(r"_+", "_", text)
    return text.strip("_")


def to_title_case(text: str) -> str:
    """Convert text to title case."""
    text = re.sub(r"_", " ", text)
    return text.title()
