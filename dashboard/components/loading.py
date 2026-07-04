# dashboard/components/loading.py
"""Loading state components."""
import streamlit as st
from contextlib import contextmanager


def loading_spinner(text: str = "Loading..."):
    """Context manager for loading states."""
    @contextmanager
    def spinner_context():
        with st.spinner(text):
            yield
    return spinner_context()


def show_loading_card(text: str = "Loading data..."):
    """Show a loading card."""
    return st.info(f"⏳ {text}")


def show_skeleton_loader(rows: int = 3):
    """Show skeleton loader for tables."""
    for i in range(rows):
        st.markdown("---")
        st.markdown("```\nLoading...\n```")