from datetime import datetime
from unittest.mock import MagicMock, patch

from components.job_card import (
    _escape_html,
    _get_job_dict,
    _render_css,
    render_job_card,
)


class SessionState(dict[str, object]):
    def __getattr__(self, name: str) -> object:
        return self[name]

    def __setattr__(self, name: str, value: object) -> None:
        self[name] = value


class JobObject:
    def __init__(self, data: dict[str, object]) -> None:
        self.id = data["id"]
        self._data = data

    def model_dump(self) -> dict[str, object]:
        return self._data


class Context:
    def __enter__(self) -> "Context":
        return self

    def __exit__(
        self,
        exc_type: object,
        exc_value: object,
        traceback: object,
    ) -> None:
        return None


def setup_streamlit_mock(mock_st: MagicMock) -> SessionState:
    session_state = SessionState()
    mock_st.session_state = session_state
    mock_st.columns.side_effect = lambda spec: [Context() for _ in range(len(spec))]
    mock_st.button.return_value = False
    return session_state


def test_get_job_dict_uses_model_dump() -> None:
    class ModelDumpJob:
        def model_dump(self) -> dict[str, str]:
            return {"title": "Data Analyst"}

    assert _get_job_dict(ModelDumpJob()) == {"title": "Data Analyst"}


def test_get_job_dict_uses_dict_method() -> None:
    class DictJob:
        def dict(self) -> dict[str, str]:
            return {"title": "Backend Engineer"}

    assert _get_job_dict(DictJob()) == {"title": "Backend Engineer"}


def test_get_job_dict_returns_plain_dict() -> None:
    job = {"title": "Data Engineer"}

    assert _get_job_dict(job) is job


def test_escape_html_handles_none() -> None:
    assert _escape_html(None) == ""


def test_escape_html_escapes_special_characters() -> None:
    assert _escape_html('<Acme & "Co">') == "&lt;Acme &amp; &quot;Co&quot;&gt;"


def test_render_css_does_nothing() -> None:
    assert _render_css() is None


@patch("components.job_card.components.html")
@patch("components.job_card.st")
def test_render_job_card_renders_minimal_job(
    mock_st: MagicMock,
    mock_html: MagicMock,
) -> None:
    setup_streamlit_mock(mock_st)

    job = JobObject(
        {
            "id": "1",
            "title": "Data Analyst",
            "company_name": "Acme",
            "location": "Nairobi",
            "posted_date": datetime(2026, 9, 15),
        }
    )

    render_job_card(job)

    html = mock_html.call_args.args[0]
    assert "Data Analyst" in html
    assert "Acme" in html
    assert "Nairobi" in html
    assert "🇬🇧 English" in html
    assert "Non-Tech" in html
    assert "Recently posted" not in html
    mock_st.button.assert_called_once_with("👁️ View Details", key="view_1")


@patch("components.job_card.components.html")
@patch("components.job_card.st")
def test_render_job_card_renders_salary_and_employment(
    mock_st: MagicMock,
    mock_html: MagicMock,
) -> None:
    setup_streamlit_mock(mock_st)

    job = JobObject(
        {
            "id": "2",
            "title": "Backend Engineer",
            "company_name": "Acme",
            "location": "London",
            "salary_min": 50000,
            "salary_max": 80000,
            "salary_currency": "GBP",
            "country_code": "GB",
            "employment_type": "FULL_TIME",
            "technology_category": "backend",
            "is_tech_role": True,
            "posted_date": "2026-09-14T10:30:00Z",
        }
    )

    render_job_card(job)

    html = mock_html.call_args.args[0]
    assert "£" not in html
    assert "$50,000 - $80,000" in html
    assert "GBP" in html
    assert "🇬🇧 London" in html
    assert "Full Time" in html
    assert "Backend" in html
    assert "Tech Role" in html
    assert "Sep 14, 2026" in html


@patch("components.job_card.components.html")
@patch("components.job_card.st")
def test_render_job_card_renders_minimum_salary(
    mock_st: MagicMock,
    mock_html: MagicMock,
) -> None:
    setup_streamlit_mock(mock_st)

    job = JobObject(
        {
            "id": "3",
            "title": "Data Engineer",
            "company_name": "Acme",
            "location": "Nairobi",
            "salary_min": 75000,
            "currency": "KES",
            "posted_date": datetime(2026, 9, 15),
        }
    )

    render_job_card(job)

    html = mock_html.call_args.args[0]
    assert "$75,000+" in html
    assert "KES" in html


@patch("components.job_card.components.html")
@patch("components.job_card.st")
def test_render_job_card_renders_skills_and_truncates_extra_skills(
    mock_st: MagicMock,
    mock_html: MagicMock,
) -> None:
    setup_streamlit_mock(mock_st)

    job = JobObject(
        {
            "id": "4",
            "title": "ML Engineer",
            "company_name": "AI Corp",
            "location": "Berlin",
            "skills": [
                "Python",
                "SQL",
                "Docker",
                "AWS",
                "PyTorch",
                "Pandas",
                "Kubernetes",
                "Spark",
            ],
            "technology_category": "ml_ai",
            "is_tech_role": True,
            "posted_date": datetime(2026, 9, 15),
        }
    )

    render_job_card(job)

    html = mock_html.call_args.args[0]
    assert "Python" in html
    assert "Pandas" in html
    assert "Kubernetes" not in html
    assert "+2 more" in html


@patch("components.job_card.components.html")
@patch("components.job_card.st")
def test_render_job_card_renders_description_and_escapes_html(
    mock_st: MagicMock,
    mock_html: MagicMock,
) -> None:
    setup_streamlit_mock(mock_st)

    job = JobObject(
        {
            "id": "5",
            "title": "<Senior Engineer>",
            "company_name": 'A & B "Tech"',
            "location": "Nairobi",
            "description": "<script>alert('x')</script>" + "a" * 200,
            "posted_date": datetime(2026, 9, 15),
        }
    )

    render_job_card(job)

    html = mock_html.call_args.args[0]
    assert "&lt;Senior Engineer&gt;" in html
    assert "A &amp; B &quot;Tech&quot;" in html
    assert "&lt;script&gt;" in html
    assert "..." in html


@patch("components.job_card.components.html")
@patch("components.job_card.st")
def test_render_job_card_renders_non_english_language(
    mock_st: MagicMock,
    mock_html: MagicMock,
) -> None:
    setup_streamlit_mock(mock_st)

    job = JobObject(
        {
            "id": "6",
            "title": "Développeur",
            "company_name": "Entreprise",
            "location": "Paris",
            "language": "fr",
            "country_code": "FR",
            "posted_date": "invalid-date",
        }
    )

    render_job_card(job)

    html = mock_html.call_args.args[0]
    assert "🇫🇷 Français" in html
    assert "invalid-da" in html


@patch("components.job_card.components.html")
@patch("components.job_card.st")
def test_render_job_card_handles_unknown_values(
    mock_st: MagicMock,
    mock_html: MagicMock,
) -> None:
    setup_streamlit_mock(mock_st)

    job = JobObject(
        {
            "id": "7",
            "title": "QA Engineer",
            "company_name": "Test Corp",
            "location": "",
            "country_code": "XX",
            "language": "xx",
            "employment_type": "CUSTOM",
            "technology_category": "unknown",
            "is_tech_role": True,
            "posted_date": datetime(2026, 9, 15),
        }
    )

    render_job_card(job)

    html = mock_html.call_args.args[0]
    assert "🌍 Remote" in html
    assert "🌐 XX" in html
    assert "CUSTOM" in html
    assert "General" in html
    assert "Tech Role" in html


@patch("components.job_card.components.html")
@patch("components.job_card.st")
def test_render_job_card_sets_css_state_once(
    mock_st: MagicMock,
    mock_html: MagicMock,
) -> None:
    session_state = setup_streamlit_mock(mock_st)

    job = JobObject(
        {
            "id": "8",
            "title": "Developer",
            "company_name": "Acme",
            "location": "Nairobi",
            "posted_date": datetime(2026, 9, 15),
        }
    )

    render_job_card(job)

    assert session_state["job_card_css_rendered"] is True
    assert mock_html.call_count == 1

    mock_html.reset_mock()
    render_job_card(job)

    assert mock_html.call_count == 1


@patch("components.job_card.components.html")
@patch("components.job_card.st")
def test_render_job_card_view_details_sets_selected_job_and_reruns(
    mock_st: MagicMock,
    mock_html: MagicMock,
) -> None:
    session_state = setup_streamlit_mock(mock_st)
    mock_st.button.return_value = True

    job = JobObject(
        {
            "id": 123,
            "title": "Developer",
            "company_name": "Acme",
            "location": "Nairobi",
            "posted_date": datetime(2026, 9, 15),
        }
    )

    render_job_card(job)

    assert session_state["selected_job_id"] == "123"
    mock_st.rerun.assert_called_once()


@patch("components.job_card.components.html")
@patch("components.job_card.st")
def test_render_job_card_renders_apply_link(
    mock_st: MagicMock,
    mock_html: MagicMock,
) -> None:
    setup_streamlit_mock(mock_st)

    job = JobObject(
        {
            "id": "9",
            "title": "Engineer",
            "company_name": "Acme",
            "location": "Nairobi",
            "source_url": "https://example.com/jobs/9",
            "posted_date": datetime(2026, 9, 15),
        }
    )

    render_job_card(job)

    markdown_calls = mock_st.markdown.call_args_list
    assert any(
        "https://example.com/jobs/9" in str(call) and "🔗 Apply" in str(call)
        for call in markdown_calls
    )
