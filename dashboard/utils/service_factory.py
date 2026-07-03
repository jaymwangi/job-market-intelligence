import streamlit as st
from dashboard.api.client import APIClient
from dashboard.services.jobs_service import JobsService
from dashboard.core.config import settings


def get_jobs_service():
    """Get or create a singleton JobsService instance."""
    if "jobs_service" not in st.session_state:
        api = APIClient(settings.API_BASE_URL, settings.API_TIMEOUT)
        st.session_state.jobs_service = JobsService(api)
    return st.session_state.jobs_service