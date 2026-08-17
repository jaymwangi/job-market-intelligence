"""Modern professional job card component with Sprint 6.6 enrichment data."""

import streamlit as st
from datetime import datetime
import html
import streamlit.components.v1 as components

# Country flag emoji mapping
COUNTRY_FLAGS = {
    "GB": "🇬🇧",
    "US": "🇺🇸",
    "DE": "🇩🇪",
    "FR": "🇫🇷",
    "CA": "🇨🇦",
    "AU": "🇦🇺",
    "IN": "🇮🇳",
    "SG": "🇸🇬",
    "NL": "🇳🇱",
    "ES": "🇪🇸",
    "IT": "🇮🇹",
    "SE": "🇸🇪",
    "CH": "🇨🇭",
    "IE": "🇮🇪",
    "NZ": "🇳🇿",
}

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

# Technology category colors and SVG icons
TECH_CONFIG = {
    "backend": {
        "color": "#6c5ce7",
        "label": "Backend",
        "svg": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>'
    },
    "frontend": {
        "color": "#0984e3",
        "label": "Frontend",
        "svg": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>'
    },
    "full_stack": {
        "color": "#00b894",
        "label": "Full Stack",
        "svg": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="2" width="20" height="20" rx="2"/><path d="M8 2v20"/><path d="M16 2v20"/><path d="M2 8h20"/><path d="M2 16h20"/></svg>'
    },
    "data": {
        "color": "#fdcb6e",
        "label": "Data",
        "svg": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16v-4"/><path d="M3 8l9 5 9-5"/><path d="M12 13v8"/></svg>'
    },
    "devops": {
        "color": "#e17055",
        "label": "DevOps",
        "svg": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/><circle cx="12" cy="12" r="3"/></svg>'
    },
    "ml_ai": {
        "color": "#fd79a8",
        "label": "ML/AI",
        "svg": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a10 10 0 1 0 10 10 10 10 0 0 0-10-10z"/><path d="M12 6v6l4 2"/><path d="M8 12a4 4 0 0 0 8 0"/></svg>'
    },
    "mobile": {
        "color": "#00cec9",
        "label": "Mobile",
        "svg": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="5" y="2" width="14" height="20" rx="2"/><line x1="12" y1="18" x2="12.01" y2="18"/></svg>'
    },
    "security": {
        "color": "#d63031",
        "label": "Security",
        "svg": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M12 8v4"/><path d="M12 16h.01"/></svg>'
    },
    "blockchain": {
        "color": "#fdcb6e",
        "label": "Blockchain",
        "svg": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 22 7 22 17 12 22 2 17 2 7 12 2"/><line x1="12" y1="22" x2="12" y2="12"/><line x1="22" y1="7" x2="12" y2="12"/><line x1="2" y1="7" x2="12" y2="12"/></svg>'
    },
    "game_dev": {
        "color": "#6c5ce7",
        "label": "Game Dev",
        "svg": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 12h4"/><path d="M10 10v4"/><rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="8" cy="12" r="1"/><circle cx="16" cy="12" r="1"/><path d="M16 10v4"/><path d="M20 10v4"/></svg>'
    },
    "qa": {
        "color": "#636e72",
        "label": "QA",
        "svg": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/><path d="M12 8v4"/><path d="M12 16h.01"/></svg>'
    },
    "other": {
        "color": "#b2bec3",
        "label": "General",
        "svg": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/></svg>'
    },
}

# SVG Icons for common elements
ICONS = {
    "company": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#636e72" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>',
    "calendar": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>',
    "tech_role": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#6c5ce7" stroke-width="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>',
    "non_tech": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#636e72" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
    "salary": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M8 12h8"/><path d="M12 8v8"/></svg>',
    "briefcase": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>',
}

EMPLOYMENT_LABELS = {
    "FULL_TIME": "Full Time",
    "PART_TIME": "Part Time",
    "CONTRACT": "Contract",
    "TEMPORARY": "Temporary",
    "INTERNSHIP": "Internship",
    "PERMANENT": "Permanent",
    "OTHER": "Other",
}


def _get_job_dict(job):
    """Extract dict from job object."""
    if hasattr(job, "model_dump"):
        return job.model_dump()
    elif hasattr(job, "dict"):
        return job.dict()
    return job


def _escape_html(text):
    """Escape HTML special characters in text."""
    if text is None:
        return ""
    return html.escape(str(text))


def render_job_card(job) -> None:
    """
    Render a modern, professional job card with SVG icons.
    
    Args:
        job: Job object (Pydantic model) or dict with enrichment fields
    """
    job_dict = _get_job_dict(job)
    
    # Extract data
    title = _escape_html(job_dict.get("title", "Untitled Position"))
    company = _escape_html(job_dict.get("company_name") or job_dict.get("company", "Unknown Company"))
    location = _escape_html(job_dict.get("location", ""))
    description = job_dict.get("description", "")
    salary_min = job_dict.get("salary_min")
    salary_max = job_dict.get("salary_max")
    currency = _escape_html(job_dict.get("currency") or job_dict.get("salary_currency") or "USD")
    posted_date = job_dict.get("posted_date")
    source_url = job_dict.get("source_url", "")
    
    # Enrichment fields
    skills = job_dict.get("skills", [])
    technology_category = job_dict.get("technology_category", "other")
    is_tech_role = job_dict.get("is_tech_role", False)
    country_code = job_dict.get("country_code")
    employment_type = job_dict.get("employment_type")
    
    # ============================================================
    # Sprint 6.6: Language fields
    # ============================================================
    language = job_dict.get("language", "en")
    language_emoji = LANGUAGE_EMOJIS.get(language, "🌐")
    language_label = LANGUAGE_LABELS.get(language, language.upper())
    is_english = language == "en"
    
    # Get tech config
    tech_config = TECH_CONFIG.get(technology_category, TECH_CONFIG["other"])
    tech_color = tech_config["color"]
    tech_svg = tech_config["svg"]
    tech_label = tech_config["label"]
    
    # Country flag
    flag = COUNTRY_FLAGS.get(country_code, "🌍") if country_code else "🌍"
    location_display = location or "Remote"
    emp_label = EMPLOYMENT_LABELS.get(employment_type, employment_type or "Other")
    
    # Format date
    date_display = "Recently posted"
    if posted_date:
        if isinstance(posted_date, str):
            try:
                dt = datetime.fromisoformat(posted_date.replace("Z", "+00:00"))
                date_display = dt.strftime("%b %d, %Y")
            except:
                date_display = posted_date[:10]
        else:
            date_display = posted_date.strftime("%b %d, %Y")
    
    # Render CSS once using st.markdown (this works for CSS)
    if "job_card_css_rendered" not in st.session_state:
        _render_css()
        st.session_state.job_card_css_rendered = True
    
    # ============================================================
    # Build tags - Sprint 6.6: Add language badge
    # ============================================================
    
    tags = [
        f'<span class="job-card-tag job-card-tag-country">{flag} {location_display}</span>'
    ]
    
    # Language badge (Sprint 6.6)
    if not is_english:
        tags.append(f'<span class="job-card-tag job-card-tag-language">{language_emoji} {language_label}</span>')
    else:
        tags.append(f'<span class="job-card-tag job-card-tag-language">🇬🇧 English</span>')
    
    if employment_type:
        tags.append(f'<span class="job-card-tag job-card-tag-employment">{ICONS["briefcase"]} {emp_label}</span>')
    
    if is_tech_role and technology_category != "other":
        tags.append(f'<span class="job-card-tag job-card-tag-category">{tech_svg} {tech_label}</span>')
    
    if is_tech_role:
        tags.append(f'<span class="job-card-tag job-card-tag-tech">{ICONS["tech_role"]} Tech Role</span>')
    else:
        tags.append(f'<span class="job-card-tag job-card-tag-nontech">{ICONS["non_tech"]} Non-Tech</span>')
    
    # Build skills
    skills_html = ""
    if is_tech_role and skills:
        skill_items = []
        for s in skills[:6]:
            skill_items.append(f'<span class="job-card-skill">{_escape_html(s)}</span>')
        if len(skills) > 6:
            skill_items.append(f'<span class="job-card-skill-more">+{len(skills) - 6} more</span>')
        if skill_items:
            skills_html = f'<div class="job-card-skills">{" ".join(skill_items)}</div>'
    
    # Build description - only show if there's description text
    desc_html = ""
    if description:
        desc_text = _escape_html(description[:180])
        if len(description) > 180:
            desc_text += "..."
        desc_html = f'<div class="job-card-description">{desc_text}</div>'
    
    # Build salary
    salary_html = ""
    if salary_min and salary_max:
        salary_html = f'<div class="job-card-salary-amount">{ICONS["salary"]} ${salary_min:,.0f} - ${salary_max:,.0f}</div><div class="job-card-salary-currency">{currency}</div>'
    elif salary_min:
        salary_html = f'<div class="job-card-salary-amount">{ICONS["salary"]} ${salary_min:,.0f}+</div><div class="job-card-salary-currency">{currency}</div>'
    
    # Build the card HTML
    salary_section = f'<div class="job-card-salary">{salary_html}</div>' if salary_html else ""
    
    card_html = f"""
<div style="margin-bottom: 0; width: 100%;">
<div class="job-card-modern">
    <div class="job-card-header">
        <div>
            <div class="job-card-title">{title}</div>
            <div class="job-card-company">{ICONS["company"]} {company}</div>
        </div>
        {salary_section}
    </div>
    <div class="job-card-meta">{" ".join(tags)}</div>
    {skills_html}
    {desc_html}
    <div class="job-card-footer">
        <span class="job-card-date">{ICONS["calendar"]} {date_display}</span>
    </div>
</div>
</div>
"""
    
    # Render the card using components.html
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ margin: 0; padding: 0; background: transparent; }}
            .job-card-modern {{
                background: #ffffff;
                border-radius: 16px;
                padding: 1.5rem 1.75rem;
                border: 1px solid #e9ecef;
                transition: all 0.25s cubic-bezier(0.25, 0.46, 0.45, 0.94);
                margin: 0 0 0.75rem 0;
                position: relative;
                overflow: hidden;
                width: 100%;
                box-sizing: border-box;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            }}
            .job-card-modern:hover {{
                border-color: {tech_color};
                box-shadow: 0 8px 40px rgba(108,92,231,0.08);
                transform: translateY(-2px);
            }}
            .job-card-modern::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                width: 4px;
                height: 100%;
                background: {tech_color if is_tech_role else '#dfe6e9'};
                border-radius: 0 2px 2px 0;
                opacity: 0.7;
            }}
            .job-card-header {{
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                gap: 1rem;
                flex-wrap: wrap;
            }}
            .job-card-title {{
                font-size: 1.15rem;
                font-weight: 600;
                color: #1a1a2e;
                margin: 0 0 0.25rem 0;
                letter-spacing: -0.01em;
            }}
            .job-card-company {{
                font-size: 0.95rem;
                color: #2d3436;
                font-weight: 500;
                display: flex;
                align-items: center;
                gap: 0.4rem;
            }}
            .job-card-company svg {{ flex-shrink: 0; }}
            .job-card-salary {{ text-align: right; flex-shrink: 0; }}
            .job-card-salary-amount {{
                font-size: 1rem;
                font-weight: 700;
                color: #1a1a2e;
                letter-spacing: -0.01em;
                display: flex;
                align-items: center;
                gap: 0.3rem;
                justify-content: flex-end;
            }}
            .job-card-salary-amount svg {{ flex-shrink: 0; }}
            .job-card-salary-currency {{
                font-size: 0.75rem;
                color: #636e72;
                font-weight: 400;
                text-align: right;
            }}
            .job-card-meta {{
                display: flex;
                flex-wrap: wrap;
                gap: 0.5rem 1rem;
                margin-top: 0.6rem;
                align-items: center;
            }}
            .job-card-tag {{
                display: inline-flex;
                align-items: center;
                gap: 0.3rem;
                padding: 0.25rem 0.75rem;
                border-radius: 20px;
                font-size: 0.7rem;
                font-weight: 500;
                letter-spacing: 0.01em;
                background: #f1f2f6;
                color: #2d3436;
                border: 1px solid #e9ecef;
                white-space: nowrap;
            }}
            .job-card-tag svg {{ flex-shrink: 0; }}
            .job-card-tag-tech {{
                background: rgba(108,92,231,0.10);
                color: #6c5ce7;
                border-color: rgba(108,92,231,0.15);
            }}
            .job-card-tag-nontech {{
                background: #f1f2f6;
                color: #636e72;
                border-color: #e9ecef;
            }}
            .job-card-tag-category {{
                background: rgba({int(tech_color[1:3], 16)}, {int(tech_color[3:5], 16)}, {int(tech_color[5:7], 16)}, 0.12);
                color: {tech_color};
                border-color: rgba({int(tech_color[1:3], 16)}, {int(tech_color[3:5], 16)}, {int(tech_color[5:7], 16)}, 0.15);
            }}
            .job-card-tag-country {{
                background: rgba(9, 132, 227, 0.08);
                color: #0984e3;
                border-color: rgba(9, 132, 227, 0.12);
            }}
            .job-card-tag-employment {{
                background: rgba(0, 184, 148, 0.08);
                color: #00b894;
                border-color: rgba(0, 184, 148, 0.12);
            }}
            .job-card-tag-language {{
                background: rgba(253, 203, 110, 0.15);
                color: #d4a017;
                border-color: rgba(253, 203, 110, 0.20);
            }}
            .job-card-skills {{
                display: flex;
                flex-wrap: wrap;
                gap: 0.35rem;
                margin-top: 0.6rem;
            }}
            .job-card-skill {{
                display: inline-block;
                padding: 0.1rem 0.6rem;
                border-radius: 12px;
                font-size: 0.7rem;
                font-weight: 500;
                background: #f1f2f6;
                color: #2d3436;
                border: 1px solid #e9ecef;
                transition: all 0.15s ease;
            }}
            .job-card-skill:hover {{
                background: {tech_color};
                color: white;
                border-color: {tech_color};
                transform: translateY(-1px);
            }}
            .job-card-skill-more {{
                display: inline-block;
                padding: 0.1rem 0.6rem;
                border-radius: 12px;
                font-size: 0.65rem;
                font-weight: 500;
                background: #f1f2f6;
                color: #636e72;
                border: 1px solid #e9ecef;
            }}
            .job-card-description {{
                color: #636e72;
                font-size: 0.85rem;
                line-height: 1.5;
                margin-top: 0.6rem;
                display: -webkit-box;
                -webkit-line-clamp: 2;
                -webkit-box-orient: vertical;
                overflow: hidden;
            }}
            .job-card-footer {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-top: 0.75rem;
                padding-top: 0.75rem;
                border-top: 1px solid #f1f2f6;
                flex-wrap: wrap;
                gap: 0.5rem;
            }}
            .job-card-date {{
                font-size: 0.75rem;
                color: #b2bec3;
                display: flex;
                align-items: center;
                gap: 0.3rem;
            }}
            .job-card-date svg {{ flex-shrink: 0; }}
            @media (max-width: 640px) {{
                .job-card-header {{ flex-direction: column; }}
                .job-card-salary {{ text-align: left; }}
                .job-card-salary-amount {{ justify-content: flex-start; }}
                .job-card-salary-currency {{ text-align: left; }}
                .job-card-meta {{ gap: 0.4rem; }}
            }}
        </style>
    </head>
    <body>
        {card_html}
    </body>
    </html>
    """
    
    components.html(full_html, height=210, scrolling=False)
    
    # ============================================================
    # View Details Button & Apply Button (Clean, hover animation)
    # ============================================================
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("👁️ View Details", key=f"view_{job.id}"):
            st.session_state.selected_job_id = str(job.id)
            st.rerun()
    with col2:
        if source_url:
            # Clean Apply button - no border, hover animation
            st.markdown(
                f'<a href="{source_url}" target="_blank" style="'
                'text-decoration: none; '
                'color: #6c5ce7; '
                'font-weight: 600; '
                'font-size: 0.9rem; '
                'padding: 0.4rem 0.8rem; '
                'border-radius: 6px; '
                'display: inline-block; '
                'transition: all 0.3s ease; '
                'background: transparent;'
                '" '
                'onmouseover="this.style.color=\'#5a4bd1\'; this.style.transform=\'translateY(-2px)\'; this.style.boxShadow=\'0 4px 12px rgba(108,92,231,0.2)\';" '
                'onmouseout="this.style.color=\'#6c5ce7\'; this.style.transform=\'translateY(0)\'; this.style.boxShadow=\'none\';" '
                '>🔗 Apply</a>',
                unsafe_allow_html=True
            )


def _render_css() -> None:
    """Render CSS styles for the parent page."""
    pass