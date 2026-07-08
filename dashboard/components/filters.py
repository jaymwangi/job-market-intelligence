import streamlit as st


def render_filters():
    """Render filter UI and return normalized filter values."""
    st.sidebar.header("🔍 Filters")

    filters = {
        "search": st.sidebar.text_input("Search", placeholder="Job title or company...", value=""),
        "company": st.sidebar.text_input("Company Name", placeholder="Filter by company..."),
        "location": st.sidebar.text_input("Location", placeholder="City, country, or 'Remote'..."),
        "source_site": st.sidebar.selectbox(
            "Source", ["All", "adzuna", "reed", "indeed", "linkedin"]
        ),
        "min_salary": st.sidebar.number_input(
            "Min Salary", min_value=0, value=0, step=5000, format="%d"
        ),
        "max_salary": st.sidebar.number_input(
            "Max Salary", min_value=0, value=0, step=5000, format="%d"
        ),
    }

    def normalize(value):
        """Normalize filter values to None for empty/invalid values."""
        if value in ["All", "", 0]:
            return None
        if isinstance(value, str) and value.strip() == "":
            return None
        return value

    return {key: normalize(value) for key, value in filters.items()}
