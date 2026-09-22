from datetime import datetime
from unittest.mock import MagicMock, patch

from components.tables import render_jobs_table
from schemas.jobs import Job


class SessionState(dict[str, object]):
    """Minimal Streamlit session-state stand-in."""

    def __getattr__(self, name: str) -> object:
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name: str, value: object) -> None:
        self[name] = value


class Context:
    """Simple context-manager stand-in for Streamlit layout elements."""

    def __enter__(self) -> "Context":
        return self

    def __exit__(
        self,
        exc_type: object,
        exc_value: object,
        traceback: object,
    ) -> None:
        return None


def make_job(
    *,
    id: str = "1",
    title: str = "Data Analyst",
    company_name: str = "Acme Corp",
    location: str = "Nairobi",
    description: str | None = None,
    salary_min: float | None = None,
    salary_max: float | None = None,
    salary_currency: str | None = "USD",
    posted_date: datetime = datetime(2026, 9, 14),
    source_site: str | None = None,
    source_url: str | None = None,
    is_active: bool = True,
) -> Job:
    """Create a Job model for table rendering tests."""
    return Job(
        id=id,
        title=title,
        company_name=company_name,
        location=location,
        description=description,
        salary_min=salary_min,
        salary_max=salary_max,
        salary_currency=salary_currency,
        posted_date=posted_date,
        source_site=source_site,
        source_url=source_url,
        is_active=is_active,
    )


def setup_streamlit_mock(mock_st: MagicMock) -> SessionState:
    """Configure Streamlit layout mocks and return session state."""
    session_state = SessionState()
    mock_st.session_state = session_state

    mock_st.container.return_value = Context()

    # render_jobs_table uses three columns for the header and two for details.
    mock_st.columns.side_effect = lambda spec: [
        Context() for _ in range(spec if isinstance(spec, int) else len(spec))
    ]

    mock_st.button.return_value = False

    return session_state


@patch("components.tables.st")
def test_render_jobs_table_returns_for_empty_jobs(mock_st: MagicMock) -> None:
    render_jobs_table([])

    mock_st.container.assert_not_called()
    mock_st.columns.assert_not_called()
    mock_st.button.assert_not_called()


@patch("components.tables.st")
def test_render_jobs_table_renders_basic_active_job(mock_st: MagicMock) -> None:
    setup_streamlit_mock(mock_st)

    job = make_job(
        id="10",
        title="Python Developer",
        company_name="Tech Corp",
        location="Nairobi",
        is_active=True,
    )

    render_jobs_table([job])

    assert mock_st.session_state["expanded_10"] is False
    mock_st.subheader.assert_called_once_with("Python Developer")
    mock_st.caption.assert_any_call("🏢 Tech Corp • 📍 Nairobi")
    mock_st.caption.assert_any_call("🟢 Active")

    mock_st.button.assert_called_once_with(
        "📄 View",
        key="toggle_10_0",
    )


@patch("components.tables.st")
def test_render_jobs_table_renders_optional_header_fields(
    mock_st: MagicMock,
) -> None:
    setup_streamlit_mock(mock_st)

    job = make_job(
        id="11",
        source_site="LinkedIn",
        salary_min=50000,
        salary_max=80000,
        salary_currency="KES",
        posted_date=datetime(2026, 9, 14),
    )

    render_jobs_table([job])

    mock_st.caption.assert_any_call("📋 Source: LinkedIn")
    mock_st.caption.assert_any_call("💰 KES 50,000 - 80,000")
    mock_st.caption.assert_any_call("📅 2026-09-14")
    mock_st.caption.assert_any_call("🟢 Active")


@patch("components.tables.st")
def test_render_jobs_table_handles_minimum_salary_only(
    mock_st: MagicMock,
) -> None:
    setup_streamlit_mock(mock_st)

    job = make_job(
        id="12",
        salary_min=45000,
        salary_max=None,
        salary_currency="KES",
    )

    render_jobs_table([job])

    mock_st.caption.assert_any_call("💰 From KES 45,000")


@patch("components.tables.st")
def test_render_jobs_table_handles_maximum_salary_only(
    mock_st: MagicMock,
) -> None:
    setup_streamlit_mock(mock_st)

    job = make_job(
        id="13",
        salary_min=None,
        salary_max=95000,
        salary_currency="USD",
    )

    render_jobs_table([job])

    mock_st.caption.assert_any_call("💰 Up to USD 95,000")


@patch("components.tables.st")
def test_render_jobs_table_uses_usd_when_currency_missing(
    mock_st: MagicMock,
) -> None:
    setup_streamlit_mock(mock_st)

    job = make_job(
        id="14",
        salary_min=50000,
        salary_max=75000,
        salary_currency=None,
    )

    render_jobs_table([job])

    mock_st.caption.assert_any_call("💰 USD 50,000 - 75,000")


@patch("components.tables.st")
def test_render_jobs_table_renders_inactive_job(
    mock_st: MagicMock,
) -> None:
    setup_streamlit_mock(mock_st)

    job = make_job(
        id="15",
        is_active=False,
        posted_date=datetime(2026, 9, 13),
    )

    render_jobs_table([job])

    mock_st.caption.assert_any_call("🔴 Inactive")
    mock_st.caption.assert_any_call("📅 2026-09-13")


@patch("components.tables.st")
def test_render_jobs_table_initializes_missing_expansion_state(
    mock_st: MagicMock,
) -> None:
    session_state = setup_streamlit_mock(mock_st)

    job = make_job(id="20")

    render_jobs_table([job])

    assert session_state["expanded_20"] is False
    mock_st.button.assert_called_once_with(
        "📄 View",
        key="toggle_20_0",
    )


@patch("components.tables.st")
def test_render_jobs_table_preserves_existing_expansion_state(
    mock_st: MagicMock,
) -> None:
    session_state = setup_streamlit_mock(mock_st)
    session_state["expanded_21"] = True

    job = make_job(id="21")

    render_jobs_table([job])

    assert session_state["expanded_21"] is True
    mock_st.button.assert_called_once_with(
        "📄 Hide",
        key="toggle_21_0",
    )


@patch("components.tables.st")
def test_render_jobs_table_toggle_button_expands_job(
    mock_st: MagicMock,
) -> None:
    session_state = setup_streamlit_mock(mock_st)
    mock_st.button.return_value = True

    job = make_job(id="22")

    render_jobs_table([job])

    assert session_state["expanded_22"] is True


@patch("components.tables.st")
def test_render_jobs_table_toggle_button_collapses_job(
    mock_st: MagicMock,
) -> None:
    session_state = setup_streamlit_mock(mock_st)
    session_state["expanded_23"] = True
    mock_st.button.return_value = True

    job = make_job(id="23")

    render_jobs_table([job])

    assert session_state["expanded_23"] is False


@patch("components.tables.st")
def test_render_expanded_job_with_full_details(
    mock_st: MagicMock,
) -> None:
    session_state = setup_streamlit_mock(mock_st)
    session_state["expanded_30"] = True

    job = make_job(
        id="30",
        title="Senior Data Engineer",
        company_name="Tech Ltd",
        location="Nairobi",
        source_site="LinkedIn",
        source_url="https://example.com/job/30",
        salary_min=100000,
        salary_max=150000,
        salary_currency="KES",
        posted_date=datetime(2026, 9, 14, 15, 30),
        is_active=True,
        description="A senior data engineering role.",
    )

    render_jobs_table([job])

    mock_st.markdown.assert_any_call("---")
    mock_st.markdown.assert_any_call("**Company:** Tech Ltd")
    mock_st.markdown.assert_any_call("**Location:** Nairobi")
    mock_st.markdown.assert_any_call("**Source:** LinkedIn")
    mock_st.markdown.assert_any_call("**URL:** https://example.com/job/30")
    mock_st.markdown.assert_any_call("**Salary:** KES 100,000 - 150,000")
    mock_st.markdown.assert_any_call("**Posted:** 2026-09-14 15:30")
    mock_st.markdown.assert_any_call("**Status:** Active")
    mock_st.markdown.assert_any_call("### 📝 Description")
    mock_st.markdown.assert_any_call("A senior data engineering role.")


@patch("components.tables.st")
def test_render_expanded_job_with_minimum_salary_and_no_source(
    mock_st: MagicMock,
) -> None:
    session_state = setup_streamlit_mock(mock_st)
    session_state["expanded_31"] = True

    job = make_job(
        id="31",
        salary_min=60000,
        salary_max=None,
        salary_currency="KES",
        source_site=None,
        source_url=None,
        posted_date=datetime(2026, 9, 14, 9, 0),
        is_active=False,
    )

    render_jobs_table([job])

    mock_st.markdown.assert_any_call("**Salary:** From KES 60,000")
    mock_st.markdown.assert_any_call("**Status:** Inactive")


@patch("components.tables.st")
def test_render_expanded_job_with_maximum_salary(
    mock_st: MagicMock,
) -> None:
    session_state = setup_streamlit_mock(mock_st)
    session_state["expanded_32"] = True

    job = make_job(
        id="32",
        salary_min=None,
        salary_max=90000,
        salary_currency="USD",
        posted_date=datetime(2026, 9, 14, 10, 15),
    )

    render_jobs_table([job])

    mock_st.markdown.assert_any_call("**Salary:** Up to USD 90,000")


@patch("components.tables.st")
def test_render_expanded_job_without_salary(
    mock_st: MagicMock,
) -> None:
    session_state = setup_streamlit_mock(mock_st)
    session_state["expanded_33"] = True

    job = make_job(
        id="33",
        salary_min=None,
        salary_max=None,
        posted_date=datetime(2026, 9, 14, 11, 45),
    )

    render_jobs_table([job])

    mock_st.markdown.assert_any_call("**Salary:** Not specified")


@patch("components.tables.st")
def test_render_expanded_job_without_description(
    mock_st: MagicMock,
) -> None:
    session_state = setup_streamlit_mock(mock_st)
    session_state["expanded_34"] = True

    job = make_job(
        id="34",
        description=None,
        posted_date=datetime(2026, 9, 14, 12, 0),
    )

    render_jobs_table([job])

    assert "### 📝 Description" not in [call.args[0] for call in mock_st.markdown.call_args_list]


@patch("components.tables.st")
def test_render_expanded_job_truncates_long_description(
    mock_st: MagicMock,
) -> None:
    session_state = setup_streamlit_mock(mock_st)
    session_state["expanded_35"] = True

    description = "A" * 1500

    job = make_job(
        id="35",
        description=description,
        posted_date=datetime(2026, 9, 14, 13, 0),
    )

    render_jobs_table([job])

    mock_st.markdown.assert_any_call("A" * 1000 + "...")


@patch("components.tables.st")
def test_render_expanded_job_keeps_short_description(
    mock_st: MagicMock,
) -> None:
    session_state = setup_streamlit_mock(mock_st)
    session_state["expanded_36"] = True

    description = "Short description"

    job = make_job(
        id="36",
        description=description,
        posted_date=datetime(2026, 9, 14, 14, 0),
    )

    render_jobs_table([job])

    mock_st.markdown.assert_any_call(description)


@patch("components.tables.st")
def test_render_multiple_jobs_uses_unique_keys(
    mock_st: MagicMock,
) -> None:
    setup_streamlit_mock(mock_st)

    jobs = [
        make_job(id="40", title="Analyst"),
        make_job(id="41", title="Engineer"),
    ]

    render_jobs_table(jobs)

    assert mock_st.button.call_count == 2
    assert mock_st.button.call_args_list[0].kwargs["key"] == "toggle_40_0"
    assert mock_st.button.call_args_list[1].kwargs["key"] == "toggle_41_1"
