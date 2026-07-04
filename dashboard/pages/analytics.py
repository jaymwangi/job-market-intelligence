# dashboard/pages/analytics.py
"""Professional analytics dashboard page with modern UI."""
import streamlit as st
from datetime import datetime
import logging
import time

# Import metrics from the new location
from dashboard.components.metrics import create_metric_card

# Import charts from charts.py
from dashboard.components.charts import (
    create_horizontal_bar_chart, create_bar_chart,
    create_pie_chart, create_donut_chart, create_line_chart, create_histogram
)

from dashboard.components.loading import loading_spinner
from dashboard.components.alerts import show_error
from dashboard.components.empty_state import empty_state_analytics
from dashboard.components.layout import page_header, section_header, timestamp, refresh_button
from dashboard.utils.state import StateManager

logger = logging.getLogger(__name__)

# Professional color palette
COLORS = {
    "primary": "#1a1a2e",
    "secondary": "#16213e",
    "accent": "#0f3460",
    "highlight": "#e94560",
    "success": "#00b894",
    "warning": "#fdcb6e",
    "info": "#0984e3",
    "background": "#f8f9fa",
    "card_bg": "#ffffff",
    "text": "#2d3436",
    "text_light": "#636e72",
}


def render():
    """Main render function for analytics page."""
    render_analytics_dashboard()


def render_analytics_dashboard():
    """Render the professional analytics dashboard."""
    # Custom CSS for professional look
    st.markdown(f"""
    <style>
        /* Professional typography */
        .main-title {{
            font-size: 2.5rem;
            font-weight: 700;
            color: {COLORS['primary']};
            letter-spacing: -0.02em;
            margin-bottom: 0.25rem;
        }}
        .main-subtitle {{
            font-size: 1rem;
            color: {COLORS['text_light']};
            font-weight: 400;
            margin-bottom: 2rem;
        }}
        .metric-card {{
            background: {COLORS['card_bg']};
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
            border: 1px solid rgba(0,0,0,0.04);
            transition: all 0.2s ease;
        }}
        .metric-card:hover {{
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            transform: translateY(-2px);
        }}
        .metric-value {{
            font-size: 2rem;
            font-weight: 700;
            color: {COLORS['primary']};
            line-height: 1.2;
        }}
        .metric-label {{
            font-size: 0.85rem;
            color: {COLORS['text_light']};
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }}
        .metric-icon {{
            font-size: 1.5rem;
            opacity: 0.7;
        }}
        .section-header {{
            font-size: 1.25rem;
            font-weight: 600;
            color: {COLORS['primary']};
            margin: 1.5rem 0 1rem 0;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid {COLORS['background']};
        }}
        .refresh-container {{
            display: flex;
            justify-content: flex-end;
            align-items: center;
            gap: 1rem;
            padding: 0.5rem 0;
        }}
        .timestamp {{
            color: {COLORS['text_light']};
            font-size: 0.8rem;
            font-weight: 400;
        }}
        .stTabs [data-baseweb="tab-list"] {{
            gap: 0.5rem;
            background-color: {COLORS['background']};
            border-radius: 10px;
            padding: 0.25rem;
        }}
        .stTabs [data-baseweb="tab"] {{
            border-radius: 8px;
            padding: 0.5rem 1.25rem;
            font-weight: 500;
            color: {COLORS['text_light']};
            transition: all 0.2s ease;
        }}
        .stTabs [data-baseweb="tab"]:hover {{
            background-color: rgba(0,0,0,0.04);
        }}
        .stTabs [data-baseweb="tab"][aria-selected="true"] {{
            background-color: {COLORS['card_bg']};
            color: {COLORS['primary']};
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        }}
        .stButton button {{
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.2s ease;
            border: 1px solid rgba(0,0,0,0.08);
        }}
        .stButton button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
    </style>
    """, unsafe_allow_html=True)

    # Header using layout component
    page_header(
        title="Market Analytics",
        subtitle="Real-time insights into the technology job market",
        icon="📊"
    )

    # Get service from StateManager
    service = StateManager.get_analytics_service()

    # Top bar with refresh
    col_left, col_right = st.columns([3, 1])
    with col_right:
        if refresh_button():
            with st.spinner("Refreshing data..."):
                StateManager.clear_cache()
                time.sleep(0.5)
                st.rerun()
    with col_left:
        timestamp()

    st.markdown("---")

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
                    icon="📭"
                )
                return

            cols = st.columns(len(metrics))
            for col, metric in zip(cols, metrics):
                with col:
                    card_html = create_metric_card(metric)
                    st.markdown(card_html['html'], unsafe_allow_html=True)

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
                    icon="📍"
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
                        icon="🎯"
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
                        icon="🏢"
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
    section_header("Compensation Analysis", "Salary trends and distribution across the market", "💰")

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
                    ("Maximum", f"${stats.maximum:,.0f}", stats.currency)
                ]

                for col, (label, value, currency) in zip(cols, metric_configs):
                    with col:
                        st.metric(
                            label=label,
                            value=value,
                            help=f"Currency: {currency}"
                        )

                st.caption(f"📊 Based on {stats.sample_size:,} job postings")
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
                        icon="📊"
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
                        icon="📍"
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
                        icon="💼"
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
            format_func=lambda x: f"{x} Days"
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
                        icon="📈"
                    )

            except Exception as e:
                show_error(f"Failed to load posting trends: {str(e)}")