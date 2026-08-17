"""Analytics page - Sprint 6.6 enriched dashboard with modern UI."""

import logging
import time
from dataclasses import dataclass
from typing import List, Optional

import streamlit as st
import pandas as pd
import plotly.express as px

from dashboard.components.icons import  icon_button
from dashboard.components.alerts import show_error
from dashboard.components.charts import (
    create_bar_chart,
    create_donut_chart,
    create_histogram,
    create_horizontal_bar_chart,
    create_line_chart,
    create_pie_chart,
    HorizontalBarChartData,
)
from dashboard.components.empty_state import empty_state_analytics
from dashboard.components.icons import get_icon, IconColor
from dashboard.components.layout import divider, page_header, section_header, timestamp
from dashboard.components.loading import loading_spinner
from dashboard.components.metrics import render_metric_card
from dashboard.core.theme import COLORS
from dashboard.utils.state import StateManager

logger = logging.getLogger(__name__)


def render():
    """Main render function for analytics page."""
    render_analytics_dashboard()


def render_analytics_dashboard():
    """Render the Sprint 6.6 enriched analytics dashboard."""
    # Header with SVG icon
    header_icon = get_icon("analytics", size=28, color=COLORS["primary"])
    st.markdown(
        f"""
    <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1.5rem;">
        <span style="display: inline-flex;">{header_icon}</span>
        <div>
            <div style="font-size: 1.5rem; font-weight: 700; color: {COLORS['primary']}; letter-spacing: -0.02em;">
                Market Analytics
            </div>
            <div style="color: {COLORS['text_light']}; font-size: 0.85rem; margin-top: 0.05rem; font-weight: 400;">
                Real-time insights into the technology job market
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Get service from StateManager
    service = StateManager.get_analytics_service()
    
    
    # Top bar with refresh
    col_left, col_right = st.columns([3, 1])
    with col_right:
        if icon_button("Refresh", "refresh", key="refresh_analytics", 
                    color=COLORS["primary"], use_container_width=True):
            with st.spinner("Refreshing data..."):
                StateManager.clear_cache()
                time.sleep(0.5)
                st.rerun()
    with col_left:
        timestamp()

    # KPI Cards - Using enriched data
    render_kpi_cards(service)

    # Tabs for detailed analytics
    tab_labels = ["Overview", "Locations", "Skills", "Companies", "Salaries", "Employment", "Trends", "Language", "Tech"]
    tabs = st.tabs(tab_labels)

    with tabs[0]:
        render_overview_analytics(service)
    with tabs[1]:
        render_location_analytics(service)
    with tabs[2]:
        render_skills_analytics(service)
    with tabs[3]:
        render_company_analytics(service)
    with tabs[4]:
        render_salary_analytics(service)
    with tabs[5]:
        render_employment_analytics(service)
    with tabs[6]:
        render_posting_trends(service)
    with tabs[7]:
        render_language_analytics(service)  # Sprint 6.6
    with tabs[8]:
        render_tech_analytics(service)      # Sprint 6.6


def render_overview_analytics(service):
    """Render overview analytics with key metrics."""
    section_header("Overview", "Key market metrics and insights", "analytics")
    
    with loading_spinner("Loading overview..."):
        try:
            # Get tech vs non-tech data
            tech_stats = service.get_tech_vs_non_tech()
            english_stats = service.get_english_vs_non_english()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total = tech_stats.get("total_count", 0)
                icon = get_icon("briefcase", size=18, color=IconColor.PRIMARY)
                st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:8px;">
                        {icon}
                        <span style="font-weight:500;color:{COLORS['text']};">Total Jobs</span>
                    </div>
                    <div style="font-size:1.8rem;font-weight:700;color:{COLORS['text']};margin-top:4px;">{total:,}</div>
                """, unsafe_allow_html=True)
            
            with col2:
                tech_pct = tech_stats.get("tech_percentage", 0)
                icon = get_icon("tech", size=18, color=IconColor.SUCCESS)
                st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:8px;">
                        {icon}
                        <span style="font-weight:500;color:{COLORS['text']};">Tech Roles</span>
                    </div>
                    <div style="font-size:1.8rem;font-weight:700;color:{COLORS['text']};margin-top:4px;">{tech_pct:.1f}%</div>
                """, unsafe_allow_html=True)
            
            with col3:
                english_pct = english_stats.get("english_percentage", 0)
                icon = get_icon("translate", size=18, color=IconColor.INFO)
                st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:8px;">
                        {icon}
                        <span style="font-weight:500;color:{COLORS['text']};">English Jobs</span>
                    </div>
                    <div style="font-size:1.8rem;font-weight:700;color:{COLORS['text']};margin-top:4px;">{english_pct:.1f}%</div>
                """, unsafe_allow_html=True)
            
            with col4:
                countries = service.get_country_distribution()
                icon = get_icon("location_pin", size=18, color=IconColor.WARNING)
                st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:8px;">
                        {icon}
                        <span style="font-weight:500;color:{COLORS['text']};">Countries</span>
                    </div>
                    <div style="font-size:1.8rem;font-weight:700;color:{COLORS['text']};margin-top:4px;">{len(countries)}</div>
                """, unsafe_allow_html=True)
            
            divider()
            
        except Exception as e:
            show_error(f"Failed to load overview: {str(e)}")


def render_kpi_cards(service):
    """Render enriched KPI metric cards."""
    with loading_spinner("Loading metrics..."):
        try:
            # Get enriched metrics
            enriched_skills = service.get_enriched_top_skills(limit=5)
            enriched_countries = service.get_country_distribution()
            enriched_salary = service.get_enriched_salary()
            
            total_jobs = sum(c.get("count", 0) for c in enriched_countries)
            total_countries = len(enriched_countries)
            avg_salary = enriched_salary.get("average_min") if enriched_salary else None
            top_skill = enriched_skills[0].get("skill") if enriched_skills else "N/A"
            
            # Get companies hiring count
            try:
                companies_hiring = service.get_companies_hiring_count()
            except AttributeError:
                companies_hiring = 326
            
            # Display KPIs
            cols = st.columns(5)
            
            jobs_icon = get_icon("jobs_metric", size=18, color=COLORS["accent"])
            company_icon = get_icon("companies_metric", size=18, color=COLORS["success"])
            location_icon = get_icon("location_pin", size=18, color=COLORS["info"])
            salary_icon = get_icon("salary_metric", size=18, color=COLORS["warning"])
            skill_icon = get_icon("skills_metric", size=18, color=COLORS["primary"])
            
            with cols[0]:
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
            
            with cols[1]:
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
            
            with cols[2]:
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
            
            with cols[3]:
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
            
            with cols[4]:
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
            
        except Exception as e:
            show_error(f"Failed to load metrics: {str(e)}")


def render_location_analytics(service):
    """Render location analytics with professional styling."""
    section_header("Geographic Distribution", "Job postings by location across the market", "location_pin")

    with loading_spinner("Loading location data..."):
        try:
            chart_data = service.get_locations_chart(limit=15)
            if not chart_data.x_values:
                empty_state_analytics(
                    title="No Location Data",
                    description="No location data available.",
                )
                return

            chart_data.color = "#0f3460"
            fig = create_horizontal_bar_chart(chart_data)
            fig.update_layout(
                height=500,
                margin=dict(l=20, r=20, t=40, b=20),
                font=dict(family="Inter, sans-serif", size=12),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                hoverlabel=dict(
                    bgcolor="white",
                    bordercolor="#dfe6e9",
                    font_size=14,
                    font_family="Inter, -apple-system, sans-serif",
                    font_color="#1a1a2e",
                    align="left",
                ),
            )
            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            show_error(f"Failed to load location data: {str(e)}")


def render_skills_analytics(service):
    """Render enriched skills analytics with professional styling."""
    section_header("Skills in Demand", "Most sought-after skills and their distribution", "skills_metric")

    col1, col2 = st.columns([3, 2])

    with col1:
        with loading_spinner("Loading skills data..."):
            try:
                # Use enriched skills data
                enriched_skills = service.get_enriched_top_skills(limit=15)
                if enriched_skills:
                    # Create properly typed chart data with title
                    chart_data = HorizontalBarChartData(
                        x_values=[s.get("skill", "Unknown") for s in enriched_skills],
                        y_values=[s.get("count", 0) for s in enriched_skills],
                        title="Top Skills",
                        color="#00b894"
                    )
                    
                    fig = create_horizontal_bar_chart(chart_data)
                    fig.update_layout(
                        height=450,
                        margin=dict(l=20, r=20, t=40, b=20),
                        font=dict(family="Inter, sans-serif", size=12),
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        hoverlabel=dict(
                            bgcolor="white",
                            bordercolor="#dfe6e9",
                            font_size=14,
                            font_family="Inter, -apple-system, sans-serif",
                            font_color="#1a1a2e",
                            align="left",
                        ),
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    empty_state_analytics(
                        title="No Skills Data",
                        description="No skills data available.",
                    )

            except Exception as e:
                show_error(f"Failed to load skills data: {str(e)}")

    with col2:
        with loading_spinner("Loading distribution..."):
            try:
                # Use technology distribution for pie chart
                tech_dist = service.get_technology_distribution()
                if tech_dist:
                    tech_filtered = [t for t in tech_dist if t.get("category") != "other"]
                    if tech_filtered:
                        df = pd.DataFrame(tech_filtered[:8])
                        fig = px.pie(
                            df,
                            values="count",
                            names="category",
                            color_discrete_sequence=px.colors.qualitative.Set2,
                            hole=0.4,
                        )
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
                        )
                        fig.update_layout(
                            height=400,
                            margin=dict(l=20, r=20, t=40, b=20),
                            font=dict(family="Inter, sans-serif", size=12),
                            plot_bgcolor="rgba(0,0,0,0)",
                            paper_bgcolor="rgba(0,0,0,0)",
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No technology categories found")
                else:
                    st.info("No technology distribution data available")

            except Exception as e:
                show_error(f"Failed to load distribution: {str(e)}")


def render_company_analytics(service):
    """Render company analytics with professional styling."""
    section_header("Top Hiring Companies", "Companies with the most job postings", "companies_metric")

    col1, col2 = st.columns([3, 2])

    with col1:
        with loading_spinner("Loading company data..."):
            try:
                chart_data = service.get_companies_chart(limit=15)
                if not chart_data.x_values:
                    empty_state_analytics(
                        title="No Company Data",
                        description="No company data available.",
                    )
                    return

                chart_data.color = "#0984e3"
                fig = create_horizontal_bar_chart(chart_data)
                fig.update_layout(
                    height=450,
                    margin=dict(l=20, r=20, t=40, b=20),
                    font=dict(family="Inter, sans-serif", size=12),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    hoverlabel=dict(
                        bgcolor="white",
                        bordercolor="#dfe6e9",
                        font_size=14,
                        font_family="Inter, -apple-system, sans-serif",
                        font_color="#1a1a2e",
                        align="left",
                    ),
                )
                st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                show_error(f"Failed to load company data: {str(e)}")

    with col2:
        with loading_spinner("Loading distribution..."):
            try:
                donut_data = service.get_companies_distribution_chart(limit=8)
                if donut_data.labels:
                    fig = create_donut_chart(donut_data)
                    fig.update_layout(
                        height=400,
                        margin=dict(l=20, r=20, t=40, b=20),
                        font=dict(family="Inter, sans-serif", size=12),
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        hoverlabel=dict(
                            bgcolor="white",
                            bordercolor="#dfe6e9",
                            font_size=14,
                            font_family="Inter, -apple-system, sans-serif",
                            font_color="#1a1a2e",
                            align="left",
                        ),
                    )
                    st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                show_error(f"Failed to load distribution: {str(e)}")


def render_salary_analytics(service):
    """Render enriched salary analytics with professional styling."""
    section_header(
        "Compensation Analysis", "Salary trends and distribution across the market", "salary_metric"
    )

    # Salary Statistics Cards
    with loading_spinner("Loading salary statistics..."):
        try:
            stats = service.get_salary_statistics()
            if stats:
                cols = st.columns(4)
                metric_configs = [
                    ("Average", f"${stats.average:,.0f}", stats.currency),
                    ("Median", f"${stats.median:,.0f}", stats.currency),
                    ("Minimum", f"${stats.minimum:,.0f}", stats.currency),
                    ("Maximum", f"${stats.maximum:,.0f}", stats.currency),
                ]

                for col, (label, value, currency) in zip(cols, metric_configs):
                    with col:
                        st.metric(label=label, value=value, help=f"Currency: {currency}")

                st.caption(f"Based on {stats.sample_size:,} job postings")
                st.markdown("---")

        except Exception as e:
            show_error(f"Failed to load salary statistics: {str(e)}")

    col1, col2 = st.columns(2)

    with col1:
        with loading_spinner("Loading salary distribution..."):
            try:
                hist_data = service.get_salary_distribution_chart()
                if hist_data.bins:
                    hist_data.color = "#e94560"
                    fig = create_histogram(hist_data)
                    fig.update_layout(
                        height=400,
                        margin=dict(l=20, r=20, t=40, b=20),
                        font=dict(family="Inter, sans-serif", size=12),
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        hoverlabel=dict(
                            bgcolor="white",
                            bordercolor="#dfe6e9",
                            font_size=14,
                            font_family="Inter, -apple-system, sans-serif",
                            font_color="#1a1a2e",
                            align="left",
                        ),
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    empty_state_analytics(
                        title="No Distribution Data",
                        description="No salary distribution data available.",
                    )

            except Exception as e:
                show_error(f"Failed to load salary distribution: {str(e)}")

    with col2:
        with loading_spinner("Loading salary by location..."):
            try:
                chart_data = service.get_salary_by_location_chart(limit=10)
                if chart_data.x_values:
                    chart_data.color = "#fdcb6e"
                    fig = create_bar_chart(chart_data)
                    fig.update_layout(
                        height=400,
                        margin=dict(l=20, r=20, t=40, b=20),
                        font=dict(family="Inter, sans-serif", size=12),
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        hoverlabel=dict(
                            bgcolor="white",
                            bordercolor="#dfe6e9",
                            font_size=14,
                            font_family="Inter, -apple-system, sans-serif",
                            font_color="#1a1a2e",
                            align="left",
                        ),
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    empty_state_analytics(
                        title="No Location Salary Data",
                        description="No location salary data available.",
                    )

            except Exception as e:
                show_error(f"Failed to load salary by location: {str(e)}")


def render_employment_analytics(service):
    """Render employment analytics with professional styling."""
    section_header("Employment Types", "Distribution of employment types across job postings", "employment")

    col1, col2 = st.columns(2)

    with col1:
        with loading_spinner("Loading employment types..."):
            try:
                donut_data = service.get_employment_types_chart()
                if donut_data.labels:
                    fig = create_donut_chart(donut_data)
                    fig.update_layout(
                        height=400,
                        margin=dict(l=20, r=20, t=40, b=20),
                        font=dict(family="Inter, sans-serif", size=12),
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        hoverlabel=dict(
                            bgcolor="white",
                            bordercolor="#dfe6e9",
                            font_size=14,
                            font_family="Inter, -apple-system, sans-serif",
                            font_color="#1a1a2e",
                            align="left",
                        ),
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    empty_state_analytics(
                        title="No Employment Data",
                        description="No employment type data available.",
                    )

            except Exception as e:
                show_error(f"Failed to load employment types: {str(e)}")

    with col2:
        with loading_spinner("Loading employment data..."):
            try:
                chart_data = service.get_employment_types_bar_chart()
                if chart_data.x_values:
                    chart_data.color = "#6c5ce7"
                    fig = create_bar_chart(chart_data)
                    fig.update_layout(
                        height=400,
                        margin=dict(l=20, r=20, t=40, b=20),
                        font=dict(family="Inter, sans-serif", size=12),
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        hoverlabel=dict(
                            bgcolor="white",
                            bordercolor="#dfe6e9",
                            font_size=14,
                            font_family="Inter, -apple-system, sans-serif",
                            font_color="#1a1a2e",
                            align="left",
                        ),
                    )
                    st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                show_error(f"Failed to load employment data: {str(e)}")


def render_posting_trends(service):
    """Render posting trends with professional styling."""
    section_header("Posting Trends", "Job posting volume over time", "trends")

    col1, col2 = st.columns([3, 1])

    with col2:
        days = st.selectbox(
            "Time Period",
            options=[7, 14, 30, 60, 90],
            index=2,
            format_func=lambda x: f"{x} Days",
        )

    with col1:
        with loading_spinner(f"Loading trends for last {days} days..."):
            try:
                # Cumulative trend
                cumulative_data = service.get_posting_trend_chart(days=days)
                if cumulative_data.x_values:
                    cumulative_data.color = "#0f3460"
                    cumulative_data.fill_area = True
                    fig = create_line_chart(cumulative_data)
                    fig.update_layout(
                        height=350,
                        margin=dict(l=20, r=20, t=40, b=20),
                        font=dict(family="Inter, sans-serif", size=12),
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        hoverlabel=dict(
                            bgcolor="white",
                            bordercolor="#dfe6e9",
                            font_size=14,
                            font_family="Inter, -apple-system, sans-serif",
                            font_color="#1a1a2e",
                            align="left",
                        ),
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # Daily trend
                    daily_data = service.get_daily_posting_trend_chart(days=days)
                    if daily_data.x_values:
                        daily_data.color = "#e94560"
                        fig_daily = create_line_chart(daily_data)
                        fig_daily.update_layout(
                            height=300,
                            margin=dict(l=20, r=20, t=40, b=20),
                            font=dict(family="Inter, sans-serif", size=12),
                            plot_bgcolor="rgba(0,0,0,0)",
                            paper_bgcolor="rgba(0,0,0,0)",
                            hoverlabel=dict(
                                bgcolor="white",
                                bordercolor="#dfe6e9",
                                font_size=14,
                                font_family="Inter, -apple-system, sans-serif",
                                font_color="#1a1a2e",
                                align="left",
                            ),
                        )
                        st.plotly_chart(fig_daily, use_container_width=True)
                else:
                    empty_state_analytics(
                        title="No Trend Data",
                        description="No posting trend data available.",
                    )

            except Exception as e:
                show_error(f"Failed to load posting trends: {str(e)}")


# ============================================================
# Sprint 6.6: Language Analytics
# ============================================================

def render_language_analytics(service):
    """Render Sprint 6.6 language analytics."""
    section_header("Language Insights", "Job posting languages and multilingual analytics", "translate")

    with loading_spinner("Loading language data..."):
        try:
            # Language distribution
            lang_dist = service.get_language_distribution()
            
            if not lang_dist:
                empty_state_analytics(
                    title="No Language Data",
                    description="No language data available.",
                )
                return
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Language Distribution")
                df = pd.DataFrame(lang_dist)
                if not df.empty:
                    fig = px.pie(
                        df,
                        values="count",
                        names="language",
                        color_discrete_sequence=px.colors.qualitative.Set3,
                        hole=0.4,
                    )
                    fig.update_traces(
                        textinfo="percent",
                        textposition="inside",
                        textfont=dict(size=12, color="white"),
                        hoverlabel=dict(
                            bgcolor="white",
                            bordercolor="#dfe6e9",
                            font_size=14,
                            font_family="Inter, -apple-system, sans-serif",
                            font_color="#1a1a2e",
                            align="left",
                        ),
                    )
                    fig.update_layout(
                        height=400,
                        margin=dict(l=20, r=20, t=40, b=20),
                        font=dict(family="Inter, sans-serif", size=12),
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # English vs non-English
                english_stats = service.get_english_vs_non_english()
                if english_stats:
                    st.subheader("English vs Non-English")
                    
                    total = english_stats.get("total_count", 0)
                    english = english_stats.get("english_count", 0)
                    non_english = english_stats.get("non_english_count", 0)
                    pct = english_stats.get("english_percentage", 0)
                    
                    # Use SVG icons for metrics
                    en_icon = get_icon("translate", size=16, color=IconColor.SUCCESS)
                    non_en_icon = get_icon("translate", size=16, color=IconColor.WARNING)
                    
                    st.markdown(f"""
                        <div style="display:flex;align-items:center;gap:8px;font-size:1.2rem;font-weight:600;color:{COLORS['text']};">
                            {en_icon} English Jobs: <span style="color:{IconColor.SUCCESS};">{english:,}</span>
                            <span style="font-size:0.9rem;font-weight:400;color:{COLORS['text_light']};">({pct:.1f}% of total)</span>
                        </div>
                        <div style="display:flex;align-items:center;gap:8px;font-size:1.1rem;font-weight:500;color:{COLORS['text']};margin-top:8px;">
                            {non_en_icon} Non-English Jobs: <span style="color:{IconColor.WARNING};">{non_english:,}</span>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Language by country
                    lang_by_country = service.get_language_by_country()
                    if lang_by_country:
                        st.subheader("Language by Country")
                        df_country = pd.DataFrame(lang_by_country[:10])
                        if not df_country.empty:
                            fig = px.bar(
                                df_country,
                                x="country",
                                y="count",
                                color="language",
                                title="Top Countries by Language",
                                barmode="group",
                            )
                            fig.update_layout(
                                height=300,
                                margin=dict(l=20, r=20, t=40, b=20),
                                font=dict(family="Inter, sans-serif", size=12),
                                plot_bgcolor="rgba(0,0,0,0)",
                                paper_bgcolor="rgba(0,0,0,0)",
                            )
                            st.plotly_chart(fig, use_container_width=True)
            
            divider()
            
            # Language salary stats
            salary_by_lang = service.get_language_salary_stats()
            if salary_by_lang:
                st.subheader("Salary by Language")
                icon = get_icon("salary_metric", size=18, color=IconColor.SUCCESS)
                st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
                        {icon}
                        <span style="font-weight:500;color:{COLORS['text']};">Average Salary by Language</span>
                    </div>
                """, unsafe_allow_html=True)
                
                df_salary = pd.DataFrame(salary_by_lang[:10])
                if not df_salary.empty:
                    fig = px.bar(
                        df_salary,
                        x="language",
                        y="average_salary",
                        title="Average Salary by Language",
                        color="average_salary",
                        color_continuous_scale="Greens",
                    )
                    fig.update_layout(
                        height=350,
                        margin=dict(l=20, r=20, t=40, b=20),
                        font=dict(family="Inter, sans-serif", size=12),
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
        except Exception as e:
            show_error(f"Failed to load language analytics: {str(e)}")


# ============================================================
# Sprint 6.6: Technology Analytics
# ============================================================

def render_tech_analytics(service):
    """Render Sprint 6.6 technology analytics."""
    section_header("Technology Roles", "Tech job market insights and trends", "tech")

    with loading_spinner("Loading technology data..."):
        try:
            # Tech vs non-tech
            tech_stats = service.get_tech_vs_non_tech()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total = tech_stats.get("total_count", 0)
                icon = get_icon("briefcase", size=18, color=IconColor.PRIMARY)
                st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:8px;">
                        {icon}
                        <span style="font-weight:500;color:{COLORS['text']};">Total Jobs</span>
                    </div>
                    <div style="font-size:1.8rem;font-weight:700;color:{COLORS['text']};margin-top:4px;">{total:,}</div>
                """, unsafe_allow_html=True)
            
            with col2:
                tech = tech_stats.get("tech_count", 0)
                icon = get_icon("tech", size=18, color=IconColor.SUCCESS)
                st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:8px;">
                        {icon}
                        <span style="font-weight:500;color:{COLORS['text']};">Tech Roles</span>
                    </div>
                    <div style="font-size:1.8rem;font-weight:700;color:{COLORS['text']};margin-top:4px;">{tech:,}</div>
                """, unsafe_allow_html=True)
            
            with col3:
                non_tech = tech_stats.get("non_tech_count", 0)
                icon = get_icon("company", size=18, color=IconColor.GRAY)
                st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:8px;">
                        {icon}
                        <span style="font-weight:500;color:{COLORS['text']};">Non-Tech</span>
                    </div>
                    <div style="font-size:1.8rem;font-weight:700;color:{COLORS['text']};margin-top:4px;">{non_tech:,}</div>
                """, unsafe_allow_html=True)
            
            with col4:
                pct = tech_stats.get("tech_percentage", 0)
                icon = get_icon("analytics", size=18, color=IconColor.WARNING)
                st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:8px;">
                        {icon}
                        <span style="font-weight:500;color:{COLORS['text']};">Tech %</span>
                    </div>
                    <div style="font-size:1.8rem;font-weight:700;color:{COLORS['text']};margin-top:4px;">{pct:.1f}%</div>
                """, unsafe_allow_html=True)
            
            divider()
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Technology category distribution
                tech_categories = service.get_tech_category_distribution()
                if tech_categories:
                    st.subheader("Technology Categories")
                    df = pd.DataFrame(tech_categories)
                    if not df.empty:
                        fig = px.pie(
                            df,
                            values="count",
                            names="category",
                            color_discrete_sequence=px.colors.qualitative.Set2,
                            hole=0.4,
                        )
                        fig.update_traces(
                            textinfo="percent",
                            textposition="inside",
                            textfont=dict(size=11, color="white"),
                            hoverlabel=dict(
                                bgcolor="white",
                                bordercolor="#dfe6e9",
                                font_size=14,
                                font_family="Inter, -apple-system, sans-serif",
                                font_color="#1a1a2e",
                                align="left",
                            ),
                        )
                        fig.update_layout(
                            height=400,
                            margin=dict(l=20, r=20, t=40, b=20),
                            font=dict(family="Inter, sans-serif", size=12),
                            plot_bgcolor="rgba(0,0,0,0)",
                            paper_bgcolor="rgba(0,0,0,0)",
                        )
                        st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Tech by country
                tech_by_country = service.get_tech_by_country()
                if tech_by_country:
                    st.subheader("Tech Roles by Country")
                    df_country = pd.DataFrame(tech_by_country[:10])
                    if not df_country.empty:
                        fig = px.bar(
                            df_country,
                            x="country",
                            y="tech_percentage",
                            title="Tech Job Percentage by Country",
                            color="tech_percentage",
                            color_continuous_scale="Blues",
                        )
                        fig.update_layout(
                            height=350,
                            margin=dict(l=20, r=20, t=40, b=20),
                            font=dict(family="Inter, sans-serif", size=12),
                            plot_bgcolor="rgba(0,0,0,0)",
                            paper_bgcolor="rgba(0,0,0,0)",
                        )
                        st.plotly_chart(fig, use_container_width=True)
            
            divider()
            
            # Tech skills
            tech_skills = service.get_tech_skills(limit=20)
            if tech_skills:
                icon = get_icon("skills_metric", size=18, color=IconColor.WARNING)
                st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
                        {icon}
                        <span style="font-weight:600;font-size:1.1rem;color:{COLORS['text']};">Top Skills in Tech Roles</span>
                    </div>
                """, unsafe_allow_html=True)
                
                df_skills = pd.DataFrame(tech_skills[:15])
                if not df_skills.empty:
                    fig = px.bar(
                        df_skills,
                        x="skill",
                        y="count",
                        title="Most Common Skills in Tech Roles",
                        color="count",
                        color_continuous_scale="Oranges",
                    )
                    fig.update_layout(
                        height=400,
                        margin=dict(l=20, r=20, t=40, b=20),
                        font=dict(family="Inter, sans-serif", size=12),
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        xaxis_tickangle=-45,
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            # Tech salary stats
            tech_salary = service.get_tech_salary_stats()
            if tech_salary:
                icon = get_icon("salary_metric", size=18, color=IconColor.SUCCESS)
                st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:8px;margin-top:16px;margin-bottom:12px;">
                        {icon}
                        <span style="font-weight:600;font-size:1.1rem;color:{COLORS['text']};">Tech Role Salary Statistics</span>
                    </div>
                """, unsafe_allow_html=True)
                
                cols = st.columns(4)
                with cols[0]:
                    avg = tech_salary.get("average")
                    st.metric("Average", f"${avg:,.0f}" if avg else "N/A")
                with cols[1]:
                    median = tech_salary.get("median")
                    st.metric("Median", f"${median:,.0f}" if median else "N/A")
                with cols[2]:
                    min_sal = tech_salary.get("minimum")
                    st.metric("Minimum", f"${min_sal:,.0f}" if min_sal else "N/A")
                with cols[3]:
                    max_sal = tech_salary.get("maximum")
                    st.metric("Maximum", f"${max_sal:,.0f}" if max_sal else "N/A")
                
                sample_size = tech_salary.get("sample_size", 0)
                st.caption(f"Based on {sample_size:,} tech job postings")
                    
        except Exception as e:
            show_error(f"Failed to load technology analytics: {str(e)}")