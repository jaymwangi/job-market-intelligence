import streamlit as st

from services.health import HealthService
from components.alerts import show_error, show_success, show_info

def render():
    """Render the analytics page."""
    st.title("📈 Analytics")
    st.markdown("🚧 **Analytics Dashboard will be implemented in Sprint 5.3**")
    st.markdown("---")
    
    show_info("Analytics features including charts, trends, and insights will be available in Sprint 5.3.")
    
    # Only test connectivity - no analytics data fetched
    with st.expander("🔌 API Connection Status"):
        try:
            service = HealthService()
            health = service.check()
            
            if health.status == "ok":
                show_success("✅ API is healthy. Analytics coming in Sprint 5.3.")
            else:
                show_error("⚠️ API connection issue.")
                
        except Exception as e:
            show_error(f"❌ Cannot connect to API: {str(e)}")