import os
from dataclasses import dataclass

@dataclass
class Settings:
    """Application configuration."""
    
    # API Configuration
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000")
    API_TIMEOUT: int = int(os.getenv("API_TIMEOUT", "30"))
    
    # Application
    APP_TITLE: str = os.getenv("APP_TITLE", "Job Market Dashboard")
    APP_ICON: str = os.getenv("APP_ICON", "📊")

settings = Settings()