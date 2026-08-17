"""Dashboard theme configuration - modern professional design."""

# Modern professional color palette
COLORS = {
    # Primary
    "primary": "#0a0a1a",
    "primary_light": "#1a1a3e",
    "primary_dark": "#050510",
    # Secondary
    "secondary": "#1a1a3e",
    "secondary_light": "#2a2a5e",
    # Accent
    "accent": "#6c5ce7",
    "accent_light": "#a29bfe",
    "accent_dark": "#4a3cb5",
    "accent_gradient": "linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%)",
    # Highlights
    "highlight": "#e94560",
    "success": "#00b894",
    "warning": "#fdcb6e",
    "info": "#0984e3",
    # Neutrals
    "background": "#f0f2f5",
    "card_bg": "#ffffff",
    "text": "#1a1a2e",
    "text_light": "#636e72",
    "text_lighter": "#b2bec3",
    "border": "#e9ecef",
    "border_light": "#f1f2f6",
    "shadow": "0 2px 12px rgba(0,0,0,0.04)",
    "shadow_hover": "0 8px 40px rgba(108,92,231,0.10)",
}

# Technology colors
TECH_COLORS = {
    "backend": "#6c5ce7",
    "frontend": "#0984e3",
    "full_stack": "#00b894",
    "data": "#fdcb6e",
    "devops": "#e17055",
    "ml_ai": "#fd79a8",
    "mobile": "#00cec9",
    "security": "#d63031",
    "blockchain": "#fdcb6e",
    "game_dev": "#6c5ce7",
    "qa": "#636e72",
    "other": "#b2bec3",
}

# Country flags
COUNTRY_FLAGS = {
    "GB": "🇬🇧",
    "US": "🇺🇸",
    "DE": "🇩🇪",
    "FR": "🇫🇷",
    "CA": "🇨🇦",
    "AU": "🇦🇺",
}

# Modern global styles
GLOBAL_STYLES = """
<style>
    /* Import professional font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* Global styles */
    .stApp {
        background: #f0f2f5;
    }
    
    .main {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        padding: 0 1rem;
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 4px;
        height: 4px;
    }
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    ::-webkit-scrollbar-thumb {
        background: #c5c5c5;
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #a8a8a8;
    }
    
    /* Sidebar */
    .css-1d391kg, .css-12oz5g7 {
        background: #0a0a1a;
    }
    
    /* Radio buttons in sidebar */
    .stRadio > div {
        gap: 0.15rem;
    }
    .stRadio label {
        padding: 0.6rem 1rem;
        border-radius: 10px;
        transition: all 0.2s ease;
        color: rgba(255,255,255,0.5);
        font-weight: 500;
        font-size: 0.9rem;
        cursor: pointer;
    }
    .stRadio label:hover {
        background: rgba(255,255,255,0.06);
        color: rgba(255,255,255,0.8);
    }
    .stRadio label[data-baseweb="radio"] {
        background: transparent;
    }
    .stRadio label[data-testid="stRadioLabel"] {
        padding: 0.6rem 1rem;
    }
    
    /* Buttons */
    .stButton button {
        background: linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%);
        color: white;
        font-weight: 600;
        border-radius: 12px;
        border: none;
        padding: 0.6rem 1.5rem;
        transition: all 0.2s ease;
        font-size: 0.9rem;
        box-shadow: 0 4px 15px rgba(108,92,231,0.25);
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(108,92,231,0.35);
    }
    .stButton button:active {
        transform: translateY(0);
    }
    
    /* Metric cards */
    .metric-card {
        background: white;
        border-radius: 16px;
        padding: 1.25rem 1.5rem;
        border: 1px solid #e9ecef;
        box-shadow: 0 2px 12px rgba(0,0,0,0.04);
        transition: all 0.3s ease;
        height: 100%;
        min-height: 100px;
    }
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 40px rgba(108,92,231,0.10);
        border-color: #d5cdf5;
    }
    .metric-card .icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 44px;
        height: 44px;
        border-radius: 12px;
        margin-bottom: 0.75rem;
    }
    .metric-card .value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0a0a1a;
        letter-spacing: -0.02em;
        line-height: 1.2;
    }
    .metric-card .label {
        font-size: 0.7rem;
        font-weight: 500;
        color: #636e72;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-top: 0.15rem;
    }
    .metric-card .subtitle {
        font-size: 0.65rem;
        color: #b2bec3;
        margin-top: 0.25rem;
    }
    
    /* Progress bars */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #6c5ce7, #a29bfe) !important;
        border-radius: 100px !important;
    }
    .stProgress > div {
        background: #f1f2f6 !important;
        border-radius: 100px !important;
    }
    
    /* Dividers */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, #e9ecef 30%, transparent 100%);
        margin: 1.5rem 0;
    }
    
    /* Containers */
    .stContainer {
        background: white;
        border-radius: 16px;
        padding: 1.25rem;
        border: 1px solid #e9ecef;
        box-shadow: 0 2px 12px rgba(0,0,0,0.04);
        transition: all 0.3s ease;
        margin-bottom: 0.5rem;
    }
    .stContainer:hover {
        box-shadow: 0 4px 24px rgba(0,0,0,0.06);
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: #0a0a1a;
        border-radius: 12px;
        transition: all 0.2s ease;
        padding: 0.75rem 1rem;
        background: white;
        border: 1px solid #e9ecef;
    }
    .streamlit-expanderHeader:hover {
        background: #f8f9fa;
        border-color: #d5cdf5;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.25rem;
        background: #f1f2f6;
        border-radius: 12px;
        padding: 0.25rem;
        border: none;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 0.5rem 1.25rem;
        font-weight: 500;
        color: #636e72;
        transition: all 0.2s ease;
        font-size: 0.85rem;
        border: none;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(0,0,0,0.04);
        color: #0a0a1a;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: white;
        color: #0a0a1a;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border: none;
    }
    
    /* Inputs */
    .stTextInput input, .stSelectbox div, .stNumberInput input {
        border-radius: 12px !important;
        border: 1px solid #e9ecef !important;
        transition: all 0.2s ease;
        padding: 0.5rem 0.75rem !important;
        font-size: 0.9rem !important;
    }
    .stTextInput input:focus, .stSelectbox div:focus, .stNumberInput input:focus {
        border-color: #6c5ce7 !important;
        box-shadow: 0 0 0 3px rgba(108,92,231,0.08) !important;
    }
    
    /* Captions */
    .stCaption {
        color: #636e72 !important;
        font-size: 0.8rem !important;
    }
    
    /* Info/Success/Warning/Error */
    .stAlert {
        border-radius: 12px !important;
        border-left-width: 4px !important;
        padding: 0.75rem 1rem !important;
    }
</style>
"""