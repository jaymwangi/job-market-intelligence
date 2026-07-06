# dashboard/core/config.py
"""Dashboard configuration."""

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass
class DashboardConfig:
    """Dashboard configuration settings."""

    # ===== App Settings =====
    app_title: str = os.getenv("APP_TITLE", "Job Market Dashboard")
    app_icon: str = os.getenv("APP_ICON", "📊")
    dashboard_title: str = os.getenv(
        "DASHBOARD_TITLE", "Job Market Intelligence Dashboard"
    )
    debug_mode: bool = os.getenv("DEBUG", "False").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # ===== API Configuration =====
    api_base_url: str = os.getenv("API_BASE_URL", "http://localhost:8000")
    api_timeout: int = int(os.getenv("API_TIMEOUT", "30"))
    api_retries: int = int(os.getenv("API_RETRIES", "3"))

    # ===== Cache Configuration =====
    enable_cache: bool = os.getenv("ENABLE_CACHE", "True").lower() == "true"
    cache_ttl_default: int = int(os.getenv("CACHE_TTL_DEFAULT", "300"))
    cache_max_size: int = int(os.getenv("CACHE_MAX_SIZE", "100"))

    # Cache TTLs per endpoint (in seconds)
    cache_ttl_dashboard_summary: int = int(
        os.getenv("CACHE_TTL_DASHBOARD_SUMMARY", "300")
    )
    cache_ttl_top_skills: int = int(os.getenv("CACHE_TTL_TOP_SKILLS", "600"))
    cache_ttl_top_companies: int = int(os.getenv("CACHE_TTL_TOP_COMPANIES", "600"))
    cache_ttl_jobs_by_location: int = int(
        os.getenv("CACHE_TTL_JOBS_BY_LOCATION", "600")
    )
    cache_ttl_salary_statistics: int = int(
        os.getenv("CACHE_TTL_SALARY_STATISTICS", "900")
    )
    cache_ttl_salary_distribution: int = int(
        os.getenv("CACHE_TTL_SALARY_DISTRIBUTION", "900")
    )
    cache_ttl_employment_types: int = int(
        os.getenv("CACHE_TTL_EMPLOYMENT_TYPES", "600")
    )
    cache_ttl_posting_trend: int = int(os.getenv("CACHE_TTL_POSTING_TREND", "300"))
    cache_ttl_recent_jobs: int = int(os.getenv("CACHE_TTL_RECENT_JOBS", "300"))

    # ===== Pagination =====
    default_page_size: int = int(os.getenv("DEFAULT_PAGE_SIZE", "20"))
    max_page_size: int = int(os.getenv("MAX_PAGE_SIZE", "100"))

    # ===== Chart Configuration =====
    chart_height: int = int(os.getenv("CHART_HEIGHT", "400"))
    chart_theme: str = os.getenv("CHART_THEME", "plotly_white")
    chart_font_family: str = os.getenv("CHART_FONT_FAMILY", "Inter, sans-serif")

    # Chart colors
    chart_color_primary: str = os.getenv("CHART_COLOR_PRIMARY", "#0f3460")
    chart_color_secondary: str = os.getenv("CHART_COLOR_SECONDARY", "#e94560")
    chart_color_success: str = os.getenv("CHART_COLOR_SUCCESS", "#00b894")
    chart_color_warning: str = os.getenv("CHART_COLOR_WARNING", "#fdcb6e")
    chart_color_info: str = os.getenv("CHART_COLOR_INFO", "#0984e3")

    # ===== Analytics Configuration =====
    default_top_skills_limit: int = int(os.getenv("DEFAULT_TOP_SKILLS_LIMIT", "15"))
    default_top_companies_limit: int = int(
        os.getenv("DEFAULT_TOP_COMPANIES_LIMIT", "15")
    )
    default_top_locations_limit: int = int(
        os.getenv("DEFAULT_TOP_LOCATIONS_LIMIT", "15")
    )
    default_posting_trend_days: int = int(os.getenv("DEFAULT_POSTING_TREND_DAYS", "30"))

    # ===== Feature Flags =====
    enable_analytics: bool = os.getenv("ENABLE_ANALYTICS", "True").lower() == "true"

    # ===== Color Palette =====
    @property
    def colors(self) -> dict:
        """Professional color palette."""
        return {
            "primary": "#1a1a2e",
            "secondary": "#16213e",
            "accent": self.chart_color_primary,
            "highlight": self.chart_color_secondary,
            "success": self.chart_color_success,
            "warning": self.chart_color_warning,
            "info": self.chart_color_info,
            "background": "#f8f9fa",
            "card_bg": "#ffffff",
            "text": "#2d3436",
            "text_light": "#636e72",
            "border": "#e9ecef",
        }

    # ===== Backward Compatibility Aliases =====
    @property
    def API_BASE_URL(self) -> str:
        """Backward compatibility alias for api_base_url."""
        return self.api_base_url

    @property
    def API_TIMEOUT(self) -> int:
        """Backward compatibility alias for api_timeout."""
        return self.api_timeout

    @property
    def APP_TITLE(self) -> str:
        """Backward compatibility alias for app_title."""
        return self.app_title

    @property
    def APP_ICON(self) -> str:
        """Backward compatibility alias for app_icon."""
        return self.app_icon

    @property
    def CACHE_TTL(self) -> int:
        """Backward compatibility alias for cache_ttl_default."""
        return self.cache_ttl_default


# ===== Singleton Instance =====
_config: Optional[DashboardConfig] = None


def get_config() -> DashboardConfig:
    """Get dashboard configuration singleton."""
    global _config
    if _config is None:
        _config = DashboardConfig()
    return _config


# Create a settings instance for backward compatibility
settings = get_config()
