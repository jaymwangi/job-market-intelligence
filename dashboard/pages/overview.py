import streamlit as st

from core.config import settings
from services.health import HealthService
from components.alerts import show_error, show_success, show_warning

def render():
    """Render the overview page."""
    st.title("📊 Overview")
    st.markdown(f"Welcome to the **{settings.APP_TITLE}**.")
    st.markdown("This page will contain dashboard metrics and summary statistics.")
    st.markdown("---")
    
    # Test API connectivity
    with st.expander("🔌 API Connection Status", expanded=True):
        try:
            service = HealthService()
            health = service.check()
            
            if health.status == "ok":
                show_success("✅ API is healthy and reachable.")
            else:
                show_warning("⚠️ API responded but status is not 'ok'.")
                
        except Exception as e:
            show_error(f"❌ Cannot connect to API: {str(e)}")
            st.markdown("""
            **Troubleshooting:**
            1. Make sure the FastAPI backend is running
            2. Check that `API_BASE_URL` is correct in `.env`
            3. Verify the backend is accessible at the configured URL
            """)