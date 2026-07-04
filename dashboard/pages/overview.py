# dashboard/pages/overview.py
import streamlit as st
from datetime import datetime

from dashboard.core.config import settings
from dashboard.services.health import HealthService
from dashboard.services.analytics_service import AnalyticsService
from dashboard.api.client import APIClient
from dashboard.components.alerts import show_error, show_success, show_warning
from dashboard.components.metrics import create_metric_card
from dashboard.components.loading import loading_spinner
from dashboard.utils.state import StateManager


def render():
    """Render the overview page with real data."""
    st.title("📊 Overview")
    st.markdown(f"Welcome to the **{settings.APP_TITLE}**.")
    st.markdown("---")
    
    # Get services
    analytics_service = StateManager.get_analytics_service()
    
    # ========== KPI METRICS ==========
    st.markdown("### 📈 Dashboard Summary")
    
    with loading_spinner("Loading metrics..."):
        try:
            metrics = analytics_service.get_dashboard_metrics()
            if metrics:
                cols = st.columns(len(metrics))
                for col, metric in zip(cols, metrics):
                    with col:
                        card_html = create_metric_card(metric)
                        st.markdown(card_html['html'], unsafe_allow_html=True)
            else:
                st.info("No analytics data found. Please run the ETL pipeline.")
        except Exception as e:
            show_error(f"Failed to load metrics: {str(e)}")
    
    st.markdown("---")
    
    # ========== RECENT JOBS ==========
    st.markdown("### 📋 Recent Job Postings")
    
    try:
        jobs_service = StateManager.get_jobs_service()
        from dashboard.schemas.jobs import JobFilters
        
        response = jobs_service.fetch_jobs(
            filters=JobFilters(),
            page=1,
            page_size=5
        )
        
        if response and response.items:
            for job in response.items[:5]:
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**{job.title}**")
                        st.caption(f"🏢 {job.company_name} • 📍 {job.location or 'Remote'}")
                    with col2:
                        if job.posted_date:
                            days_ago = (datetime.now() - job.posted_date).days
                            st.caption(f"📅 {days_ago}d ago")
                        if job.salary_min and job.salary_max:
                            st.caption(f"💰 ${job.salary_min:,.0f} - ${job.salary_max:,.0f}")
        else:
            st.info("No recent job postings found.")
    except Exception as e:
        st.caption(f"Could not load recent jobs: {str(e)}")
    
    st.markdown("---")
    
    # ========== QUICK LINKS ==========
    st.markdown("### 🚀 Quick Navigation")
    cols = st.columns(3)
    
    with cols[0]:
        if st.button("📊 View Analytics", use_container_width=True):
            StateManager.set_current_page("analytics")
            st.rerun()
    
    with cols[1]:
        if st.button("💼 Browse Jobs", use_container_width=True):
            StateManager.set_current_page("jobs")
            st.rerun()
    
    with cols[2]:
        if st.button("ℹ️ About", use_container_width=True):
            StateManager.set_current_page("about")
            st.rerun()
    
    st.markdown("---")
    
    # ========== API CONNECTION STATUS ==========
    with st.expander("🔌 API Connection Status", expanded=True):
        try:
            api_client = APIClient(settings.API_BASE_URL, settings.API_TIMEOUT)
            service = HealthService(api_client)
            health = service.check()
            
            if health.status == "healthy":
                show_success("✅ API is healthy and reachable.")
            elif health.status == "ok":
                show_success("✅ API is healthy and reachable.")
            else:
                show_warning(f"⚠️ API responded with status: {health.status}")
                
        except Exception as e:
            show_error(f"❌ Cannot connect to API: {str(e)}")
            st.markdown("""
            **Troubleshooting:**
            1. Make sure the FastAPI backend is running
            2. Check that `API_BASE_URL` is correct in `.env`
            3. Verify the backend is accessible at the configured URL
            """)