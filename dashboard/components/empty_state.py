import streamlit as st


def render_empty_state():
    """Render empty state when no jobs found."""
    with st.container(border=True):
        st.info("🔍 No jobs found matching your filters.")
        st.caption("Try adjusting your search criteria or removing some filters.")
        
        # Quick reset button
        if st.button("🔄 Clear All Filters"):
            st.session_state.job_filters = {}
            st.session_state.page = 1
            st.session_state.selected_job_id = None
            st.rerun()