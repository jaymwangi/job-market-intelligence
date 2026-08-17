"""Professional Job Explorer page with modern UI."""

import streamlit as st

from components.alerts import show_error
from components.empty_state import render_empty_state
from components.filters import render_filters
from components.icons import get_icon
from components.job_card import render_job_card
from components.job_detail import render_job_detail  # ✅ ADD THIS IMPORT
from components.pagination import render_pagination
from components.tables import render_jobs_table
from core.config import settings
from schemas import JobFilters
from utils import StateManager
from utils.service_factory import get_jobs_service

# Professional color palette
COLORS = {
    "primary": "#1a1a2e",
    "secondary": "#16213e",
    "accent": "#0f3460",
    "highlight": "#e94560",
    "success": "#00b894",
    "warning": "#fdcb6e",
    "info": "#0984e3",
    "background": "#f8f9fa",
    "card_bg": "#ffffff",
    "text": "#2d3436",
    "text_light": "#636e72",
    "border": "#e9ecef",
}


@st.cache_data(ttl=settings.CACHE_TTL)
def fetch_jobs_cached(
    _service,
    search,
    company,
    location,
    source_site,
    min_salary,
    max_salary,
    is_tech_role,
    page,
    page_size,
):
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
        is_tech_role=is_tech_role,  # Sprint 6.6.1: Tech Jobs Only filter
    )
    return _service.fetch_jobs(filters, page, page_size)


def render():
    """Render the professional Job Explorer page."""
    
    # Initialize ALL session state variables at the very beginning
    if "jobs_page" not in st.session_state:
        st.session_state.jobs_page = 1
    if "jobs_page_size" not in st.session_state:
        st.session_state.jobs_page_size = 20
    if "jobs_filters" not in st.session_state:
        st.session_state.jobs_filters = {}
    if "filters_changed" not in st.session_state:
        st.session_state.filters_changed = False
    if "is_tech_role" not in st.session_state:
        st.session_state.is_tech_role = True  # Default: Tech Jobs Only
    if "selected_job_id" not in st.session_state:
        st.session_state.selected_job_id = None  # ✅ Add this
    
    # Custom CSS for professional styling
    st.markdown(
        f"""
    <style>
        .jobs-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
        }}
        .jobs-title {{
            font-size: 2rem;
            font-weight: 700;
            color: {COLORS['primary']};
            letter-spacing: -0.02em;
            margin: 0;
        }}
        .jobs-subtitle {{
            font-size: 0.95rem;
            color: {COLORS['text_light']};
            font-weight: 400;
            margin-top: 0.25rem;
        }}
        .jobs-stats {{
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 0.75rem 1.25rem;
            background: {COLORS['card_bg']};
            border-radius: 10px;
            border: 1px solid {COLORS['border']};
            margin: 1rem 0 1.5rem 0;
        }}
        .jobs-stat-item {{
            display: flex;
            align-items: baseline;
            gap: 0.5rem;
        }}
        .jobs-stat-number {{
            font-weight: 700;
            font-size: 1.1rem;
            color: {COLORS['primary']};
        }}
        .jobs-stat-label {{
            color: {COLORS['text_light']};
            font-size: 0.85rem;
        }}
        .jobs-stat-divider {{
            color: {COLORS['border']};
            font-size: 1.25rem;
        }}
        .jobs-container {{
            background: {COLORS['card_bg']};
            border-radius: 12px;
            border: 1px solid {COLORS['border']};
            padding: 1.25rem;
            margin-top: 1rem;
        }}
        .jobs-empty {{
            text-align: center;
            padding: 4rem 2rem;
        }}
        .jobs-empty-icon {{
            font-size: 3rem;
            margin-bottom: 1rem;
        }}
        .jobs-empty-title {{
            font-size: 1.25rem;
            font-weight: 600;
            color: {COLORS['primary']};
            margin-bottom: 0.5rem;
        }}
        .jobs-empty-description {{
            color: {COLORS['text_light']};
            font-size: 0.95rem;
        }}
        .stat-icon {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-right: 0.25rem;
        }}
        .header-icon-wrapper {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-right: 0.75rem;
        }}
        .tech-filter-container {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.5rem 1rem;
            background: {COLORS['background']};
            border-radius: 8px;
            border: 1px solid {COLORS['border']};
            margin-bottom: 1rem;
        }}
        .tech-filter-label {{
            font-weight: 500;
            color: {COLORS['text']};
        }}
        .tech-filter-badge {{
            display: inline-block;
            padding: 0.15rem 0.6rem;
            border-radius: 12px;
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .tech-filter-badge-on {{
            background: #00b894;
            color: white;
        }}
        .tech-filter-badge-off {{
            background: #dfe6e9;
            color: #636e72;
        }}
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Header with SVG icon
    header_icon = get_icon("jobs", size=32, color="#1a1a2e")
    st.markdown(
        f"""
    <div class="jobs-header">
        <div style="display:flex;align-items:center;gap:0.75rem;">
            <span class="header-icon-wrapper">{header_icon}</span>
            <div>
                <div class="jobs-title">Job Explorer</div>
                <div class="jobs-subtitle">Search and explore job opportunities in the technology market</div>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # ============================================================
    # Sprint 6.6.1: Tech Jobs Only Filter
    # ============================================================
    st.markdown(
        f"""
    <div class="tech-filter-container">
        <span>💻</span>
        <span class="tech-filter-label">Show only technology roles</span>
        <span class="tech-filter-badge {'tech-filter-badge-on' if st.session_state.is_tech_role else 'tech-filter-badge-off'}">
            {'ON' if st.session_state.is_tech_role else 'OFF'}
        </span>
    </div>
    """,
        unsafe_allow_html=True,
    )
    
    # Use columns for the toggle and filters
    filter_col1, filter_col2 = st.columns([3, 1])
    
    with filter_col2:
        # Tech Jobs Only toggle
        tech_only = st.toggle(
            "💻 Tech Jobs Only",
            value=st.session_state.is_tech_role,
            key="tech_only_toggle",
            help="When enabled, only shows technology-related roles (engineers, developers, etc.)",
        )
        
        # Update session state if toggle changed
        if tech_only != st.session_state.is_tech_role:
            st.session_state.is_tech_role = tech_only
            st.session_state.jobs_page = 1  # Reset to page 1
            # Clear cache to refresh data
            st.cache_data.clear()
            st.rerun()
    
    with filter_col1:
        # Get service singleton
        service = get_jobs_service()

        # Get filters - don't call st.rerun() here
        raw_filters = render_filters()
        
        # Only update if filters actually changed
        current_filters = st.session_state.jobs_filters
        if raw_filters != current_filters:
            st.session_state.jobs_filters = raw_filters
            st.session_state.jobs_page = 1  # Reset to page 1 when filters change

        # Use filters from session state
        ui_filters = st.session_state.jobs_filters

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
    is_tech_role = st.session_state.is_tech_role

    # Get pagination state
    page = st.session_state.jobs_page
    page_size = st.session_state.jobs_page_size

    # Fetch data with caching
    try:
        response = fetch_jobs_cached(
            service,
            search,
            company,
            location,
            source_site,
            min_salary,
            max_salary,
            is_tech_role,
            page,
            page_size,
        )
    except Exception as e:
        show_error(f"Failed to load jobs: {str(e)}")
        return

    jobs = response.items

    # Stats bar with SVG icons
    jobs_icon = get_icon("jobs", size=16, color="#1a1a2e")
    page_icon = get_icon("overview", size=16, color="#1a1a2e")

    if response.total > 0:
        st.markdown(
            f"""
        <div class="jobs-stats">
            <div class="jobs-stat-item">
                <span class="stat-icon">{jobs_icon}</span>
                <span class="jobs-stat-number">{response.total:,}</span>
                <span class="jobs-stat-label">total jobs</span>
            </div>
            <span class="jobs-stat-divider">•</span>
            <div class="jobs-stat-item">
                <span class="stat-icon">{page_icon}</span>
                <span class="jobs-stat-number">{len(jobs):,}</span>
                <span class="jobs-stat-label">shown on this page</span>
            </div>
            <span class="jobs-stat-divider">•</span>
            <div class="jobs-stat-item">
                <span class="jobs-stat-number">{response.total_pages}</span>
                <span class="jobs-stat-label">pages</span>
            </div>
            <span class="jobs-stat-divider">•</span>
            <div class="jobs-stat-item">
                <span class="jobs-stat-number">{page}</span>
                <span class="jobs-stat-label">current page</span>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
        <div class="jobs-stats">
            <div class="jobs-stat-item">
                <span class="stat-icon">{jobs_icon}</span>
                <span class="jobs-stat-number">0</span>
                <span class="jobs-stat-label">jobs found</span>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Render content
    if not jobs:
        empty_icon = get_icon("jobs", size=48, color="#636e72")
        st.markdown(
            f"""
        <div class="jobs-empty">
            <div class="jobs-empty-icon">{empty_icon}</div>
            <div class="jobs-empty-title">No jobs found</div>
            <div class="jobs-empty-description">Try adjusting your search criteria or removing some filters</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
        render_empty_state()
        return

    # Render jobs in a professional container
    st.markdown('<div class="jobs-container">', unsafe_allow_html=True)
        
    # ============================================================
    # Sprint 6.6.1: Render each job with detail support
    # ============================================================
    for job in jobs:
        # Check if this job is selected for detail view
        job_id_str = str(job.id)
        if st.session_state.get("selected_job_id") == job_id_str:
            # Render full detail with translation support
            render_job_detail(job)  # ✅ Now imported at top
        else:
            # Render job card
            render_job_card(job)
    
    st.markdown("</div>", unsafe_allow_html=True)

    # Render pagination with professional styling
    if response.total_pages > 1:
        render_pagination(page, response.total_pages)

    # Safety guard - prevents invalid pagination states
    if page > response.total_pages and response.total_pages > 0:
        st.session_state.jobs_page = response.total_pages