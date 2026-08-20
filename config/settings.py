from enum import StrEnum
from functools import lru_cache
from urllib.parse import quote_plus

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# ============================================================
# Enums for type-safe configuration
# ============================================================


class Environment(StrEnum):
    """Application environments."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(StrEnum):
    """Log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(StrEnum):
    """Log output formats."""

    STANDARD = "standard"
    JSON = "json"


class TranslationProvider(StrEnum):
    """Supported translation providers."""

    GOOGLE = "google"  # Development/demo only
    DEEPL = "deepl"  # Production-ready
    AZURE = "azure"  # Production-ready
    MOCK = "mock"  # Testing


# ============================================================
# Mixin Classes (Using BaseModel for configuration sections)
# ============================================================


class ApplicationSettings(BaseModel):
    """Application configuration."""

    app_name: str = Field(default="Job Market Intelligence")
    environment: Environment = Field(default=Environment.DEVELOPMENT)
    debug: bool = Field(default=False)

    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION

    @property
    def is_development(self) -> bool:
        return self.environment == Environment.DEVELOPMENT

    @property
    def is_staging(self) -> bool:
        return self.environment == Environment.STAGING


class ServerSettings(BaseModel):
    """Server configuration."""

    host: str = Field(default="0.0.0.0", description="Server host to bind to")
    port: int = Field(default=8000, description="Server port to bind to", ge=1, le=65535)


class SecuritySettings(BaseModel):
    """Security configuration."""

    secret_key: str | None = Field(
        default=None, description="Secret key for JWT and sessions. Required in production."
    )


class DatabaseSettings(BaseModel):
    """Database configuration."""

    # Support both DATABASE_URL and individual fields
    database_url: str | None = Field(default=None)
    database_host: str = Field(default="localhost")
    database_port: int = Field(default=5432)
    database_name: str = Field(default="job_market_intelligence")
    database_user: str = Field(default="postgres")
    database_password: str = Field(default="password")

    # Connection pool
    db_pool_size: int = Field(default=5, ge=1, le=50)
    db_max_overflow: int = Field(default=10, ge=0, le=100)
    db_pool_timeout: int = Field(default=30, ge=5)
    db_pool_pre_ping: bool = Field(default=True)

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


class LoggingSettings(BaseModel):
    """Logging configuration."""

    log_level: LogLevel = Field(default=LogLevel.INFO)
    log_format: LogFormat = Field(default=LogFormat.STANDARD)

    @property
    def structured_logging(self) -> bool:
        """Enable structured logging when format is JSON."""
        return self.log_format == LogFormat.JSON


class APISettings(BaseModel):
    """API configuration."""

    api_title: str = Field(default="Job Market Intelligence API")
    api_description: str = Field(
        default="REST API for technology job market analytics and insights."
    )
    api_version: str = Field(default="1.0.0")
    api_prefix: str = Field(default="/api/v1")
    allowed_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8501", "http://localhost:8000"]
    )


class AdzunaSettings(BaseModel):
    """Adzuna API configuration."""

    adzuna_base_url: str = Field(default="https://api.adzuna.com/v1/api")
    adzuna_app_id: str = Field(default="")
    adzuna_app_key: str = Field(default="")


class PipelineSettings(BaseModel):
    """ETL pipeline configuration."""

    etl_timeout_minutes: int = Field(
        default=240, ge=1, description="Maximum ETL pipeline runtime in minutes"
    )

    pipeline_results_per_page: int = Field(
        default=25, ge=1, le=50, description="Number of results per page when fetching jobs"
    )
    pipeline_max_pages: int = Field(
        default=5, ge=1, le=20, description="Maximum number of pages to fetch"
    )
    pipeline_retention_days: int = Field(
        default=90,
        ge=30,
        le=365,
        description="Number of days to retain jobs (based on scraped_date)",
    )


class LanguageSettings(BaseModel):
    """Language detection configuration."""

    language_detection_enabled: bool = Field(
        default=True, description="Enable language detection during ETL"
    )
    default_language: str = Field(
        default="en",
        description="Default language code (ISO 639-1) for jobs without detected language",
    )


class TranslationSettings(BaseModel):
    """Translation configuration."""

    translation_provider: TranslationProvider = Field(
        default=TranslationProvider.GOOGLE, description="Translation provider"
    )
    translation_timeout: int = Field(
        default=15, ge=5, le=60, description="Translation API timeout in seconds"
    )

    # DeepL
    deepl_api_key: str | None = Field(
        default=None, description="DeepL API key for production translation"
    )

    # Azure Translator
    azure_translator_key: str | None = Field(default=None, description="Azure Translator API key")
    azure_translator_endpoint: str | None = Field(
        default=None, description="Azure Translator endpoint"
    )
    azure_translator_region: str | None = Field(default=None, description="Azure Translator region")

    # Google Cloud Translation
    google_cloud_project: str | None = Field(default=None, description="Google Cloud project ID")
    google_application_credentials: str | None = Field(
        default=None, description="Path to Google Cloud service account key JSON"
    )

    @property
    def translation_enabled(self) -> bool:
        """Check if translation is enabled."""
        return self.translation_provider != TranslationProvider.MOCK


class TechClassificationSettings(BaseModel):
    """Technology classification configuration."""

    tech_classification_enabled: bool = Field(
        default=True, description="Enable technology classification during ETL"
    )
    tech_classification_config_path: str = Field(
        default="config/tech_classification.yaml",
        description="Path to technology classification YAML config",
    )
    tech_only_analytics: bool = Field(
        default=True, description="Filter analytics to technology roles only"
    )
    tech_classification_min_confidence: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for tech classification",
    )


class GeographicSettings(BaseModel):
    """Geographic configuration."""

    default_countries: list[str] = Field(
        default=["gb", "us", "de", "fr", "ca", "au"],
        description="Default countries to fetch jobs from (ISO 3166-1 alpha-2)",
    )


class FeatureFlags(BaseModel):
    """Feature flags for optional functionality."""

    feature_enable_translation: bool = Field(default=True, description="Enable translation feature")
    feature_enable_tech_classification: bool = Field(
        default=True, description="Enable technology classification feature"
    )
    feature_enable_multi_country: bool = Field(
        default=True, description="Enable multi-country ingestion"
    )
    feature_enable_language_filter: bool = Field(
        default=True, description="Enable language filtering in dashboard"
    )


class AcquisitionSettings(BaseModel):
    """Acquisition strategy configuration for balanced dataset collection."""

    # ------------------------------------------------------------------
    # Core acquisition controls
    # ------------------------------------------------------------------
    acquisition_enabled: bool = Field(
        default=True, description="Enable balanced acquisition strategy"
    )
    acquisition_target_tech_ratio: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Target ratio of tech jobs in acquired dataset"
    )
    acquisition_use_category_filter: bool = Field(
        default=True, description="Use 'it-jobs' category for tech queries"
    )

    # ------------------------------------------------------------------
    # Per-run limits (used by adaptive acquisition)
    # ------------------------------------------------------------------
    acquisition_max_jobs_per_run: int = Field(
        default=2000,
        ge=100,
        le=10000,
        description="Maximum jobs to acquire per pipeline run (adaptive mode)",
    )
    acquisition_batch_size: int = Field(
        default=100,
        ge=10,
        le=500,
        description="Number of jobs to process per batch before updating controller",
    )
    acquisition_max_queries_per_country: int = Field(
        default=25, ge=1, le=100, description="Maximum queries per country per run"
    )
    acquisition_parity_tolerance: float = Field(
        default=0.05, ge=0.0, le=0.10, description="Tolerance for balanced check (±5%)"
    )

    # ------------------------------------------------------------------
    # Legacy / total limit (kept for backward compatibility)
    # ------------------------------------------------------------------
    acquisition_max_jobs_total: int = Field(
        default=10000,
        ge=100,
        le=100000,
        description="[Deprecated] Maximum total jobs to acquire across all runs",
    )

    # ------------------------------------------------------------------
    # Query lists
    # ------------------------------------------------------------------
    acquisition_broad_queries: list[str] = Field(
        default=[
            "nurse",
            "doctor",
            "healthcare",
            "medical",
            "teacher",
            "professor",
            "educator",
            "retail",
            "cashier",
            "customer service",
            "barista",
            "driver",
            "delivery",
            "logistics",
            "construction",
            "electrician",
            "plumber",
            "carpenter",
            "mechanic",
            "accountant",
            "administrative",
            "receptionist",
            "clerk",
            "chef",
            "hospitality",
            "hotel",
        ],
        description="Broad query terms for non-tech jobs",
    )
    acquisition_tech_queries: list[str] = Field(
        default=[
            "software engineer",
            "software developer",
            "backend developer",
            "frontend developer",
            "full stack developer",
            "devops engineer",
            "site reliability engineer",
            "data scientist",
            "data engineer",
            "data analyst",
            "machine learning engineer",
            "ai engineer",
            "cloud engineer",
            "cloud architect",
            "security engineer",
            "network engineer",
            "systems administrator",
            "ios developer",
            "android developer",
            "mobile developer",
            "qa engineer",
            "test automation engineer",
            "quality assurance",
            "game developer",
            "unity developer",
            "unreal developer",
            "embedded engineer",
            "firmware engineer",
            "iot engineer",
            "blockchain developer",
            "web3 developer",
            "smart contract developer",
        ],
        description="Tech query terms for IT jobs",
    )


# ============================================================
# Combined Settings Class
# ============================================================


class Settings(
    ApplicationSettings,
    ServerSettings,
    SecuritySettings,
    DatabaseSettings,
    LoggingSettings,
    APISettings,
    AdzunaSettings,
    PipelineSettings,
    LanguageSettings,
    TranslationSettings,
    TechClassificationSettings,
    GeographicSettings,
    FeatureFlags,
    AcquisitionSettings,
    BaseSettings,
):
    """
    Application settings loaded from environment variables.

    Inherits from multiple mixin classes for clean organization.
    Supports both DATABASE_URL and individual database fields.
    """

    # Use SettingsConfigDict from pydantic_settings
    # This resolves the type conflict between BaseModel.ConfigDict and BaseSettings.SettingsConfigDict
    model_config: SettingsConfigDict = SettingsConfigDict(  # type: ignore[assignment]
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ============================================================
    # Validators
    # ============================================================

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

    @field_validator("default_language")
    @classmethod
    def validate_default_language(cls, v: str) -> str:
        """Validate default language is a valid ISO 639-1 code (2 letters)."""
        if len(v) != 2 or not v.isalpha():
            raise ValueError("default_language must be a valid ISO 639-1 code (2 letters)")
        return v.lower()

    @field_validator("default_countries")
    @classmethod
    def validate_default_countries(cls, v: list[str]) -> list[str]:
        """Validate that default countries are valid ISO 3166-1 alpha-2 codes."""
        if not v:
            raise ValueError("default_countries cannot be empty")
        for country in v:
            if len(country) != 2 or not country.isalpha():
                raise ValueError(f"Invalid country code: {country}. Must be ISO 3166-1 alpha-2")
        return [c.lower() for c in v]

    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        """Validate that log format is valid."""
        allowed = {"standard", "json"}
        if v.lower() not in allowed:
            raise ValueError(f"log_format must be one of {allowed}")
        return v.lower()

    @field_validator("tech_classification_min_confidence")
    @classmethod
    def validate_tech_min_confidence(cls, v: float) -> float:
        """Validate confidence threshold is in valid range."""
        if not (0.0 <= v <= 1.0):
            raise ValueError("tech_classification_min_confidence must be between 0.0 and 1.0")
        return v

    # Acquisition validators
    @field_validator("acquisition_target_tech_ratio")
    @classmethod
    def validate_acquisition_target_tech_ratio(cls, v: float) -> float:
        """Validate target tech ratio is in valid range."""
        if not (0.0 <= v <= 1.0):
            raise ValueError("acquisition_target_tech_ratio must be between 0.0 and 1.0")
        return v

    @field_validator("acquisition_max_jobs_per_run")
    @classmethod
    def validate_acquisition_max_jobs_per_run(cls, v: int) -> int:
        """Validate max jobs per run is in valid range."""
        if not (100 <= v <= 10000):
            raise ValueError("acquisition_max_jobs_per_run must be between 100 and 10000")
        return v

    @field_validator("acquisition_batch_size")
    @classmethod
    def validate_acquisition_batch_size(cls, v: int) -> int:
        """Validate batch size is in valid range."""
        if not (10 <= v <= 500):
            raise ValueError("acquisition_batch_size must be between 10 and 500")
        return v

    @field_validator("acquisition_max_queries_per_country")
    @classmethod
    def validate_acquisition_max_queries_per_country(cls, v: int) -> int:
        """Validate max queries per country is in valid range."""
        if not (1 <= v <= 100):
            raise ValueError("acquisition_max_queries_per_country must be between 1 and 100")
        return v

    @field_validator("acquisition_parity_tolerance")
    @classmethod
    def validate_acquisition_parity_tolerance(cls, v: float) -> float:
        """Validate parity tolerance is in valid range."""
        if not (0.0 <= v <= 0.10):
            raise ValueError("acquisition_parity_tolerance must be between 0.0 and 0.10")
        return v

    @field_validator("acquisition_max_jobs_total")
    @classmethod
    def validate_acquisition_max_jobs_total(cls, v: int) -> int:
        """Validate max jobs total is in valid range."""
        if not (100 <= v <= 100000):
            raise ValueError("acquisition_max_jobs_total must be between 100 and 100000")
        return v

    @field_validator("acquisition_broad_queries", "acquisition_tech_queries")
    @classmethod
    def validate_acquisition_queries_not_empty(cls, v: list[str]) -> list[str]:
        """Validate that query lists are not empty when acquisition is enabled."""
        if not v:
            raise ValueError("Acquisition query list cannot be empty")
        return v

    # ============================================================
    # Production Validation
    # ============================================================

    def validate_production(self) -> list[str]:
        """Validate production configuration, return list of errors."""
        if not self.is_production:
            return []

        errors = []

        if self.debug:
            errors.append("DEBUG must be False in production")

        if "*" in self.allowed_origins:
            errors.append("Wildcard CORS origins (*) not allowed in production")

        if self.secret_key in [None, "", "change-me", "change-me-in-production"]:
            errors.append("SECRET_KEY must be configured in production")

        if self.log_level == LogLevel.DEBUG:
            errors.append("LOG_LEVEL DEBUG is not recommended in production")

        # Validate pipeline settings
        if self.pipeline_retention_days < 30 or self.pipeline_retention_days > 365:
            errors.append("pipeline_retention_days must be between 30 and 365")

        # Validate default countries
        if not self.default_countries:
            errors.append("default_countries cannot be empty")

        # Validate translation provider in production
        if self.translation_provider == TranslationProvider.GOOGLE:
            errors.append(
                "TRANSLATION_PROVIDER=google (googletrans) is not recommended in production. "
                "Use deepl, azure, or configure a production provider."
            )

        if self.translation_provider == TranslationProvider.DEEPL and not self.deepl_api_key:
            errors.append("DEEPL_API_KEY is required when using DeepL in production")

        if self.translation_provider == TranslationProvider.AZURE:
            if not self.azure_translator_key:
                errors.append("AZURE_TRANSLATOR_KEY is required when using Azure in production")
            if not self.azure_translator_endpoint:
                errors.append(
                    "AZURE_TRANSLATOR_ENDPOINT is required when using Azure in production"
                )

        # Validate acquisition settings in production
        if self.acquisition_enabled:
            if not self.acquisition_broad_queries:
                errors.append("ACQUISITION_BROAD_QUERIES cannot be empty in production")
            if not self.acquisition_tech_queries:
                errors.append("ACQUISITION_TECH_QUERIES cannot be empty in production")
            if self.acquisition_target_tech_ratio < 0.1 or self.acquisition_target_tech_ratio > 0.9:
                errors.append(
                    f"ACQUISITION_TARGET_TECH_RATIO={self.acquisition_target_tech_ratio} "
                    "should be between 0.1 and 0.9 in production"
                )
            # Additional production checks for new fields
            if self.acquisition_max_jobs_per_run < 500:
                errors.append(
                    f"acquisition_max_jobs_per_run={self.acquisition_max_jobs_per_run} "
                    "should be at least 500 in production to reduce overhead"
                )
            if self.acquisition_batch_size > 200:
                errors.append(
                    f"acquisition_batch_size={self.acquisition_batch_size} "
                    "should be <= 200 in production to ensure timely feedback"
                )

        return errors


# ============================================================
# Singleton Instance
# ============================================================


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
