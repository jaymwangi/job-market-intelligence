import streamlit as st
from dashboard.utils import StateManager

def render_pagination(page: int, total_pages: int):
    """Render pagination controls."""
    if total_pages <= 1:
        return
    
    max_visible = 5
    half = max_visible // 2
    
    if total_pages <= max_visible:
        page_range = range(1, total_pages + 1)
    else:
        if page <= half:
            page_range = range(1, max_visible + 1)
        elif page >= total_pages - half:
            page_range = range(total_pages - max_visible + 1, total_pages + 1)
        else:
            page_range = range(page - half, page + half + 1)
    
    cols = st.columns([1, 3, 1])
    
    with cols[0]:
        if st.button("⬅ Previous", disabled=page <= 1):
            StateManager.set_jobs_page(page - 1)
            st.rerun()
    
    with cols[1]:
        button_cols = st.columns(len(page_range))
        for idx, page_num in enumerate(page_range):
            with button_cols[idx]:
                if st.button(
                    str(page_num),
                    key=f"page_{page_num}",
                    type="primary" if page_num == page else "secondary",
                    use_container_width=True
                ):
                    StateManager.set_jobs_page(page_num)
                    st.rerun()
    
    with cols[2]:
        if st.button("Next ➡", disabled=page >= total_pages):
            StateManager.set_jobs_page(page + 1)
            st.rerun()