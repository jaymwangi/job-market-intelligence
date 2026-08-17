"""Filter UI components for the dashboard."""

import streamlit as st
from components.icons import get_icon


def render_filters():
    """Render filter UI and return normalized filter values."""
    
    # Header with SVG icon
    st.sidebar.markdown(
        f"### {get_icon('search', 18)} Filters",
        unsafe_allow_html=True
    )
    
    # Search with SVG icon
    st.sidebar.markdown(
        f"{get_icon('search', 14)} **Search**",
        unsafe_allow_html=True
    )
    search = st.sidebar.text_input(
        "search",
        placeholder="Job title or company...",
        value="",
        label_visibility="collapsed"
    )
    
    # Company with SVG icon
    st.sidebar.markdown(
        f"{get_icon('company', 14)} **Company Name**",
        unsafe_allow_html=True
    )
    company = st.sidebar.text_input(
        "company",
        placeholder="Filter by company...",
        label_visibility="collapsed"
    )
    
    # Location with SVG icon
    st.sidebar.markdown(
        f"{get_icon('location', 14)} **Location**",
        unsafe_allow_html=True
    )
    location = st.sidebar.text_input(
        "location",
        placeholder="City, country, or 'Remote'...",
        label_visibility="collapsed"
    )
    
    # Source with SVG icon
    st.sidebar.markdown(
        f"{get_icon('source', 14)} **Source**",
        unsafe_allow_html=True
    )
    source = st.sidebar.selectbox(
        "source",
        ["All", "adzuna", "reed", "indeed", "linkedin"],
        label_visibility="collapsed"
    )
    
    # Salary with SVG icon
    st.sidebar.markdown(
        f"{get_icon('salary', 14)} **Salary Range**",
        unsafe_allow_html=True
    )
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        min_salary = st.number_input(
            "min_salary",
            min_value=0,
            value=0,
            step=5000,
            format="%d",
            label_visibility="collapsed",
            placeholder="Min"
        )
    with col2:
        max_salary = st.number_input(
            "max_salary",
            min_value=0,
            value=0,
            step=5000,
            format="%d",
            label_visibility="collapsed",
            placeholder="Max"
        )
    
    # Normalize values
    def normalize(value):
        """Normalize filter values to None for empty/invalid values."""
        if value in ["All", "", 0, None]:
            return None
        if isinstance(value, str) and value.strip() == "":
            return None
        return value
    
    return {
        "search": normalize(search),
        "company": normalize(company),
        "location": normalize(location),
        "source_site": normalize(source),
        "min_salary": normalize(min_salary),
        "max_salary": normalize(max_salary),
    }