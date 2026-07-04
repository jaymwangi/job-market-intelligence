# dashboard/app.py
"""Professional Streamlit dashboard application."""
import streamlit as st
import sys
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add dashboard directory to path
dashboard_dir = os.path.dirname(os.path.abspath(__file__))
if dashboard_dir not in sys.path:
    sys.path.insert(0, dashboard_dir)

from core.config import settings
from utils.state import StateManager
from components.sidebar import render_sidebar

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
    "border": "#e9ecef",
}

# Page configuration
st.set_page_config(
    page_title=settings.APP_TITLE,
    page_icon=settings.APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# Professional custom CSS
st.markdown(f"""
<style>
    /* Reset and base styles */
    .main {{
        padding: 0 1rem;
    }}
    
    /* Typography */
    h1, h2, h3, h4, h5, h6 {{
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', sans-serif;
        color: {COLORS['primary']};
        font-weight: 600;
        letter-spacing: -0.01em;
    }}
    
    /* Sidebar styling */
    .css-1d391kg, .css-12oz5g7 {{
        background: {COLORS['primary']};
    }}
    
    .sidebar .sidebar-content {{
        background: {COLORS['primary']};
        padding: 1.5rem 0;
    }}
    
    /* Sidebar navigation */
    .stRadio > div {{
        gap: 0.25rem;
    }}
    
    .stRadio label {{
        padding: 0.5rem 1rem;
        border-radius: 8px;
        transition: all 0.2s ease;
        color: rgba(255,255,255,0.7);
        font-weight: 500;
        cursor: pointer;
    }}
    
    .stRadio label:hover {{
        background: rgba(255,255,255,0.08);
        color: #ffffff;
    }}
    
    .stRadio label[data-baseweb="radio"] {{
        background: transparent;
    }}
    
    .stRadio label[data-testid="stRadioLabel"] {{
        padding: 0.5rem 1rem;
    }}
    
    /* Button styling */
    .stButton button {{
        background: {COLORS['accent']};
        color: white;
        font-weight: 500;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1.25rem;
        transition: all 0.2s ease;
        font-size: 0.9rem;
    }}
    
    .stButton button:hover {{
        background: {COLORS['secondary']};
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }}
    
    .stButton button:active {{
        transform: translateY(0);
    }}
    
    /* Metric cards */
    .stMetric {{
        background: {COLORS['card_bg']};
        padding: 1.25rem;
        border-radius: 12px;
        border: 1px solid {COLORS['border']};
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        transition: all 0.2s ease;
    }}
    
    .stMetric:hover {{
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        transform: translateY(-2px);
    }}
    
    .stMetric label {{
        color: {COLORS['text_light']};
        font-weight: 500;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }}
    
    .stMetric div[data-testid="stMetricValue"] {{
        color: {COLORS['primary']};
        font-weight: 700;
        font-size: 1.75rem;
    }}
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.25rem;
        background: {COLORS['background']};
        border-radius: 10px;
        padding: 0.25rem;
        border: 1px solid {COLORS['border']};
    }}
    
    .stTabs [data-baseweb="tab"] {{
        border-radius: 8px;
        padding: 0.5rem 1.25rem;
        font-weight: 500;
        color: {COLORS['text_light']};
        transition: all 0.2s ease;
        font-size: 0.9rem;
    }}
    
    .stTabs [data-baseweb="tab"]:hover {{
        background: rgba(0,0,0,0.04);
        color: {COLORS['text']};
    }}
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {{
        background: {COLORS['card_bg']};
        color: {COLORS['primary']};
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        border: 1px solid {COLORS['border']};
    }}
    
    /* Containers and borders */
    .stContainer {{
        border: 1px solid {COLORS['border']};
        border-radius: 12px;
        padding: 1.25rem;
        background: {COLORS['card_bg']};
        transition: all 0.2s ease;
    }}
    
    .stContainer:hover {{
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }}
    
    /* Expander styling */
    .streamlit-expanderHeader {{
        font-weight: 600;
        color: {COLORS['primary']};
        border-radius: 8px;
        transition: all 0.2s ease;
    }}
    
    .streamlit-expanderHeader:hover {{
        background: {COLORS['background']};
    }}
    
    /* Selectbox and inputs */
    .stSelectbox div[data-baseweb="select"] {{
        border-radius: 8px;
        border: 1px solid {COLORS['border']};
        transition: all 0.2s ease;
    }}
    
    .stSelectbox div[data-baseweb="select"]:hover {{
        border-color: {COLORS['accent']};
    }}
    
    .stTextInput input {{
        border-radius: 8px;
        border: 1px solid {COLORS['border']};
        transition: all 0.2s ease;
        padding: 0.5rem 0.75rem;
    }}
    
    .stTextInput input:focus {{
        border-color: {COLORS['accent']};
        box-shadow: 0 0 0 3px rgba(15, 52, 96, 0.1);
    }}
    
    .stNumberInput input {{
        border-radius: 8px;
        border: 1px solid {COLORS['border']};
        transition: all 0.2s ease;
        padding: 0.5rem 0.75rem;
    }}
    
    .stNumberInput input:focus {{
        border-color: {COLORS['accent']};
        box-shadow: 0 0 0 3px rgba(15, 52, 96, 0.1);
    }}
    
    /* Footer */
    .footer {{
        padding: 2rem 0 1rem 0;
        border-top: 1px solid {COLORS['border']};
        margin-top: 2rem;
        text-align: center;
    }}
    
    .footer-text {{
        color: {COLORS['text_light']};
        font-size: 0.85rem;
        font-weight: 400;
        letter-spacing: 0.02em;
    }}
    
    .footer-text strong {{
        color: {COLORS['primary']};
        font-weight: 500;
    }}
    
    /* Loading and progress */
    .stSpinner > div {{
        border-color: {COLORS['accent']} !important;
    }}
    
    /* Info, success, warning, error boxes */
    .stAlert {{
        border-radius: 10px;
        border-left-width: 4px;
        padding: 1rem;
    }}
    
    /* Dataframe styling */
    .dataframe {{
        border-radius: 8px !important;
        border: 1px solid {COLORS['border']} !important;
        overflow: hidden !important;
    }}
    
    .dataframe thead {{
        background: {COLORS['background']} !important;
    }}
    
    .dataframe th {{
        color: {COLORS['primary']} !important;
        font-weight: 600 !important;
        padding: 0.75rem 1rem !important;
        font-size: 0.85rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.04em !important;
    }}
    
    .dataframe td {{
        padding: 0.75rem 1rem !important;
        border-bottom: 1px solid {COLORS['border']} !important;
    }}
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: {COLORS['background']};
        border-radius: 4px;
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: {COLORS['text_light']};
        border-radius: 4px;
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: {COLORS['text']};
    }}
</style>
""", unsafe_allow_html=True)

# Initialize session state
StateManager.init()

# Render sidebar
render_sidebar()

# Get navigation state
page = StateManager.get_current_page()

# Page routing with professional page titles
page_titles = {
    "overview": "Dashboard Overview",
    "jobs": "Job Explorer",
    "analytics": "Market Analytics",
    "about": "About"
}

# Page routing
try:
    if page == "overview":
        from pages.overview import render
        render()
    elif page == "jobs":
        from pages.jobs import render
        render()
    elif page == "analytics":
        from pages.analytics import render
        render()
    elif page == "about":
        from pages.about import render
        render()
    else:
        st.error(f"Page '{page}' not found")
except Exception as e:
    st.error(f"Failed to load page: {str(e)}")
    logger.error(f"Page load error: {e}", exc_info=True)

# Professional Footer
st.markdown("""
<div class="footer">
    <div class="footer-text">
        <strong>Job Market Intelligence</strong> • Real-time analytics platform
    </div>
    <div class="footer-text" style="margin-top: 0.25rem; font-size: 0.75rem;">
        © 2024 • Data powered by FastAPI backend
    </div>
</div>
""", unsafe_allow_html=True)