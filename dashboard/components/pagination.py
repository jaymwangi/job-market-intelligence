"""Pagination component for job listings."""

import streamlit as st


def render_pagination(current_page: int, total_pages: int) -> None:
    """
    Render pagination controls with proper state management.
    
    Args:
        current_page: Current page number (1-indexed)
        total_pages: Total number of pages
    """
    if total_pages <= 1:
        return
    
    st.markdown("---")
    
    # Create columns for pagination controls
    col1, col2, col3 = st.columns([1, 3, 1])
    
    # Previous button
    with col1:
        if st.button("⬅ Previous", disabled=current_page <= 1, use_container_width=True):
            st.session_state.jobs_page = current_page - 1
            st.rerun()  # ← Force immediate rerun
    
    # Page number buttons
    with col2:
        # Calculate which page numbers to show
        max_visible = 5
        half = max_visible // 2
        
        if total_pages <= max_visible:
            page_range = list(range(1, total_pages + 1))
        else:
            if current_page <= half:
                page_range = list(range(1, max_visible + 1))
            elif current_page >= total_pages - half:
                page_range = list(range(total_pages - max_visible + 1, total_pages + 1))
            else:
                page_range = list(range(current_page - half, current_page + half + 1))
        
        # Create columns for each page button
        button_cols = st.columns(len(page_range))
        
        for idx, page_num in enumerate(page_range):
            with button_cols[idx]:
                is_current = page_num == current_page
                label = f"**{page_num}**" if is_current else str(page_num)
                
                if st.button(
                    label,
                    key=f"page_btn_{page_num}",
                    disabled=is_current,
                    use_container_width=True,
                ):
                    st.session_state.jobs_page = page_num
                    st.rerun()  # ← Force immediate rerun
    
    # Next button
    with col3:
        if st.button("Next ➡", disabled=current_page >= total_pages, use_container_width=True):
            st.session_state.jobs_page = current_page + 1
            st.rerun()  # ← Force immediate rerun
    
    # Show page info
    st.caption(f"Page {current_page} of {total_pages}")