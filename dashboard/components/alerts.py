
import streamlit as st

def show_error(message: str):
    """Show an error message."""
    st.error(f"❌ {message}")

def show_success(message: str):
    """Show a success message."""
    st.success(f"✅ {message}")

def show_warning(message: str):
    """Show a warning message."""
    st.warning(f"⚠️ {message}")

def show_info(message: str):
    """Show an info message."""
    st.info(f"ℹ️ {message}")