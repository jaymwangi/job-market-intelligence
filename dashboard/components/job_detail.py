import streamlit as st

from schemas.jobs import Job


def render_job_detail(job: Job):
    """Render detailed job information."""
    with st.container(border=True):
        st.subheader(f"📄 {job.title}")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"**Company:** {job.company_name}")
            st.markdown(f"**Location:** {job.location}")
            if job.source_site:
                st.markdown(f"**Source:** {job.source_site}")
            if job.source_url:
                st.markdown(f"**URL:** {job.source_url}")

        with col2:
            if job.salary_min and job.salary_max:
                currency = job.salary_currency or "USD"
                st.markdown(f"**Salary:** {currency} {job.salary_min:,.0f} - {job.salary_max:,.0f}")
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
                job.description[:1000] + "..." if len(job.description) > 1000 else job.description
            )

        # Close button
        if st.button("✕ Close Details", type="primary"):
            st.session_state.selected_job_id = None
            st.rerun()
