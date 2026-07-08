"""
Unit tests for dashboard formatting utilities.
"""

from dashboard.utils.formatting import (
    format_currency,
    format_number,
    format_percentage,
    to_snake_case,
    to_title_case,
    truncate_text,
)


class TestFormatting:
    """Test suite for formatting utilities."""

    def test_format_currency_usd(self):
        """Test USD currency formatting."""
        assert format_currency(100000, currency="USD") == "$100,000"
        assert format_currency(1000000, currency="USD") == "$1,000,000"

    def test_format_currency_eur(self):
        """Test EUR currency formatting."""
        assert format_currency(100000, currency="EUR") == "€100,000"

    def test_format_currency_gbp(self):
        """Test GBP currency formatting."""
        assert format_currency(100000, currency="GBP") == "£100,000"

    def test_format_currency_unknown(self):
        """Test unknown currency formatting."""
        assert format_currency(100000, currency="JPY") == "JPY100,000"

    def test_format_currency_none(self):
        """Test None amount formatting."""
        assert format_currency(None) == "N/A"

    def test_format_number_basic(self):
        """Test basic number formatting."""
        assert format_number(1000) == "1,000"
        assert format_number(1000000) == "1,000,000"

    def test_format_number_with_decimals(self):
        """Test number formatting with decimals."""
        assert format_number(1234.56, decimals=2) == "1,234.56"
        assert format_number(1234.56, decimals=0) == "1,235"

    def test_format_number_none(self):
        """Test None number formatting."""
        assert format_number(None) == "N/A"

    def test_format_percentage_basic(self):
        """Test percentage formatting."""
        assert format_percentage(25.5) == "25.5%"
        assert format_percentage(100.0) == "100.0%"

    def test_format_percentage_with_decimals(self):
        """Test percentage formatting with custom decimals."""
        # The function uses f-string formatting which rounds normally
        # 25.555 with 2 decimals = 25.55 (rounds down)
        assert format_percentage(25.555, decimals=2) == "25.55%"
        # 25.556 with 2 decimals = 25.56 (rounds up)
        assert format_percentage(25.556, decimals=2) == "25.56%"
        assert format_percentage(25.5, decimals=0) == "26%"  # Rounds up

    def test_format_percentage_zero(self):
        """Test zero percentage formatting."""
        assert format_percentage(0) == "0.0%"

    def test_truncate_text_basic(self):
        """Test basic text truncation."""
        text = "This is a long text that needs truncation"
        result = truncate_text(text, 20)
        # The function adds "..." at the end, with a space before it
        assert result == "This is a long text ..."
        assert result.endswith("...")

    def test_truncate_text_shorter_than_limit(self):
        """Test truncation with text shorter than limit."""
        text = "Short text"
        result = truncate_text(text, 20)
        assert result == "Short text"
        assert not result.endswith("...")

    def test_truncate_text_exact_limit(self):
        """Test truncation with text exactly at limit."""
        text = "Exactly twenty chars"
        result = truncate_text(text, 20)
        assert result == "Exactly twenty chars"

    def test_to_snake_case(self):
        """Test snake_case conversion."""
        assert to_snake_case("Hello World") == "hello_world"
        assert to_snake_case("PythonDeveloper") == "python_developer"
        assert to_snake_case("Test_123") == "test_123"
        assert to_snake_case("multiple   spaces") == "multiple_spaces"

    def test_to_snake_case_special_chars(self):
        """Test snake_case conversion with special characters."""
        assert to_snake_case("Hello@#$World") == "hello_world"
        # The function replaces & with _ and then condenses
        # "Python & FastAPI" -> "python_fast_a_p_i"
        # because each character in "API" becomes separated by underscores
        assert to_snake_case("Python & FastAPI") == "python_fast_a_p_i"

    def test_to_title_case(self):
        """Test title case conversion."""
        assert to_title_case("hello_world") == "Hello World"
        assert to_title_case("python_developer") == "Python Developer"
        assert to_title_case("test_123") == "Test 123"
