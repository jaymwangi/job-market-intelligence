from datetime import datetime
from unittest.mock import MagicMock, patch

from utils.state import (
    ServiceFactory,
    StateManager,
    get_analytics_service,
    get_etl_status,
    get_health_service,
    get_jobs_service,
    get_last_etl_run,
    get_pipeline_status,
    get_service_factory,
    refresh_dashboard,
)


class SessionState(dict):
    """Dict with attribute access like Streamlit session state."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name, value):
        self[name] = value


def reset_state_manager():
    StateManager._services = {}
    StateManager._api_client = None
    StateManager._cache_manager = None
    StateManager._etl_status_cache = None
    StateManager._etl_cache_timestamp = None


def setup_function():
    reset_state_manager()
    getattr(StateManager.get_etl_status, "clear")()


def test_init_sets_default_session_state():
    session = SessionState()

    with patch("utils.state.st.session_state", session):
        StateManager.init()

    assert session["initialized"] is True
    assert session["current_page"] == "overview"
    assert session["job_filters"] == {}
    assert session["jobs_page"] == 1
    assert session["jobs_page_size"] == 10
    assert session["selected_job_id"] is None
    assert session["services"] == {}


def test_init_does_nothing_when_already_initialized():
    session = SessionState(
        initialized=True,
        current_page="jobs",
        jobs_page=5,
    )

    with patch("utils.state.st.session_state", session):
        StateManager.init()

    assert session["current_page"] == "jobs"
    assert session["jobs_page"] == 5


def test_get_cache_manager_creates_and_reuses_singleton():
    manager = MagicMock()

    with patch(
        "utils.state.CacheManager",
        return_value=manager,
    ) as mock_manager:
        result_one = StateManager.get_cache_manager()
        result_two = StateManager.get_cache_manager()

    assert result_one is manager
    assert result_two is manager
    mock_manager.assert_called_once_with()


def test_get_service_returns_class_cached_service():
    session = SessionState()
    existing = object()
    StateManager._services["FakeService"] = existing

    class FakeService:
        pass

    with patch("utils.state.st.session_state", session):
        result = StateManager.get_service(FakeService)

    assert result is existing


def test_get_service_restores_service_from_session_state():
    session_service = object()
    session = SessionState(
        services={"FakeService": session_service},
    )

    class FakeService:
        pass

    with patch("utils.state.st.session_state", session):
        result = StateManager.get_service(FakeService)

    assert result is session_service
    assert StateManager._services["FakeService"] is session_service


def test_get_service_creates_and_caches_new_service():
    session = SessionState()
    api_client = object()
    cache_manager = object()

    class FakeService:
        def __init__(self, api_client, cache_manager):
            self.api_client = api_client
            self.cache_manager = cache_manager

    with (
        patch("utils.state.st.session_state", session),
        patch.object(
            StateManager,
            "get_api_client",
            return_value=api_client,
        ),
        patch.object(
            StateManager,
            "get_cache_manager",
            return_value=cache_manager,
        ),
    ):
        result = StateManager.get_service(FakeService)

    assert result.api_client is api_client
    assert result.cache_manager is cache_manager
    assert StateManager._services["FakeService"] is result
    assert session.services["FakeService"] is result


def test_get_service_creates_services_dict_if_missing():
    session = SessionState()
    api_client = object()
    cache_manager = object()

    class FakeService:
        def __init__(self, api_client, cache_manager):
            self.api_client = api_client
            self.cache_manager = cache_manager

    with (
        patch("utils.state.st.session_state", session),
        patch.object(
            StateManager,
            "get_api_client",
            return_value=api_client,
        ),
        patch.object(
            StateManager,
            "get_cache_manager",
            return_value=cache_manager,
        ),
    ):
        result = StateManager.get_service(FakeService)

    assert result.api_client is api_client
    assert result.cache_manager is cache_manager
    assert session.services["FakeService"] is result


def test_service_getters_delegate_to_get_service():
    analytics = object()
    jobs = object()
    health = object()

    with (
        patch(
            "services.analytics_service.AnalyticsService",
            return_value=analytics,
        ) as analytics_class,
        patch(
            "services.jobs_service.JobsService",
            return_value=jobs,
        ) as jobs_class,
        patch(
            "services.health.HealthService",
            return_value=health,
        ) as health_class,
    ):
        with patch.object(
            StateManager,
            "get_service",
            side_effect=[analytics, jobs, health],
        ) as mock_get:
            assert StateManager.get_analytics_service() is analytics
            assert StateManager.get_jobs_service() is jobs
            assert StateManager.get_health_service() is health

    assert mock_get.call_count == 3
    analytics_class.assert_not_called()
    jobs_class.assert_not_called()
    health_class.assert_not_called()


def test_clear_cache_clears_cache_manager_and_services():
    session = SessionState(
        services={"old": object()},
    )
    cache_manager = MagicMock()

    refreshable = MagicMock()
    non_refreshable = object()

    StateManager._cache_manager = cache_manager
    StateManager._services = {
        "refreshable": refreshable,
        "other": non_refreshable,
    }

    with patch("utils.state.st.session_state", session):
        StateManager.clear_cache()

    cache_manager.clear.assert_called_once_with()
    refreshable.refresh.assert_called_once_with()
    assert session.services == {}
    assert StateManager._etl_status_cache is None
    assert StateManager._etl_cache_timestamp is None


def test_clear_cache_logs_refresh_error():
    session = SessionState(services={})
    service = MagicMock()
    service.refresh.side_effect = RuntimeError("refresh failed")
    StateManager._services = {"broken": service}

    with (
        patch("utils.state.st.session_state", session),
        patch("utils.state.logger.error") as mock_error,
    ):
        StateManager.clear_cache()

    mock_error.assert_called_once()
    assert "refresh failed" in mock_error.call_args.args[0]


def test_clear_cache_handles_no_cache_manager_and_no_session_services():
    session = SessionState()
    StateManager._cache_manager = None
    StateManager._services = {}

    with patch("utils.state.st.session_state", session):
        StateManager.clear_cache()

    assert StateManager._etl_status_cache is None
    assert StateManager._etl_cache_timestamp is None


def test_page_methods():
    session = SessionState()

    with patch("utils.state.st.session_state", session):
        assert StateManager.get_current_page() == "overview"

        StateManager.set_current_page("jobs")
        assert StateManager.get_current_page() == "jobs"

        session["current_page"] = "analytics"
        assert StateManager.get_current_page() == "analytics"


def test_filter_methods():
    session = SessionState()

    with patch("utils.state.st.session_state", session):
        assert StateManager.get_jobs_filters() == {}

        filters = {"country": "Kenya"}
        StateManager.set_jobs_filters(filters)
        assert StateManager.get_jobs_filters() == filters

        assert StateManager.get_job_filters() == filters

        StateManager.set_job_filters({"role": "Data Scientist"})
        assert StateManager.get_jobs_filters() == {"role": "Data Scientist"}


def test_reset_jobs_context():
    session = SessionState(
        job_filters={"country": "Kenya"},
        jobs_page=8,
        selected_job_id="123",
    )

    with patch("utils.state.st.session_state", session):
        StateManager.reset_jobs_context()

    assert session.job_filters == {}
    assert session.jobs_page == 1
    assert session.selected_job_id is None


def test_pagination_methods():
    session = SessionState()

    with patch("utils.state.st.session_state", session):
        assert StateManager.get_jobs_page() == 1
        assert StateManager.get_jobs_page_size() == 20

        StateManager.set_jobs_page(5)
        assert StateManager.get_jobs_page() == 5

        StateManager.set_jobs_page(0)
        assert StateManager.get_jobs_page() == 1

        StateManager.set_jobs_page_size(50)
        assert StateManager.get_jobs_page_size() == 50

        StateManager.set_jobs_page_size(0)
        assert StateManager.get_jobs_page_size() == 1

        StateManager.set_jobs_page_size(500)
        assert StateManager.get_jobs_page_size() == 100

        assert StateManager.get_page() == 1
        StateManager.set_page(7)
        assert StateManager.get_page() == 7


def test_pagination_getters_use_existing_values():
    session = SessionState(
        jobs_page=4,
        jobs_page_size=25,
    )

    with patch("utils.state.st.session_state", session):
        assert StateManager.get_jobs_page() == 4
        assert StateManager.get_jobs_page_size() == 25


def test_selected_job_methods():
    session = SessionState()

    with patch("utils.state.st.session_state", session):
        assert StateManager.get_selected_job_id() is None

        StateManager.set_selected_job_id("job-123")
        assert StateManager.get_selected_job_id() == "job-123"

        StateManager.set_selected_job_id(None)
        assert StateManager.get_selected_job_id() is None


def test_get_etl_status_logs_api_warning():
    api_client = MagicMock()
    api_client.get.side_effect = RuntimeError("API unavailable")
    analytics = MagicMock()
    analytics.get_pipeline_status.return_value = "idle"
    analytics.get_last_etl_run.return_value = "N/A"
    analytics.get_last_etl_run_time.return_value = None
    analytics.get_db_status.return_value = "healthy"

    with (
        patch.object(
            StateManager,
            "get_api_client",
            return_value=api_client,
        ),
        patch.object(
            StateManager,
            "get_analytics_service",
            return_value=analytics,
        ),
        patch("utils.state.logger.warning") as mock_warning,
    ):
        StateManager.get_etl_status()

    mock_warning.assert_called_once()
    assert "API unavailable" in mock_warning.call_args.args[0]


def test_etl_status_convenience_methods():
    status = {
        "status": "running",
        "last_run": "2026-09-15 12:00",
        "db_status": "healthy",
    }

    with patch.object(
        StateManager,
        "get_etl_status",
        return_value=status,
    ):
        assert StateManager.get_last_etl_run() == "2026-09-15 12:00"
        assert StateManager.get_pipeline_status() == "running"
        assert StateManager.get_db_status() == "healthy"


def test_etl_status_convenience_methods_use_defaults():
    with patch.object(
        StateManager,
        "get_etl_status",
        return_value={},
    ):
        assert StateManager.get_last_etl_run() == "No runs yet"
        assert StateManager.get_pipeline_status() == "Unknown"
        assert StateManager.get_db_status() == "Unknown"


def test_refresh_etl_status():
    StateManager._etl_status_cache = {"status": "old"}
    StateManager._etl_cache_timestamp = datetime.now()

    with patch("utils.state.st.cache_data.clear") as mock_clear:
        StateManager.refresh_etl_status()

    assert StateManager._etl_status_cache is None
    assert StateManager._etl_cache_timestamp is None
    mock_clear.assert_called_once_with()


def test_refresh_dashboard():
    with (
        patch.object(StateManager, "clear_cache") as mock_clear,
        patch.object(
            StateManager,
            "refresh_etl_status",
        ) as mock_refresh,
        patch.object(
            StateManager,
            "set_jobs_page",
        ) as mock_page,
        patch.object(
            StateManager,
            "set_selected_job_id",
        ) as mock_selected,
    ):
        StateManager.refresh_dashboard()

    mock_clear.assert_called_once_with()
    mock_refresh.assert_called_once_with()
    mock_page.assert_called_once_with(1)
    mock_selected.assert_called_once_with(None)


def test_module_level_service_functions():
    analytics = object()
    jobs = object()
    health = object()

    with (
        patch.object(
            StateManager,
            "get_analytics_service",
            return_value=analytics,
        ),
        patch.object(
            StateManager,
            "get_jobs_service",
            return_value=jobs,
        ),
        patch.object(
            StateManager,
            "get_health_service",
            return_value=health,
        ),
    ):
        assert get_analytics_service() is analytics
        assert get_jobs_service() is jobs
        assert get_health_service() is health


def test_module_level_etl_functions():
    status = {"status": "running"}

    with (
        patch.object(
            StateManager,
            "get_etl_status",
            return_value=status,
        ),
        patch.object(
            StateManager,
            "get_last_etl_run",
            return_value="today",
        ),
        patch.object(
            StateManager,
            "get_pipeline_status",
            return_value="running",
        ),
    ):
        assert get_etl_status() is status
        assert get_last_etl_run() == "today"
        assert get_pipeline_status() == "running"


def test_module_level_refresh_dashboard():
    with patch.object(StateManager, "refresh_dashboard") as mock_refresh:
        refresh_dashboard()

    mock_refresh.assert_called_once_with()


def test_get_service_factory_returns_state_manager():
    assert get_service_factory() is StateManager


def test_service_factory_is_singleton():
    first = ServiceFactory()
    second = ServiceFactory()

    assert first is second


def test_service_factory_delegates_service_methods():
    factory = ServiceFactory()
    analytics = object()
    jobs = object()
    health = object()

    with (
        patch.object(
            StateManager,
            "get_analytics_service",
            return_value=analytics,
        ),
        patch.object(
            StateManager,
            "get_jobs_service",
            return_value=jobs,
        ),
        patch.object(
            StateManager,
            "get_health_service",
            return_value=health,
        ),
    ):
        assert factory.get_analytics_service() is analytics
        assert factory.get_jobs_service() is jobs
        assert factory.get_health_service() is health


def test_service_factory_refresh_all():
    factory = ServiceFactory()

    with patch.object(StateManager, "clear_cache") as mock_clear:
        result = factory.refresh_all()

    mock_clear.assert_called_once_with()
    assert result is None


def test_service_factory_etl_methods():
    factory = ServiceFactory()

    with (
        patch.object(
            StateManager,
            "get_etl_status",
            return_value={"status": "running"},
        ),
        patch.object(
            StateManager,
            "get_last_etl_run",
            return_value="today",
        ),
        patch.object(
            StateManager,
            "get_pipeline_status",
            return_value="running",
        ),
    ):
        assert factory.get_etl_status() == {"status": "running"}
        assert factory.get_last_etl_run() == "today"
        assert factory.get_pipeline_status() == "running"


def test_get_api_client_creates_and_reuses_singleton():
    first = MagicMock()

    with patch(
        "utils.state.APIClient",
        return_value=first,
    ) as mock_client:
        result_one = StateManager.get_api_client()
        result_two = StateManager.get_api_client()

    assert result_one is first
    assert result_two is first
    mock_client.assert_called_once()


def test_get_etl_status_returns_api_response():
    response = {
        "status": "completed",
        "last_run": "2026-09-15",
        "db_status": "healthy",
    }

    api_client = MagicMock()
    api_client.get.return_value = response

    with patch.object(
        StateManager,
        "get_api_client",
        return_value=api_client,
    ):
        result = StateManager.get_etl_status()

    assert result == response
    api_client.get.assert_called_once_with("/analytics/etl/status")


def test_get_etl_status_falls_back_to_analytics_service():
    api_client = MagicMock()
    api_client.get.side_effect = RuntimeError("API unavailable")

    analytics_service = MagicMock()
    analytics_service.get_pipeline_status.return_value = "running"
    analytics_service.get_last_etl_run.return_value = "2026-09-15"
    analytics_service.get_last_etl_run_time.return_value = "12:00"
    analytics_service.get_db_status.return_value = "healthy"

    with (
        patch.object(
            StateManager,
            "get_api_client",
            return_value=api_client,
        ),
        patch.object(
            StateManager,
            "get_analytics_service",
            return_value=analytics_service,
        ),
    ):
        result = StateManager.get_etl_status()

    assert result == {
        "status": "running",
        "last_run": "2026-09-15",
        "last_run_time": "12:00",
        "db_status": "healthy",
    }


def test_get_etl_status_returns_unknown_when_fallback_fails():
    api_client = MagicMock()
    api_client.get.side_effect = RuntimeError("API unavailable")

    with (
        patch.object(
            StateManager,
            "get_api_client",
            return_value=api_client,
        ),
        patch.object(
            StateManager,
            "get_analytics_service",
            side_effect=RuntimeError("database unavailable"),
        ),
    ):
        result = StateManager.get_etl_status()

    assert result == {
        "status": "unknown",
        "last_run": "N/A",
        "error": "database unavailable",
    }
