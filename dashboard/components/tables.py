import streamlit as st

from dashboard.schemas.jobs import Job


def render_jobs_table(jobs: list[Job]):
    """Render jobs in a clean, readable table format with inline expansion."""
    if not jobs:
        return

    for idx, job in enumerate(jobs):
        # Create a unique key for this job's expansion state
        expand_key = f"expanded_{job.id}"

        # Initialize expansion state if not exists
        if expand_key not in st.session_state:
            st.session_state[expand_key] = False

        with st.container(border=True):
            # Header row - always visible
            col1, col2, col3 = st.columns([3, 1, 0.8])

            with col1:
                st.subheader(job.title)
                st.caption(f"🏢 {job.company_name} • 📍 {job.location}")

                if job.source_site:
                    st.caption(f"📋 Source: {job.source_site}")

                # Salary summary in header
                if job.salary_min and job.salary_max:
                    currency = job.salary_currency or "USD"
                    st.caption(f"💰 {currency} {job.salary_min:,.0f} - {job.salary_max:,.0f}")
                elif job.salary_min:
                    currency = job.salary_currency or "USD"
                    st.caption(f"💰 From {currency} {job.salary_min:,.0f}")
                elif job.salary_max:
                    currency = job.salary_currency or "USD"
                    st.caption(f"💰 Up to {currency} {job.salary_max:,.0f}")

            with col2:
                if job.posted_date:
                    st.caption(f"📅 {job.posted_date.strftime('%Y-%m-%d')}")
                status = "🟢 Active" if job.is_active else "🔴 Inactive"
                st.caption(status)

            with col3:
                # Toggle button - changes text based on state
                button_label = "📄 Hide" if st.session_state[expand_key] else "📄 View"
                # Use callback to toggle state - NO rerun needed!
                if st.button(button_label, key=f"toggle_{job.id}_{idx}"):
                    st.session_state[expand_key] = not st.session_state[expand_key]
                    # st.rerun() - REMOVED! No rerun needed

            # Expanded details - shown inline when expanded
            if st.session_state[expand_key]:
                st.markdown("---")

                # Two column layout for details
                detail_col1, detail_col2 = st.columns(2)

                with detail_col1:
                    st.markdown(f"**Company:** {job.company_name}")
                    st.markdown(f"**Location:** {job.location}")
                    if job.source_site:
                        st.markdown(f"**Source:** {job.source_site}")
                    if job.source_url:
                        st.markdown(f"**URL:** {job.source_url}")

                with detail_col2:
                    if job.salary_min and job.salary_max:
                        currency = job.salary_currency or "USD"
                        st.markdown(
                            f"**Salary:** {currency} {job.salary_min:,.0f} - {job.salary_max:,.0f}"
                        )
                    elif job.salary_min:
                        currency = job.salary_currency or "USD"
                        st.markdown(f"**Salary:** From {currency} {job.salary_min:,.0f}")
                    elif job.salary_max:
                        currency = job.salary_currency or "USD"
                        st.markdown(f"**Salary:** Up to {currency} {job.salary_max:,.0f}")
                    else:
                        st.markdown("**Salary:** Not specified")

                    st.markdown(f"**Posted:** {job.posted_date.strftime('%Y-%m-%d %H:%M')}")
                    status = "Active" if job.is_active else "Inactive"
                    st.markdown(f"**Status:** {status}")

                # Description
                if job.description:
                    st.markdown("---")
                    st.markdown("### 📝 Description")
                    st.markdown(
                        job.description[:1000] + "..."
                        if len(job.description) > 1000
                        else job.description
                    )
