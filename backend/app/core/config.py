"""
Centralised application configuration.

All environment variables are loaded here via Pydantic Settings.
No other module should read os.environ directly — always import `settings`.

Usage:
    from app.core.config import settings
    print(settings.app_name)
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Required variables must be set before the application starts.
    Secret values are NEVER echoed back through any API response.
    """

    model_config = SettingsConfigDict(
        env_file=[str(_BACKEND_DIR / ".env"), ".env"],
        env_file_encoding="utf-8",
        case_sensitive=False,
        # Ignore extra env vars that don't map to fields
        extra="ignore",
    )

    # ------------------------------------------------------------------ #
    # Application metadata                                                 #
    # ------------------------------------------------------------------ #
    APP_NAME: str = "TrustGuard AI"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"  # development | staging | production
    APP_DEBUG: bool = True  # Set False in production

    # ------------------------------------------------------------------ #
    # API routing                                                          #
    # ------------------------------------------------------------------ #
    API_V1_PREFIX: str = "/api/v1"

    # ------------------------------------------------------------------ #
    # Server                                                               #
    # ------------------------------------------------------------------ #
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ------------------------------------------------------------------ #
    # CORS — frontend origins allowed to call this API                     #
    # Comma-separated string in env; parsed into a list below.            #
    # ------------------------------------------------------------------ #
    FRONTEND_URL: str = "http://localhost:5173"

    @property
    def primary_frontend_url(self) -> str:
        """
        Returns the primary frontend base URL (single URL),
        even if FRONTEND_URL is configured as a comma-separated list of origins.
        """
        origins = [o.strip() for o in self.FRONTEND_URL.split(",") if o.strip()]
        return origins[0] if origins else "http://localhost:5173"

    @property
    def cors_origins(self) -> List[str]:
        """
        Returns a deduplicated list of allowed CORS origins.

        In development both localhost:5173 (Vite default) and
        localhost:3000 (CRA default) are allowed so any team member
        can run the frontend without touching this config.
        """
        origins = [o.strip() for o in self.FRONTEND_URL.split(",") if o.strip()]
        # Always allow local dev origins so team members are unblocked
        if self.APP_ENV != "production":
            dev_origins = [
                "http://localhost:5173",
                "http://localhost:3000",
                "http://127.0.0.1:5173",
                "http://127.0.0.1:3000",
            ]
            for o in dev_origins:
                if o not in origins:
                    origins.append(o)
        return origins

    # ------------------------------------------------------------------ #
    # Supabase credentials  (NEVER expose via API)                         #
    # ------------------------------------------------------------------ #
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""  # Backend-only; never sent to frontend
    SUPABASE_JWT_SECRET: str = ""  # Used to verify Supabase-issued JWTs

    # ------------------------------------------------------------------ #
    # Google OAuth credentials (NEVER expose secret via API)             #
    # ------------------------------------------------------------------ #
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # ------------------------------------------------------------------ #
    # Threat intelligence API keys  (NEVER expose via API)                 #
    # ------------------------------------------------------------------ #
    VIRUSTOTAL_API_KEY: str = ""
    VIRUSTOTAL_BASE_URL: str = "https://www.virustotal.com/api/v3"
    VIRUSTOTAL_CACHE_TTL_SECONDS: int = 3600
    # URLhaus does not require an API key — query is public

    # ------------------------------------------------------------------ #
    # Machine Learning & AI Settings                                       #
    # ------------------------------------------------------------------ #
    ML_MODEL_PATH: str = "ml/models/phishing_rf_v1.joblib"
    ML_METADATA_PATH: str = "ml/models/model_metadata.json"
    ML_METRICS_PATH: str = "ml/models/metrics.json"
    ML_THRESHOLD_LEGITIMATE: float = 0.30
    ML_THRESHOLD_PHISHING: float = 0.70

    # ------------------------------------------------------------------ #
    # SSL/TLS Certificate Validation Settings                              #
    # ------------------------------------------------------------------ #
    SSL_CONNECTION_TIMEOUT: float = 5.0
    SSL_CACHE_TTL_SECONDS: int = 1800
    SSL_EXPIRING_SOON_DAYS: int = 30

    # ------------------------------------------------------------------ #
    # Digital Trust Score & Risk Assessment Settings                       #
    # ------------------------------------------------------------------ #
    SCORING_VERSION: str = "v1.0.0"
    WEIGHT_VIRUSTOTAL: float = 0.40
    WEIGHT_ML_PHISHING: float = 0.30
    WEIGHT_URL_HEURISTICS: float = 0.15
    WEIGHT_SSL_TLS: float = 0.15
    TRUST_SCORE_LOW_RISK_MIN: int = 80
    TRUST_SCORE_MODERATE_RISK_MIN: int = 60
    TRUST_SCORE_HIGH_RISK_MIN: int = 30
    MIN_COVERAGE_FOR_ASSESSMENT: float = 0.45

    # ------------------------------------------------------------------ #
    # Rate limiting                                                        #
    # ------------------------------------------------------------------ #
    RATE_LIMIT_SCAN: str = "5/minute"  # Applied to POST /api/v1/scan
    RATE_LIMIT_GLOBAL: str = "60/minute"  # Applied to all other endpoints

    # ------------------------------------------------------------------ #
    # HTTP client settings (used by all outbound async requests)           #
    # ------------------------------------------------------------------ #
    HTTP_TIMEOUT_SECONDS: float = 10.0  # Hard timeout for all outbound HTTP calls
    HTTP_MAX_REDIRECTS: int = 0  # Never follow redirects (SSRF mitigation)

    # ------------------------------------------------------------------ #
    # Input constraints                                                    #
    # ------------------------------------------------------------------ #
    URL_MAX_LENGTH: int = 2048  # Maximum submitted URL length in characters

    # ------------------------------------------------------------------ #
    # Computed / derived helpers                                           #
    # ------------------------------------------------------------------ #
    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def supabase_configured(self) -> bool:
        """True when all Supabase credentials are valid (non-empty and not default placeholders)."""
        return bool(
            self.SUPABASE_URL
            and not self.SUPABASE_URL.startswith("https://your-project")
            and self.SUPABASE_ANON_KEY
            and not self.SUPABASE_ANON_KEY.startswith("your-")
            and self.SUPABASE_SERVICE_ROLE_KEY
            and not self.SUPABASE_SERVICE_ROLE_KEY.startswith("your-")
        )

    @property
    def virustotal_configured(self) -> bool:
        """True when the VirusTotal API key is valid (non-empty and not default placeholders)."""
        return bool(self.VIRUSTOTAL_API_KEY and not self.VIRUSTOTAL_API_KEY.startswith("your-"))

    @property
    def google_oauth_configured(self) -> bool:
        """True when Google OAuth client credentials are populated."""
        return bool(
            self.GOOGLE_CLIENT_ID
            and not self.GOOGLE_CLIENT_ID.startswith("your-")
            and self.GOOGLE_CLIENT_SECRET
            and not self.GOOGLE_CLIENT_SECRET.startswith("your-")
        )

    # ------------------------------------------------------------------ #
    # Validators                                                           #
    # ------------------------------------------------------------------ #
    @field_validator("APP_ENV")
    @classmethod
    def validate_app_env(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"APP_ENV must be one of {allowed}, got '{v}'")
        return v

    @field_validator("PORT")
    @classmethod
    def validate_port(cls, v: int) -> int:
        if not (1 <= v <= 65535):
            raise ValueError(f"PORT must be between 1 and 65535, got {v}")
        return v

    @model_validator(mode="after")
    def warn_missing_credentials(self) -> "Settings":
        """
        In production, fail fast if critical credentials are absent.
        In development, log a warning so developers know what to configure.
        """
        import logging

        log = logging.getLogger(__name__)

        if self.APP_ENV == "production":
            missing: list[str] = []
            if not self.SUPABASE_URL:
                missing.append("SUPABASE_URL")
            if not self.SUPABASE_ANON_KEY:
                missing.append("SUPABASE_ANON_KEY")
            if not self.SUPABASE_SERVICE_ROLE_KEY:
                missing.append("SUPABASE_SERVICE_ROLE_KEY")
            if not self.VIRUSTOTAL_API_KEY:
                missing.append("VIRUSTOTAL_API_KEY")
            if missing:
                raise ValueError(
                    f"Production startup failed — missing required environment variables: "
                    f"{', '.join(missing)}"
                )
        else:
            if not self.SUPABASE_URL:
                log.warning(
                    "SUPABASE_URL is not set — database operations will fail. "
                    "Copy .env.example to .env and fill in your Supabase credentials."
                )
            if not self.VIRUSTOTAL_API_KEY:
                log.warning(
                    "VIRUSTOTAL_API_KEY is not set — VirusTotal analysis will return UNKNOWN."
                )
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Returns a cached singleton Settings instance.

    Use this throughout the application:
        from app.core.config import get_settings
        settings = get_settings()

    The @lru_cache ensures the .env file is read exactly once at startup.
    """
    return Settings()


# Module-level convenience alias — import this in other modules
settings: Settings = get_settings()
