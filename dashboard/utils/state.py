import streamlit as st

class StateManager:
    """Centralized session state management."""
    
    @staticmethod
    def init():
        """Initialize session state."""
        if "page" not in st.session_state:
            st.session_state.page = "overview"
    
    @staticmethod
    def get_current_page() -> str:
        return st.session_state.get("page", "overview")
    
    @staticmethod
    def set_current_page(page: str):
        st.session_state.page = page