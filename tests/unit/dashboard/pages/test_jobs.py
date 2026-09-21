from unittest.mock import MagicMock, Mock

import pytest

from dashboard.pages import jobs


@pytest.fixture(autouse=True)
def mock_streamlit(mocker):
    mocker.patch.object(jobs.st, "markdown")
    mocker.patch.object(jobs.st, "toggle", return_value=True)
    mocker.patch.object(jobs.st, "columns", side_effect=lambda spec: [
        MagicMock(__enter__=Mock(), __exit__=Mock(return_value=False))
        for _ in range(len(spec))
    ])
    mocker.patch.object(jobs.st, "cache_data")
    mocker.patch.object(jobs.st, "rerun")
    mocker.patch.object(jobs, "get_icon", return_value="<svg></svg>")
    mocker.patch.object(jobs, "render_filters", return_value={})
    mocker.patch.object(jobs, "render_job_card")
    mocker.patch.object(jobs, "render_job_detail")
    mocker.patch.object(jobs, "render_pagination")
    mocker.patch.object(jobs, "render_empty_state")
    mocker.patch.object(jobs, "show_error")



def test_render_jobs_success(mocker):
    service = Mock()
    job = Mock()
    job.id = 1

    response = Mock()
    response.items = [job]
    response.total = 1
    response.total_pages = 1

    mocker.patch.object(jobs, "get_jobs_service", return_value=service)
    fetch_jobs_cached = mocker.patch.object(
        jobs,
        "fetch_jobs_cached",
        return_value=response,
    )
    render_job_card = mocker.patch.object(jobs, "render_job_card")
    render_job_detail = mocker.patch.object(jobs, "render_job_detail")
    render_pagination = mocker.patch.object(jobs, "render_pagination")

    jobs.st.session_state.clear()
    jobs.render()

    fetch_jobs_cached.assert_called_once()
    render_job_card.assert_called_once_with(job)
    render_job_detail.assert_not_called()
    render_pagination.assert_not_called()


def test_render_jobs_empty(mocker):
    service = Mock()

    response = Mock()
    response.items = []
    response.total = 0
    response.total_pages = 0

    mocker.patch.object(jobs, "get_jobs_service", return_value=service)
    mocker.patch.object(
        jobs,
        "fetch_jobs_cached",
        return_value=response,
    )
    render_empty_state = mocker.patch.object(jobs, "render_empty_state")
    render_job_card = mocker.patch.object(jobs, "render_job_card")
    render_job_detail = mocker.patch.object(jobs, "render_job_detail")
    render_pagination = mocker.patch.object(jobs, "render_pagination")

    jobs.st.session_state.clear()
    jobs.render()

    render_empty_state.assert_called_once()
    render_job_card.assert_not_called()
    render_job_detail.assert_not_called()
    render_pagination.assert_not_called()


def test_render_jobs_fetch_error(mocker):
    service = Mock()

    mocker.patch.object(jobs, "get_jobs_service", return_value=service)
    mocker.patch.object(
        jobs,
        "fetch_jobs_cached",
        side_effect=Exception("API unavailable"),
    )
    show_error = mocker.patch.object(jobs, "show_error")
    render_job_card = mocker.patch.object(jobs, "render_job_card")
    render_empty_state = mocker.patch.object(jobs, "render_empty_state")

    jobs.st.session_state.clear()
    jobs.render()

    show_error.assert_called_once_with(
        "Failed to load jobs: API unavailable"
    )
    render_job_card.assert_not_called()
    render_empty_state.assert_not_called()


def test_render_jobs_filters_changed_resets_page(mocker):
    service = Mock()

    response = Mock()
    response.items = []
    response.total = 0
    response.total_pages = 0

    mocker.patch.object(jobs, "get_jobs_service", return_value=service)
    mocker.patch.object(
        jobs,
        "fetch_jobs_cached",
        return_value=response,
    )
    mocker.patch.object(
        jobs,
        "render_filters",
        return_value={"search": "Python"},
    )

    jobs.st.session_state.clear()
    jobs.st.session_state.jobs_page = 3
    jobs.st.session_state.jobs_filters = {}

    jobs.render()

    assert jobs.st.session_state.jobs_filters == {"search": "Python"}
    assert jobs.st.session_state.jobs_page == 1


def test_render_jobs_tech_toggle_changed_resets_page(mocker):
    service = Mock()

    mocker.patch.object(jobs, "get_jobs_service", return_value=service)
    mocker.patch.object(
        jobs.st,
        "toggle",
        return_value=False,
    )
    cache_clear = mocker.patch.object(jobs.st.cache_data, "clear")
    rerun = mocker.patch.object(jobs.st, "rerun")

    jobs.st.session_state.clear()
    jobs.st.session_state.is_tech_role = True
    jobs.st.session_state.jobs_page = 3

    jobs.render()

    assert jobs.st.session_state.is_tech_role is False
    assert jobs.st.session_state.jobs_page == 1
    cache_clear.assert_called_once()
    rerun.assert_called_once()



@pytest.mark.parametrize(
    ("min_salary", "max_salary", "expected_min", "expected_max"),
    [
        (None, None, None, None),
        ("50000", "100000", 50000.0, 100000.0),
        ("invalid", "also-invalid", None, None),
    ],
)
def test_render_jobs_salary_filter_conversion(
    mocker,
    min_salary,
    max_salary,
    expected_min,
    expected_max,
):
    service = Mock()

    response = Mock()
    response.items = []
    response.total = 0
    response.total_pages = 0
    service.fetch_jobs.return_value = response

    mocker.patch.object(jobs, "get_jobs_service", return_value=service)
    mocker.patch.object(
        jobs,
        "render_filters",
        return_value={
            "min_salary": min_salary,
            "max_salary": max_salary,
        },
    )

    jobs.st.session_state.clear()
    jobs.st.session_state.jobs_filters = {}

    jobs.render()

    filters = service.fetch_jobs.call_args.args[0]

    assert filters.min_salary == expected_min
    assert filters.max_salary == expected_max


def test_render_jobs_selected_job_shows_detail(mocker):
    service = Mock()

    job = Mock()
    job.id = 42

    response = Mock()
    response.items = [job]
    response.total = 1
    response.total_pages = 1

    mocker.patch.object(jobs, "get_jobs_service", return_value=service)
    mocker.patch.object(
        jobs,
        "fetch_jobs_cached",
        return_value=response,
    )
    render_job_detail = mocker.patch.object(jobs, "render_job_detail")
    render_job_card = mocker.patch.object(jobs, "render_job_card")

    jobs.st.session_state.clear()
    jobs.st.session_state.selected_job_id = "42"

    jobs.render()

    render_job_detail.assert_called_once_with(job)
    render_job_card.assert_not_called()


def test_render_jobs_pagination(mocker):
    service = Mock()

    job = Mock()
    job.id = 1

    response = Mock()
    response.items = [job]
    response.total = 45
    response.total_pages = 3

    mocker.patch.object(jobs, "get_jobs_service", return_value=service)
    mocker.patch.object(
        jobs,
        "fetch_jobs_cached",
        return_value=response,
    )
    render_pagination = mocker.patch.object(jobs, "render_pagination")

    jobs.st.session_state.clear()
    jobs.st.session_state.jobs_page = 2

    jobs.render()

    render_pagination.assert_called_once_with(2, 3)


def test_render_jobs_page_exceeds_total_pages_resets_page(mocker):
    service = Mock()

    job = Mock()
    job.id = 1

    response = Mock()
    response.items = [job]
    response.total = 10
    response.total_pages = 2

    mocker.patch.object(jobs, "get_jobs_service", return_value=service)
    mocker.patch.object(
        jobs,
        "fetch_jobs_cached",
        return_value=response,
    )

    jobs.st.session_state.clear()
    jobs.st.session_state.jobs_page = 5

    jobs.render()

    assert jobs.st.session_state.jobs_page == 2
