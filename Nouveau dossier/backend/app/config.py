"""Configuration applicative centralisée (Pydantic Settings).

Toute la config provient de variables d'environnement et est validée au démarrage.
Aucun secret en dur dans le code.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Paramètres applicatifs typés et validés."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Environnement ---
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # --- API ---
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_base_url: str = "http://localhost:8000"
    allowed_origins: str = "http://localhost:5173"

    # --- Sécurité ---
    secret_key: SecretStr
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 480
    jwt_refresh_token_expire_days: int = 30
    password_min_length: int = 12
    bcrypt_rounds: int = 12

    field_encryption_key: SecretStr
    pdf_signing_secret: SecretStr
    pdf_url_ttl_days: int = 7

    # --- BDD ---
    database_url: PostgresDsn

    # --- Redis ---
    redis_url: RedisDsn

    # --- Anthropic ---
    anthropic_api_key: SecretStr
    claude_model_expert: str = "claude-opus-4-7"
    claude_model_chat: str = "claude-sonnet-4-6"
    claude_max_tokens: int = 2000
    claude_temperature: float = Field(default=0.3, ge=0.0, le=1.0)
    claude_timeout_seconds: int = 30

    # --- Email ---
    email_provider: Literal["smtp", "sendgrid"] = "smtp"
    email_from: str = "noreply@nexusrh.ci"
    email_from_name: str = "NexusRH Diagnostix"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: SecretStr = SecretStr("")
    sendgrid_api_key: SecretStr = SecretStr("")

    # --- Stockage ---
    reports_storage_path: str = "/var/data/reports"
    reports_retention_days: int = 730

    # --- Rate limit ---
    ratelimit_public_per_minute: int = 60
    ratelimit_login_per_minute: int = 10
    ratelimit_admin_per_minute: int = 600

    # --- hCaptcha ---
    hcaptcha_site_key: str = ""
    hcaptcha_secret_key: SecretStr = SecretStr("")

    # --- Admin initial ---
    initial_admin_email: str = "admin@openlabconsulting.com"
    initial_admin_password: SecretStr = SecretStr("")

    # --- ML ---
    ml_models_path: str = "/app/ml_artifacts"
    ml_min_confidence: float = Field(default=0.60, ge=0.0, le=1.0)

    # --- Validations dérivées ---
    @field_validator("allowed_origins")
    @classmethod
    def _split_origins(cls, v: str) -> str:
        return v

    @property
    def cors_origins(self) -> list[str]:
        """Liste des origines CORS autorisées."""
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Singleton Settings (cache LRU).

    `lru_cache` garantit qu'on ne recharge pas l'environnement à chaque appel.
    """
    return Settings()  # type: ignore[call-arg]
