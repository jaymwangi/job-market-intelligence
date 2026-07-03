import streamlit as st

from dashboard.core.config import settings
from dashboard.services.health import HealthService
from dashboard.api.client import APIClient
from dashboard.components.alerts import show_error, show_success, show_warning


def render():
    """Render the overview page."""
    st.title("📊 Overview")
    st.markdown(f"Welcome to the **{settings.APP_TITLE}**.")
    st.markdown("---")
    
    st.markdown("### 📈 Dashboard Summary")
    st.markdown("Dashboard metrics and summary statistics will appear here.")
    st.caption("🚧 Sprint 5.3 will add analytics charts and insights.")
    st.markdown("---")
    
    # Test API connectivity
    with st.expander("🔌 API Connection Status", expanded=True):
        try:
            # Create API client and pass to service
            api_client = APIClient(settings.API_BASE_URL, settings.API_TIMEOUT)
            service = HealthService(api_client)
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