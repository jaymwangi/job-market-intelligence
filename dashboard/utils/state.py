import streamlit as st

class StateManager:
    """Centralized session state management with distinct keys for each concern."""
    
    # Navigation
    NAV_KEY = "nav_current_page"
    
    # Job Explorer
    JOBS_PAGE_KEY = "jobs_page"
    JOBS_PAGE_SIZE_KEY = "jobs_page_size"
    JOBS_FILTERS_KEY = "jobs_filters"
    JOBS_SELECTED_ID_KEY = "jobs_selected_id"
    
    @staticmethod
    def init():
        """Initialize all session state keys with defaults."""
        # Navigation
        if StateManager.NAV_KEY not in st.session_state:
            st.session_state[StateManager.NAV_KEY] = "overview"
        
        # Job Explorer
        if StateManager.JOBS_PAGE_KEY not in st.session_state:
            st.session_state[StateManager.JOBS_PAGE_KEY] = 1
        if StateManager.JOBS_PAGE_SIZE_KEY not in st.session_state:
            st.session_state[StateManager.JOBS_PAGE_SIZE_KEY] = 10
        if StateManager.JOBS_FILTERS_KEY not in st.session_state:
            st.session_state[StateManager.JOBS_FILTERS_KEY] = {}
        if StateManager.JOBS_SELECTED_ID_KEY not in st.session_state:
            st.session_state[StateManager.JOBS_SELECTED_ID_KEY] = None
    
    # Navigation methods
    @staticmethod
    def get_current_page() -> str:
        return st.session_state.get(StateManager.NAV_KEY, "overview")
    
    @staticmethod
    def set_current_page(page: str):
        st.session_state[StateManager.NAV_KEY] = page
    
    # Job Explorer methods
    @staticmethod
    def get_jobs_page() -> int:
        return max(1, st.session_state.get(StateManager.JOBS_PAGE_KEY, 1))
    
    @staticmethod
    def set_jobs_page(page: int):
        st.session_state[StateManager.JOBS_PAGE_KEY] = max(1, page)
    
    @staticmethod
    def get_jobs_page_size() -> int:
        return max(1, st.session_state.get(StateManager.JOBS_PAGE_SIZE_KEY, 10))
    
    @staticmethod
    def set_jobs_page_size(size: int):
        st.session_state[StateManager.JOBS_PAGE_SIZE_KEY] = max(1, size)
    
    @staticmethod
    def get_jobs_filters() -> dict:
        return st.session_state.get(StateManager.JOBS_FILTERS_KEY, {})
    
    @staticmethod
    def set_jobs_filters(filters: dict):
        st.session_state[StateManager.JOBS_FILTERS_KEY] = filters
    
    @staticmethod
    def get_selected_job_id() -> str | None:
        return st.session_state.get(StateManager.JOBS_SELECTED_ID_KEY)
    
    @staticmethod
    def set_selected_job_id(job_id: str | None):
        st.session_state[StateManager.JOBS_SELECTED_ID_KEY] = job_id
    
    @staticmethod
    def reset_jobs_context():
        """Reset pagination and selection when filters change."""
        st.session_state[StateManager.JOBS_PAGE_KEY] = 1
        st.session_state[StateManager.JOBS_SELECTED_ID_KEY] = None