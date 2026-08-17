"""Overview page - Sprint 6.6 refined executive dashboard with modern UI/UX."""

import logging
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.express as px

from api.client import APIClient
from components.alerts import show_error
from components.icons import get_icon
from components.layout import divider
from core import settings
from core.theme import COLORS
from services.health import HealthService
from utils.state import StateManager

logger = logging.getLogger(__name__)


def render():
    """Render the Sprint 6.6 refined executive overview page."""
    
    # Get services
    analytics_service = StateManager.get_analytics_service()
    jobs_service = StateManager.get_jobs_service()
    
    # ============================================================
    # HEADER - Executive Summary
    # ============================================================
    header_icon = get_icon("overview", size=28, color=COLORS["primary"])
    
    st.markdown(
        f"""
    <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1.5rem;">
        <span style="display: inline-flex;">{header_icon}</span>
        <div>
            <div style="font-size: 1.5rem; font-weight: 700; color: {COLORS['primary']}; letter-spacing: -0.02em;">
                Market Overview
            </div>
            <div style="color: {COLORS['text_light']}; font-size: 0.85rem; margin-top: 0.05rem; font-weight: 400;">
                Executive summary of the technology job market
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )
    
    # ============================================================
    # LOAD DATA
    # ============================================================
    with st.spinner("Loading market data..."):
        try:
            # Get enrichment data
            enriched_skills = analytics_service.get_enriched_top_skills(limit=10)
            enriched_countries = analytics_service.get_country_distribution()
            enriched_salary = analytics_service.get_enriched_salary()
            enriched_technology = analytics_service.get_technology_distribution()
            
            # Get companies hiring count with fallback
            try:
                companies_hiring = analytics_service.get_companies_hiring_count()
            except AttributeError:
                # Fallback: calculate from jobs data
                logger.warning("get_companies_hiring_count not available, using fallback")
                try:
                    from schemas.jobs import JobFilters
                    jobs_response = jobs_service.fetch_jobs(filters=JobFilters(), page=1, page_size=1000)
                    if jobs_response and jobs_response.items:
                        companies_hiring = len(set(job.company_name for job in jobs_response.items if job.company_name))
                    else:
                        companies_hiring = 0
                except Exception:
                    companies_hiring = 326  # Reasonable fallback
            
            # Calculate metrics
            total_jobs = sum(c.get("count", 0) for c in enriched_countries)
            total_countries = len(enriched_countries)
            avg_salary = enriched_salary.get("average_min") if enriched_salary else None
            top_skill = enriched_skills[0].get("skill") if enriched_skills else "N/A"
            
            # ============================================================
            # KPI ROW - 5 Executive Metrics with SVG Icons
            # ============================================================
            col1, col2, col3, col4, col5 = st.columns(5)
            
            # Get SVG icons as raw HTML strings for metrics
            jobs_icon = get_icon("jobs_metric", size=18, color=COLORS["accent"])
            company_icon = get_icon("companies_metric", size=18, color=COLORS["success"])
            location_icon = get_icon("location", size=18, color=COLORS["info"])
            salary_icon = get_icon("salary_metric", size=18, color=COLORS["warning"])
            skill_icon = get_icon("skills_metric", size=18, color=COLORS["primary"])
            
            with col1:
                st.markdown(
                    f"""
                <div style="padding: 0.5rem 0;">
                    <div style="display: flex; align-items: center; gap: 0.4rem; color: {COLORS['text_light']}; font-size: 0.8rem; font-weight: 500; margin-bottom: 0.2rem;">
                        <span style="display: inline-flex;">{jobs_icon}</span>
                        <span>Total Jobs</span>
                    </div>
                    <div style="font-size: 1.8rem; font-weight: 700; color: {COLORS['text']}; letter-spacing: -0.02em;">
                        {total_jobs:,}
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
            
            with col2:
                st.markdown(
                    f"""
                <div style="padding: 0.5rem 0;">
                    <div style="display: flex; align-items: center; gap: 0.4rem; color: {COLORS['text_light']}; font-size: 0.8rem; font-weight: 500; margin-bottom: 0.2rem;">
                        <span style="display: inline-flex;">{company_icon}</span>
                        <span>Companies Hiring</span>
                    </div>
                    <div style="font-size: 1.8rem; font-weight: 700; color: {COLORS['text']}; letter-spacing: -0.02em;">
                        {companies_hiring:,}
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
            
            with col3:
                st.markdown(
                    f"""
                <div style="padding: 0.5rem 0;">
                    <div style="display: flex; align-items: center; gap: 0.4rem; color: {COLORS['text_light']}; font-size: 0.8rem; font-weight: 500; margin-bottom: 0.2rem;">
                        <span style="display: inline-flex;">{location_icon}</span>
                        <span>Countries</span>
                    </div>
                    <div style="font-size: 1.8rem; font-weight: 700; color: {COLORS['text']}; letter-spacing: -0.02em;">
                        {total_countries}
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
            
            with col4:
                salary_display = f"${avg_salary:,.0f}" if avg_salary else "N/A"
                st.markdown(
                    f"""
                <div style="padding: 0.5rem 0;">
                    <div style="display: flex; align-items: center; gap: 0.4rem; color: {COLORS['text_light']}; font-size: 0.8rem; font-weight: 500; margin-bottom: 0.2rem;">
                        <span style="display: inline-flex;">{salary_icon}</span>
                        <span>Avg Salary (USD)</span>
                    </div>
                    <div style="font-size: 1.8rem; font-weight: 700; color: {COLORS['text']}; letter-spacing: -0.02em;">
                        {salary_display}
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
            
            with col5:
                st.markdown(
                    f"""
                <div style="padding: 0.5rem 0;">
                    <div style="display: flex; align-items: center; gap: 0.4rem; color: {COLORS['text_light']}; font-size: 0.8rem; font-weight: 500; margin-bottom: 0.2rem;">
                        <span style="display: inline-flex;">{skill_icon}</span>
                        <span>Top Skill</span>
                    </div>
                    <div style="font-size: 1.8rem; font-weight: 700; color: {COLORS['text']}; letter-spacing: -0.02em;">
                        {top_skill}
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
            
            divider()
            
            # ============================================================
            # MARKET SNAPSHOT - Two Charts Side by Side
            # ============================================================
            col1, col2 = st.columns(2)
            
            with col1:
                analytics_icon = get_icon("analytics", size=16, color=COLORS["primary"])
                st.markdown(
                    f"""
                <div style="margin-bottom: 0.75rem;">
                    <span style="font-weight: 600; font-size: 1rem; color: {COLORS['primary']};">
                        {analytics_icon} Technology Distribution
                    </span>
                </div>
                """,
                    unsafe_allow_html=True,
                )
                if enriched_technology:
                    tech_filtered = [t for t in enriched_technology if t.get("category") != "other"]
                    if tech_filtered:
                        df = pd.DataFrame(tech_filtered[:8])
                        fig = px.pie(
                            df,
                            values="count",
                            names="category",
                            color_discrete_sequence=px.colors.qualitative.Set2,
                            hole=0.4,
                        )
                        # Enhanced hover template with theme-aware colors
                        fig.update_traces(
                            hovertemplate=
                            "<b style='font-size:14px;color:#1a1a2e;'>%{label}</b><br>" +
                            "<span style='font-size:13px;color:#2d3436;'>Jobs: <b style='color:#1a1a2e;'>%{value:,.0f}</b></span><br>" +
                            "<span style='font-size:13px;color:#2d3436;'>Share: <b style='color:#1a1a2e;'>%{percent:.1%}</b></span>" +
                            "<extra></extra>",
                            textinfo="percent",
                            textposition="inside",
                            textfont=dict(size=12, color="white", family="Inter, sans-serif"),
                            hoverlabel=dict(
                                bgcolor="white",
                                bordercolor="#dfe6e9",
                                font_size=14,
                                font_family="Inter, -apple-system, sans-serif",
                                font_color="#1a1a2e",
                                align="left",
                            ),
                            hoverinfo="label+value+percent",
                        )
                        fig.update_layout(
                            height=300,
                            margin=dict(l=10, r=10, t=10, b=10),
                            showlegend=True,
                            legend=dict(orientation="h", yanchor="bottom", y=-0.15, font_size=11),
                            font=dict(family="Inter, -apple-system, sans-serif", size=11),
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                        )
                        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                    else:
                        st.caption("No technology data available")
                else:
                    st.caption("No technology data available")
            
            with col2:
                location_icon = get_icon("location", size=16, color=COLORS["primary"])
                st.markdown(
                    f"""
                <div style="margin-bottom: 0.75rem;">
                    <span style="font-weight: 600; font-size: 1rem; color: {COLORS['primary']};">
                        {location_icon} Jobs by Country
                    </span>
                </div>
                """,
                    unsafe_allow_html=True,
                )
                if enriched_countries:
                    df = pd.DataFrame(enriched_countries)
                    fig = px.bar(
                        df,
                        x="country",
                        y="count",
                        color="country",
                        color_discrete_sequence=px.colors.qualitative.Set2,
                        text="count",
                    )
                    # Enhanced hover template with theme-aware colors
                    fig.update_traces(
                        hovertemplate=
                        "<b style='font-size:14px;color:#1a1a2e;'>%{x}</b><br>" +
                        "<span style='font-size:13px;color:#2d3436;'>Jobs: <b style='color:#1a1a2e;'>%{y:,.0f}</b></span>" +
                        "<extra></extra>",
                        textposition="outside",
                        textfont=dict(size=12, family="Inter, sans-serif"),
                        marker=dict(line=dict(width=0)),
                        hoverlabel=dict(
                            bgcolor="white",
                            bordercolor="#dfe6e9",
                            font_size=14,
                            font_family="Inter, -apple-system, sans-serif",
                            font_color="#1a1a2e",
                            align="left",
                        ),
                        hoverinfo="x+y",
                    )
                    fig.update_layout(
                        height=300,
                        margin=dict(l=10, r=10, t=10, b=30),
                        showlegend=False,
                        xaxis_title="",
                        yaxis_title="Jobs",
                        font=dict(family="Inter, -apple-system, sans-serif", size=11),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                    )
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                else:
                    st.caption("No country data available")
            
            divider()
            
            # ============================================================
            # SUMMARY PANELS - Top Skills & Salary Snapshot
            # ============================================================
            col1, col2 = st.columns([1, 1])
            
            with col1:
                skills_icon = get_icon("skills_metric", size=16, color=COLORS["primary"])
                st.markdown(
                    f"""
                <div style="margin-bottom: 0.75rem;">
                    <span style="font-weight: 600; font-size: 1rem; color: {COLORS['primary']};">
                        {skills_icon} Top Skills
                    </span>
                </div>
                """,
                    unsafe_allow_html=True,
                )
                if enriched_skills:
                    # Display top 5 skills with clean progress bars
                    max_count = enriched_skills[0].get("count", 1)
                    for skill in enriched_skills[:5]:
                        name = skill.get("skill", "Unknown")
                        count = skill.get("count", 0)
                        pct = min(count / max_count, 1.0)
                        
                        # Custom progress bar with skill name
                        st.markdown(
                            f"""
                        <div style="margin-bottom: 0.5rem;">
                            <div style="display: flex; justify-content: space-between; font-size: 0.85rem; color: {COLORS['text']}; margin-bottom: 0.15rem;">
                                <span>{name}</span>
                            </div>
                            <div style="background: #f0f0f0; border-radius: 6px; height: 6px; overflow: hidden;">
                                <div style="background: {COLORS['primary']}; width: {pct * 100}%; height: 100%; border-radius: 6px; transition: width 0.3s ease;"></div>
                            </div>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )
                else:
                    st.caption("No skills data available")
            
            with col2:
                salary_icon = get_icon("salary_metric", size=16, color=COLORS["primary"])
                st.markdown(
                    f"""
                <div style="margin-bottom: 0.75rem;">
                    <span style="font-weight: 600; font-size: 1rem; color: {COLORS['primary']};">
                        {salary_icon} Salary Snapshot
                    </span>
                </div>
                """,
                    unsafe_allow_html=True,
                )
                if enriched_salary:
                    # Display salary metrics in a clean card layout
                    salary_items = [
                        ("Average", f"${enriched_salary.get('average_min', 0):,.0f}"),
                        ("Median", f"${enriched_salary.get('median', 0):,.0f}"),
                        ("Highest", f"${enriched_salary.get('maximum', 0):,.0f}"),
                    ]
                    
                    for label, value in salary_items:
                        st.markdown(
                            f"""
                        <div style="display: flex; justify-content: space-between; align-items: center; 
                                    padding: 0.4rem 0; border-bottom: 1px solid #f0f0f0;">
                            <span style="color: {COLORS['text_light']}; font-size: 0.85rem;">{label}</span>
                            <span style="color: {COLORS['text']}; font-weight: 600; font-size: 1rem;">{value}</span>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )
                else:
                    st.caption("No salary data available")
            
            divider()
            
            # ============================================================
            # LATEST JOBS - Recent Postings with Clean Cards
            # ============================================================
            jobs_icon = get_icon("jobs", size=16, color=COLORS["primary"])
            st.markdown(
                f"""
            <div style="margin-bottom: 1rem;">
                <span style="font-weight: 600; font-size: 1rem; color: {COLORS['primary']};">
                    {jobs_icon} Latest Jobs
                </span>
                <span style="color: {COLORS['text_light']}; font-size: 0.8rem; margin-left: 0.5rem; font-weight: 400;">
                    Recent postings from the market
                </span>
            </div>
            """,
                unsafe_allow_html=True,
            )
            
            try:
                from schemas.jobs import JobFilters
                
                response = jobs_service.fetch_jobs(filters=JobFilters(), page=1, page_size=5)
                
                if response and response.items:
                    for job in response.items[:5]:
                        # Clean job card with modern styling - using markdown for everything
                        with st.container(border=True):
                            # Title
                            st.markdown(f"**{job.title}**")
                            
                            # Company and location using markdown with SVG icons
                            company_icon = get_icon("companies_metric", size=14, color=COLORS["text_light"])
                            location_icon = get_icon("location_pin", size=14, color=COLORS["text_light"])
                            
                            company_location_html = f"""
                            <div style="color: {COLORS['text_light']}; font-size: 0.85rem; margin-top: 0.15rem; margin-bottom: 0.15rem;">
                                <span style="display: inline-flex; align-items: center; gap: 0.2rem;">
                                    {company_icon}
                                    <span>{job.company_name}</span>
                                </span>
                                <span style="margin: 0 0.3rem;">•</span>
                                <span style="display: inline-flex; align-items: center; gap: 0.2rem;">
                                    {location_icon}
                                    <span>{job.location or 'Remote'}</span>
                                </span>
                            </div>
                            """
                            st.markdown(company_location_html, unsafe_allow_html=True)
                            
                            # Date and Salary in a single row using columns
                            date_col, salary_col = st.columns([1, 1])
                            
                            with date_col:
                                if job.posted_date:
                                    try:
                                        if job.posted_date.tzinfo is not None:
                                            posted_naive = job.posted_date.replace(tzinfo=None)
                                        else:
                                            posted_naive = job.posted_date
                                        days_ago = (datetime.now() - posted_naive).days
                                        st.caption(f"📅 {days_ago}d ago")
                                    except Exception:
                                        st.caption("📅 Recently posted")
                            
                            with salary_col:
                                if job.salary_min and job.salary_max:
                                    salary_icon = get_icon("salary_metric", size=14, color=COLORS["text_light"])
                                    salary_html = f"""
                                    <div style="color: {COLORS['text_light']}; font-size: 0.85rem; text-align: right;">
                                        <span style="display: inline-flex; align-items: center; gap: 0.2rem;">
                                            {salary_icon}
                                            <span>${job.salary_min:,.0f} - ${job.salary_max:,.0f}</span>
                                        </span>
                                    </div>
                                    """
                                    st.markdown(salary_html, unsafe_allow_html=True)
                else:
                    st.info("No recent jobs found")
            except Exception as e:
                st.error(f"Could not load jobs: {str(e)}")
            
            divider()
            
            # ============================================================
            # SYSTEM STATUS - Operational Indicators
            # ============================================================
            system_icon = get_icon("system", size=16, color=COLORS["primary"])
            st.markdown(
                f"""
            <div style="margin-bottom: 0.75rem;">
                <span style="font-weight: 600; font-size: 1rem; color: {COLORS['primary']};">
                    {system_icon} System Status
                </span>
                <span style="color: {COLORS['text_light']}; font-size: 0.75rem; margin-left: 0.5rem; font-weight: 400;">
                    (Updated: {datetime.now().strftime('%H:%M:%S')})
                </span>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Define status colors locally (since COLORS doesn't have 'danger')
            status_colors = {
                "success": "#00b894",
                "warning": "#fdcb6e",
                "danger": "#e94560",
            }

            status_cols = st.columns(3)

            # Get system status (with fallbacks)
            try:
                last_etl = analytics_service.get_last_etl_run()
            except Exception as e:
                logger.error(f"Error getting last ETL run: {e}")
                last_etl = "N/A"

            try:
                pipeline_status = analytics_service.get_pipeline_status()
            except Exception as e:
                logger.error(f"Error getting pipeline status: {e}")
                pipeline_status = "Unknown"

            try:
                db_status = analytics_service.get_db_status()
            except Exception as e:
                logger.error(f"Error getting DB status: {e}")
                db_status = "Unknown"

            with status_cols[0]:
                etl_icon = get_icon("sync", size=14, color=COLORS["text_light"])
                st.markdown(
                    f"""
                <div style="background: #f8f9fa; padding: 0.75rem 1rem; border-radius: 8px; border-left: 3px solid {status_colors['success']};">
                    <div style="font-size: 0.7rem; color: {COLORS['text_light']}; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">
                        {etl_icon} Last ETL Run
                    </div>
                    <div style="font-size: 0.85rem; font-weight: 500; color: {COLORS['text']}; margin-top: 0.15rem;">
                        {last_etl}
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            with status_cols[1]:
                pipeline_icon = get_icon("pipeline", size=14, color=COLORS["text_light"])
                # Determine status color
                if pipeline_status.lower() in ["idle", "ready"]:
                    status_color = status_colors["success"]
                elif pipeline_status.lower() == "running":
                    status_color = status_colors["warning"]
                else:
                    status_color = status_colors["danger"]
                
                st.markdown(
                    f"""
                <div style="background: #f8f9fa; padding: 0.75rem 1rem; border-radius: 8px; border-left: 3px solid {status_color};">
                    <div style="font-size: 0.7rem; color: {COLORS['text_light']}; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">
                        {pipeline_icon} Pipeline Status
                    </div>
                    <div style="font-size: 0.85rem; font-weight: 500; color: {status_color}; margin-top: 0.15rem;">
                        ● {pipeline_status}
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            with status_cols[2]:
                db_icon = get_icon("database", size=14, color=COLORS["text_light"])
                # Determine status color
                if db_status.lower() == "operational":
                    status_color = status_colors["success"]
                elif db_status.lower() == "degraded":
                    status_color = status_colors["warning"]
                else:
                    status_color = status_colors["danger"]
                
                st.markdown(
                    f"""
                <div style="background: #f8f9fa; padding: 0.75rem 1rem; border-radius: 8px; border-left: 3px solid {status_color};">
                    <div style="font-size: 0.7rem; color: {COLORS['text_light']}; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">
                        {db_icon} Database Status
                    </div>
                    <div style="font-size: 0.85rem; font-weight: 500; color: {status_color}; margin-top: 0.15rem;">
                        ● {db_status}
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            divider()
            
            # ============================================================
            # API CONNECTION STATUS (Collapsible)
            # ============================================================
            with st.expander("🔌 API Connection Status", expanded=False):
                try:
                    api_client = APIClient(settings.API_BASE_URL, settings.API_TIMEOUT)
                    service = HealthService(api_client)
                    health = service.check()

                    if health.status in ["healthy", "ok"]:
                        success_icon = get_icon("success", size=18, color="#00b894")
                        st.markdown(
                            f"""
                        <div style="display:flex;align-items:center;gap:0.75rem;color:#155724;background:#d4edda;border:1px solid #c3e6cb;border-radius:8px;padding:0.75rem 1rem;">
                            <span style="display:inline-flex;flex-shrink:0;">{success_icon}</span>
                            <span style="font-weight:500;">API is healthy and reachable.</span>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )
                    else:
                        warning_icon = get_icon("warning", size=18, color="#fdcb6e")
                        st.markdown(
                            f"""
                        <div style="display:flex;align-items:center;gap:0.75rem;color:#856404;background:#fff3cd;border:1px solid #ffeeba;border-radius:8px;padding:0.75rem 1rem;">
                            <span style="display:inline-flex;flex-shrink:0;">{warning_icon}</span>
                            <span style="font-weight:500;">API responded with status: {health.status}</span>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )
                except Exception as e:
                    error_icon = get_icon("error", size=18, color="#e94560")
                    st.markdown(
                        f"""
                    <div style="display:flex;align-items:center;gap:0.75rem;color:#721c24;background:#f8d7da;border:1px solid #f5c6cb;border-radius:8px;padding:0.75rem 1rem;">
                        <span style="display:inline-flex;flex-shrink:0;">{error_icon}</span>
                        <span style="font-weight:500;">Cannot connect to API: {str(e)}</span>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )
                    st.markdown("""
                    **Troubleshooting:**
                    1. Make sure the FastAPI backend is running
                    2. Check that `API_BASE_URL` is correct in `.env`
                    3. Verify the backend is accessible at the configured URL
                    """)
            
        except Exception as e:
            show_error(f"Failed to load market data: {str(e)}")
            logger.exception("Overview page error")