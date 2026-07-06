"""Empty state components."""

import logging

import streamlit as st

logger = logging.getLogger(__name__)


def render_empty_state(
    title: str = "No Data Available",
    description: str = "",
    icon: str = "📭",
    show_reset: bool = False,
) -> None:
    """
    Render empty state with optional reset button.

    Args:
        title: Main title text
        description: Description text
        icon: Emoji icon
        show_reset: Show reset filters button
    """
    with st.container(border=True):
        col_icon, col_text = st.columns([1, 4])

        with col_icon:
            st.markdown(
                f"<h1 style='text-align: center;'>{icon}</h1>",
                unsafe_allow_html=True,
            )

        with col_text:
            st.markdown(f"**{title}**")
            if description:
                st.caption(description)

        if show_reset:
            if st.button("🔄 Clear All Filters", key="reset_empty_state"):
                _reset_filters_state()
                st.rerun()


def _reset_filters_state() -> None:
    """
    Reset filter state in session.

    This resets all job filters, pagination, and selected job.
    Analytics cache refresh is attempted but failures are logged.
    """
    # Reset job filters - assign directly (keys created if missing)
    st.session_state["job_filters"] = {}
    st.session_state["page"] = 1
    st.session_state["selected_job_id"] = None

    # Reset analytics cache if available - non-critical operation
    if "service_factory" in st.session_state:
        try:
            st.session_state.service_factory.refresh_all()
        except Exception:
            logger.exception("Failed to refresh analytics cache during filter reset")


def empty_state_analytics(
    title: str = "No Data Available",
    description: str = "No analytics data found. Please run the ETL pipeline.",
    icon: str = "📭",
) -> None:
    """Render empty state specifically for analytics pages."""
    render_empty_state(
        title=title,
        description=description,
        icon=icon,
        show_reset=False,
    )


def empty_state_jobs(
    title: str = "No Jobs Found",
    description: str = "No jobs matching your filters.",
    icon: str = "🔍",
) -> None:
    """Render empty state specifically for jobs page."""
    render_empty_state(
        title=title,
        description=description,
        icon=icon,
        show_reset=True,
    )
