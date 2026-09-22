from datetime import datetime
from unittest.mock import MagicMock, patch

from components.job_detail import (
    get_translation,
    is_job_translated,
    render_job_detail,
    toggle_translation,
)
from schemas.jobs import Job


class Context:
    """Context manager for mocked Streamlit containers."""

    def __enter__(self) -> "Context":
        return self

    def __exit__(self, *args: object) -> None:
        return None


class SessionState(dict[str, object]):
    """Dictionary with Streamlit-style attribute access."""

    def __getattr__(self, name: str) -> object:
        return self[name]

    def __setattr__(self, name: str, value: object) -> None:
        self[name] = value


def make_job(
    *,
    id: str = "1",
    language: str = "en",
    description: str | None = "A useful job description.",
    salary_min: float | None = None,
    salary_max: float | None = None,
    salary_currency: str | None = "USD",
    source_site: str | None = None,
    source_url: str | None = None,
    is_tech_role: bool = False,
    technology_category: str | None = None,
    skills: list[str] | None = None,
    is_active: bool = True,
) -> Job:
    """Create a Job model for job-detail tests."""
    return Job(
        id=id,
        title="Data Analyst",
        company_name="Acme Corp",
        location="Nairobi",
        description=description,
        salary_min=salary_min,
        salary_max=salary_max,
        salary_currency=salary_currency,
        posted_date=datetime(2026, 9, 15, 10, 30),
        source_site=source_site,
        source_url=source_url,
        is_active=is_active,
        skills=skills or [],
        technology_category=technology_category,
        is_tech_role=is_tech_role,
        language=language,
    )


@patch("components.job_detail.st")
def test_render_job_detail_minimal_english_job(mock_st: MagicMock) -> None:
    """Render a minimal English job with no optional details."""
    setup_streamlit_mock(mock_st)
    job = make_job()

    render_job_detail(job)

    mock_st.subheader.assert_called_once_with("📄 Data Analyst")
    mock_st.success.assert_called_once_with("🇬🇧 English")
    mock_st.warning.assert_not_called()

    markdown = [str(call) for call in mock_st.markdown.call_args_list]
    assert any("Company" in call for call in markdown)
    assert any("Location" in call for call in markdown)
    assert any("Salary:** Not specified" in call for call in markdown)
    assert any("Status:** Active" in call for call in markdown)
    assert any("A useful job description." in call for call in markdown)


@patch("components.job_detail.st")
def test_render_job_detail_renders_optional_job_fields(
    mock_st: MagicMock,
) -> None:
    """Render source, URL, technology, category, and skills."""
    setup_streamlit_mock(mock_st)

    job = make_job(
        source_site="LinkedIn",
        source_url="https://example.com/job/1",
        is_tech_role=True,
        technology_category="Backend",
        skills=["Python", "SQL", "FastAPI"],
        salary_min=50000,
        salary_max=80000,
        salary_currency="USD",
    )

    render_job_detail(job)

    markdown = [str(call) for call in mock_st.markdown.call_args_list]

    assert any("Source:** LinkedIn" in call for call in markdown)
    assert any("URL:** https://example.com/job/1" in call for call in markdown)
    assert any("Role:** 💻 Technology" in call for call in markdown)
    assert any("Category:** 🏷️ Backend" in call for call in markdown)
    assert any("Skills:** Python, SQL, FastAPI" in call for call in markdown)
    assert any("$" not in call and "USD 50,000 - 80,000" in call for call in markdown)


@patch("components.job_detail.st")
def test_render_job_detail_salary_min_only_and_nontech(
    mock_st: MagicMock,
) -> None:
    """Render minimum-only salary and non-technology role."""
    setup_streamlit_mock(mock_st)

    job = make_job(
        salary_min=40000,
        salary_currency="GBP",
        is_tech_role=False,
        technology_category=None,
        is_active=False,
    )

    render_job_detail(job)

    markdown = [str(call) for call in mock_st.markdown.call_args_list]

    assert any("Salary:** From GBP 40,000" in call for call in markdown)
    assert any("Role:** 👤 Non-Technology" in call for call in markdown)
    assert any("Status:** Inactive" in call for call in markdown)


@patch("components.job_detail.st")
def test_render_job_detail_salary_max_only(mock_st: MagicMock) -> None:
    """Render maximum-only salary."""
    setup_streamlit_mock(mock_st)

    job = make_job(
        salary_max=90000,
        salary_currency=None,
    )

    render_job_detail(job)

    markdown = [str(call) for call in mock_st.markdown.call_args_list]
    assert any("Salary:** Up to USD 90,000" in call for call in markdown)


@patch("components.job_detail.st")
def test_render_job_detail_non_english_language(mock_st: MagicMock) -> None:
    """Render a translated-language badge."""
    setup_streamlit_mock(mock_st)

    job = make_job(
        language="fr",
        description=None,
    )

    render_job_detail(job)

    mock_st.warning.assert_called_once_with("🇫🇷 Français")
    mock_st.success.assert_not_called()


@patch("components.job_detail.st")
def test_render_job_detail_unknown_language(mock_st: MagicMock) -> None:
    """Use fallback emoji and uppercase label for unknown language."""
    setup_streamlit_mock(mock_st)

    job = make_job(language="xx")

    render_job_detail(job)

    mock_st.warning.assert_called_once_with("🌐 XX")


@patch("components.job_detail.st")
def test_render_job_detail_translation_already_available(
    mock_st: MagicMock,
) -> None:
    """Show translated text and original text in an expander."""
    session_state = setup_streamlit_mock(mock_st)

    job = make_job(id="42", language="fr")
    session_state["translated_42"] = True
    session_state["translation_text_42"] = "Description en anglais."

    render_job_detail(job)

    markdown = [str(call) for call in mock_st.markdown.call_args_list]

    assert any("English Translation" in call for call in markdown)
    assert any("Description en anglais." in call for call in markdown)
    mock_st.expander.assert_called_once_with("🔍 View Original (FR)")


@patch("components.job_detail.st")
def test_render_job_detail_translate_success(mock_st: MagicMock) -> None:
    """Translate a non-English job successfully through the API."""
    session_state = setup_streamlit_mock(mock_st)
    mock_st.button.side_effect = [True, False]

    job = make_job(id="42", language="fr")

    mock_config = MagicMock()
    mock_config.api_base_url = "http://api.test"

    mock_client = MagicMock()
    mock_client.translate_job.return_value = {
        "success": True,
        "translated_description": "Translated description.",
    }

    with (
        patch("components.job_detail.get_config", return_value=mock_config),
        patch("components.job_detail.APIClient", return_value=mock_client),
    ):
        render_job_detail(job)

    mock_client.translate_job.assert_called_once_with("42", "en")
    assert session_state["translated_42"] is True
    assert session_state["translation_text_42"] == "Translated description."
    mock_st.success.assert_any_call("✅ Translation complete!")
    mock_st.rerun.assert_called_once_with()


@patch("components.job_detail.st")
def test_render_job_detail_translate_fallback(mock_st: MagicMock) -> None:
    """Use the fallback translation when the API returns no success."""
    session_state = setup_streamlit_mock(mock_st)
    mock_st.button.side_effect = [True, False]

    job = make_job(id="43", language="de")

    mock_config = MagicMock()
    mock_config.api_base_url = "http://api.test"

    mock_client = MagicMock()
    mock_client.translate_job.return_value = {"success": False}

    with (
        patch("components.job_detail.get_config", return_value=mock_config),
        patch("components.job_detail.APIClient", return_value=mock_client),
    ):
        render_job_detail(job)

    assert session_state["translated_43"] is True
    assert session_state["translation_text_43"] == (
        "[Translated from DE] A useful job description."
    )
    mock_st.success.assert_any_call("✅ Translation complete!")
    mock_st.rerun.assert_called_once_with()


@patch("components.job_detail.st")
def test_render_job_detail_translate_error(mock_st: MagicMock) -> None:
    """Show an error when translation raises an exception."""
    setup_streamlit_mock(mock_st)
    mock_st.button.side_effect = [True, False]

    job = make_job(id="44", language="es")

    mock_config = MagicMock()
    mock_config.api_base_url = "http://api.test"

    mock_client = MagicMock()
    mock_client.translate_job.side_effect = RuntimeError("backend unavailable")

    with (
        patch("components.job_detail.get_config", return_value=mock_config),
        patch("components.job_detail.APIClient", return_value=mock_client),
    ):
        render_job_detail(job)

    mock_st.error.assert_called_once_with("Translation failed: backend unavailable")
    mock_st.rerun.assert_not_called()


@patch("components.job_detail.st")
def test_render_job_detail_hide_translation(mock_st: MagicMock) -> None:
    """Hide an existing translation."""
    session_state = setup_streamlit_mock(mock_st)
    mock_st.button.side_effect = [True, False]

    job = make_job(id="45", language="fr")
    session_state["translated_45"] = True
    session_state["translation_text_45"] = "Translated."

    render_job_detail(job)

    assert session_state["translated_45"] is False
    assert session_state["translation_text_45"] == ""
    mock_st.rerun.assert_called_once_with()


@patch("components.job_detail.st")
def test_render_job_detail_close_button(mock_st: MagicMock) -> None:
    """Clear the selected job when closing details."""
    session_state = setup_streamlit_mock(mock_st)
    mock_st.button.side_effect = [False, True]

    job = make_job(language="fr")

    render_job_detail(job)

    assert session_state["selected_job_id"] is None
    mock_st.rerun.assert_called_once_with()


@patch("components.job_detail.st")
def test_get_translation_returns_translation(mock_st: MagicMock) -> None:
    """Return stored translation information."""
    session_state = setup_streamlit_mock(mock_st)
    session_state["translation_text_1"] = "Translated."
    session_state["translated_1"] = True

    assert get_translation("1") == {
        "text": "Translated.",
        "is_translated": True,
    }


@patch("components.job_detail.st")
def test_get_translation_returns_none_when_missing(mock_st: MagicMock) -> None:
    """Return None when no translation text exists."""
    setup_streamlit_mock(mock_st)

    assert get_translation("1") is None


@patch("components.job_detail.st")
def test_is_job_translated(mock_st: MagicMock) -> None:
    """Check translated and untranslated states."""
    session_state = setup_streamlit_mock(mock_st)

    assert is_job_translated("1") is False

    session_state["translated_1"] = True

    assert is_job_translated("1") is True


@patch("components.job_detail.st")
def test_toggle_translation_shows_translation(mock_st: MagicMock) -> None:
    """Toggle an untranslated job to translated."""
    session_state = setup_streamlit_mock(mock_st)

    toggle_translation("1")

    assert session_state["translated_1"] is True


@patch("components.job_detail.st")
def test_toggle_translation_hides_translation(mock_st: MagicMock) -> None:
    """Toggle a translated job off and clear its text."""
    session_state = setup_streamlit_mock(mock_st)
    session_state["translated_1"] = True
    session_state["translation_text_1"] = "Translated."

    toggle_translation("1")

    assert session_state["translated_1"] is False
    assert session_state["translation_text_1"] == ""


def setup_streamlit_mock(mock_st: MagicMock) -> SessionState:
    """Configure Streamlit mocks used by render_job_detail."""
    session_state = SessionState()

    mock_st.session_state = session_state
    mock_st.container.return_value = Context()
    mock_st.expander.return_value = Context()
    mock_st.spinner.return_value = Context()

    def make_columns(spec: int | list[int]) -> list[Context]:
        count = spec if isinstance(spec, int) else len(spec)
        return [Context() for _ in range(count)]

    mock_st.columns.side_effect = make_columns
    mock_st.button.return_value = False

    return session_state
