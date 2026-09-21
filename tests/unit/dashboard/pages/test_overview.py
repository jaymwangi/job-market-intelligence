import sys
from unittest.mock import MagicMock, Mock

import pytest
from datetime import datetime, timezone

sys.path.insert(0, "dashboard")

from dashboard.pages import overview


@pytest.fixture
def services():
    analytics_service = Mock()
    jobs_service = Mock()

    analytics_service.get_enriched_top_skills.return_value = [
        {"skill": "Python", "count": 100},
        {"skill": "SQL", "count": 80},
    ]
    analytics_service.get_country_distribution.return_value = [
        {"country": "Kenya", "count": 50},
        {"country": "Germany", "count": 30},
    ]
    analytics_service.get_enriched_salary.return_value = {
        "average_min": 50000,
        "median": 55000,
        "maximum": 100000,
    }
    analytics_service.get_technology_distribution.return_value = [
        {"category": "Python", "count": 60},
        {"category": "SQL", "count": 40},
    ]
    analytics_service.get_companies_hiring_count.return_value = 25
    analytics_service.get_last_etl_run.return_value = "2026-09-16 10:00:00"
    analytics_service.get_pipeline_status.return_value = "idle"
    analytics_service.get_db_status.return_value = "operational"

    jobs_response = Mock()
    jobs_response.items = []
    jobs_service.fetch_jobs.return_value = jobs_response

    return analytics_service, jobs_service


@pytest.fixture(autouse=True)
def mock_health_service(mocker):
    health_service = MagicMock()
    health_service.check.return_value.status = "healthy"
    mocker.patch.object(
        overview,
        "HealthService",
        return_value=health_service,
    )


def test_render_success(services, mocker):
    analytics_service, jobs_service = services

    mocker.patch.object(
        overview.StateManager,
        "get_analytics_service",
        return_value=analytics_service,
    )
    mocker.patch.object(
        overview.StateManager,
        "get_jobs_service",
        return_value=jobs_service,
    )

    mocker.patch.object(overview.st, "markdown")
    mocker.patch.object(overview.st, "caption")
    mocker.patch.object(overview.st, "info")
    mocker.patch.object(overview.st, "error")
    mocker.patch.object(overview.st, "success")
    mocker.patch.object(overview.st, "warning")
    mocker.patch.object(overview.st, "plotly_chart")
    def mock_columns(spec):
        count = spec if isinstance(spec, int) else len(spec)
        columns = []
        for _ in range(count):
            column = MagicMock()
            column.__enter__ = Mock(return_value=column)
            column.__exit__ = Mock(return_value=False)
            columns.append(column)
        return columns

    mocker.patch.object(overview.st, "columns", side_effect=mock_columns)
    mocker.patch.object(overview.st, "spinner", return_value=MagicMock())
    mocker.patch.object(overview.st, "expander", return_value=MagicMock())
    mocker.patch.object(overview.st, "container", return_value=MagicMock())

    mocker.patch.object(
        overview,
        "get_icon",
        return_value="<svg></svg>",
    )
    mocker.patch.object(overview, "divider")

    overview.render()

    analytics_service.get_enriched_top_skills.assert_called_once_with(limit=10)
    analytics_service.get_country_distribution.assert_called_once_with()
    analytics_service.get_enriched_salary.assert_called_once_with()
    analytics_service.get_technology_distribution.assert_called_once_with()
    analytics_service.get_companies_hiring_count.assert_called_once_with()

def test_render_company_count_fallback_with_jobs(services, mocker):
    analytics_service, jobs_service = services

    analytics_service.get_companies_hiring_count.side_effect = AttributeError

    job1 = Mock()
    job1.company_name = "Company A"
    job2 = Mock()
    job2.company_name = "Company B"
    job3 = Mock()
    job3.company_name = "Company A"
    job4 = Mock()
    job4.company_name = None

    jobs_response = Mock()
    jobs_response.items = [job1, job2, job3, job4]
    jobs_service.fetch_jobs.return_value = jobs_response

    mocker.patch.object(
        overview.StateManager,
        "get_analytics_service",
        return_value=analytics_service,
    )
    mocker.patch.object(
        overview.StateManager,
        "get_jobs_service",
        return_value=jobs_service,
    )

    mocker.patch.object(overview.st, "markdown")
    mocker.patch.object(overview.st, "caption")
    mocker.patch.object(overview.st, "info")
    mocker.patch.object(overview.st, "error")
    mocker.patch.object(overview.st, "success")
    mocker.patch.object(overview.st, "warning")
    mocker.patch.object(overview.st, "plotly_chart")
    def mock_columns(spec):
        count = spec if isinstance(spec, int) else len(spec)
        columns = []
        for _ in range(count):
            column = MagicMock()
            column.__enter__ = Mock(return_value=column)
            column.__exit__ = Mock(return_value=False)
            columns.append(column)
        return columns

    mocker.patch.object(overview.st, "columns", side_effect=mock_columns)
    mocker.patch.object(overview.st, "spinner", return_value=MagicMock())
    mocker.patch.object(overview.st, "expander", return_value=MagicMock())
    mocker.patch.object(overview.st, "container", return_value=MagicMock())

    mocker.patch.object(overview, "get_icon", return_value="<svg></svg>")
    mocker.patch.object(overview, "divider")

    overview.render()

    jobs_service.fetch_jobs.assert_called()


def test_render_company_count_fallback_with_no_jobs(services, mocker):
    analytics_service, jobs_service = services

    analytics_service.get_companies_hiring_count.side_effect = AttributeError

    jobs_response = Mock()
    jobs_response.items = []
    jobs_service.fetch_jobs.return_value = jobs_response

    mocker.patch.object(
        overview.StateManager,
        "get_analytics_service",
        return_value=analytics_service,
    )
    mocker.patch.object(
        overview.StateManager,
        "get_jobs_service",
        return_value=jobs_service,
    )

    mocker.patch.object(overview.st, "markdown")
    mocker.patch.object(overview.st, "caption")
    mocker.patch.object(overview.st, "info")
    mocker.patch.object(overview.st, "error")
    mocker.patch.object(overview.st, "success")
    mocker.patch.object(overview.st, "warning")
    mocker.patch.object(overview.st, "plotly_chart")
    def mock_columns(spec):
        count = spec if isinstance(spec, int) else len(spec)
        columns = []
        for _ in range(count):
            column = MagicMock()
            column.__enter__ = Mock(return_value=column)
            column.__exit__ = Mock(return_value=False)
            columns.append(column)
        return columns

    mocker.patch.object(overview.st, "columns", side_effect=mock_columns)
    mocker.patch.object(overview.st, "spinner", return_value=MagicMock())
    mocker.patch.object(overview.st, "expander", return_value=MagicMock())
    mocker.patch.object(overview.st, "container", return_value=MagicMock())

    mocker.patch.object(overview, "get_icon", return_value="<svg></svg>")
    mocker.patch.object(overview, "divider")

    overview.render()

    jobs_service.fetch_jobs.assert_called()

@pytest.mark.parametrize(
    "empty_field",
    ["technology", "countries", "skills", "salary"],
)
def test_render_empty_analytics_data(services, mocker, empty_field):
    analytics_service, jobs_service = services

    if empty_field == "technology":
        analytics_service.get_technology_distribution.return_value = []
    elif empty_field == "countries":
        analytics_service.get_country_distribution.return_value = []
    elif empty_field == "skills":
        analytics_service.get_enriched_top_skills.return_value = []
    elif empty_field == "salary":
        analytics_service.get_enriched_salary.return_value = None

    jobs_response = Mock()
    jobs_response.items = []
    jobs_service.fetch_jobs.return_value = jobs_response

    mocker.patch.object(
        overview.StateManager,
        "get_analytics_service",
        return_value=analytics_service,
    )
    mocker.patch.object(
        overview.StateManager,
        "get_jobs_service",
        return_value=jobs_service,
    )

    mocker.patch.object(overview.st, "markdown")
    mocker.patch.object(overview.st, "caption")
    mocker.patch.object(overview.st, "info")
    mocker.patch.object(overview.st, "error")
    mocker.patch.object(overview.st, "success")
    mocker.patch.object(overview.st, "warning")
    mocker.patch.object(overview.st, "plotly_chart")
    def mock_columns(spec):
        count = spec if isinstance(spec, int) else len(spec)
        columns = []
        for _ in range(count):
            column = MagicMock()
            column.__enter__ = Mock(return_value=column)
            column.__exit__ = Mock(return_value=False)
            columns.append(column)
        return columns

    mocker.patch.object(overview.st, "columns", side_effect=mock_columns)
    mocker.patch.object(overview.st, "spinner", return_value=MagicMock())
    mocker.patch.object(overview.st, "expander", return_value=MagicMock())
    mocker.patch.object(overview.st, "container", return_value=MagicMock())

    mocker.patch.object(overview, "get_icon", return_value="<svg></svg>")
    mocker.patch.object(overview, "divider")

    overview.render()

    assert jobs_service.fetch_jobs.called

def test_render_technology_data_only_other(services, mocker):
    analytics_service, jobs_service = services

    analytics_service.get_technology_distribution.return_value = [
        {"category": "other", "count": 100},
    ]

    jobs_response = Mock()
    jobs_response.items = []
    jobs_service.fetch_jobs.return_value = jobs_response

    mocker.patch.object(
        overview.StateManager,
        "get_analytics_service",
        return_value=analytics_service,
    )
    mocker.patch.object(
        overview.StateManager,
        "get_jobs_service",
        return_value=jobs_service,
    )

    mocker.patch.object(overview.st, "markdown")
    caption_mock = mocker.patch.object(overview.st, "caption")
    mocker.patch.object(overview.st, "info")
    mocker.patch.object(overview.st, "error")
    mocker.patch.object(overview.st, "success")
    mocker.patch.object(overview.st, "warning")
    mocker.patch.object(overview.st, "plotly_chart")
    def mock_columns(spec):
        count = spec if isinstance(spec, int) else len(spec)
        columns = []
        for _ in range(count):
            column = MagicMock()
            column.__enter__ = Mock(return_value=column)
            column.__exit__ = Mock(return_value=False)
            columns.append(column)
        return columns

    mocker.patch.object(overview.st, "columns", side_effect=mock_columns)
    mocker.patch.object(overview.st, "spinner", return_value=MagicMock())
    mocker.patch.object(overview.st, "expander", return_value=MagicMock())
    mocker.patch.object(overview.st, "container", return_value=MagicMock())

    mocker.patch.object(overview, "get_icon", return_value="<svg></svg>")
    mocker.patch.object(overview, "divider")

    overview.render()

    caption_mock.assert_any_call("No technology data available")

def test_render_company_count_fallback_exception(services, mocker):
    analytics_service, jobs_service = services

    del analytics_service.get_companies_hiring_count

    jobs_service.fetch_jobs.side_effect = Exception("database unavailable")

    mocker.patch.object(
        overview.StateManager,
        "get_analytics_service",
        return_value=analytics_service,
    )
    mocker.patch.object(
        overview.StateManager,
        "get_jobs_service",
        return_value=jobs_service,
    )

    mocker.patch.object(overview.st, "markdown")
    mocker.patch.object(overview.st, "caption")
    mocker.patch.object(overview.st, "info")
    mocker.patch.object(overview.st, "error")
    mocker.patch.object(overview.st, "success")
    mocker.patch.object(overview.st, "warning")
    mocker.patch.object(overview.st, "plotly_chart")

    def mock_columns(spec):
        count = spec if isinstance(spec, int) else len(spec)
        columns = []
        for _ in range(count):
            column = MagicMock()
            column.__enter__ = Mock(return_value=column)
            column.__exit__ = Mock(return_value=False)
            columns.append(column)
        return columns

    mocker.patch.object(overview.st, "columns", side_effect=mock_columns)
    mocker.patch.object(overview.st, "spinner", return_value=MagicMock())
    mocker.patch.object(overview.st, "expander", return_value=MagicMock())
    mocker.patch.object(overview.st, "container", return_value=MagicMock())

    mocker.patch.object(overview, "get_icon", return_value="<svg></svg>")
    mocker.patch.object(overview, "divider")

    overview.render()

    assert jobs_service.fetch_jobs.called


def test_render_jobs_with_date_and_salary(services, mocker):
    analytics_service, jobs_service = services

    job = Mock()
    job.title = "Data Scientist"
    job.company_name = "Example Corp"
    job.location = "Nairobi"
    job.posted_date = datetime.now(timezone.utc)
    job.salary_min = 50000
    job.salary_max = 80000

    jobs_response = Mock()
    jobs_response.items = [job]
    jobs_service.fetch_jobs.return_value = jobs_response

    mocker.patch.object(
        overview.StateManager,
        "get_analytics_service",
        return_value=analytics_service,
    )
    mocker.patch.object(
        overview.StateManager,
        "get_jobs_service",
        return_value=jobs_service,
    )

    mocker.patch.object(overview.st, "markdown")
    mocker.patch.object(overview.st, "caption")
    mocker.patch.object(overview.st, "info")
    mocker.patch.object(overview.st, "error")
    mocker.patch.object(overview.st, "success")
    mocker.patch.object(overview.st, "warning")
    mocker.patch.object(overview.st, "plotly_chart")

    def mock_columns(spec):
        count = spec if isinstance(spec, int) else len(spec)
        columns = []
        for _ in range(count):
            column = MagicMock()
            column.__enter__ = Mock(return_value=column)
            column.__exit__ = Mock(return_value=False)
            columns.append(column)
        return columns

    mocker.patch.object(overview.st, "columns", side_effect=mock_columns)
    mocker.patch.object(overview.st, "spinner", return_value=MagicMock())
    mocker.patch.object(overview.st, "expander", return_value=MagicMock())
    mocker.patch.object(overview.st, "container", return_value=MagicMock())

    mocker.patch.object(overview, "get_icon", return_value="<svg></svg>")
    mocker.patch.object(overview, "divider")

    overview.render()

    assert jobs_service.fetch_jobs.called

def test_render_job_with_invalid_posted_date(services, mocker):
    analytics_service, jobs_service = services

    job = Mock()
    job.title = "Data Scientist"
    job.company_name = "Example Corp"
    job.location = "Nairobi"
    job.posted_date = "invalid-date"
    job.salary_min = None
    job.salary_max = None

    jobs_response = Mock()
    jobs_response.items = [job]
    jobs_service.fetch_jobs.return_value = jobs_response

    mocker.patch.object(
        overview.StateManager,
        "get_analytics_service",
        return_value=analytics_service,
    )
    mocker.patch.object(
        overview.StateManager,
        "get_jobs_service",
        return_value=jobs_service,
    )

    mocker.patch.object(overview.st, "markdown")
    caption_mock = mocker.patch.object(overview.st, "caption")
    mocker.patch.object(overview.st, "info")
    mocker.patch.object(overview.st, "error")
    mocker.patch.object(overview.st, "success")
    mocker.patch.object(overview.st, "warning")
    mocker.patch.object(overview.st, "plotly_chart")

    def mock_columns(spec):
        count = spec if isinstance(spec, int) else len(spec)
        columns = []
        for _ in range(count):
            column = MagicMock()
            column.__enter__ = Mock(return_value=column)
            column.__exit__ = Mock(return_value=False)
            columns.append(column)
        return columns

    mocker.patch.object(overview.st, "columns", side_effect=mock_columns)
    mocker.patch.object(overview.st, "spinner", return_value=MagicMock())
    mocker.patch.object(overview.st, "expander", return_value=MagicMock())
    mocker.patch.object(overview.st, "container", return_value=MagicMock())

    mocker.patch.object(overview, "get_icon", return_value="<svg></svg>")
    mocker.patch.object(overview, "divider")

    overview.render()

    caption_mock.assert_any_call("📅 Recently posted")

def test_render_job_with_posted_date_exception(services, mocker):
    analytics_service, jobs_service = services

    class BrokenDate:
        tzinfo = None

        def __sub__(self, other):
            raise ValueError("invalid date")

    job = Mock()
    job.title = "Data Scientist"
    job.company_name = "Example Corp"
    job.location = "Nairobi"
    job.posted_date = BrokenDate()
    job.salary_min = None
    job.salary_max = None

    jobs_response = Mock()
    jobs_response.items = [job]
    jobs_service.fetch_jobs.return_value = jobs_response

    mocker.patch.object(
        overview.StateManager,
        "get_analytics_service",
        return_value=analytics_service,
    )
    mocker.patch.object(
        overview.StateManager,
        "get_jobs_service",
        return_value=jobs_service,
    )

    mocker.patch.object(overview.st, "markdown")
    caption_mock = mocker.patch.object(overview.st, "caption")
    mocker.patch.object(overview.st, "info")
    mocker.patch.object(overview.st, "error")
    mocker.patch.object(overview.st, "success")
    mocker.patch.object(overview.st, "warning")
    mocker.patch.object(overview.st, "plotly_chart")

    def mock_columns(spec):
        count = spec if isinstance(spec, int) else len(spec)
        columns = []
        for _ in range(count):
            column = MagicMock()
            column.__enter__ = Mock(return_value=column)
            column.__exit__ = Mock(return_value=False)
            columns.append(column)
        return columns

    mocker.patch.object(overview.st, "columns", side_effect=mock_columns)
    mocker.patch.object(overview.st, "spinner", return_value=MagicMock())
    mocker.patch.object(overview.st, "expander", return_value=MagicMock())
    mocker.patch.object(overview.st, "container", return_value=MagicMock())

    mocker.patch.object(overview, "get_icon", return_value="<svg></svg>")
    mocker.patch.object(overview, "divider")

    overview.render()

    caption_mock.assert_any_call("📅 Recently posted")

@pytest.mark.parametrize(
    ("pipeline_status", "db_status"),
    [
        ("running", "operational"),
        ("failed", "degraded"),
        ("failed", "offline"),
    ],
)
def test_render_system_status_variants(services, mocker, pipeline_status, db_status):
    analytics_service, jobs_service = services

    analytics_service.get_pipeline_status.return_value = pipeline_status
    analytics_service.get_db_status.return_value = db_status

    jobs_response = Mock()
    jobs_response.items = []
    jobs_service.fetch_jobs.return_value = jobs_response

    mocker.patch.object(
        overview.StateManager,
        "get_analytics_service",
        return_value=analytics_service,
    )
    mocker.patch.object(
        overview.StateManager,
        "get_jobs_service",
        return_value=jobs_service,
    )

    mocker.patch.object(overview.st, "markdown")
    mocker.patch.object(overview.st, "caption")
    mocker.patch.object(overview.st, "info")
    mocker.patch.object(overview.st, "error")
    mocker.patch.object(overview.st, "success")
    mocker.patch.object(overview.st, "warning")
    mocker.patch.object(overview.st, "plotly_chart")

    def mock_columns(spec):
        count = spec if isinstance(spec, int) else len(spec)
        columns = []
        for _ in range(count):
            column = MagicMock()
            column.__enter__ = Mock(return_value=column)
            column.__exit__ = Mock(return_value=False)
            columns.append(column)
        return columns

    mocker.patch.object(overview.st, "columns", side_effect=mock_columns)
    mocker.patch.object(overview.st, "spinner", return_value=MagicMock())
    mocker.patch.object(overview.st, "expander", return_value=MagicMock())
    mocker.patch.object(overview.st, "container", return_value=MagicMock())

    mocker.patch.object(overview, "get_icon", return_value="<svg></svg>")
    mocker.patch.object(overview, "divider")

    overview.render()

def test_render_api_health_warning(services, mocker):
    analytics_service, jobs_service = services

    health_service = MagicMock()
    health_service.check.return_value.status = "degraded"

    mocker.patch.object(
        overview,
        "HealthService",
        return_value=health_service,
    )

    mocker.patch.object(
        overview.StateManager,
        "get_analytics_service",
        return_value=analytics_service,
    )
    mocker.patch.object(
        overview.StateManager,
        "get_jobs_service",
        return_value=jobs_service,
    )

    mocker.patch.object(overview.st, "markdown")
    mocker.patch.object(overview.st, "caption")
    mocker.patch.object(overview.st, "info")
    mocker.patch.object(overview.st, "error")
    mocker.patch.object(overview.st, "success")
    mocker.patch.object(overview.st, "warning")
    mocker.patch.object(overview.st, "plotly_chart")

    def mock_columns(spec):
        count = spec if isinstance(spec, int) else len(spec)
        columns = []
        for _ in range(count):
            column = MagicMock()
            column.__enter__ = Mock(return_value=column)
            column.__exit__ = Mock(return_value=False)
            columns.append(column)
        return columns

    mocker.patch.object(overview.st, "columns", side_effect=mock_columns)
    mocker.patch.object(overview.st, "spinner", return_value=MagicMock())
    mocker.patch.object(overview.st, "expander", return_value=MagicMock())
    mocker.patch.object(overview.st, "container", return_value=MagicMock())

    mocker.patch.object(overview, "get_icon", return_value="<svg></svg>")
    mocker.patch.object(overview, "divider")

    overview.render()

def test_render_api_health_exception(services, mocker):
    analytics_service, jobs_service = services

    health_service = MagicMock()
    health_service.check.side_effect = Exception("API unavailable")

    mocker.patch.object(
        overview,
        "HealthService",
        return_value=health_service,
    )

    mocker.patch.object(
        overview.StateManager,
        "get_analytics_service",
        return_value=analytics_service,
    )
    mocker.patch.object(
        overview.StateManager,
        "get_jobs_service",
        return_value=jobs_service,
    )

    mocker.patch.object(overview.st, "markdown")
    mocker.patch.object(overview.st, "caption")
    mocker.patch.object(overview.st, "info")
    mocker.patch.object(overview.st, "error")
    mocker.patch.object(overview.st, "success")
    mocker.patch.object(overview.st, "warning")
    mocker.patch.object(overview.st, "plotly_chart")

    def mock_columns(spec):
        count = spec if isinstance(spec, int) else len(spec)
        columns = []
        for _ in range(count):
            column = MagicMock()
            column.__enter__ = Mock(return_value=column)
            column.__exit__ = Mock(return_value=False)
            columns.append(column)
        return columns

    mocker.patch.object(overview.st, "columns", side_effect=mock_columns)
    mocker.patch.object(overview.st, "spinner", return_value=MagicMock())
    mocker.patch.object(overview.st, "expander", return_value=MagicMock())
    mocker.patch.object(overview.st, "container", return_value=MagicMock())

    mocker.patch.object(overview, "get_icon", return_value="<svg></svg>")
    mocker.patch.object(overview, "divider")

    overview.render()

def test_render_system_status_fallbacks(services, mocker):
    analytics_service, jobs_service = services

    analytics_service.get_last_etl_run.side_effect = Exception(
        "ETL unavailable"
    )
    analytics_service.get_pipeline_status.side_effect = Exception(
        "pipeline unavailable"
    )
    analytics_service.get_db_status.side_effect = Exception(
        "DB unavailable"
    )

    jobs_response = Mock()
    jobs_response.items = []
    jobs_service.fetch_jobs.return_value = jobs_response

    mocker.patch.object(
        overview.StateManager,
        "get_analytics_service",
        return_value=analytics_service,
    )
    mocker.patch.object(
        overview.StateManager,
        "get_jobs_service",
        return_value=jobs_service,
    )

    mocker.patch.object(overview.st, "markdown")
    mocker.patch.object(overview.st, "caption")
    mocker.patch.object(overview.st, "info")
    mocker.patch.object(overview.st, "error")
    mocker.patch.object(overview.st, "success")
    mocker.patch.object(overview.st, "warning")
    mocker.patch.object(overview.st, "plotly_chart")

    def mock_columns(spec):
        count = spec if isinstance(spec, int) else len(spec)
        columns = []
        for _ in range(count):
            column = MagicMock()
            column.__enter__ = Mock(return_value=column)
            column.__exit__ = Mock(return_value=False)
            columns.append(column)
        return columns

    mocker.patch.object(
        overview.st,
        "columns",
        side_effect=mock_columns,
    )
    mocker.patch.object(overview.st, "spinner", return_value=MagicMock())
    mocker.patch.object(overview.st, "expander", return_value=MagicMock())
    mocker.patch.object(overview.st, "container", return_value=MagicMock())

    mocker.patch.object(overview, "get_icon", return_value="<svg></svg>")
    mocker.patch.object(overview, "divider")

    overview.render()

def test_render_market_data_exception(services, mocker):
    analytics_service, jobs_service = services

    analytics_service.get_enriched_top_skills.side_effect = Exception(
        "Analytics unavailable"
    )

    mocker.patch.object(
        overview.StateManager,
        "get_analytics_service",
        return_value=analytics_service,
    )
    mocker.patch.object(
        overview.StateManager,
        "get_jobs_service",
        return_value=jobs_service,
    )

    show_error = mocker.patch.object(overview, "show_error")
    logger_exception = mocker.patch.object(
        overview.logger,
        "exception",
    )

    overview.render()

    show_error.assert_called_once_with(
        "Failed to load market data: Analytics unavailable"
    )
    logger_exception.assert_called_once_with("Overview page error")