import streamlit as st

from dashboard.utils import StateManager
from dashboard.utils.service_factory import get_jobs_service
from dashboard.components.filters import render_filters
from dashboard.components.tables import render_jobs_table
from dashboard.components.pagination import render_pagination
from dashboard.components.empty_state import render_empty_state
from dashboard.components.alerts import show_error
from dashboard.schemas import JobFilters
from dashboard.core.config import settings


@st.cache_data(ttl=settings.CACHE_TTL)  # Use configurable TTL
def fetch_jobs_cached(_service, search, company, location, source_site, min_salary, max_salary, page, page_size):
    """
    Cached function to fetch jobs.
    
    The underscore prefix on _service tells Streamlit not to hash it.
    TTL is configured in settings (default: 300 seconds / 5 minutes).
    """
    filters = JobFilters(
        search=search,
        company=company,
        location=location,
        source_site=source_site,
        min_salary=min_salary,
        max_salary=max_salary,
    )
    return _service.fetch_jobs(filters, page, page_size)


def render():
    """Render the Job Explorer page."""
    st.title("💼 Job Explorer")
    
    # Get service singleton
    service = get_jobs_service()
    
    # 1. Get filters from state
    raw_filters = render_filters()
    current_filters = StateManager.get_jobs_filters()
    
    if raw_filters != current_filters:
        StateManager.set_jobs_filters(raw_filters)
        StateManager.reset_jobs_context()
    
    ui_filters = StateManager.get_jobs_filters()
    
    def to_float_or_none(value):
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    # Extract filter values for caching
    search = ui_filters.get("search")
    company = ui_filters.get("company")
    location = ui_filters.get("location")
    source_site = ui_filters.get("source_site")
    min_salary = to_float_or_none(ui_filters.get("min_salary"))
    max_salary = to_float_or_none(ui_filters.get("max_salary"))
    
    # Get pagination state
    page = StateManager.get_jobs_page()
    page_size = StateManager.get_jobs_page_size()
    
    # Fetch data with caching
    try:
        response = fetch_jobs_cached(
            service, search, company, location, source_site, 
            min_salary, max_salary, page, page_size
        )
    except Exception as e:
        show_error(f"Failed to load jobs: {str(e)}")
        return
    
    jobs = response.items
    
    # Show results count
    if response.total > 0:
        st.caption(f"Showing {len(jobs)} of {response.total} jobs")
    else:
        st.caption("No jobs found")
    
    # Render content
    if not jobs:
        render_empty_state()
        return
    
    # Render jobs table with inline expansion
    render_jobs_table(jobs)
    
    # Render pagination
    render_pagination(page, response.total_pages)
    
    # Safety guard - prevents invalid pagination states
    if page > response.total_pages and response.total_pages > 0:
        StateManager.set_jobs_page(response.total_pages)
        st.rerun()