import streamlit as st

from dashboard.services.health import HealthService
from dashboard.api.client import APIClient
from dashboard.core.config import settings
from dashboard.components.alerts import show_error, show_success, show_info


def render():
    """Render the analytics page."""
    st.title("📈 Analytics")
    st.markdown("🚧 **Analytics Dashboard will be implemented in Sprint 5.3**")
    st.markdown("---")
    
    show_info("Analytics features including charts, trends, and insights will be available in Sprint 5.3.")
    
    # Only test connectivity - no analytics data fetched
    with st.expander("🔌 API Connection Status"):
        try:
            # Create API client and pass to service
            api_client = APIClient(settings.API_BASE_URL, settings.API_TIMEOUT)
            service = HealthService(api_client)
            health = service.check()
            
            if health.status == "ok":
                show_success("✅ API is healthy. Analytics coming in Sprint 5.3.")
            else:
                show_error("⚠️ API connection issue.")
                
        except Exception as e:
            show_error(f"❌ Cannot connect to API: {str(e)}")