# dashboard/components/alerts.py
"""Alert components."""
import streamlit as st


def show_error(message: str):
    """Show error alert."""
    st.error(f"❌ {message}")


def show_success(message: str):
    """Show success alert."""
    st.success(f"✅ {message}")


def show_warning(message: str):
    """Show warning alert."""
    st.warning(f"⚠️ {message}")


def show_info(message: str):
    """Show info alert."""
    st.info(f"ℹ️ {message}")


def show_api_error(error: Exception):
    """Show API error with details."""
    st.error(f"🚨 API Error: {str(error)}")
    with st.expander("Error Details"):
        st.code(f"Type: {type(error).__name__}\nMessage: {str(error)}")