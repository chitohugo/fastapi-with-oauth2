import os
from functools import lru_cache
from typing import List

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment / `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    env: str = Field(default="dev", validation_alias=AliasChoices("ENV"))
    api: str = "/api"
    prefix: str = "/api/v1"
    project_name: str = "BoilerPlate"

    datetime_format: str = "%Y-%m-%dT%H:%M:%S"
    date_format: str = "%Y-%m-%d"

    secret_key: str = Field(validation_alias=AliasChoices("SECRET_KEY"))
    access_token_expire: int = 60 * 24 * 30

    backend_cors_origins: str = Field(
        default="*",
        validation_alias=AliasChoices("BACKEND_CORS_ORIGINS"),
    )

    engine: str = Field(validation_alias=AliasChoices("ENGINE"))
    user: str = Field(validation_alias=AliasChoices("POSTGRES_USER"))
    password: str = Field(validation_alias=AliasChoices("POSTGRES_PASSWORD"))
    database_name: str = Field(validation_alias=AliasChoices("POSTGRES_DB"))
    host: str = Field(validation_alias=AliasChoices("POSTGRES_HOST"))
    port: str = Field(validation_alias=AliasChoices("POSTGRES_PORT"))

    google_client_id: str = Field(default="", validation_alias=AliasChoices("GOOGLE_CLIENT_ID"))
    google_client_secret: str = Field(default="", validation_alias=AliasChoices("GOOGLE_CLIENT_SECRET"))
    google_redirect_uri: str = Field(default="", validation_alias=AliasChoices("GOOGLE_REDIRECT_URI"))
    google_auth_url: str = Field(default="", validation_alias=AliasChoices("GOOGLE_AUTH_URL"))
    google_token_url: str = Field(default="", validation_alias=AliasChoices("GOOGLE_TOKEN_URL"))
    google_jwks_url: str = Field(default="", validation_alias=AliasChoices("GOOGLE_JWKS_URL"))

    github_client_id: str = Field(default="", validation_alias=AliasChoices("GITHUB_CLIENT_ID"))
    github_client_secret: str = Field(default="", validation_alias=AliasChoices("GITHUB_CLIENT_SECRET"))
    github_redirect_uri: str = Field(default="", validation_alias=AliasChoices("GITHUB_REDIRECT_URI"))
    github_auth_url: str = Field(default="", validation_alias=AliasChoices("GITHUB_AUTH_URL"))
    github_token_url: str = Field(default="", validation_alias=AliasChoices("GITHUB_TOKEN_URL"))
    github_user_info_url: str = Field(default="", validation_alias=AliasChoices("GITHUB_USER_INFO_URL"))

    frontend_url: str = Field(default="http://localhost:5173", validation_alias=AliasChoices("FRONTEND_URL"))

    rate_limit_signin: str = Field(default="10/minute", validation_alias=AliasChoices("RATE_LIMIT_SIGNIN"))

    @property
    def database_url(self) -> str:
        return f"{self.engine}://{self.user}:{self.password}@{self.host}:{self.port}/{self.database_name}"

    @property
    def cors_origins(self) -> List[str]:
        raw = self.backend_cors_origins.strip()
        if raw == "*" or not raw:
            return ["*"]
        return [part.strip() for part in raw.split(",") if part.strip()]

    @field_validator("secret_key")
    @classmethod
    def secret_key_not_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("SECRET_KEY must be set")
        return value


class TestSettings(Settings):
    """Settings for pytest (SQLite, no external Postgres)."""

    model_config = SettingsConfigDict(extra="ignore")

    env: str = "test"
    secret_key: str = "test-secret-key"
    engine: str = "sqlite"
    user: str = "test"
    password: str = "test"
    database_name: str = "test"
    host: str = "localhost"
    port: str = "5432"
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost/callback"
    google_auth_url: str = "https://accounts.google.com/o/oauth2/v2/auth"
    google_token_url: str = "https://oauth2.googleapis.com/token"
    google_jwks_url: str = "https://www.googleapis.com/oauth2/v3/certs"
    github_client_id: str = ""
    github_client_secret: str = ""
    github_redirect_uri: str = "http://localhost/callback"
    github_auth_url: str = "https://github.com/login/oauth/authorize"
    github_token_url: str = "https://github.com/login/oauth/access_token"
    github_user_info_url: str = "https://api.github.com/user"
    frontend_url: str = "http://localhost:5173"

    @property
    def database_url(self) -> str:
        return "sqlite+aiosqlite:///character_test.db"


@lru_cache
def get_settings() -> Settings:
    if os.getenv("ENV", "dev") == "test":
        return TestSettings()
    return Settings()


settings = get_settings()

# Backward-compatible alias for type hints
BaseConfig = Settings
