"""Tests for dashboard analytics page."""

import sys
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, "dashboard")

from dashboard.pages import analytics  # noqa: E402


@pytest.fixture
def service():
    return Mock()


def context_manager_mock():
    mock = Mock()
    mock.__enter__ = Mock(return_value=mock)
    mock.__exit__ = Mock(return_value=False)
    return mock


# ============================================================
# render() delegation
# ============================================================


def test_render_delegates_to_dashboard():
    with patch.object(analytics, "render_analytics_dashboard") as render_dashboard:
        analytics.render()

    render_dashboard.assert_called_once_with()


# ============================================================
# render_skills_analytics
# ============================================================


def test_render_skills_analytics_success(service):
    service.get_enriched_top_skills.return_value = [
        {"skill": "Python", "count": 20},
        {"skill": "SQL", "count": 15},
    ]
    service.get_technology_distribution.return_value = [
        {"category": "Python", "count": 20},
        {"category": "SQL", "count": 15},
        {"category": "other", "count": 5},
    ]

    fig = Mock()
    columns = [context_manager_mock(), context_manager_mock()]

    with (
        patch.object(analytics, "section_header"),
        patch.object(analytics.st, "columns", return_value=columns),
        patch.object(
            analytics,
            "loading_spinner",
            return_value=context_manager_mock(),
        ),
        patch.object(
            analytics,
            "create_horizontal_bar_chart",
            return_value=fig,
        ) as create_chart,
        patch.object(analytics.st, "plotly_chart") as plotly_chart,
        patch.object(analytics.px, "pie", return_value=fig) as pie,
    ):
        analytics.render_skills_analytics(service)

    service.get_enriched_top_skills.assert_called_once_with(limit=15)
    service.get_technology_distribution.assert_called_once_with()

    create_chart.assert_called_once()
    pie.assert_called_once()

    assert create_chart.call_args[0][0].x_values == ["Python", "SQL"]
    assert create_chart.call_args[0][0].y_values == [20, 15]
    assert create_chart.call_args[0][0].title == "Top Skills"
    assert create_chart.call_args[0][0].color == "#00b894"

    assert plotly_chart.call_count == 2
    fig.update_layout.assert_called()


def test_render_skills_analytics_no_skills(service):
    service.get_enriched_top_skills.return_value = []
    service.get_technology_distribution.return_value = []

    columns = [context_manager_mock(), context_manager_mock()]

    with (
        patch.object(analytics, "section_header"),
        patch.object(analytics.st, "columns", return_value=columns),
        patch.object(
            analytics,
            "loading_spinner",
            return_value=context_manager_mock(),
        ),
        patch.object(analytics, "empty_state_analytics") as empty_state,
        patch.object(analytics.st, "info") as info,
    ):
        analytics.render_skills_analytics(service)

    empty_state.assert_called_once_with(
        title="No Skills Data",
        description="No skills data available.",
    )
    info.assert_called_once_with("No technology distribution data available")


def test_render_skills_analytics_no_filtered_technology(service):
    service.get_enriched_top_skills.return_value = []
    service.get_technology_distribution.return_value = [
        {"category": "other", "count": 10},
        {"category": "other", "count": 5},
    ]

    columns = [context_manager_mock(), context_manager_mock()]

    with (
        patch.object(analytics, "section_header"),
        patch.object(analytics.st, "columns", return_value=columns),
        patch.object(
            analytics,
            "loading_spinner",
            return_value=context_manager_mock(),
        ),
        patch.object(analytics, "empty_state_analytics"),
        patch.object(analytics.st, "info") as info,
    ):
        analytics.render_skills_analytics(service)

    info.assert_called_once_with("No technology categories found")


def test_render_skills_analytics_skills_exception(service):
    service.get_enriched_top_skills.side_effect = RuntimeError("skills database error")
    service.get_technology_distribution.return_value = []

    columns = [context_manager_mock(), context_manager_mock()]

    with (
        patch.object(analytics, "section_header"),
        patch.object(analytics.st, "columns", return_value=columns),
        patch.object(
            analytics,
            "loading_spinner",
            return_value=context_manager_mock(),
        ),
        patch.object(analytics, "show_error") as show_error,
        patch.object(analytics, "empty_state_analytics"),
        patch.object(analytics.st, "info"),
    ):
        analytics.render_skills_analytics(service)

    assert any("skills database error" in call.args[0] for call in show_error.call_args_list)


def test_render_skills_analytics_technology_exception(service):
    service.get_enriched_top_skills.return_value = []
    service.get_technology_distribution.side_effect = RuntimeError("technology database error")

    columns = [context_manager_mock(), context_manager_mock()]

    with (
        patch.object(analytics, "section_header"),
        patch.object(analytics.st, "columns", return_value=columns),
        patch.object(
            analytics,
            "loading_spinner",
            return_value=context_manager_mock(),
        ),
        patch.object(analytics, "empty_state_analytics"),
        patch.object(analytics.st, "info"),
        patch.object(analytics, "show_error") as show_error,
    ):
        analytics.render_skills_analytics(service)

    assert any("technology database error" in call.args[0] for call in show_error.call_args_list)


# ============================================================
# render_analytics_dashboard
# ============================================================


def test_render_analytics_dashboard_normal_flow(service):
    service.get_enriched_top_skills.return_value = [{"skill": "Python", "count": 10}]
    service.get_country_distribution.return_value = {"Kenya": 10}
    service.get_enriched_salary.return_value = {"average": 100000}

    with (
        patch.object(
            analytics.StateManager,
            "get_analytics_service",
            return_value=service,
        ) as get_analytics_service,
        patch.object(analytics, "get_icon", return_value="icon"),
        patch.object(analytics, "icon_button", return_value=False),
        patch.object(analytics, "timestamp"),
        patch.object(analytics, "render_kpi_cards") as render_kpi_cards,
        patch.object(analytics, "render_overview_analytics") as render_overview_analytics,
        patch.object(analytics, "render_location_analytics") as render_location_analytics,
        patch.object(analytics, "render_skills_analytics") as render_skills_analytics,
        patch.object(analytics, "render_company_analytics") as render_company_analytics,
        patch.object(analytics, "render_salary_analytics") as render_salary_analytics,
        patch.object(analytics, "render_employment_analytics") as render_employment_analytics,
        patch.object(analytics, "render_posting_trends") as render_posting_trends,
        patch.object(analytics, "render_language_analytics") as render_language_analytics,
        patch.object(analytics, "render_tech_analytics") as render_tech_analytics,
        patch.object(
            analytics.st, "columns", return_value=[context_manager_mock(), context_manager_mock()]
        ),
        patch.object(analytics.st, "tabs", return_value=[context_manager_mock() for _ in range(9)]),
    ):
        analytics.render_analytics_dashboard()

    get_analytics_service.assert_called_once_with()
    render_kpi_cards.assert_called_once_with(service)
    render_overview_analytics.assert_called_once_with(service)
    render_location_analytics.assert_called_once_with(service)
    render_skills_analytics.assert_called_once_with(service)
    render_company_analytics.assert_called_once_with(service)
    render_salary_analytics.assert_called_once_with(service)
    render_employment_analytics.assert_called_once_with(service)
    render_posting_trends.assert_called_once_with(service)
    render_language_analytics.assert_called_once_with(service)
    render_tech_analytics.assert_called_once_with(service)


def test_render_analytics_dashboard_refresh():
    service = Mock()

    with (
        patch.object(analytics.StateManager, "get_analytics_service", return_value=service),
        patch.object(analytics.StateManager, "clear_cache") as clear_cache,
        patch.object(analytics, "get_icon", return_value="icon"),
        patch.object(analytics, "icon_button", return_value=True),
        patch.object(analytics, "timestamp"),
        patch.object(analytics, "render_kpi_cards"),
        patch.object(analytics, "render_overview_analytics"),
        patch.object(analytics, "render_location_analytics"),
        patch.object(analytics, "render_skills_analytics"),
        patch.object(analytics, "render_company_analytics"),
        patch.object(analytics, "render_salary_analytics"),
        patch.object(analytics, "render_employment_analytics"),
        patch.object(analytics, "render_posting_trends"),
        patch.object(analytics, "render_language_analytics"),
        patch.object(analytics, "render_tech_analytics"),
        patch.object(
            analytics.st, "columns", return_value=[context_manager_mock(), context_manager_mock()]
        ),
        patch.object(analytics.st, "tabs", return_value=[context_manager_mock() for _ in range(9)]),
        patch.object(analytics.st, "spinner") as spinner,
        patch.object(analytics.time, "sleep") as sleep,
        patch.object(analytics.st, "rerun") as rerun,
    ):
        spinner.return_value.__enter__ = Mock()
        spinner.return_value.__exit__ = Mock(return_value=False)

        analytics.render_analytics_dashboard()

    clear_cache.assert_called_once_with()
    sleep.assert_called_once_with(0.5)
    rerun.assert_called_once_with()


# ============================================================
# render_company_analytics
# ============================================================


def test_render_company_analytics_success(service):
    company_chart_data = Mock()
    company_chart_data.x_values = ["Google", "Microsoft"]

    donut_data = Mock()
    donut_data.labels = ["Google", "Microsoft"]

    service.get_companies_chart.return_value = company_chart_data
    service.get_companies_distribution_chart.return_value = donut_data

    company_fig = Mock()
    donut_fig = Mock()

    columns = [context_manager_mock(), context_manager_mock()]

    with (
        patch.object(analytics, "section_header"),
        patch.object(analytics.st, "columns", return_value=columns),
        patch.object(
            analytics,
            "loading_spinner",
            return_value=context_manager_mock(),
        ),
        patch.object(
            analytics,
            "create_horizontal_bar_chart",
            return_value=company_fig,
        ) as create_bar_chart,
        patch.object(
            analytics,
            "create_donut_chart",
            return_value=donut_fig,
        ) as create_donut,
        patch.object(analytics.st, "plotly_chart") as plotly_chart,
    ):
        analytics.render_company_analytics(service)

    service.get_companies_chart.assert_called_once_with(limit=15)
    service.get_companies_distribution_chart.assert_called_once_with(limit=8)

    create_bar_chart.assert_called_once_with(company_chart_data)
    create_donut.assert_called_once_with(donut_data)

    assert company_chart_data.color == "#0984e3"
    assert plotly_chart.call_count == 2

    company_fig.update_layout.assert_called_once()
    donut_fig.update_layout.assert_called_once()


def test_render_company_analytics_no_company_data(service):
    company_chart_data = Mock()
    company_chart_data.x_values = []

    service.get_companies_chart.return_value = company_chart_data

    columns = [context_manager_mock(), context_manager_mock()]

    with (
        patch.object(analytics, "section_header"),
        patch.object(analytics.st, "columns", return_value=columns),
        patch.object(
            analytics,
            "loading_spinner",
            return_value=context_manager_mock(),
        ),
        patch.object(analytics, "empty_state_analytics") as empty_state,
        patch.object(
            analytics,
            "create_horizontal_bar_chart",
        ) as create_bar_chart,
        patch.object(
            analytics,
            "create_donut_chart",
        ) as create_donut,
    ):
        analytics.render_company_analytics(service)

    service.get_companies_chart.assert_called_once_with(limit=15)

    empty_state.assert_called_once_with(
        title="No Company Data",
        description="No company data available.",
    )

    create_bar_chart.assert_not_called()
    create_donut.assert_not_called()
    service.get_companies_distribution_chart.assert_not_called()


def test_render_company_analytics_no_distribution_labels(service):
    company_chart_data = Mock()
    company_chart_data.x_values = ["Google"]

    donut_data = Mock()
    donut_data.labels = []

    service.get_companies_chart.return_value = company_chart_data
    service.get_companies_distribution_chart.return_value = donut_data

    company_fig = Mock()

    columns = [context_manager_mock(), context_manager_mock()]

    with (
        patch.object(analytics, "section_header"),
        patch.object(analytics.st, "columns", return_value=columns),
        patch.object(
            analytics,
            "loading_spinner",
            return_value=context_manager_mock(),
        ),
        patch.object(
            analytics,
            "create_horizontal_bar_chart",
            return_value=company_fig,
        ),
        patch.object(analytics, "create_donut_chart") as create_donut,
        patch.object(analytics.st, "plotly_chart") as plotly_chart,
    ):
        analytics.render_company_analytics(service)

    service.get_companies_chart.assert_called_once_with(limit=15)
    service.get_companies_distribution_chart.assert_called_once_with(limit=8)

    create_donut.assert_not_called()
    assert plotly_chart.call_count == 1


def test_render_company_analytics_company_exception(service):
    service.get_companies_chart.side_effect = RuntimeError("company database error")

    columns = [context_manager_mock(), context_manager_mock()]

    with (
        patch.object(analytics, "section_header"),
        patch.object(analytics.st, "columns", return_value=columns),
        patch.object(
            analytics,
            "loading_spinner",
            return_value=context_manager_mock(),
        ),
        patch.object(analytics, "show_error") as show_error,
        patch.object(analytics, "create_donut_chart"),
        patch.object(analytics.st, "plotly_chart"),
    ):
        analytics.render_company_analytics(service)

    assert any("company database error" in call.args[0] for call in show_error.call_args_list)


def test_render_company_analytics_distribution_exception(service):
    company_chart_data = Mock()
    company_chart_data.x_values = ["Google"]

    service.get_companies_chart.return_value = company_chart_data
    service.get_companies_distribution_chart.side_effect = RuntimeError(
        "distribution database error"
    )

    company_fig = Mock()

    columns = [context_manager_mock(), context_manager_mock()]

    with (
        patch.object(analytics, "section_header"),
        patch.object(analytics.st, "columns", return_value=columns),
        patch.object(
            analytics,
            "loading_spinner",
            return_value=context_manager_mock(),
        ),
        patch.object(
            analytics,
            "create_horizontal_bar_chart",
            return_value=company_fig,
        ),
        patch.object(analytics, "show_error") as show_error,
        patch.object(analytics.st, "plotly_chart"),
    ):
        analytics.render_company_analytics(service)

    assert any("distribution database error" in call.args[0] for call in show_error.call_args_list)


# ============================================================
# render_overview_analytics
# ============================================================


def test_render_overview_analytics_success(service):
    service.get_tech_vs_non_tech.return_value = {"tech": 10, "non_tech": 5}
    service.get_english_vs_non_english.return_value = {"english": 8, "non_english": 7}
    service.get_country_distribution.return_value = [
        {"country": "Kenya", "count": 10},
        {"country": "Uganda", "count": 5},
    ]

    with (
        patch.object(analytics, "section_header"),
        patch.object(analytics, "divider"),
        patch.object(
            analytics,
            "loading_spinner",
            return_value=context_manager_mock(),
        ),
        patch.object(
            analytics.st,
            "columns",
            return_value=[context_manager_mock() for _ in range(4)],
        ),
    ):
        analytics.render_overview_analytics(service)

    service.get_tech_vs_non_tech.assert_called_once_with()
    service.get_english_vs_non_english.assert_called_once_with()
    service.get_country_distribution.assert_called_once_with()


def test_render_overview_analytics_exception(service):
    service.get_tech_vs_non_tech.side_effect = RuntimeError("database error")

    with (
        patch.object(analytics, "section_header"),
        patch.object(analytics, "show_error") as show_error,
    ):
        analytics.render_overview_analytics(service)

    show_error.assert_called_once()
    assert "database error" in show_error.call_args[0][0]


# ============================================================
# render_location_analytics
# ============================================================


def test_render_location_analytics_success(service):
    chart_data = Mock()
    chart_data.x_values = ["Nairobi", "Mombasa"]
    service.get_locations_chart.return_value = chart_data

    fig = Mock()

    with (
        patch.object(analytics, "section_header"),
        patch.object(
            analytics,
            "loading_spinner",
            return_value=context_manager_mock(),
        ),
        patch.object(
            analytics,
            "create_horizontal_bar_chart",
            return_value=fig,
        ) as create_chart,
        patch.object(analytics.st, "plotly_chart") as plotly_chart,
    ):
        analytics.render_location_analytics(service)

    service.get_locations_chart.assert_called_once_with(limit=15)
    create_chart.assert_called_once_with(chart_data)
    fig.update_layout.assert_called_once()
    plotly_chart.assert_called_once_with(fig, use_container_width=True)
    assert chart_data.color == "#0f3460"


def test_render_location_analytics_empty(service):
    chart_data = Mock()
    chart_data.x_values = []
    service.get_locations_chart.return_value = chart_data

    with (
        patch.object(analytics, "section_header"),
        patch.object(
            analytics,
            "loading_spinner",
            return_value=context_manager_mock(),
        ),
        patch.object(analytics, "empty_state_analytics") as empty_state,
        patch.object(analytics, "create_horizontal_bar_chart") as create_chart,
    ):
        analytics.render_location_analytics(service)

    service.get_locations_chart.assert_called_once_with(limit=15)
    empty_state.assert_called_once_with(
        title="No Location Data",
        description="No location data available.",
    )
    create_chart.assert_not_called()


def test_render_location_analytics_exception(service):
    service.get_locations_chart.side_effect = RuntimeError("database error")

    with (
        patch.object(analytics, "section_header"),
        patch.object(
            analytics,
            "loading_spinner",
            return_value=context_manager_mock(),
        ),
        patch.object(analytics, "show_error") as show_error,
    ):
        analytics.render_location_analytics(service)

    show_error.assert_called_once()
    assert "database error" in show_error.call_args[0][0]


# ============================================================
# render_kpi_cards
# ============================================================


def test_render_kpi_cards_success(service):
    service.get_enriched_top_skills.return_value = [{"skill": "Python", "count": 20}]
    service.get_country_distribution.return_value = [
        {"country": "Kenya", "count": 10},
        {"country": "Uganda", "count": 5},
    ]
    service.get_enriched_salary.return_value = {"average": 120000}
    service.get_companies_hiring_count.return_value = 25

    with (
        patch.object(
            analytics,
            "loading_spinner",
            return_value=context_manager_mock(),
        ),
        patch.object(
            analytics.st,
            "columns",
            return_value=[context_manager_mock() for _ in range(5)],
        ),
        patch.object(analytics, "divider"),
    ):
        analytics.render_kpi_cards(service)

    service.get_enriched_top_skills.assert_called_once_with(limit=5)
    service.get_country_distribution.assert_called_once_with()
    service.get_enriched_salary.assert_called_once_with()
    service.get_companies_hiring_count.assert_called_once_with()


def test_render_kpi_cards_companies_fallback(service):
    service.get_enriched_top_skills.return_value = []
    service.get_country_distribution.return_value = {}
    service.get_enriched_salary.return_value = {}
    service.get_companies_hiring_count.side_effect = AttributeError

    with (
        patch.object(
            analytics,
            "loading_spinner",
            return_value=context_manager_mock(),
        ),
        patch.object(
            analytics.st,
            "columns",
            return_value=[context_manager_mock() for _ in range(5)],
        ),
        patch.object(analytics, "divider"),
    ):
        analytics.render_kpi_cards(service)

    service.get_companies_hiring_count.assert_called_once_with()


def test_render_kpi_cards_exception(service):
    service.get_enriched_top_skills.side_effect = RuntimeError("analytics failure")

    with patch.object(analytics, "show_error") as show_error:
        analytics.render_kpi_cards(service)

    show_error.assert_called_once()
    assert "analytics failure" in show_error.call_args[0][0]


# ============================================================
# render_salary_analytics
# ============================================================


def test_render_salary_analytics_success(service):
    stats = Mock()
    stats.average = 100000
    stats.median = 90000
    stats.minimum = 50000
    stats.maximum = 200000
    stats.currency = "USD"
    stats.sample_size = 150

    hist_data = Mock()
    hist_data.bins = [50000, 75000, 100000]

    location_data = Mock()
    location_data.x_values = ["Nairobi", "Mombasa"]

    service.get_salary_statistics.return_value = stats
    service.get_salary_distribution_chart.return_value = hist_data
    service.get_salary_by_location_chart.return_value = location_data

    hist_fig = Mock()
    location_fig = Mock()

    columns = [context_manager_mock() for _ in range(2)]
    stats_columns = [context_manager_mock() for _ in range(4)]

    with (
        patch.object(analytics, "section_header"),
        patch.object(analytics, "loading_spinner", return_value=context_manager_mock()),
        patch.object(
            analytics.st,
            "columns",
            side_effect=[stats_columns, columns],
        ),
        patch.object(analytics, "create_histogram", return_value=hist_fig) as create_histogram,
        patch.object(analytics, "create_bar_chart", return_value=location_fig) as create_bar_chart,
        patch.object(analytics.st, "plotly_chart") as plotly_chart,
        patch.object(analytics.st, "metric") as metric,
        patch.object(analytics.st, "caption") as caption,
        patch.object(analytics.st, "markdown") as markdown,
    ):
        analytics.render_salary_analytics(service)

    service.get_salary_statistics.assert_called_once_with()
    service.get_salary_distribution_chart.assert_called_once_with()
    service.get_salary_by_location_chart.assert_called_once_with(limit=10)

    assert metric.call_count == 4
    caption.assert_called_once_with("Based on 150 job postings")
    markdown.assert_called_once_with("---")

    create_histogram.assert_called_once_with(hist_data)
    create_bar_chart.assert_called_once_with(location_data)

    assert hist_data.color == "#e94560"
    assert location_data.color == "#fdcb6e"

    assert hist_fig.update_layout.call_count == 1
    assert location_fig.update_layout.call_count == 1
    assert plotly_chart.call_count == 2


def test_render_salary_analytics_no_salary_statistics(service):
    service.get_salary_statistics.return_value = None

    hist_data = Mock()
    hist_data.bins = []

    location_data = Mock()
    location_data.x_values = []

    service.get_salary_distribution_chart.return_value = hist_data
    service.get_salary_by_location_chart.return_value = location_data

    columns = [context_manager_mock() for _ in range(2)]

    with (
        patch.object(analytics, "section_header"),
        patch.object(analytics, "loading_spinner", return_value=context_manager_mock()),
        patch.object(analytics.st, "columns", return_value=columns),
        patch.object(analytics, "empty_state_analytics") as empty_state,
        patch.object(analytics.st, "metric") as metric,
        patch.object(analytics.st, "caption") as caption,
        patch.object(analytics.st, "markdown") as markdown,
    ):
        analytics.render_salary_analytics(service)

    metric.assert_not_called()
    caption.assert_not_called()
    markdown.assert_not_called()

    assert empty_state.call_count == 2


def test_render_salary_analytics_no_salary_distribution(service):
    stats = Mock()
    stats.average = 100000
    stats.median = 90000
    stats.minimum = 50000
    stats.maximum = 200000
    stats.currency = "USD"
    stats.sample_size = 100

    hist_data = Mock()
    hist_data.bins = []

    location_data = Mock()
    location_data.x_values = ["Nairobi"]

    service.get_salary_statistics.return_value = stats
    service.get_salary_distribution_chart.return_value = hist_data
    service.get_salary_by_location_chart.return_value = location_data

    columns = [context_manager_mock() for _ in range(2)]
    stats_columns = [context_manager_mock() for _ in range(4)]

    with (
        patch.object(analytics, "section_header"),
        patch.object(analytics, "loading_spinner", return_value=context_manager_mock()),
        patch.object(
            analytics.st,
            "columns",
            side_effect=[stats_columns, columns],
        ),
        patch.object(analytics, "empty_state_analytics") as empty_state,
        patch.object(analytics, "create_bar_chart", return_value=Mock()),
        patch.object(analytics.st, "plotly_chart"),
        patch.object(analytics.st, "metric"),
        patch.object(analytics.st, "caption"),
        patch.object(analytics.st, "markdown"),
    ):
        analytics.render_salary_analytics(service)

    empty_state.assert_called_once_with(
        title="No Distribution Data",
        description="No salary distribution data available.",
    )


def test_render_salary_analytics_no_location_salary_data(service):
    stats = None

    hist_data = Mock()
    hist_data.bins = [50000, 75000]

    location_data = Mock()
    location_data.x_values = []

    service.get_salary_statistics.return_value = stats
    service.get_salary_distribution_chart.return_value = hist_data
    service.get_salary_by_location_chart.return_value = location_data

    columns = [context_manager_mock() for _ in range(2)]

    with (
        patch.object(analytics, "section_header"),
        patch.object(analytics, "loading_spinner", return_value=context_manager_mock()),
        patch.object(analytics.st, "columns", return_value=columns),
        patch.object(analytics, "create_histogram", return_value=Mock()),
        patch.object(analytics.st, "plotly_chart"),
        patch.object(analytics, "empty_state_analytics") as empty_state,
    ):
        analytics.render_salary_analytics(service)

    empty_state.assert_called_once_with(
        title="No Location Salary Data",
        description="No location salary data available.",
    )


def test_render_salary_analytics_statistics_exception(service):
    service.get_salary_statistics.side_effect = RuntimeError("statistics database error")

    hist_data = Mock()
    hist_data.bins = []

    location_data = Mock()
    location_data.x_values = []

    service.get_salary_distribution_chart.return_value = hist_data
    service.get_salary_by_location_chart.return_value = location_data

    columns = [context_manager_mock() for _ in range(2)]

    with (
        patch.object(analytics, "section_header"),
        patch.object(analytics, "loading_spinner", return_value=context_manager_mock()),
        patch.object(analytics.st, "columns", return_value=columns),
        patch.object(analytics, "show_error") as show_error,
        patch.object(analytics, "empty_state_analytics"),
    ):
        analytics.render_salary_analytics(service)

    assert any("statistics database error" in call.args[0] for call in show_error.call_args_list)


def test_render_salary_analytics_distribution_exception(service):
    service.get_salary_statistics.return_value = None
    service.get_salary_distribution_chart.side_effect = RuntimeError("distribution database error")

    location_data = Mock()
    location_data.x_values = []

    service.get_salary_by_location_chart.return_value = location_data

    columns = [context_manager_mock() for _ in range(2)]

    with (
        patch.object(analytics, "section_header"),
        patch.object(analytics, "loading_spinner", return_value=context_manager_mock()),
        patch.object(analytics.st, "columns", return_value=columns),
        patch.object(analytics, "show_error") as show_error,
        patch.object(analytics, "empty_state_analytics"),
    ):
        analytics.render_salary_analytics(service)

    assert any("distribution database error" in call.args[0] for call in show_error.call_args_list)


def test_render_salary_analytics_location_exception(service):
    service.get_salary_statistics.return_value = None

    hist_data = Mock()
    hist_data.bins = []

    service.get_salary_distribution_chart.return_value = hist_data
    service.get_salary_by_location_chart.side_effect = RuntimeError(
        "location salary database error"
    )

    columns = [context_manager_mock() for _ in range(2)]

    with (
        patch.object(analytics, "section_header"),
        patch.object(analytics, "loading_spinner", return_value=context_manager_mock()),
        patch.object(analytics.st, "columns", return_value=columns),
        patch.object(analytics, "show_error") as show_error,
        patch.object(analytics, "empty_state_analytics"),
    ):
        analytics.render_salary_analytics(service)

    assert any(
        "location salary database error" in call.args[0] for call in show_error.call_args_list
    )


# ============================================================
# render_employment_analytics
# ============================================================


def test_render_employment_analytics_success(service):
    donut_data = Mock()
    donut_data.labels = ["Full-time", "Part-time"]

    bar_data = Mock()
    bar_data.x_values = ["Full-time", "Part-time"]

    service.get_employment_types_chart.return_value = donut_data
    service.get_employment_types_bar_chart.return_value = bar_data

    donut_fig = Mock()
    bar_fig = Mock()

    columns = [context_manager_mock(), context_manager_mock()]

    with (
        patch.object(analytics, "section_header"),
        patch.object(analytics.st, "columns", return_value=columns),
        patch.object(
            analytics,
            "loading_spinner",
            return_value=context_manager_mock(),
        ),
        patch.object(
            analytics,
            "create_donut_chart",
            return_value=donut_fig,
        ) as create_donut,
        patch.object(
            analytics,
            "create_bar_chart",
            return_value=bar_fig,
        ) as create_bar_chart,
        patch.object(analytics.st, "plotly_chart") as plotly_chart,
    ):
        analytics.render_employment_analytics(service)

    service.get_employment_types_chart.assert_called_once_with()
    service.get_employment_types_bar_chart.assert_called_once_with()

    create_donut.assert_called_once_with(donut_data)
    create_bar_chart.assert_called_once_with(bar_data)

    assert bar_data.color == "#6c5ce7"

    donut_fig.update_layout.assert_called_once()
    bar_fig.update_layout.assert_called_once()

    assert plotly_chart.call_count == 2


def test_render_employment_analytics_no_donut_data(service):
    donut_data = Mock()
    donut_data.labels = []

    bar_data = Mock()
    bar_data.x_values = ["Full-time"]

    service.get_employment_types_chart.return_value = donut_data
    service.get_employment_types_bar_chart.return_value = bar_data

    bar_fig = Mock()

    columns = [context_manager_mock(), context_manager_mock()]

    with (
        patch.object(analytics, "section_header"),
        patch.object(analytics.st, "columns", return_value=columns),
        patch.object(
            analytics,
            "loading_spinner",
            return_value=context_manager_mock(),
        ),
        patch.object(analytics, "empty_state_analytics") as empty_state,
        patch.object(
            analytics,
            "create_donut_chart",
        ) as create_donut,
        patch.object(
            analytics,
            "create_bar_chart",
            return_value=bar_fig,
        ),
        patch.object(analytics.st, "plotly_chart"),
    ):
        analytics.render_employment_analytics(service)

    empty_state.assert_called_once_with(
        title="No Employment Data",
        description="No employment type data available.",
    )

    create_donut.assert_not_called()
    service.get_employment_types_bar_chart.assert_called_once_with()


def test_render_employment_analytics_no_bar_data(service):
    donut_data = Mock()
    donut_data.labels = ["Full-time", "Part-time"]

    bar_data = Mock()
    bar_data.x_values = []

    service.get_employment_types_chart.return_value = donut_data
    service.get_employment_types_bar_chart.return_value = bar_data

    donut_fig = Mock()

    columns = [context_manager_mock(), context_manager_mock()]

    with (
        patch.object(analytics, "section_header"),
        patch.object(analytics.st, "columns", return_value=columns),
        patch.object(
            analytics,
            "loading_spinner",
            return_value=context_manager_mock(),
        ),
        patch.object(
            analytics,
            "create_donut_chart",
            return_value=donut_fig,
        ),
        patch.object(analytics, "create_bar_chart") as create_bar_chart,
        patch.object(analytics.st, "plotly_chart") as plotly_chart,
    ):
        analytics.render_employment_analytics(service)

    create_bar_chart.assert_not_called()
    assert plotly_chart.call_count == 1


def test_render_employment_analytics_donut_exception(service):
    service.get_employment_types_chart.side_effect = RuntimeError("employment types database error")

    bar_data = Mock()
    bar_data.x_values = []

    service.get_employment_types_bar_chart.return_value = bar_data

    columns = [context_manager_mock(), context_manager_mock()]

    with (
        patch.object(analytics, "section_header"),
        patch.object(analytics.st, "columns", return_value=columns),
        patch.object(
            analytics,
            "loading_spinner",
            return_value=context_manager_mock(),
        ),
        patch.object(analytics, "show_error") as show_error,
    ):
        analytics.render_employment_analytics(service)

    assert any(
        "employment types database error" in call.args[0] for call in show_error.call_args_list
    )


def test_render_employment_analytics_bar_exception(service):
    donut_data = Mock()
    donut_data.labels = []

    service.get_employment_types_chart.return_value = donut_data
    service.get_employment_types_bar_chart.side_effect = RuntimeError(
        "employment bar database error"
    )

    columns = [context_manager_mock(), context_manager_mock()]

    with (
        patch.object(analytics, "section_header"),
        patch.object(analytics.st, "columns", return_value=columns),
        patch.object(
            analytics,
            "loading_spinner",
            return_value=context_manager_mock(),
        ),
        patch.object(analytics, "show_error") as show_error,
        patch.object(analytics, "empty_state_analytics"),
    ):
        analytics.render_employment_analytics(service)

    assert any(
        "employment bar database error" in call.args[0] for call in show_error.call_args_list
    )


def test_render_posting_trends_success(service):
    cumulative_data = Mock()
    cumulative_data.x_values = ["2026-09-01", "2026-09-02"]

    daily_data = Mock()
    daily_data.x_values = ["2026-09-01", "2026-09-02"]

    service.get_posting_trend_chart.return_value = cumulative_data
    service.get_daily_posting_trend_chart.return_value = daily_data

    fig = Mock()
    fig_daily = Mock()

    with (
        patch.object(analytics, "section_header"),
        patch.object(
            analytics.st,
            "columns",
            return_value=[context_manager_mock(), context_manager_mock()],
        ),
        patch.object(analytics.st, "selectbox", return_value=30) as selectbox,
        patch.object(
            analytics,
            "loading_spinner",
            return_value=context_manager_mock(),
        ),
        patch.object(
            analytics,
            "create_line_chart",
            side_effect=[fig, fig_daily],
        ) as create_chart,
        patch.object(analytics.st, "plotly_chart") as plotly_chart,
    ):
        analytics.render_posting_trends(service)

    selectbox.assert_called_once()
    service.get_posting_trend_chart.assert_called_once_with(days=30)
    service.get_daily_posting_trend_chart.assert_called_once_with(days=30)

    assert cumulative_data.color == "#0f3460"
    assert cumulative_data.fill_area is True
    assert daily_data.color == "#e94560"

    assert create_chart.call_count == 2
    fig.update_layout.assert_called_once()
    fig_daily.update_layout.assert_called_once()
    assert plotly_chart.call_count == 2


def test_render_posting_trends_no_cumulative_data(service):
    cumulative_data = Mock()
    cumulative_data.x_values = []

    service.get_posting_trend_chart.return_value = cumulative_data

    with (
        patch.object(analytics, "section_header"),
        patch.object(
            analytics.st,
            "columns",
            return_value=[context_manager_mock(), context_manager_mock()],
        ),
        patch.object(analytics.st, "selectbox", return_value=30),
        patch.object(
            analytics,
            "loading_spinner",
            return_value=context_manager_mock(),
        ),
        patch.object(analytics, "empty_state_analytics") as empty_state,
        patch.object(analytics, "create_line_chart") as create_chart,
    ):
        analytics.render_posting_trends(service)

    service.get_posting_trend_chart.assert_called_once_with(days=30)
    service.get_daily_posting_trend_chart.assert_not_called()

    empty_state.assert_called_once_with(
        title="No Trend Data",
        description="No posting trend data available.",
    )
    create_chart.assert_not_called()


def test_render_posting_trends_daily_data_empty(service):
    cumulative_data = Mock()
    cumulative_data.x_values = ["2026-09-01"]

    daily_data = Mock()
    daily_data.x_values = []

    service.get_posting_trend_chart.return_value = cumulative_data
    service.get_daily_posting_trend_chart.return_value = daily_data

    fig = Mock()

    with (
        patch.object(analytics, "section_header"),
        patch.object(
            analytics.st,
            "columns",
            return_value=[context_manager_mock(), context_manager_mock()],
        ),
        patch.object(analytics.st, "selectbox", return_value=30),
        patch.object(
            analytics,
            "loading_spinner",
            return_value=context_manager_mock(),
        ),
        patch.object(
            analytics,
            "create_line_chart",
            return_value=fig,
        ) as create_chart,
        patch.object(analytics.st, "plotly_chart") as plotly_chart,
    ):
        analytics.render_posting_trends(service)

    service.get_posting_trend_chart.assert_called_once_with(days=30)
    service.get_daily_posting_trend_chart.assert_called_once_with(days=30)

    assert cumulative_data.color == "#0f3460"
    assert cumulative_data.fill_area is True
    assert create_chart.call_count == 1
    plotly_chart.assert_called_once_with(fig, use_container_width=True)


def test_render_posting_trends_exception(service):
    service.get_posting_trend_chart.side_effect = RuntimeError("database error")

    with (
        patch.object(analytics, "section_header"),
        patch.object(
            analytics.st,
            "columns",
            return_value=[context_manager_mock(), context_manager_mock()],
        ),
        patch.object(analytics.st, "selectbox", return_value=30),
        patch.object(
            analytics,
            "loading_spinner",
            return_value=context_manager_mock(),
        ),
        patch.object(analytics, "show_error") as show_error,
    ):
        analytics.render_posting_trends(service)

    show_error.assert_called_once()
    assert "database error" in show_error.call_args[0][0]


def test_render_language_analytics_success(service):
    lang_dist = [
        {"language": "English", "count": 80},
        {"language": "French", "count": 20},
    ]
    english_stats = {
        "english_count": 80,
        "non_english_count": 20,
        "english_percentage": 80.0,
    }
    lang_by_country = [
        {"country": "Kenya", "language": "English", "count": 50},
        {"country": "France", "language": "French", "count": 20},
    ]
    salary_by_lang = [
        {"language": "English", "average_salary": 80000},
        {"language": "French", "average_salary": 70000},
    ]

    service.get_language_distribution.return_value = lang_dist
    service.get_english_vs_non_english.return_value = english_stats
    service.get_language_by_country.return_value = lang_by_country
    service.get_language_salary_stats.return_value = salary_by_lang

    pie_fig = Mock()
    country_fig = Mock()
    salary_fig = Mock()

    with (
        patch.object(analytics, "section_header"),
        patch.object(
            analytics,
            "loading_spinner",
            return_value=context_manager_mock(),
        ),
        patch.object(
            analytics.st,
            "columns",
            return_value=[
                context_manager_mock(),
                context_manager_mock(),
            ],
        ),
        patch.object(analytics.px, "pie", return_value=pie_fig) as pie,
        patch.object(analytics.px, "bar", side_effect=[country_fig, salary_fig]) as bar,
        patch.object(analytics, "get_icon", return_value="<svg>") as get_icon,
        patch.object(analytics, "divider"),
        patch.object(analytics.st, "plotly_chart") as plotly_chart,
    ):
        analytics.render_language_analytics(service)

    service.get_language_distribution.assert_called_once_with()
    service.get_english_vs_non_english.assert_called_once_with()
    service.get_language_by_country.assert_called_once_with()
    service.get_language_salary_stats.assert_called_once_with()

    pie.assert_called_once()
    assert bar.call_count == 2
    assert get_icon.call_count == 3

    pie_fig.update_traces.assert_called_once()
    pie_fig.update_layout.assert_called_once()
    country_fig.update_layout.assert_called_once()
    salary_fig.update_layout.assert_called_once()

    assert plotly_chart.call_count == 3


def test_render_language_analytics_no_language_data(service):
    service.get_language_distribution.return_value = []

    with (
        patch.object(analytics, "section_header"),
        patch.object(
            analytics,
            "loading_spinner",
            return_value=context_manager_mock(),
        ),
        patch.object(analytics, "empty_state_analytics") as empty_state,
    ):
        analytics.render_language_analytics(service)

    service.get_language_distribution.assert_called_once_with()
    empty_state.assert_called_once_with(
        title="No Language Data",
        description="No language data available.",
    )
    service.get_english_vs_non_english.assert_not_called()


def test_render_language_analytics_no_english_stats(service):
    service.get_language_distribution.return_value = [
        {"language": "English", "count": 100},
    ]
    service.get_english_vs_non_english.return_value = None
    service.get_language_salary_stats.return_value = None

    pie_fig = Mock()

    with (
        patch.object(analytics, "section_header"),
        patch.object(
            analytics,
            "loading_spinner",
            return_value=context_manager_mock(),
        ),
        patch.object(
            analytics.st,
            "columns",
            return_value=[
                context_manager_mock(),
                context_manager_mock(),
            ],
        ),
        patch.object(analytics.px, "pie", return_value=pie_fig),
        patch.object(analytics, "divider"),
        patch.object(analytics.st, "plotly_chart"),
    ):
        analytics.render_language_analytics(service)

    service.get_language_distribution.assert_called_once_with()
    service.get_english_vs_non_english.assert_called_once_with()
    service.get_language_by_country.assert_not_called()
    service.get_language_salary_stats.assert_called_once_with()


def test_render_language_analytics_no_country_data(service):
    service.get_language_distribution.return_value = [
        {"language": "English", "count": 100},
    ]
    service.get_english_vs_non_english.return_value = {
        "english_count": 100,
        "non_english_count": 0,
        "english_percentage": 100.0,
    }
    service.get_language_by_country.return_value = []
    service.get_language_salary_stats.return_value = None

    pie_fig = Mock()

    with (
        patch.object(analytics, "section_header"),
        patch.object(
            analytics,
            "loading_spinner",
            return_value=context_manager_mock(),
        ),
        patch.object(
            analytics.st,
            "columns",
            return_value=[
                context_manager_mock(),
                context_manager_mock(),
            ],
        ),
        patch.object(analytics.px, "pie", return_value=pie_fig),
        patch.object(analytics, "get_icon", return_value="<svg>"),
        patch.object(analytics, "divider"),
        patch.object(analytics.st, "plotly_chart"),
    ):
        analytics.render_language_analytics(service)

    service.get_english_vs_non_english.assert_called_once_with()
    service.get_language_by_country.assert_called_once_with()
    service.get_language_salary_stats.assert_called_once_with()


def test_render_language_analytics_no_salary_data(service):
    service.get_language_distribution.return_value = [
        {"language": "English", "count": 100},
    ]
    service.get_english_vs_non_english.return_value = None
    service.get_language_salary_stats.return_value = []

    pie_fig = Mock()

    with (
        patch.object(analytics, "section_header"),
        patch.object(
            analytics,
            "loading_spinner",
            return_value=context_manager_mock(),
        ),
        patch.object(
            analytics.st,
            "columns",
            return_value=[
                context_manager_mock(),
                context_manager_mock(),
            ],
        ),
        patch.object(analytics.px, "pie", return_value=pie_fig),
        patch.object(analytics, "divider"),
        patch.object(analytics.st, "plotly_chart"),
    ):
        analytics.render_language_analytics(service)

    service.get_language_salary_stats.assert_called_once_with()


def test_render_language_analytics_exception(service):
    service.get_language_distribution.side_effect = RuntimeError("database error")

    with (
        patch.object(analytics, "section_header"),
        patch.object(
            analytics,
            "loading_spinner",
            return_value=context_manager_mock(),
        ),
        patch.object(analytics, "show_error") as show_error,
    ):
        analytics.render_language_analytics(service)

    show_error.assert_called_once()
    assert "database error" in show_error.call_args[0][0]


def test_render_tech_analytics_success(service):
    tech_stats = {
        "total_count": 1000,
        "tech_count": 600,
        "non_tech_count": 400,
        "tech_percentage": 60.0,
    }
    tech_categories = [
        {"category": "Software", "count": 300},
        {"category": "Data", "count": 200},
    ]
    tech_by_country = [
        {"country": "Kenya", "tech_percentage": 65.0},
        {"country": "Germany", "tech_percentage": 55.0},
    ]
    tech_skills = [
        {"skill": "Python", "count": 250},
        {"skill": "SQL", "count": 200},
    ]
    tech_salary = {
        "average": 80000,
        "median": 75000,
        "minimum": 40000,
        "maximum": 120000,
        "sample_size": 500,
    }

    service.get_tech_vs_non_tech.return_value = tech_stats
    service.get_tech_category_distribution.return_value = tech_categories
    service.get_tech_by_country.return_value = tech_by_country
    service.get_tech_skills.return_value = tech_skills
    service.get_tech_salary_stats.return_value = tech_salary

    category_fig = Mock()
    country_fig = Mock()
    skills_fig = Mock()

    with (
        patch.object(analytics, "section_header"),
        patch.object(
            analytics,
            "loading_spinner",
            return_value=context_manager_mock(),
        ),
        patch.object(
            analytics.st,
            "columns",
            side_effect=[
                [
                    context_manager_mock(),
                    context_manager_mock(),
                    context_manager_mock(),
                    context_manager_mock(),
                ],
                [
                    context_manager_mock(),
                    context_manager_mock(),
                ],
                [
                    context_manager_mock(),
                    context_manager_mock(),
                    context_manager_mock(),
                    context_manager_mock(),
                ],
            ],
        ),
        patch.object(
            analytics,
            "get_icon",
            return_value="<svg>",
        ) as get_icon,
        patch.object(analytics, "divider") as divider,
        patch.object(
            analytics.px,
            "pie",
            return_value=category_fig,
        ) as pie,
        patch.object(
            analytics.px,
            "bar",
            side_effect=[country_fig, skills_fig],
        ) as bar,
        patch.object(analytics.st, "plotly_chart") as plotly_chart,
        patch.object(analytics.st, "metric") as metric,
    ):
        analytics.render_tech_analytics(service)

    service.get_tech_vs_non_tech.assert_called_once_with()
    service.get_tech_category_distribution.assert_called_once_with()
    service.get_tech_by_country.assert_called_once_with()
    service.get_tech_skills.assert_called_once_with(limit=20)
    service.get_tech_salary_stats.assert_called_once_with()

    assert pie.call_count == 1
    assert bar.call_count == 2
    assert plotly_chart.call_count == 3

    category_fig.update_traces.assert_called_once()
    category_fig.update_layout.assert_called_once()
    country_fig.update_layout.assert_called_once()
    skills_fig.update_layout.assert_called_once()

    assert get_icon.call_count == 6
    assert divider.call_count == 2
    assert metric.call_count == 4


def test_render_tech_analytics_empty_optional_data(service):
    service.get_tech_vs_non_tech.return_value = {
        "total_count": 100,
        "tech_count": 60,
        "non_tech_count": 40,
        "tech_percentage": 60.0,
    }
    service.get_tech_category_distribution.return_value = []
    service.get_tech_by_country.return_value = []
    service.get_tech_skills.return_value = []
    service.get_tech_salary_stats.return_value = None

    with (
        patch.object(analytics, "section_header"),
        patch.object(
            analytics,
            "loading_spinner",
            return_value=context_manager_mock(),
        ),
        patch.object(
            analytics.st,
            "columns",
            side_effect=[
                [
                    context_manager_mock(),
                    context_manager_mock(),
                    context_manager_mock(),
                    context_manager_mock(),
                ],
                [
                    context_manager_mock(),
                    context_manager_mock(),
                ],
            ],
        ),
        patch.object(analytics, "get_icon", return_value="<svg>"),
        patch.object(analytics, "divider"),
        patch.object(analytics.st, "plotly_chart") as plotly_chart,
    ):
        analytics.render_tech_analytics(service)

    service.get_tech_category_distribution.assert_called_once_with()
    service.get_tech_by_country.assert_called_once_with()
    service.get_tech_skills.assert_called_once_with(limit=20)
    service.get_tech_salary_stats.assert_called_once_with()
    plotly_chart.assert_not_called()


def test_render_tech_analytics_salary_na_values(service):
    service.get_tech_vs_non_tech.return_value = {
        "total_count": 100,
        "tech_count": 60,
        "non_tech_count": 40,
        "tech_percentage": 60.0,
    }
    service.get_tech_category_distribution.return_value = []
    service.get_tech_by_country.return_value = []
    service.get_tech_skills.return_value = []
    service.get_tech_salary_stats.return_value = {
        "average": None,
        "median": None,
        "minimum": None,
        "maximum": None,
        "sample_size": 0,
    }

    with (
        patch.object(analytics, "section_header"),
        patch.object(
            analytics,
            "loading_spinner",
            return_value=context_manager_mock(),
        ),
        patch.object(
            analytics.st,
            "columns",
            side_effect=[
                [
                    context_manager_mock(),
                    context_manager_mock(),
                    context_manager_mock(),
                    context_manager_mock(),
                ],
                [
                    context_manager_mock(),
                    context_manager_mock(),
                ],
                [
                    context_manager_mock(),
                    context_manager_mock(),
                    context_manager_mock(),
                    context_manager_mock(),
                ],
            ],
        ),
        patch.object(analytics, "get_icon", return_value="<svg>"),
        patch.object(analytics, "divider"),
        patch.object(analytics.st, "plotly_chart"),
        patch.object(analytics.st, "metric") as metric,
    ):
        analytics.render_tech_analytics(service)

    assert metric.call_count == 4
    metric.assert_any_call("Average", "N/A")
    metric.assert_any_call("Median", "N/A")
    metric.assert_any_call("Minimum", "N/A")
    metric.assert_any_call("Maximum", "N/A")


def test_render_tech_analytics_exception(service):
    service.get_tech_vs_non_tech.side_effect = RuntimeError("database error")

    with (
        patch.object(analytics, "section_header"),
        patch.object(
            analytics,
            "loading_spinner",
            return_value=context_manager_mock(),
        ),
        patch.object(analytics, "show_error") as show_error,
    ):
        analytics.render_tech_analytics(service)

    show_error.assert_called_once()
    assert "database error" in show_error.call_args[0][0]
