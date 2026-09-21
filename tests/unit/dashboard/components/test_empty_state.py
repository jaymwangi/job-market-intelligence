"""Tests for empty state components."""

from unittest.mock import MagicMock, Mock, patch

from dashboard.components.empty_state import (
    _reset_filters_state,
    empty_state_analytics,
    empty_state_jobs,
    render_empty_state,
)


class SessionState(dict):
    """Minimal Streamlit session-state stand-in supporting attributes."""

    def __getattr__(self, name: str) -> object:
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name: str, value: object) -> None:
        self[name] = value


def mock_streamlit_layout(mock_st: MagicMock) -> None:
    """Configure Streamlit layout mocks used by render_empty_state."""
    container = MagicMock()
    mock_st.container.return_value = container

    icon_column = MagicMock()
    text_column = MagicMock()
    mock_st.columns.return_value = (icon_column, text_column)


class TestRenderEmptyState:
    """Tests for render_empty_state."""

    @patch("dashboard.components.empty_state.st")
    def test_renders_default_empty_state(self, mock_st: MagicMock) -> None:
        """Render an empty state with default arguments."""
        mock_streamlit_layout(mock_st)

        render_empty_state()

        mock_st.container.assert_called_once_with(border=True)
        mock_st.columns.assert_called_once_with([1, 4])

    @patch("dashboard.components.empty_state.st")
    def test_renders_title_description_and_icon(
        self,
        mock_st: MagicMock,
    ) -> None:
        """Render custom title, description, and icon."""
        mock_streamlit_layout(mock_st)

        render_empty_state(
            title="Nothing Found",
            description="Try changing your filters.",
            icon="🔎",
        )

        assert mock_st.markdown.call_count >= 2
        mock_st.caption.assert_called_once_with("Try changing your filters.")

    @patch("dashboard.components.empty_state.st")
    def test_skips_description_when_empty(
        self,
        mock_st: MagicMock,
    ) -> None:
        """Do not render a caption when description is empty."""
        mock_streamlit_layout(mock_st)

        render_empty_state(description="")

        mock_st.caption.assert_not_called()

    @patch("dashboard.components.empty_state.st")
    def test_reset_button_not_shown_by_default(
        self,
        mock_st: MagicMock,
    ) -> None:
        """Do not render a reset button unless requested."""
        mock_streamlit_layout(mock_st)

        render_empty_state(show_reset=False)

        mock_st.button.assert_not_called()

    @patch("dashboard.components.empty_state.st")
    @patch("dashboard.components.empty_state._reset_filters_state")
    def test_reset_button_resets_and_reruns(
        self,
        mock_reset: Mock,
        mock_st: MagicMock,
    ) -> None:
        """Reset filters and rerun when reset button is clicked."""
        mock_streamlit_layout(mock_st)
        mock_st.button.return_value = True

        render_empty_state(show_reset=True)

        mock_st.button.assert_called_once_with(
            "🔄 Clear All Filters",
            key="reset_empty_state",
        )
        mock_reset.assert_called_once()
        mock_st.rerun.assert_called_once()


class TestResetFiltersState:
    """Tests for _reset_filters_state."""

    @patch("dashboard.components.empty_state.st")
    def test_resets_session_state_without_service_factory(
        self,
        mock_st: MagicMock,
    ) -> None:
        """Reset filters without an analytics service factory."""
        mock_st.session_state = SessionState()

        _reset_filters_state()

        assert mock_st.session_state["job_filters"] == {}
        assert mock_st.session_state["page"] == 1
        assert mock_st.session_state["selected_job_id"] is None

    @patch("dashboard.components.empty_state.st")
    def test_refreshes_service_factory(
        self,
        mock_st: MagicMock,
    ) -> None:
        """Refresh analytics cache when service factory exists."""
        service_factory = Mock()
        session_state = SessionState(service_factory=service_factory)
        mock_st.session_state = session_state

        _reset_filters_state()

        assert mock_st.session_state["job_filters"] == {}
        assert mock_st.session_state["page"] == 1
        assert mock_st.session_state["selected_job_id"] is None
        service_factory.refresh_all.assert_called_once()

    @patch("dashboard.components.empty_state.st")
    @patch("dashboard.components.empty_state.logger")
    def test_logs_refresh_failure(
        self,
        mock_logger: MagicMock,
        mock_st: MagicMock,
    ) -> None:
        """Log and continue when analytics cache refresh fails."""
        service_factory = Mock()
        service_factory.refresh_all.side_effect = RuntimeError("refresh failed")
        session_state = SessionState(service_factory=service_factory)
        mock_st.session_state = session_state

        _reset_filters_state()

        assert mock_st.session_state["job_filters"] == {}
        assert mock_st.session_state["page"] == 1
        assert mock_st.session_state["selected_job_id"] is None
        mock_logger.exception.assert_called_once_with(
            "Failed to refresh analytics cache during filter reset"
        )


class TestEmptyStateWrappers:
    """Tests for analytics and jobs empty-state wrappers."""

    @patch("dashboard.components.empty_state.render_empty_state")
    def test_empty_state_analytics_delegates(
        self,
        mock_render: Mock,
    ) -> None:
        """Analytics wrapper delegates with reset disabled."""
        empty_state_analytics(
            title="Analytics Empty",
            description="No analytics.",
            icon="📊",
        )

        mock_render.assert_called_once_with(
            title="Analytics Empty",
            description="No analytics.",
            icon="📊",
            show_reset=False,
        )

    @patch("dashboard.components.empty_state.render_empty_state")
    def test_empty_state_jobs_delegates(
        self,
        mock_render: Mock,
    ) -> None:
        """Jobs wrapper delegates with reset enabled."""
        empty_state_jobs(
            title="Jobs Empty",
            description="No jobs.",
            icon="🔍",
        )

        mock_render.assert_called_once_with(
            title="Jobs Empty",
            description="No jobs.",
            icon="🔍",
            show_reset=True,
        )
