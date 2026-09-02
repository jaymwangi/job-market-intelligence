"""Unit tests for dashboard metrics component."""

from unittest.mock import MagicMock, patch

from dashboard.components.metrics import MetricCardData, render_metric_row


class TestMetrics:
    """Test suite for dashboard metrics component."""

    def test_metric_card_data(self):
        """Test metric card data model."""
        data = MetricCardData(
            title="Total Jobs",
            value=1000,
            icon="jobs_metric",
        )

        assert data.title == "Total Jobs"
        assert data.value == 1000
        assert data.icon == "jobs_metric"

    @patch("dashboard.components.metrics.render_metric_card")
    @patch("dashboard.components.metrics.st.columns")
    def test_render_metric_row(self, mock_columns, mock_render_card):
        """Test rendering a row of metric cards."""
        # Production code uses each column as a context manager:
        # with cols[i]:
        mock_col1 = MagicMock()
        mock_col2 = MagicMock()

        mock_columns.return_value = [mock_col1, mock_col2]

        metrics = [
            MetricCardData(title="Jobs", value=100),
            MetricCardData(title="Companies", value=50),
        ]

        render_metric_row(metrics, columns=2)

        assert mock_render_card.call_count == 2
        mock_columns.assert_called_once_with(2)