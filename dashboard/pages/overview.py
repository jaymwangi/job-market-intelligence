# dashboard/pages/overview.py
"""Overview page with real dashboard metrics."""
import streamlit as st
from datetime import datetime
import logging

from dashboard.core.config import settings
from dashboard.services.health import HealthService
from dashboard.api.client import APIClient
from dashboard.components.alerts import show_error
from dashboard.components.metrics import render_metric_card
from dashboard.components.loading import loading_spinner
from dashboard.components.layout import divider
from dashboard.components.icons import get_icon
from dashboard.utils.state import StateManager

logger = logging.getLogger(__name__)


def render():
    """Render the overview page with real data."""
    # Header with SVG icon
    icon_svg = get_icon("overview", size=32, color="#1a1a2e")
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1.5rem;">
        <span style="display: inline-flex;">{icon_svg}</span>
        <div>
            <div style="font-size: 2rem; font-weight: 700; color: #1a1a2e; letter-spacing: -0.02em;">
                Dashboard Overview
            </div>
            <div style="color: #636e72; font-size: 0.95rem; font-weight: 400; margin-top: 0.25rem;">
                Welcome to the Job Market Dashboard
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Get services
    analytics_service = StateManager.get_analytics_service()
    
    # ========== KPI METRICS ==========
    st.markdown("### Dashboard Summary")
    
    with loading_spinner("Loading metrics..."):
        try:
            metrics = analytics_service.get_dashboard_metrics()
            if metrics:
                cols = st.columns(len(metrics))
                for col, metric in zip(cols, metrics):
                    with col:
                        render_metric_card(metric)
            else:
                st.info("No analytics data found. Please run the ETL pipeline.")
        except Exception as e:
            show_error(f"Failed to load metrics: {str(e)}")
    
    divider()
    
    # ========== RECENT JOBS ==========
    # Section header with SVG icon
    section_icon = get_icon("jobs", size=20, color="#1a1a2e")
    st.markdown(f"""
    <div style="margin: 1.5rem 0 1rem 0;">
        <div style="display: flex; align-items: center; gap: 0.5rem; font-size: 1.25rem; font-weight: 600; color: #1a1a2e;">
            <span style="display: inline-flex;">{section_icon}</span>
            Recent Job Postings
        </div>
        <div style="border-bottom: 2px solid #f8f9fa; margin-top: 0.5rem; padding-bottom: 0.5rem;"></div>
    </div>
    """, unsafe_allow_html=True)
    
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
                        # Use SVG icons for company and location
                        company_icon = get_icon("companies_metric", size=14, color="#636e72")
                        location_icon = get_icon("location", size=14, color="#636e72")
                        st.markdown(
                            f'<span style="color: #636e72; font-size: 0.9rem;">{company_icon} {job.company_name} • {location_icon} {job.location or "Remote"}</span>',
                            unsafe_allow_html=True
                        )
                    with col2:
                        if job.posted_date:
                            try:
                                if job.posted_date.tzinfo is not None:
                                    posted_date_naive = job.posted_date.replace(tzinfo=None)
                                else:
                                    posted_date_naive = job.posted_date
                                days_ago = (datetime.now() - posted_date_naive).days
                                st.caption(f"📅 {days_ago}d ago")
                            except Exception:
                                st.caption("📅 Recently posted")
                        if job.salary_min and job.salary_max:
                            salary_icon = get_icon("salary_metric", size=14, color="#636e72")
                            st.markdown(
                                f'<span style="color: #636e72; font-size: 0.85rem;">{salary_icon} ${job.salary_min:,.0f} - ${job.salary_max:,.0f}</span>',
                                unsafe_allow_html=True
                            )
        else:
            st.info("No recent job postings found.")
    except Exception as e:
        st.caption(f"Could not load recent jobs: {str(e)}")
    
    divider()
    
    # ========== QUICK LINKS ==========
    # Section header with SVG icon
    nav_icon = get_icon("overview", size=20, color="#1a1a2e")
    st.markdown(f"""
    <div style="margin: 1.5rem 0 1rem 0;">
        <div style="display: flex; align-items: center; gap: 0.5rem; font-size: 1.25rem; font-weight: 600; color: #1a1a2e;">
            <span style="display: inline-flex;">{nav_icon}</span>
            Quick Navigation
        </div>
        <div style="border-bottom: 2px solid #f8f9fa; margin-top: 0.5rem; padding-bottom: 0.5rem;"></div>
    </div>
    """, unsafe_allow_html=True)
    
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
    
    divider()
    
    # ========== API CONNECTION STATUS ==========
    # Use simple text for expander label (no HTML)
    with st.expander("🔌 API Connection Status", expanded=True):
        try:
            api_client = APIClient(settings.API_BASE_URL, settings.API_TIMEOUT)
            service = HealthService(api_client)
            health = service.check()
            
            if health.status in ["healthy", "ok"]:
                # Use SVG checkmark icon
                success_icon = get_icon("success", size=18, color="#00b894")
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:0.75rem;color:#155724;background:#d4edda;border:1px solid #c3e6cb;border-radius:8px;padding:0.75rem 1rem;">'
                    f'<span style="display:inline-flex;flex-shrink:0;">{success_icon}</span>'
                    f'<span style="font-weight:500;">API is healthy and reachable.</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            else:
                warning_icon = get_icon("warning", size=18, color="#fdcb6e")
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:0.75rem;color:#856404;background:#fff3cd;border:1px solid #ffeeba;border-radius:8px;padding:0.75rem 1rem;">'
                    f'<span style="display:inline-flex;flex-shrink:0;">{warning_icon}</span>'
                    f'<span style="font-weight:500;">API responded with status: {health.status}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                
        except Exception as e:
            error_icon = get_icon("error", size=18, color="#e94560")
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:0.75rem;color:#721c24;background:#f8d7da;border:1px solid #f5c6cb;border-radius:8px;padding:0.75rem 1rem;">'
                f'<span style="display:inline-flex;flex-shrink:0;">{error_icon}</span>'
                f'<span style="font-weight:500;">Cannot connect to API: {str(e)}</span>'
                f'</div>',
                unsafe_allow_html=True
            )
            st.markdown("""
            **Troubleshooting:**
            1. Make sure the FastAPI backend is running
            2. Check that `API_BASE_URL` is correct in `.env`
            3. Verify the backend is accessible at the configured URL
            """)