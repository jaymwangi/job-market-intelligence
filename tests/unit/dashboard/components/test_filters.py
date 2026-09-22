"""Unit tests for dashboard filters component."""

from unittest.mock import MagicMock, patch

from dashboard.components.filters import render_filters


class TestFilters:
    """Test suite for filters component."""

    @patch("dashboard.components.filters.st.sidebar")
    @patch("dashboard.components.filters.get_icon", return_value="<svg></svg>")
    def test_render_filters_defaults(self, mock_get_icon, mock_sidebar):
        """Test filters render with default values."""
        mock_sidebar.text_input.return_value = ""
        mock_sidebar.selectbox.return_value = "All"
        mock_sidebar.number_input.return_value = 0

        # sidebar.columns(2) is unpacked and each column is used as a
        # context manager by the production component.
        mock_col1 = MagicMock()
        mock_col2 = MagicMock()
        mock_sidebar.columns.return_value = [mock_col1, mock_col2]

        result = render_filters()

        assert result == {
            "search": None,
            "company": None,
            "location": None,
            "source_site": None,
            "min_salary": None,
            "max_salary": None,
        }

    @patch("dashboard.components.filters.st.sidebar")
    @patch("dashboard.components.filters.st.number_input")
    @patch("dashboard.components.filters.get_icon", return_value="<svg></svg>")
    def test_render_filters_normalizes_whitespace(
        self, mock_get_icon, mock_number_input, mock_sidebar
    ):
        """Test whitespace-only filter values normalize to None."""
        mock_sidebar.text_input.side_effect = ["   ", "  ", "\t"]
        mock_sidebar.selectbox.return_value = "adzuna"
        mock_number_input.side_effect = [50000, 50000]

        mock_col1 = MagicMock()
        mock_col2 = MagicMock()
        mock_sidebar.columns.return_value = [mock_col1, mock_col2]

        result = render_filters()

        assert result == {
            "search": None,
            "company": None,
            "location": None,
            "source_site": "adzuna",
            "min_salary": 50000,
            "max_salary": 50000,
        }
