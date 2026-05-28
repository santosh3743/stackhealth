"""Application settings, loaded from environment variables / .env files."""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env.local", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- App ---
    env: str = Field(default="development")
    log_level: str = Field(default="INFO")
    cors_allowed_origins: str = Field(default="http://localhost:3000")

    # --- Database ---
    database_url: str

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"

    # --- GitHub ---
    github_token: str = ""

    # --- R2 ---
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket: str = "stackhealth-artifacts"
    r2_public_url: str = ""

    # --- Observability ---
    sentry_dsn: str = ""

    # --- Formula + scan limits ---
    formula_version: str = "v1.0"
    scan_wall_clock_timeout_seconds: int = 300
    clone_timeout_seconds: int = 30
    clone_size_limit_mb: int = 500
    rate_limit_scans_per_ip_per_hour: int = 5

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
