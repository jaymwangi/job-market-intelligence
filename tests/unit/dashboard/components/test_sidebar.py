from unittest.mock import MagicMock, patch

from components.sidebar import render_sidebar


class Context:
    """Context manager for mocked Streamlit containers."""

    def __enter__(self) -> "Context":
        return self

    def __exit__(self, *args: object) -> None:
        return None


def setup_streamlit_mock(mock_st: MagicMock) -> None:
    """Configure the Streamlit mock for sidebar rendering."""
    mock_st.sidebar = Context()
    mock_st.container.return_value = Context()
    mock_st.button.return_value = False


@patch("components.sidebar.StateManager")
@patch("components.sidebar.st")
def test_render_sidebar_renders_default_page(
    mock_st: MagicMock,
    mock_state: MagicMock,
) -> None:
    """Render the sidebar with a non-active page selection."""
    setup_streamlit_mock(mock_st)
    mock_state.get_current_page.return_value = "overview"

    render_sidebar()

    mock_state.get_current_page.assert_called_once_with()
    assert mock_st.markdown.call_count >= 4
    assert mock_st.button.call_count == 4

    first_button = mock_st.button.call_args_list[0]
    assert first_button.args[0] == "Overview →"
    assert first_button.kwargs["key"] == "nav_overview"


@patch("components.sidebar.StateManager")
@patch("components.sidebar.st")
def test_render_sidebar_marks_jobs_as_active(
    mock_st: MagicMock,
    mock_state: MagicMock,
) -> None:
    """Render the Jobs navigation item as active."""
    setup_streamlit_mock(mock_st)
    mock_state.get_current_page.return_value = "jobs"

    render_sidebar()

    button_calls = mock_st.button.call_args_list

    assert button_calls[0].args[0] == "Overview"
    assert button_calls[1].args[0] == "Jobs →"
    assert button_calls[2].args[0] == "Analytics"
    assert button_calls[3].args[0] == "About"

    markdown_calls = [str(call) for call in mock_st.markdown.call_args_list]
    assert any("active-nav" in call for call in markdown_calls)


@patch("components.sidebar.StateManager")
@patch("components.sidebar.st")
def test_render_sidebar_marks_analytics_as_active(
    mock_st: MagicMock,
    mock_state: MagicMock,
) -> None:
    """Render the Analytics navigation item as active."""
    setup_streamlit_mock(mock_st)
    mock_state.get_current_page.return_value = "analytics"

    render_sidebar()

    button_calls = mock_st.button.call_args_list

    assert button_calls[2].args[0] == "Analytics →"

    markdown_calls = [str(call) for call in mock_st.markdown.call_args_list]
    assert any("</div>" in call for call in markdown_calls)


@patch("components.sidebar.StateManager")
@patch("components.sidebar.st")
def test_render_sidebar_marks_about_as_active(
    mock_st: MagicMock,
    mock_state: MagicMock,
) -> None:
    """Render the About navigation item as active."""
    setup_streamlit_mock(mock_st)
    mock_state.get_current_page.return_value = "about"

    render_sidebar()

    button_calls = mock_st.button.call_args_list

    assert button_calls[3].args[0] == "About →"


@patch("components.sidebar.StateManager")
@patch("components.sidebar.st")
def test_render_sidebar_navigates_when_different_page_clicked(
    mock_st: MagicMock,
    mock_state: MagicMock,
) -> None:
    """Navigate when a non-active page button is clicked."""
    setup_streamlit_mock(mock_st)
    mock_state.get_current_page.return_value = "overview"
    mock_st.button.side_effect = [False, True, False, False]

    render_sidebar()

    mock_state.set_current_page.assert_called_once_with("jobs")
    mock_st.rerun.assert_called_once_with()


@patch("components.sidebar.StateManager")
@patch("components.sidebar.st")
def test_render_sidebar_does_not_navigate_when_active_page_clicked(
    mock_st: MagicMock,
    mock_state: MagicMock,
) -> None:
    """Do not navigate when the already-active page is clicked."""
    setup_streamlit_mock(mock_st)
    mock_state.get_current_page.return_value = "overview"
    mock_st.button.side_effect = [True, False, False, False]

    render_sidebar()

    mock_state.set_current_page.assert_not_called()
    mock_st.rerun.assert_not_called()


@patch("components.sidebar.StateManager")
@patch("components.sidebar.st")
def test_render_sidebar_does_not_navigate_when_no_button_clicked(
    mock_st: MagicMock,
    mock_state: MagicMock,
) -> None:
    """Do nothing when no navigation button is clicked."""
    setup_streamlit_mock(mock_st)
    mock_state.get_current_page.return_value = "overview"

    render_sidebar()

    mock_state.set_current_page.assert_not_called()
    mock_st.rerun.assert_not_called()


@patch("components.sidebar.StateManager")
@patch("components.sidebar.st")
def test_render_sidebar_renders_footer(
    mock_st: MagicMock,
    mock_state: MagicMock,
) -> None:
    """Render the sidebar footer with status and statistics."""
    setup_streamlit_mock(mock_st)
    mock_state.get_current_page.return_value = "overview"

    render_sidebar()

    markdown_calls = [str(call) for call in mock_st.markdown.call_args_list]

    assert any("24/7" in call for call in markdown_calls)
    assert any("99.9%" in call for call in markdown_calls)
    assert any("Production • Stable" in call for call in markdown_calls)
    assert any("Real-time Analytics Platform" in call for call in markdown_calls)


@patch("components.sidebar.StateManager")
@patch("components.sidebar.st")
def test_render_sidebar_passes_navigation_button_configuration(
    mock_st: MagicMock,
    mock_state: MagicMock,
) -> None:
    """Verify navigation buttons receive their expected Streamlit options."""
    setup_streamlit_mock(mock_st)
    mock_state.get_current_page.return_value = "overview"

    render_sidebar()

    first_button = mock_st.button.call_args_list[0]

    assert first_button.kwargs["use_container_width"] is True
    assert first_button.kwargs["key"] == "nav_overview"
    assert first_button.kwargs["help"] == "Navigate to Overview"
