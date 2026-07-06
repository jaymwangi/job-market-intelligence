# dashboard/components/sidebar.py
"""Professional sidebar navigation."""
import streamlit as st
from datetime import datetime

from core.config import settings
from utils.state import StateManager


def render_sidebar():
    """Render the professional sidebar navigation."""
    
    st.markdown("""
    <style>
        .css-1d391kg, .css-12oz5g7 {
            background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
        }
        .sidebar-title {
            font-size: 1.25rem;
            font-weight: 700;
            color: #ffffff;
            letter-spacing: -0.02em;
            padding: 0.5rem 0 0.25rem 0;
        }
        .sidebar-subtitle {
            font-size: 0.75rem;
            color: rgba(255,255,255,0.5);
            font-weight: 400;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid rgba(255,255,255,0.08);
        }
        /* Style the actual Streamlit button */
        .stButton button {
            background: rgba(255,255,255,0.04) !important;
            color: rgba(255,255,255,0.8) !important;
            border: 1px solid rgba(255,255,255,0.06) !important;
            border-radius: 10px !important;
            padding: 0.65rem 1rem !important;
            font-weight: 500 !important;
            font-size: 0.9rem !important;
            text-align: left !important;
            justify-content: flex-start !important;
            transition: all 0.15s ease !important;
            width: 100% !important;
            cursor: pointer !important;
            box-shadow: none !important;
            height: auto !important;
            line-height: 1.4 !important;
        }
        .stButton button:hover {
            background: rgba(255,255,255,0.08) !important;
            color: #ffffff !important;
            border-color: rgba(255,255,255,0.12) !important;
            transform: translateX(3px);
            box-shadow: none !important;
        }
        .stButton button:active {
            transform: scale(0.98) translateX(2px);
            box-shadow: none !important;
        }
        .stButton button:focus {
            box-shadow: none !important;
            border-color: rgba(255,255,255,0.15) !important;
        }
        .stButton button:focus-visible {
            outline: none !important;
            box-shadow: 0 0 0 2px rgba(108, 92, 231, 0.3) !important;
        }
        /* Active state */
        .active-nav .stButton button {
            background: rgba(108, 92, 231, 0.15) !important;
            color: #ffffff !important;
            border-color: rgba(108, 92, 231, 0.3) !important;
            border-left: 3px solid #6c5ce7 !important;
            box-shadow: none !important;
        }
        .active-nav .stButton button:hover {
            background: rgba(108, 92, 231, 0.25) !important;
            box-shadow: none !important;
        }
        .sidebar-divider {
            border: none;
            height: 1px;
            background: linear-gradient(90deg, rgba(255,255,255,0.08), rgba(255,255,255,0.02));
            margin: 0.5rem 0;
        }
        .sidebar-footer {
            padding: 0.75rem 0 0 0;
            border-top: 1px solid rgba(255,255,255,0.04);
            margin-top: 0.5rem;
        }
        .sidebar-version {
            color: rgba(255,255,255,0.2);
            font-size: 0.65rem;
            font-weight: 400;
            letter-spacing: 0.04em;
        }
        .sidebar-time {
            color: rgba(255,255,255,0.12);
            font-size: 0.6rem;
            font-weight: 300;
            margin-top: 0.15rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        # Brand
        st.markdown(f"""
        <div class="sidebar-title">📊 {settings.APP_TITLE}</div>
        <div class="sidebar-subtitle">Real-time Analytics</div>
        """, unsafe_allow_html=True)
        
        st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)
        
        # Navigation with clean text
        pages = [
            ("Overview", "overview"),
            ("Jobs", "jobs"),
            ("Analytics", "analytics"),
            ("About", "about"),
        ]
        
        current_page = StateManager.get_current_page()
        
        for label, page_id in pages:
            is_active = current_page == page_id
            
            # Simple display label
            display_label = label
            if is_active:
                display_label = f"{label} →"
            
            # Wrap in container for active class
            with st.container():
                if is_active:
                    st.markdown('<div class="active-nav">', unsafe_allow_html=True)
                
                clicked = st.button(
                    display_label,
                    use_container_width=True,
                    key=f"nav_{page_id}",
                    help=f"Navigate to {label}",
                )
                
                if is_active:
                    st.markdown('</div>', unsafe_allow_html=True)
                
                if clicked and current_page != page_id:
                    StateManager.set_current_page(page_id)
                    st.rerun()
        
        st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)
        
        # Footer
        st.markdown(f"""
        <div class="sidebar-footer">
            <div class="sidebar-version">Sprint 5.4 • Job Explorer</div>
            <div class="sidebar-time">{datetime.now().strftime("%b %d, %Y • %I:%M %p")}</div>
        </div>
        """, unsafe_allow_html=True)