# dashboard/pages/analytics.py
"""Professional analytics dashboard page with modern UI."""

import logging
import time

import streamlit as st

from dashboard.components.alerts import show_error

# Import charts from charts.py
from dashboard.components.charts import (
    create_bar_chart,
    create_donut_chart,
    create_histogram,
    create_horizontal_bar_chart,
    create_line_chart,
    create_pie_chart,
)
from dashboard.components.empty_state import empty_state_analytics
from dashboard.components.layout import divider, page_header, section_header, timestamp
from dashboard.components.loading import loading_spinner

# Import metrics from the new location
from dashboard.components.metrics import render_metric_card
from dashboard.utils.state import StateManager

logger = logging.getLogger(__name__)


def render():
    """Main render function for analytics page."""
    render_analytics_dashboard()


def render_analytics_dashboard():
    """Render the professional analytics dashboard."""
    # Header
    page_header(
        title="Market Analytics",
        subtitle="Real-time insights into the technology job market",
        icon="📊",
    )

    # Get service from StateManager
    service = StateManager.get_analytics_service()

    # Top bar with refresh - using simple button
    col_left, col_right = st.columns([3, 1])
    with col_right:
        # Simple refresh button - works everywhere
        if st.button("↻ Refresh", use_container_width=True, key="refresh_analytics"):
            with st.spinner("Refreshing data..."):
                StateManager.clear_cache()
                time.sleep(0.5)
                st.rerun()
    with col_left:
        timestamp()

    divider()

    # KPI Cards
    render_kpi_cards(service)

    # Tabs for detailed analytics
    tab_labels = ["Locations", "Skills", "Companies", "Salaries", "Employment", "Trends"]
    tabs = st.tabs(tab_labels)

    with tabs[0]:
        render_location_analytics(service)
    with tabs[1]:
        render_skills_analytics(service)
    with tabs[2]:
        render_company_analytics(service)
    with tabs[3]:
        render_salary_analytics(service)
    with tabs[4]:
        render_employment_analytics(service)
    with tabs[5]:
        render_posting_trends(service)


def render_kpi_cards(service):
    """Render professional KPI metric cards."""
    with loading_spinner("Loading metrics..."):
        try:
            metrics = service.get_dashboard_metrics()
            if not metrics:
                empty_state_analytics(
                    title="No Data Available",
                    description="No analytics data found. Please run the ETL pipeline.",
                )
                return

            cols = st.columns(len(metrics))
            for col, metric in zip(cols, metrics):
                with col:
                    render_metric_card(metric)
        except Exception as e:
            show_error(f"Failed to load metrics: {str(e)}")


def render_location_analytics(service):
    """Render location analytics with professional styling."""
    section_header("Geographic Distribution", "Job postings by location across the market", "📍")

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
            )
            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            show_error(f"Failed to load location data: {str(e)}")


def render_skills_analytics(service):
    """Render skills analytics with professional styling."""
    section_header("Skills in Demand", "Most sought-after skills and their distribution", "🎯")

    col1, col2 = st.columns([3, 2])

    with col1:
        with loading_spinner("Loading skills data..."):
            try:
                chart_data = service.get_skills_chart(limit=15)
                if not chart_data.x_values:
                    empty_state_analytics(
                        title="No Skills Data",
                        description="No skills data available.",
                    )
                    return

                chart_data.color = "#00b894"
                fig = create_horizontal_bar_chart(chart_data)
                fig.update_layout(
                    height=450,
                    margin=dict(l=20, r=20, t=40, b=20),
                    font=dict(family="Inter, sans-serif", size=12),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                show_error(f"Failed to load skills data: {str(e)}")

    with col2:
        with loading_spinner("Loading distribution..."):
            try:
                pie_data = service.get_skills_distribution_chart(limit=8)
                if pie_data.labels:
                    fig = create_pie_chart(pie_data)
                    fig.update_layout(
                        height=400,
                        margin=dict(l=20, r=20, t=40, b=20),
                        font=dict(family="Inter, sans-serif", size=12),
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                    )
                    st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                show_error(f"Failed to load distribution: {str(e)}")


def render_company_analytics(service):
    """Render company analytics with professional styling."""
    section_header("Top Hiring Companies", "Companies with the most job postings", "🏢")

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
                    )
                    st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                show_error(f"Failed to load distribution: {str(e)}")


def render_salary_analytics(service):
    """Render salary analytics with professional styling."""
    section_header(
        "Compensation Analysis", "Salary trends and distribution across the market", "💰"
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
    section_header("Employment Types", "Distribution of employment types across job postings", "💼")

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
                    )
                    st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                show_error(f"Failed to load employment data: {str(e)}")


def render_posting_trends(service):
    """Render posting trends with professional styling."""
    section_header("Posting Trends", "Job posting volume over time", "📈")

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
                        )
                        st.plotly_chart(fig_daily, use_container_width=True)
                else:
                    empty_state_analytics(
                        title="No Trend Data",
                        description="No posting trend data available.",
                    )

            except Exception as e:
                show_error(f"Failed to load posting trends: {str(e)}")
