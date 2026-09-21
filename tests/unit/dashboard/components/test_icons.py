from unittest.mock import MagicMock, patch

from components.icons import (
    ICONS,
    IconColor,
    company_icon,
    filter_icon,
    get_icon,
    icon_button,
    icon_html,
    icon_with_text,
    job_icon,
    location_icon,
    metric_icon,
    refresh_icon,
    render_icon,
    salary_icon,
    score_icon,
    tech_icon,
    time_icon,
    translate_icon,
)


class Context:
    def __enter__(self) -> "Context":
        return self

    def __exit__(self, *args: object) -> None:
        return None


def setup_streamlit_mock(mock_st: MagicMock) -> None:
    mock_st.container.return_value = Context()
    mock_st.columns.return_value = [Context(), Context()]
    mock_st.button.return_value = False


def test_icon_color_constants() -> None:
    assert IconColor.PRIMARY == "#6366f1"
    assert IconColor.SUCCESS == "#10b981"
    assert IconColor.WARNING == "#f59e0b"
    assert IconColor.DANGER == "#ef4444"
    assert IconColor.INFO == "#3b82f6"
    assert IconColor.GRAY == "#6b7280"
    assert IconColor.DARK == "#1f2937"


def test_icons_dictionary_contains_expected_icons() -> None:
    expected = {
        "success",
        "error",
        "warning",
        "info",
        "company",
        "location_pin",
        "calendar",
        "salary",
        "overview",
        "jobs",
        "analytics",
        "about",
        "jobs_metric",
        "companies_metric",
        "skills_metric",
        "salary_metric",
        "location",
        "trends",
        "employment",
        "refresh",
        "tech",
        "score",
        "filter",
        "download",
        "translate",
        "briefcase",
        "clock",
    }

    assert expected.issubset(ICONS)
    assert all("svg" in icon and "label" in icon for icon in ICONS.values())


def test_get_icon_returns_empty_for_unknown_icon() -> None:
    assert get_icon("does_not_exist") == ""


def test_get_icon_default_values() -> None:
    result = get_icon("success")

    assert result.startswith("<svg")
    assert 'width="20"' in result
    assert 'height="20"' in result
    assert 'stroke="currentColor"' in result


def test_get_icon_custom_size_and_color() -> None:
    result = get_icon("success", size=32, color="#ff0000")

    assert 'width="32"' in result
    assert 'height="32"' in result
    assert 'stroke="#ff0000"' in result


@patch("components.icons.st")
def test_render_icon_renders_existing_icon(mock_st: MagicMock) -> None:
    render_icon("success", size=24, color="#123456")

    mock_st.markdown.assert_called_once()
    html = mock_st.markdown.call_args.args[0]

    assert 'width="24"' in html
    assert 'stroke="#123456"' in html
    assert mock_st.markdown.call_args.kwargs["unsafe_allow_html"] is True


@patch("components.icons.st")
def test_render_icon_does_nothing_for_unknown_icon(mock_st: MagicMock) -> None:
    render_icon("unknown")

    mock_st.markdown.assert_not_called()


def test_icon_html_existing_icon() -> None:
    result = icon_html("success", size=24, color="#123456")

    assert result.startswith('<span style="display:inline-flex')
    assert 'width="24"' in result
    assert 'stroke="#123456"' in result


def test_icon_html_unknown_icon() -> None:
    assert icon_html("unknown") == ""


def test_icon_with_text_existing_icon() -> None:
    result = icon_with_text(
        "success",
        "Completed",
        size=18,
        color="#123456",
        gap="10px",
    )

    assert "Completed" in result
    assert 'width="18"' in result
    assert 'stroke="#123456"' in result
    assert "gap:10px" in result


def test_icon_with_text_unknown_icon() -> None:
    assert icon_with_text("unknown", "Completed") == "Completed"


def test_metric_icon_existing_icon() -> None:
    result = metric_icon("jobs_metric", size=28, color="#123456")

    assert result.startswith("<div")
    assert "background:#12345615" in result
    assert "width:52px" in result
    assert "height:52px" in result
    assert 'width="28"' in result


def test_metric_icon_unknown_icon() -> None:
    assert metric_icon("unknown") == ""


def test_convenience_icon_functions() -> None:
    assert job_icon() == get_icon("briefcase")
    assert tech_icon() == get_icon("tech")
    assert score_icon() == get_icon("score")
    assert location_icon() == get_icon("location_pin")
    assert time_icon() == get_icon("clock")
    assert company_icon() == get_icon("company")
    assert filter_icon() == get_icon("filter")
    assert translate_icon() == get_icon("translate")
    assert refresh_icon() == get_icon("refresh")
    assert salary_icon() == get_icon("salary")


@patch("components.icons.st")
def test_icon_button_without_key(mock_st: MagicMock) -> None:
    setup_streamlit_mock(mock_st)
    mock_st.button.return_value = True

    result = icon_button(
        "Refresh",
        "refresh",
        use_container_width=True,
    )

    assert result is True
    mock_st.button.assert_called_once_with(
        "Refresh",
        use_container_width=True,
    )
    mock_st.markdown.assert_called_once()


@patch("components.icons.st")
def test_icon_button_with_key(mock_st: MagicMock) -> None:
    setup_streamlit_mock(mock_st)
    mock_st.button.return_value = False

    result = icon_button(
        "Translate",
        "translate",
        key="translate_1",
        color="#123456",
        size=18,
    )

    assert result is False
    mock_st.button.assert_called_once_with(
        "Translate",
        key="translate_1",
        use_container_width=False,
    )

    html = mock_st.markdown.call_args.args[0]
    assert 'width="18"' in html
    assert 'stroke="#123456"' in html
    assert mock_st.markdown.call_args.kwargs["unsafe_allow_html"] is True
