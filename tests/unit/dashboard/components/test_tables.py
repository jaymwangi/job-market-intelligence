"""Unit tests for dashboard tables component."""

from unittest.mock import patch

from dashboard.components.tables import render_jobs_table


class TestTables:
    """Test suite for tables component."""

    @patch("dashboard.components.tables.st")
    def test_render_jobs_table_empty(self, mock_st):
        """Test empty jobs list renders nothing."""
        render_jobs_table([])

        mock_st.container.assert_not_called()