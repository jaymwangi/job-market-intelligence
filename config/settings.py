from functools import lru_cache
from urllib.parse import quote_plus
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Supports both DATABASE_URL and individual database fields.
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

    # Server
    host: str = Field(default="0.0.0.0", description="Server host to bind to")
    port: int = Field(default=8000, description="Server port to bind to", ge=1, le=65535)

    # Security - Optional for development, required in production
    secret_key: str | None = Field(default=None)

    # Database - Support both DATABASE_URL and individual fields
    database_url: str | None = Field(default=None)
    database_host: str = Field(default="localhost")
    database_port: int = Field(default=5432)
    database_name: str = Field(default="job_market_intelligence")
    database_user: str = Field(default="postgres")
    database_password: str = Field(default="password")

    # Database Pool
    db_pool_size: int = Field(default=5, ge=1, le=50)
    db_max_overflow: int = Field(default=10, ge=0, le=100)
    db_pool_timeout: int = Field(default=30, ge=5)
    db_pool_pre_ping: bool = Field(default=True)

    # Adzuna API
    adzuna_base_url: str = Field(default="https://api.adzuna.com/v1/api")
    adzuna_app_id: str = Field(default="")
    adzuna_app_key: str = Field(default="")

    # ============================================================
    # Pipeline Configuration (Sprint 6.4 - 6.5)
    # ============================================================
    pipeline_results_per_page: int = Field(
        default=25,
        ge=1,
        le=50,
        description="Number of results per page when fetching jobs"
    )
    pipeline_max_pages: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of pages to fetch"
    )
    pipeline_retention_days: int = Field(
        default=90,
        ge=30,
        le=365,
        description="Number of days to retain jobs (based on scraped_date)"
    )

    # ============================================================
    # Sprint 6.6: Enrichment Configuration (Pure Configuration)
    # ============================================================
    
    # Geographic
    default_countries: List[str] = Field(
        default=["gb", "us", "de", "fr", "ca", "au"],
        description="Default countries to fetch jobs from"
    )
    
    # Analytics Filtering
    tech_only_analytics: bool = Field(
        default=True,
        description="Filter analytics to technology roles only"
    )
    
    # Salary Normalization (optional - off by default)
    normalize_salaries: bool = Field(
        default=False,
        description="Whether to normalize salaries to USD (requires exchange rates)"
    )
    
    # Technology Keywords (configurable, can be overridden via external file)
    tech_keywords: List[str] = Field(
        default=[
            # Programming Languages
            "python", "javascript", "typescript", "java", "go", "rust",
            "c++", "c#", "ruby", "php", "swift", "kotlin", "scala",
            # Frameworks & Libraries
            "react", "angular", "vue", "node", "django", "flask",
            "spring", "rails", "laravel", "fastapi", "nextjs",
            # Cloud & DevOps
            "aws", "azure", "gcp", "docker", "kubernetes",
            "terraform", "ansible", "jenkins", "gitlab",
            # Data & ML
            "sql", "postgresql", "mongodb", "redis", "elasticsearch",
            "kafka", "spark", "hadoop", "airflow", "dbt",
            "machine learning", "data science", "ai", "deep learning",
            "tensorflow", "pytorch", "nlp", "computer vision",
            # Frontend
            "html", "css", "sass", "tailwind", "bootstrap",
            # Backend
            "nginx", "apache", "gunicorn", "celery", "rabbitmq",
            "graphql", "rest", "api", "microservices"
        ],
        description="Keywords used for technology skill extraction"
    )
    
    # Path to external skill data (optional - overrides tech_keywords)
    skills_data_path: Optional[str] = Field(
        default=None,
        description="Path to external skills data file (JSON) - overrides tech_keywords"
    )

    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="standard")  # 'standard' or 'json'

    # API Configuration
    api_title: str = Field(default="Job Market Intelligence API")
    api_description: str = Field(
        default="REST API for technology job market analytics and insights."
    )
    api_version: str = Field(default="1.0.0")
    api_prefix: str = Field(default="/api/v1")
    allowed_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8501", "http://localhost:8000"]
    )

    @property
    def sqlalchemy_database_url(self) -> str:
        """Get SQLAlchemy database URL with proper driver."""
        if self.database_url:
            url = self.database_url

            # Handle various URL formats
            if url.startswith("postgres://"):
                return url.replace("postgres://", "postgresql+psycopg://", 1)
            elif url.startswith("postgresql://"):
                return url.replace("postgresql://", "postgresql+psycopg://", 1)
            elif url.startswith("postgresql+psycopg://"):
                return url
            else:
                # Assume it's a valid URL, add driver if needed
                return url

        # Build from individual fields
        encoded_password = quote_plus(self.database_password)
        return (
            f"postgresql+psycopg://"
            f"{self.database_user}:"
            f"{encoded_password}@"
            f"{self.database_host}:"
            f"{self.database_port}/"
            f"{self.database_name}"
        )

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    def validate_production(self) -> list[str]:
        """Validate production configuration, return list of errors."""
        if not self.is_production():
            return []

        errors = []

        if self.debug:
            errors.append("DEBUG must be False in production")

        if "*" in self.allowed_origins:
            errors.append("Wildcard CORS origins (*) not allowed in production")

        if self.secret_key in [None, "", "change-me", "change-me-in-production"]:
            errors.append("SECRET_KEY must be configured in production")

        if self.log_level.upper() == "DEBUG":
            errors.append("LOG_LEVEL DEBUG is not recommended in production")

        # Validate pipeline settings
        if self.pipeline_retention_days < 30 or self.pipeline_retention_days > 365:
            errors.append("pipeline_retention_days must be between 30 and 365")

        # Sprint 6.6: Validate enrichment settings
        if not self.default_countries:
            errors.append("default_countries cannot be empty")

        if self.tech_only_analytics and not self.tech_keywords:
            errors.append("tech_keywords cannot be empty when tech_only_analytics is True")

        return errors

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate that environment is one of the allowed values."""
        allowed = {"development", "staging", "production"}
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

    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        """Validate that log format is valid."""
        allowed = {"standard", "json"}
        if v.lower() not in allowed:
            raise ValueError(f"log_format must be one of {allowed}")
        return v.lower()

    @field_validator("database_port")
    @classmethod
    def validate_database_port(cls, v: int) -> int:
        """Validate that database port is in valid range."""
        if not (1 <= v <= 65535):
            raise ValueError("database_port must be between 1 and 65535")
        return v

    @field_validator("pipeline_results_per_page")
    @classmethod
    def validate_pipeline_results_per_page(cls, v: int) -> int:
        """Validate results per page is in valid range."""
        if not (1 <= v <= 50):
            raise ValueError("pipeline_results_per_page must be between 1 and 50")
        return v

    @field_validator("pipeline_max_pages")
    @classmethod
    def validate_pipeline_max_pages(cls, v: int) -> int:
        """Validate max pages is in valid range."""
        if not (1 <= v <= 20):
            raise ValueError("pipeline_max_pages must be between 1 and 20")
        return v

    @field_validator("pipeline_retention_days")
    @classmethod
    def validate_pipeline_retention_days(cls, v: int) -> int:
        """Validate retention days is in valid range."""
        if not (30 <= v <= 365):
            raise ValueError("pipeline_retention_days must be between 30 and 365")
        return v

    # ============================================================
    # Sprint 6.6: Field Validators
    # ============================================================
    
    @field_validator("default_countries")
    @classmethod
    def validate_default_countries(cls, v: List[str]) -> List[str]:
        """Validate that default countries is non-empty."""
        if not v:
            raise ValueError("default_countries cannot be empty")
        return [c.lower() for c in v]
    
    @field_validator("tech_keywords")
    @classmethod
    def validate_tech_keywords(cls, v: List[str]) -> List[str]:
        """Validate that tech keywords is non-empty."""
        if not v:
            raise ValueError("tech_keywords cannot be empty")
        return [kw.lower() for kw in v]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()