"""Tests for alert components."""

from unittest.mock import MagicMock, Mock, patch

from dashboard.components.alerts import (
    show_api_error,
    show_error,
    show_info,
    show_success,
    show_warning,
)


class TestBasicAlerts:
    """Tests for basic alert components."""

    @patch("dashboard.components.alerts.get_icon")
    @patch("dashboard.components.alerts.st")
    def test_show_error(
        self,
        mock_st: MagicMock,
        mock_get_icon: Mock,
    ) -> None:
        """Render an error alert with the correct icon and role."""
        mock_get_icon.return_value = "<svg>error</svg>"

        show_error("Something went wrong")

        mock_get_icon.assert_called_once_with(
            "error",
            size=18,
            color="#e94560",
        )
        assert mock_st.markdown.call_count == 2

        first_call = mock_st.markdown.call_args_list[0]
        second_call = mock_st.markdown.call_args_list[1]

        assert "Something went wrong" in first_call.args[0]
        assert "<svg>error</svg>" in first_call.args[0]
        assert "role=\"alert\"" in second_call.args[0]
        assert 'aria-label="Error: Something went wrong"' in second_call.args[0]

    @patch("dashboard.components.alerts.get_icon")
    @patch("dashboard.components.alerts.st")
    def test_show_error_custom_role(
        self,
        mock_st: MagicMock,
        mock_get_icon: Mock,
    ) -> None:
        """Render an error alert with a custom accessibility role."""
        show_error("Failed", role="status")

        assert 'role="status"' in mock_st.markdown.call_args_list[1].args[0]

    @patch("dashboard.components.alerts.get_icon")
    @patch("dashboard.components.alerts.st")
    def test_show_success(
        self,
        mock_st: MagicMock,
        mock_get_icon: Mock,
    ) -> None:
        """Render a success alert."""
        mock_get_icon.return_value = "<svg>success</svg>"

        show_success("Saved successfully")

        mock_get_icon.assert_called_once_with(
            "success",
            size=18,
            color="#00b894",
        )
        assert mock_st.markdown.call_count == 2
        assert "Saved successfully" in mock_st.markdown.call_args_list[0].args[0]
        assert "<svg>success</svg>" in mock_st.markdown.call_args_list[0].args[0]
        assert 'role="status"' in mock_st.markdown.call_args_list[1].args[0]
        assert (
            'aria-label="Success: Saved successfully"'
            in mock_st.markdown.call_args_list[1].args[0]
        )

    @patch("dashboard.components.alerts.get_icon")
    @patch("dashboard.components.alerts.st")
    def test_show_warning(
        self,
        mock_st: MagicMock,
        mock_get_icon: Mock,
    ) -> None:
        """Render a warning alert."""
        mock_get_icon.return_value = "<svg>warning</svg>"

        show_warning("Check your filters", role="status")

        mock_get_icon.assert_called_once_with(
            "warning",
            size=18,
            color="#fdcb6e",
        )
        assert mock_st.markdown.call_count == 2
        assert "Check your filters" in mock_st.markdown.call_args_list[0].args[0]
        assert "<svg>warning</svg>" in mock_st.markdown.call_args_list[0].args[0]
        assert 'role="status"' in mock_st.markdown.call_args_list[1].args[0]
        assert (
            'aria-label="Warning: Check your filters"'
            in mock_st.markdown.call_args_list[1].args[0]
        )

    @patch("dashboard.components.alerts.get_icon")
    @patch("dashboard.components.alerts.st")
    def test_show_info(
        self,
        mock_st: MagicMock,
        mock_get_icon: Mock,
    ) -> None:
        """Render an info alert."""
        mock_get_icon.return_value = "<svg>info</svg>"

        show_info("Here is some information")

        mock_get_icon.assert_called_once_with(
            "info",
            size=18,
            color="#0984e3",
        )
        assert mock_st.markdown.call_count == 2
        assert "Here is some information" in mock_st.markdown.call_args_list[0].args[0]
        assert "<svg>info</svg>" in mock_st.markdown.call_args_list[0].args[0]
        assert 'role="status"' in mock_st.markdown.call_args_list[1].args[0]
        assert (
            'aria-label="Info: Here is some information"'
            in mock_st.markdown.call_args_list[1].args[0]
        )


class TestShowApiError:
    """Tests for API error handling."""

    @patch("dashboard.components.alerts.show_error")
    @patch("dashboard.components.alerts.st")
    def test_connection_error(
        self,
        mock_st: MagicMock,
        mock_show_error: Mock,
    ) -> None:
        """Map connection errors to a friendly message."""
        error = Exception("ConnectionError: connection refused")

        show_api_error(error)

        mock_show_error.assert_called_once_with(
            "Unable to connect to the server. Please check your internet connection.",
            "alert",
        )

    @patch("dashboard.components.alerts.show_error")
    @patch("dashboard.components.alerts.st")
    def test_timeout_error(
        self,
        mock_st: MagicMock,
        mock_show_error: Mock,
    ) -> None:
        """Map timeout errors to a friendly message."""
        error = Exception("Request timed out")

        show_api_error(error)

        mock_show_error.assert_called_once_with(
            "The request timed out. Please try again.",
            "alert",
        )

    @patch("dashboard.components.alerts.show_error")
    @patch("dashboard.components.alerts.st")
    def test_not_found_error(
        self,
        mock_st: MagicMock,
        mock_show_error: Mock,
    ) -> None:
        """Map 404 errors to a friendly message."""
        error = Exception("API returned 404")

        show_api_error(error)

        mock_show_error.assert_called_once_with(
            "The requested resource was not found.",
            "alert",
        )

    @patch("dashboard.components.alerts.show_error")
    @patch("dashboard.components.alerts.st")
    def test_server_error(
        self,
        mock_st: MagicMock,
        mock_show_error: Mock,
    ) -> None:
        """Map 500 errors to a friendly message."""
        error = Exception("API returned 500")

        show_api_error(error)

        mock_show_error.assert_called_once_with(
            "The server encountered an error. Please try again later.",
            "alert",
        )

    @patch("dashboard.components.alerts.show_error")
    @patch("dashboard.components.alerts.st")
    def test_generic_error(
        self,
        mock_st: MagicMock,
        mock_show_error: Mock,
    ) -> None:
        """Use the original message for unknown errors."""
        error = ValueError("Invalid response")

        show_api_error(error, role="status")

        mock_show_error.assert_called_once_with(
            "An error occurred: Invalid response",
            "status",
        )

    @patch("dashboard.components.alerts.show_error")
    @patch("dashboard.components.alerts.st")
    def test_shows_error_details(
        self,
        mock_st: MagicMock,
        mock_show_error: Mock,
    ) -> None:
        """Show technical error details inside the expander."""
        error = ValueError("Invalid response")

        show_api_error(error)

        mock_st.expander.assert_called_once_with("🔍 Error Details")

        expander = mock_st.expander.return_value
        expander.__enter__.assert_called_once()
        expander.__exit__.assert_called_once()

        mock_st.code.assert_called_once_with(
            "Type: ValueError\nMessage: Invalid response"
        )
