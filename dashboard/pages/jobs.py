import streamlit as st

from services.health import HealthService
from components.alerts import show_error, show_success

def render():
    """Render the jobs page."""
    st.title("💼 Jobs")
    st.markdown("🚧 **Job Explorer will be implemented in Sprint 5.2**")
    st.markdown("---")
    
    # Only test connectivity - no job data fetched
    with st.expander("🔌 API Connection Status"):
        try:
            service = HealthService()
            health = service.check()
            
            if health.status == "ok":
                show_success("✅ API is healthy. Job features coming in Sprint 5.2.")
            else:
                show_error("⚠️ API connection issue.")
                
        except Exception as e:
            show_error(f"❌ Cannot connect to API: {str(e)}")