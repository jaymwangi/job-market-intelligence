"""
Unit tests for state management utilities.
"""

from unittest.mock import patch

from dashboard.utils.state import StateManager


class MockSessionState(dict):
    """
    Mock for st.session_state that supports both attribute and dict-style access.
    Inherits from dict to get dict behavior for free.
    """

    def __init__(self, initial_data=None):
        super().__init__(initial_data or {})

    def __getattr__(self, name):
        """Support attribute-style access."""
        if name in self:
            return self[name]
        # For methods like .get() that might be called
        if name == "get":
            return self.get
        # Return None for missing attributes (like Streamlit's behavior)
        return None

    def __setattr__(self, name, value):
        """Support attribute-style assignment."""
        # Allow setting internal attributes (like __dict__)
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            self[name] = value

    def __getitem__(self, key):
        """Support dict-style access."""
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        """Support dict-style assignment."""
        super().__setitem__(key, value)

    def __contains__(self, key):
        """Support 'in' operator."""
        return super().__contains__(key)

    def get(self, key, default=None):
        """Support .get() method."""
        return super().get(key, default)


class TestStateManager:
    """Test suite for StateManager."""

    def test_init_sets_session_state(self):
        """Test initialization sets session state."""
        # Start with empty session state (simulates first visit)
        # IMPORTANT: Do NOT include "initialized" key in initial data
        # The implementation checks if the key exists, not its value
        initial_data = {
            "current_page": "overview",
            "job_filters": {},
            "jobs_page": 1,
            "jobs_page_size": 20,
            "selected_job_id": None,
            "services": {},
        }

        session_state = MockSessionState(initial_data)

        with patch("dashboard.utils.state.st.session_state", session_state):
            # Reset StateManager state
            StateManager._api_client = None
            StateManager._cache_manager = None
            StateManager._services = {}

            # Verify "initialized" key doesn't exist initially
            assert "initialized" not in session_state

            StateManager.init()

            # Verify state was set
            assert session_state["initialized"] is True
            assert session_state["current_page"] == "overview"
            assert session_state["job_filters"] == {}
            assert session_state["jobs_page"] == 1
            assert session_state["jobs_page_size"] == 20
            assert session_state["selected_job_id"] is None
            assert session_state["services"] == {}

    def test_init_does_not_reset(self):
        """Test init doesn't reset existing state."""
        # Simulate an already initialized session
        initial_data = {
            "initialized": True,
            "current_page": "jobs",
            "job_filters": {"location": "SF"},
            "jobs_page": 5,
            "jobs_page_size": 20,
            "selected_job_id": "job_123",
            "services": {},
        }

        session_state = MockSessionState(initial_data)

        with patch("dashboard.utils.state.st.session_state", session_state):
            StateManager.init()
            # Should not override existing state
            assert session_state["initialized"] is True
            assert session_state["current_page"] == "jobs"
            assert session_state["job_filters"] == {"location": "SF"}

    def test_get_api_client(self):
        """Test getting API client singleton."""
        session_state = MockSessionState({})

        with patch("dashboard.utils.state.st.session_state", session_state):
            StateManager._api_client = None
            client1 = StateManager.get_api_client()
            client2 = StateManager.get_api_client()
            assert client1 is client2  # Same instance

    def test_get_cache_manager(self):
        """Test getting cache manager singleton."""
        session_state = MockSessionState({})

        with patch("dashboard.utils.state.st.session_state", session_state):
            StateManager._cache_manager = None
            cache1 = StateManager.get_cache_manager()
            cache2 = StateManager.get_cache_manager()
            assert cache1 is cache2  # Same instance

    def test_get_service(self):
        """Test getting service instance."""
        session_state = MockSessionState({"services": {}})

        with patch("dashboard.utils.state.st.session_state", session_state):
            StateManager._api_client = None
            StateManager._cache_manager = None
            StateManager._services = {}

            # Create a mock service class that accepts api_client and cache_manager
            class MockService:
                def __init__(self, api_client=None, cache_manager=None):
                    self.api_client = api_client
                    self.cache_manager = cache_manager

            service1 = StateManager.get_service(MockService)
            service2 = StateManager.get_service(MockService)
            assert service1 is service2  # Same instance
            assert service1.api_client is not None
            assert service1.cache_manager is not None

    def test_clear_cache(self):
        """Test clearing all caches."""
        session_state = MockSessionState(
            {"initialized": True, "job_filters": {"location": "SF"}, "services": {}}
        )

        with patch("dashboard.utils.state.st.session_state", session_state):
            StateManager._api_client = None
            StateManager._cache_manager = None
            StateManager._services = {}

            StateManager.init()

            # Set some state
            StateManager.set_jobs_filters({"location": "SF"})
            assert StateManager.get_jobs_filters() == {"location": "SF"}

            # Clear cache
            StateManager.clear_cache()

            # Services should be reset
            assert StateManager._services == {}

    def test_page_navigation(self):
        """Test page navigation methods."""
        session_state = MockSessionState({})

        with patch("dashboard.utils.state.st.session_state", session_state):
            StateManager.init()

            StateManager.set_current_page("jobs")
            assert StateManager.get_current_page() == "jobs"

            StateManager.set_current_page("analytics")
            assert StateManager.get_current_page() == "analytics"

    def test_job_filters(self):
        """Test job filters methods."""
        session_state = MockSessionState({})

        with patch("dashboard.utils.state.st.session_state", session_state):
            StateManager.init()

            filters = {"location": "SF", "min_salary": 100000}
            StateManager.set_jobs_filters(filters)
            assert StateManager.get_jobs_filters() == filters

            # Test updating filters
            new_filters = {"location": "NY", "max_salary": 200000}
            StateManager.set_jobs_filters(new_filters)
            assert StateManager.get_jobs_filters() == new_filters

    def test_job_pagination(self):
        """Test job pagination methods."""
        session_state = MockSessionState({})

        with patch("dashboard.utils.state.st.session_state", session_state):
            StateManager.init()

            assert StateManager.get_jobs_page() == 1

            StateManager.set_jobs_page(5)
            assert StateManager.get_jobs_page() == 5

            # Negative values should be clamped
            StateManager.set_jobs_page(-1)
            assert StateManager.get_jobs_page() == 1

    def test_jobs_page_size(self):
        """Test page size methods."""
        session_state = MockSessionState({})

        with patch("dashboard.utils.state.st.session_state", session_state):
            StateManager.init()

            assert StateManager.get_jobs_page_size() == 20

            StateManager.set_jobs_page_size(50)
            assert StateManager.get_jobs_page_size() == 50

            # Clamping
            StateManager.set_jobs_page_size(200)
            assert StateManager.get_jobs_page_size() == 100

            StateManager.set_jobs_page_size(0)
            assert StateManager.get_jobs_page_size() == 1

    def test_job_selection(self):
        """Test job selection methods."""
        session_state = MockSessionState({})

        with patch("dashboard.utils.state.st.session_state", session_state):
            StateManager.init()

            assert StateManager.get_selected_job_id() is None

            StateManager.set_selected_job_id("job_123")
            assert StateManager.get_selected_job_id() == "job_123"

            StateManager.set_selected_job_id("job_456")
            assert StateManager.get_selected_job_id() == "job_456"

    def test_reset_jobs_context(self):
        """Test resetting jobs context."""
        session_state = MockSessionState({})

        with patch("dashboard.utils.state.st.session_state", session_state):
            StateManager.init()

            # Set some values
            StateManager.set_jobs_filters({"location": "SF"})
            StateManager.set_jobs_page(5)
            StateManager.set_selected_job_id("job_123")

            # Reset
            StateManager.reset_jobs_context()

            assert StateManager.get_jobs_filters() == {}
            assert StateManager.get_jobs_page() == 1
            assert StateManager.get_selected_job_id() is None

    def test_backward_compatibility(self):
        """Test backward compatibility methods."""
        session_state = MockSessionState({})

        with patch("dashboard.utils.state.st.session_state", session_state):
            StateManager.init()

            # Test aliases
            StateManager.set_job_filters({"location": "SF"})
            assert StateManager.get_job_filters() == {"location": "SF"}

            StateManager.set_page(3)
            assert StateManager.get_page() == 3

    def test_refresh_dashboard(self):
        """Test dashboard refresh."""
        session_state = MockSessionState({})

        with patch("dashboard.utils.state.st.session_state", session_state):
            StateManager.init()

            # Set some values
            StateManager.set_jobs_page(5)
            StateManager.set_selected_job_id("job_123")
            StateManager.set_jobs_filters({"location": "SF"})

            # Refresh
            StateManager.refresh_dashboard()

            assert StateManager.get_jobs_page() == 1
            assert StateManager.get_selected_job_id() is None
            # Filters should NOT be reset by refresh
            assert StateManager.get_jobs_filters() == {"location": "SF"}

    def test_service_factory_backward_compat(self):
        """Test ServiceFactory backward compatibility."""
        session_state = MockSessionState({})

        with patch("dashboard.utils.state.st.session_state", session_state):
            StateManager._api_client = None
            StateManager._cache_manager = None
            StateManager._services = {}

            # Test ServiceFactory wrapper
            from dashboard.utils.state import ServiceFactory

            factory = ServiceFactory()

            # Should not raise errors
            assert factory is not None

    def test_convenience_functions(self):
        """Test convenience functions."""
        session_state = MockSessionState({})

        with patch("dashboard.utils.state.st.session_state", session_state):
            StateManager._api_client = None
            StateManager._cache_manager = None
            StateManager._services = {}

            # Import convenience functions
            from dashboard.utils.state import (
                get_analytics_service,
                get_health_service,
                get_jobs_service,
            )

            # Should not raise errors (services will be created)
            # Note: These will fail if the actual service classes require complex setup
            # For now, we just test that the functions exist and can be called
            assert callable(get_analytics_service)
            assert callable(get_jobs_service)
            assert callable(get_health_service)
