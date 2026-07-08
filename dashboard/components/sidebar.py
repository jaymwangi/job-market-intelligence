# dashboard/components/sidebar.py
"""Professional sidebar navigation."""

from datetime import datetime

import streamlit as st
from utils.state import StateManager


def render_sidebar():
    """Render the professional sidebar navigation."""

    st.markdown(
        """
    <style>
        /* Hide default Streamlit navigation */
        [data-testid="stSidebarNav"] {
            display: none !important;
        }

        /* Main sidebar container */
        .css-1d391kg, .css-12oz5g7 {
            background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 40%, #16213e 100%) !important;
            border-right: 1px solid rgba(255,255,255,0.03) !important;
        }

        /* Brand section with icon left of title */
        .sidebar-brand {
            padding: 1.5rem 0 0.75rem 0;
            position: relative;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        .sidebar-brand-icon {
            font-size: 2rem;
            flex-shrink: 0;
            background: linear-gradient(135deg, #6c5ce7, #a29bfe);
            padding: 0.5rem 0.6rem;
            border-radius: 12px;
            line-height: 1;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 15px rgba(108,92,231,0.3);
            width: 44px;
            height: 44px;
        }
        .sidebar-brand-icon svg {
            width: 24px;
            height: 24px;
            fill: white;
        }
        .sidebar-brand-text {
            display: flex;
            flex-direction: column;
            gap: 0.05rem;
        }
        .sidebar-title {
            font-size: 1.3rem;
            font-weight: 700;
            color: #ffffff;
            letter-spacing: -0.02em;
            background: linear-gradient(135deg, #ffffff 60%, rgba(255,255,255,0.6));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            line-height: 1.2;
        }
        .sidebar-subtitle {
            font-size: 0.65rem;
            color: rgba(255,255,255,0.25);
            font-weight: 400;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            -webkit-text-fill-color: rgba(255,255,255,0.25);
        }

        /* Divider with glow */
        .sidebar-divider {
            border: none;
            height: 1px;
            background: linear-gradient(90deg, rgba(108,92,231,0.3), rgba(255,255,255,0.05), rgba(108,92,231,0.3));
            margin: 0.75rem 0;
            position: relative;
        }
        .sidebar-divider::after {
            content: '';
            position: absolute;
            left: 50%;
            top: -2px;
            transform: translateX(-50%);
            width: 4px;
            height: 4px;
            background: #6c5ce7;
            border-radius: 50%;
            box-shadow: 0 0 10px rgba(108,92,231,0.5);
        }

        /* Navigation buttons */
        .stButton button {
            background: transparent !important;
            color: rgba(255,255,255,0.5) !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 0.7rem 1rem !important;
            font-weight: 500 !important;
            font-size: 0.9rem !important;
            text-align: left !important;
            justify-content: flex-start !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            width: 100% !important;
            cursor: pointer !important;
            box-shadow: none !important;
            height: auto !important;
            line-height: 1.4 !important;
            position: relative !important;
            overflow: hidden !important;
        }

        /* Hover: Smooth fill animation */
        .stButton button::before {
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            width: 0;
            height: 100%;
            background: linear-gradient(90deg, rgba(108,92,231,0.15), rgba(162,155,254,0.05));
            border-radius: 12px;
            transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
            z-index: 0;
        }
        .stButton button:hover::before {
            width: 100%;
        }

        .stButton button:hover {
            color: #ffffff !important;
            transform: translateX(4px) !important;
            background: transparent !important;
            box-shadow: none !important;
        }

        .stButton button:active {
            transform: scale(0.97) translateX(2px) !important;
        }

        .stButton button:focus {
            box-shadow: none !important;
            outline: none !important;
        }
        .stButton button:focus-visible {
            outline: 2px solid rgba(108,92,231,0.5) !important;
            outline-offset: 2px !important;
        }

        /* ACTIVE STATE - Distinct color to show current page */
        .active-nav .stButton button {
            background: linear-gradient(135deg, rgba(108,92,231,0.3), rgba(108,92,231,0.15)) !important;
            color: #ffffff !important;
            border: 1px solid rgba(108,92,231,0.4) !important;
            box-shadow: 0 4px 25px rgba(108,92,231,0.25) !important;
            transform: translateX(4px) !important;
            font-weight: 600 !important;
        }
        .active-nav .stButton button::before {
            width: 100%;
            background: linear-gradient(135deg, rgba(108,92,231,0.4), rgba(162,155,254,0.15));
        }
        /* Left accent bar for active state */
        .active-nav .stButton button::after {
            content: '';
            position: absolute;
            left: 0;
            top: 50%;
            transform: translateY(-50%);
            width: 4px;
            height: 60%;
            background: linear-gradient(180deg, #6c5ce7, #a29bfe);
            border-radius: 0 4px 4px 0;
            box-shadow: 0 0 30px rgba(108,92,231,0.6);
            z-index: 1;
        }
        .active-nav .stButton button:hover {
            background: linear-gradient(135deg, rgba(108,92,231,0.4), rgba(108,92,231,0.2)) !important;
            transform: translateX(4px) !important;
        }

        /* Ensure button content is above gradient */
        .stButton button .nav-content {
            position: relative;
            z-index: 1;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            width: 100%;
        }

        /* Footer with stats */
        .sidebar-footer {
            padding: 0.75rem 0 0.5rem 0;
            border-top: 1px solid rgba(255,255,255,0.04);
            margin-top: 0.5rem;
        }
        .sidebar-footer-content {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }
        .footer-stats {
            display: flex;
            gap: 1rem;
            justify-content: space-between;
        }
        .footer-stat-item {
            display: flex;
            flex-direction: column;
            gap: 0.1rem;
        }
        .footer-stat-value {
            color: rgba(255,255,255,0.6);
            font-size: 0.85rem;
            font-weight: 600;
        }
        .footer-stat-label {
            color: rgba(255,255,255,0.15);
            font-size: 0.55rem;
            font-weight: 400;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }
        .footer-divider {
            border: none;
            height: 1px;
            background: linear-gradient(90deg, rgba(255,255,255,0.05), rgba(255,255,255,0.01));
            margin: 0.25rem 0;
        }
        .footer-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .sidebar-version {
            color: rgba(255,255,255,0.12);
            font-size: 0.55rem;
            font-weight: 400;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }
        .sidebar-time {
            color: rgba(255,255,255,0.08);
            font-size: 0.5rem;
            font-weight: 300;
            letter-spacing: 0.04em;
        }
        .sidebar-status {
            display: inline-block;
            width: 5px;
            height: 5px;
            background: #00d2d3;
            border-radius: 50%;
            margin-right: 0.4rem;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.3; transform: scale(0.8); }
        }

        /* Scrollbar styling */
        ::-webkit-scrollbar {
            width: 3px;
        }
        ::-webkit-scrollbar-track {
            background: transparent;
        }
        ::-webkit-scrollbar-thumb {
            background: rgba(108,92,231,0.3);
            border-radius: 10px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(108,92,231,0.5);
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        # Brand Section - SVG Icon beside title
        st.markdown(
            """
        <div class="sidebar-brand">
            <div class="sidebar-brand-icon">
                <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z"/>
                </svg>
            </div>
            <div class="sidebar-brand-text">
                <div class="sidebar-title">Job Market Dashboard</div>
                <div class="sidebar-subtitle">Real-time Analytics Platform</div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

        # Navigation - Professional text only
        pages = [
            ("Overview", "overview"),
            ("Jobs", "jobs"),
            ("Analytics", "analytics"),
            ("About", "about"),
        ]

        current_page = StateManager.get_current_page()

        for label, page_id in pages:
            is_active = current_page == page_id

            with st.container():
                if is_active:
                    st.markdown('<div class="active-nav">', unsafe_allow_html=True)

                # Professional text with arrow for active
                display_text = label
                if is_active:
                    display_text = f"{label} →"

                clicked = st.button(
                    display_text,
                    use_container_width=True,
                    key=f"nav_{page_id}",
                    help=f"Navigate to {label}",
                )

                if is_active:
                    st.markdown("</div>", unsafe_allow_html=True)

                if clicked and current_page != page_id:
                    StateManager.set_current_page(page_id)
                    st.rerun()

        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

        # Footer with meaningful stats
        current_time = datetime.now().strftime("%b %d, %Y")
        st.markdown(
            f"""
        <div class="sidebar-footer">
            <div class="sidebar-footer-content">
                <div class="footer-stats">
                    <div class="footer-stat-item">
                        <div class="footer-stat-value">24/7</div>
                        <div class="footer-stat-label">Uptime</div>
                    </div>
                    <div class="footer-stat-item">
                        <div class="footer-stat-value">99.9%</div>
                        <div class="footer-stat-label">Reliability</div>
                    </div>
                    <div class="footer-stat-item">
                        <div class="footer-stat-value">v1.0</div>
                        <div class="footer-stat-label">Version</div>
                    </div>
                </div>
                <hr class="footer-divider">
                <div class="footer-meta">
                    <div class="sidebar-version">
                        <span class="sidebar-status"></span>
                        Production • Stable
                    </div>
                    <div class="sidebar-time">{current_time}</div>
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )
