# dashboard/components/alerts.py
"""Alert components with SVG icons."""

import streamlit as st

from dashboard.components.icons import get_icon


def show_error(message: str, role: str = "alert") -> None:
    """Show error alert with SVG icon."""
    icon = get_icon("error", size=18, color="#e94560")
    # Use markdown with unsafe_allow_html=True to render the SVG
    st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;color:#721c24;background:#f8d7da;border:1px solid #f5c6cb;border-radius:8px;padding:0.75rem 1rem;"><span style="display:inline-flex;">{icon}</span> <span>{message}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div role="{role}" aria-label="Error: {message}"></div>', unsafe_allow_html=True)


def show_success(message: str, role: str = "status") -> None:
    """Show success alert with SVG icon."""
    icon = get_icon("success", size=18, color="#00b894")
    st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;color:#155724;background:#d4edda;border:1px solid #c3e6cb;border-radius:8px;padding:0.75rem 1rem;"><span style="display:inline-flex;">{icon}</span> <span>{message}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div role="{role}" aria-label="Success: {message}"></div>', unsafe_allow_html=True)


def show_warning(message: str, role: str = "alert") -> None:
    """Show warning alert with SVG icon."""
    icon = get_icon("warning", size=18, color="#fdcb6e")
    st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;color:#856404;background:#fff3cd;border:1px solid #ffeeba;border-radius:8px;padding:0.75rem 1rem;"><span style="display:inline-flex;">{icon}</span> <span>{message}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div role="{role}" aria-label="Warning: {message}"></div>', unsafe_allow_html=True)


def show_info(message: str, role: str = "status") -> None:
    """Show info alert with SVG icon."""
    icon = get_icon("info", size=18, color="#0984e3")
    st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;color:#0c5460;background:#d1ecf1;border:1px solid #bee5eb;border-radius:8px;padding:0.75rem 1rem;"><span style="display:inline-flex;">{icon}</span> <span>{message}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div role="{role}" aria-label="Info: {message}"></div>', unsafe_allow_html=True)


def show_api_error(error: Exception, role: str = "alert") -> None:
    """Show API error with friendly message and accessibility."""
    message = str(error)
    
    # Map technical errors to friendly messages
    if "ConnectionError" in message or "Connection refused" in message:
        friendly_message = "Unable to connect to the server. Please check your internet connection."
    elif "Timeout" in message or "timed out" in message:
        friendly_message = "The request timed out. Please try again."
    elif "404" in message:
        friendly_message = "The requested resource was not found."
    elif "500" in message:
        friendly_message = "The server encountered an error. Please try again later."
    else:
        friendly_message = f"An error occurred: {message}"
    
    show_error(friendly_message, role)
    
    # Show details in expander for debugging
    with st.expander("🔍 Error Details"):
        st.code(f"Type: {type(error).__name__}\nMessage: {str(error)}")