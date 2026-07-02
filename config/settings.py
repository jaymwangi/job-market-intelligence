# config/settings.py
from functools import lru_cache
from urllib.parse import quote_plus
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="Job Market Intelligence")
    environment: str = Field(default="development")
    debug: bool = Field(default=False)

    # Database
    database_host: str = Field(default="localhost")
    database_port: int = Field(default=5432)
    database_name: str = Field(default="job_market_intelligence")
    database_user: str = Field(default="postgres")
    database_password: str = Field(default="password")

    # Adzuna API
    adzuna_base_url: str = Field(default="https://api.adzuna.com/v1/api")
    adzuna_app_id: str = Field(default="")
    adzuna_app_key: str = Field(default="")

    # Logging
    log_level: str = Field(default="INFO")
    
    # API Configuration
    api_title: str = Field(default="Job Market Intelligence API")
    api_description: str = Field(
        default="REST API for technology job market analytics and insights."
    )
    api_version: str = Field(default="1.0.0")
    api_prefix: str = Field(default="/api/v1")
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8501", "http://localhost:8000"]
    )

    @property
    def database_url(self) -> str:
        """Build database URL with properly encoded password."""
        encoded_password = quote_plus(self.database_password)
        return (
            f"postgresql+psycopg://"
            f"{self.database_user}:"
            f"{encoded_password}@"
            f"{self.database_host}:"
            f"{self.database_port}/"
            f"{self.database_name}"
        )

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate that environment is one of the allowed values."""
        allowed = {"development", "testing", "production"}
        if v not in allowed:
            raise ValueError(f"environment must be one of {allowed}")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate that log level is valid."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return v.upper()

    @field_validator("database_port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Validate that database port is in valid range."""
        if not (1 <= v <= 65535):
            raise ValueError("database_port must be between 1 and 65535")
        return v


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()