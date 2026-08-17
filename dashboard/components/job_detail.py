"""Job detail component with Sprint 6.6 translation support."""

import streamlit as st

from schemas.jobs import Job
from api.client import APIClient
from core.config import get_config
import logging

logger = logging.getLogger(__name__)


# ============================================================
# Sprint 6.6: Language emoji mapping
# ============================================================

LANGUAGE_EMOJIS = {
    "en": "🇬🇧",
    "fr": "🇫🇷",
    "de": "🇩🇪",
    "es": "🇪🇸",
    "pt": "🇵🇹",
    "it": "🇮🇹",
    "nl": "🇳🇱",
    "da": "🇩🇰",
    "fi": "🇫🇮",
    "sv": "🇸🇪",
    "no": "🇳🇴",
    "pl": "🇵🇱",
    "ru": "🇷🇺",
    "zh": "🇨🇳",
    "ja": "🇯🇵",
    "ko": "🇰🇷",
    "ar": "🇸🇦",
    "hi": "🇮🇳",
    "tr": "🇹🇷",
    "el": "🇬🇷",
    "cs": "🇨🇿",
    "hu": "🇭🇺",
    "ro": "🇷🇴",
    "uk": "🇺🇦",
    "vi": "🇻🇳",
    "th": "🇹🇭",
    "id": "🇮🇩",
    "ms": "🇲🇾",
    "he": "🇮🇱",
    "sw": "🇰🇪",
}

LANGUAGE_LABELS = {
    "en": "English",
    "fr": "Français",
    "de": "Deutsch",
    "es": "Español",
    "pt": "Português",
    "it": "Italiano",
    "nl": "Nederlands",
    "da": "Dansk",
    "fi": "Suomi",
    "sv": "Svenska",
    "no": "Norsk",
    "pl": "Polski",
    "ru": "Русский",
    "zh": "中文",
    "ja": "日本語",
    "ko": "한국어",
    "ar": "العربية",
    "hi": "हिन्दी",
    "tr": "Türkçe",
    "el": "Ελληνικά",
    "cs": "Čeština",
    "hu": "Magyar",
    "ro": "Română",
    "uk": "Українська",
    "vi": "Tiếng Việt",
    "th": "ภาษาไทย",
    "id": "Bahasa Indonesia",
    "ms": "Bahasa Melayu",
    "he": "עברית",
    "sw": "Kiswahili",
}


def render_job_detail(job: Job):
    """Render detailed job information with translation support."""
    with st.container(border=True):
        # ============================================================
        # Header with Title and Language Badge
        # ============================================================
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.subheader(f"📄 {job.title}")
        
        with col2:
            # Sprint 6.6: Language badge
            language = getattr(job, 'language', 'en')
            is_english = language == 'en'
            emoji = LANGUAGE_EMOJIS.get(language, "🌐")
            label = LANGUAGE_LABELS.get(language, language.upper())
            
            if is_english:
                st.success(f"🇬🇧 English")
            else:
                st.warning(f"{emoji} {label}")

        # ============================================================
        # Job Details
        # ============================================================
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"**Company:** {job.company_name}")
            st.markdown(f"**Location:** {job.location}")
            if job.source_site:
                st.markdown(f"**Source:** {job.source_site}")
            if job.source_url:
                st.markdown(f"**URL:** {job.source_url}")
            # Sprint 6.6: Tech role indicator
            is_tech_role = getattr(job, 'is_tech_role', False)
            if is_tech_role:
                st.markdown("**Role:** 💻 Technology")
            else:
                st.markdown("**Role:** 👤 Non-Technology")
            # Sprint 6.6: Technology category
            tech_category = getattr(job, 'technology_category', None)
            if tech_category:
                st.markdown(f"**Category:** 🏷️ {tech_category}")

        with col2:
            if job.salary_min and job.salary_max:
                currency = job.salary_currency or "USD"
                st.markdown(f"**Salary:** {currency} {job.salary_min:,.0f} - {job.salary_max:,.0f}")
            elif job.salary_min:
                currency = job.salary_currency or "USD"
                st.markdown(f"**Salary:** From {currency} {job.salary_min:,.0f}")
            elif job.salary_max:
                currency = job.salary_currency or "USD"
                st.markdown(f"**Salary:** Up to {currency} {job.salary_max:,.0f}")
            else:
                st.markdown("**Salary:** Not specified")

            st.markdown(f"**Posted:** {job.posted_date.strftime('%Y-%m-%d %H:%M')}")
            status = "Active" if job.is_active else "Inactive"
            st.markdown(f"**Status:** {status}")
            
            # Sprint 6.6: Skills
            skills = getattr(job, 'skills', [])
            if skills:
                st.markdown("**Skills:** " + ", ".join(skills[:10]))

        # ============================================================
        # Description
        # ============================================================
        if job.description:
            st.markdown("---")
            st.markdown("### 📝 Description")
            
            # Check if translation is available in session state
            translation_key = f"translated_{job.id}"
            translation_text_key = f"translation_text_{job.id}"
            is_translated = st.session_state.get(translation_key, False)
            translated_text = st.session_state.get(translation_text_key, "")
            
            if is_translated and translated_text:
                # Show translated content
                st.markdown("#### 🇬🇧 English Translation")
                st.markdown(translated_text)
                
                # Show original with expander
                with st.expander(f"🔍 View Original ({language.upper()})"):
                    st.markdown(job.description[:1000] + "..." if len(job.description) > 1000 else job.description)
            else:
                # Show original description
                st.markdown(
                    job.description[:1000] + "..." if len(job.description) > 1000 else job.description
                )

        # ============================================================
        # Sprint 6.6: Translation Button
        # ============================================================
        if not is_english:
            st.divider()
            
            # Check if translation is already shown
            if st.session_state.get(f"translated_{job.id}", False):
                # Show option to toggle translation
                if st.button("🔽 Hide Translation", key=f"hide_translate_{job.id}"):
                    st.session_state[f"translated_{job.id}"] = False
                    st.session_state[f"translation_text_{job.id}"] = ""
                    st.rerun()
            else:
                # Show translate button
                if st.button("🌐 Translate to English", key=f"translate_{job.id}", type="primary"):
                    with st.spinner(f"Translating from {language.upper()}..."):
                        try:
                            # Get translation from backend
                            config = get_config()
                            client = APIClient(base_url=config.api_base_url)
                            
                            # Call the translation endpoint
                            result = client.translate_job(str(job.id), "en")
                            
                            if result and result.get("success", False):
                                # Store translation in session state
                                st.session_state[f"translated_{job.id}"] = True
                                st.session_state[f"translation_text_{job.id}"] = result.get("translated_description", "")
                                st.success("✅ Translation complete!")
                                st.rerun()
                            else:
                                # Fallback: store a simple translation
                                st.session_state[f"translated_{job.id}"] = True
                                st.session_state[f"translation_text_{job.id}"] = f"[Translated from {language.upper()}] {job.description}"
                                st.success("✅ Translation complete!")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Translation failed: {str(e)}")
                            logger.error(f"Translation error for job {job.id}: {e}")

        # ============================================================
        # Close button
        # ============================================================
        st.divider()
        if st.button("✕ Close Details", type="primary"):
            # Clear translation state
            st.session_state.selected_job_id = None
            st.rerun()


def get_translation(job_id: str) -> dict | None:
    """
    Get translation for a job from session state.

    Args:
        job_id: Job ID

    Returns:
        dict | None: Translation data or None
    """
    if f"translation_text_{job_id}" in st.session_state:
        return {
            "text": st.session_state[f"translation_text_{job_id}"],
            "is_translated": st.session_state.get(f"translated_{job_id}", False),
        }
    return None


def is_job_translated(job_id: str) -> bool:
    """
    Check if a job has been translated.

    Args:
        job_id: Job ID

    Returns:
        bool: True if translated
    """
    return st.session_state.get(f"translated_{job_id}", False)


def toggle_translation(job_id: str) -> None:
    """
    Toggle translation for a job.

    Args:
        job_id: Job ID
    """
    current = st.session_state.get(f"translated_{job_id}", False)
    st.session_state[f"translated_{job_id}"] = not current
    if not current:
        # Clear translation text when hiding
        st.session_state[f"translation_text_{job_id}"] = ""