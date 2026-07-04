# dashboard/components/empty_state.py
"""Empty state components."""
import streamlit as st


def render_empty_state(
    title: str = "No Data Available",
    description: str = "",
    icon: str = "📭",
    show_reset: bool = False,
    reset_filters: bool = True
):
    """
    Render empty state with optional reset button.
    
    Args:
        title: Main title text
        description: Description text
        icon: Emoji icon
        show_reset: Show reset filters button
        reset_filters: Whether to reset filters or entire state
    """
    with st.container(border=True):
        col_icon, col_text = st.columns([1, 4])
        
        with col_icon:
            st.markdown(f"<h1 style='text-align: center;'>{icon}</h1>", unsafe_allow_html=True)
        
        with col_text:
            st.markdown(f"**{title}**")
            if description:
                st.caption(description)
        
        if show_reset:
            if st.button("🔄 Clear All Filters", key="reset_empty_state"):
                if reset_filters:
                    # Reset job filters
                    if 'job_filters' in st.session_state:
                        st.session_state.job_filters = {}
                    if 'page' in st.session_state:
                        st.session_state.page = 1
                    if 'selected_job_id' in st.session_state:
                        st.session_state.selected_job_id = None
                # Reset analytics cache if needed
                if 'service_factory' in st.session_state:
                    try:
                        st.session_state.service_factory.refresh_all()
                    except:
                        pass
                st.rerun()


def empty_state_analytics(
    title: str = "No Data Available",
    description: str = "No analytics data found. Please run the ETL pipeline.",
    icon: str = "📭"
):
    """Render empty state specifically for analytics pages."""
    render_empty_state(
        title=title,
        description=description,
        icon=icon,
        show_reset=False
    )


def empty_state_jobs(
    title: str = "No Jobs Found",
    description: str = "No jobs matching your filters.",
    icon: str = "🔍"
):
    """Render empty state specifically for jobs page."""
    render_empty_state(
        title=title,
        description=description,
        icon=icon,
        show_reset=True,
        reset_filters=True
    )