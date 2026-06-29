# config/settings.py
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra environment variables
    )

    # Application
    app_name: str = Field(default="Job Market Intelligence")
    environment: str = Field(default="development")
    debug: bool = Field(default=False)

    # Database - these will be loaded from .env
    database_host: str = Field(default="localhost")
    database_port: int = Field(default=5432)
    database_name: str = Field(default="job_market_intelligence")
    database_user: str = Field(default="postgres")
    database_password: str = Field(default="password")

    # Logging
    log_level: str = Field(default="INFO")

    @property
    def database_url(self) -> str:
        """Build database URL with properly encoded password."""
        # URL-encode the password to handle special characters (@, #, :, etc.)
        encoded_password = quote_plus(self.database_password)
        
        return (
            f"postgresql+psycopg://"
            f"{self.database_user}:"
            f"{encoded_password}@"
            f"{self.database_host}:"
            f"{self.database_port}/"
            f"{self.database_name}"
        )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()