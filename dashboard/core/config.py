# dashboard/core/config.py
"""Dashboard configuration."""
import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class DashboardConfig:
    """Dashboard configuration settings."""
    
    # API Configuration
    api_base_url: str = os.getenv("API_BASE_URL", "http://localhost:8000")
    api_timeout: int = int(os.getenv("API_TIMEOUT", "30"))
    api_retries: int = int(os.getenv("API_RETRIES", "3"))
    
    # Cache Configuration
    cache_ttl_default: int = int(os.getenv("CACHE_TTL_DEFAULT", "300"))
    cache_max_size: int = int(os.getenv("CACHE_MAX_SIZE", "100"))
    
    # Dashboard Configuration
    dashboard_title: str = os.getenv("DASHBOARD_TITLE", "Job Market Intelligence Dashboard")
    app_title: str = os.getenv("APP_TITLE", "Job Market Dashboard")
    app_icon: str = os.getenv("APP_ICON", "📊")
    debug_mode: bool = os.getenv("DEBUG", "False").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Feature Flags
    enable_cache: bool = os.getenv("ENABLE_CACHE", "True").lower() == "true"
    enable_analytics: bool = os.getenv("ENABLE_ANALYTICS", "True").lower() == "true"
    
    # Backward compatibility aliases
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


_config: Optional[DashboardConfig] = None


def get_config() -> DashboardConfig:
    """Get dashboard configuration singleton."""
    global _config
    if _config is None:
        _config = DashboardConfig()
    return _config


# Create a settings instance for backward compatibility
settings = get_config()