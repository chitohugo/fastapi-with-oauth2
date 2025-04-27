import os
from typing import List

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class BaseConfig(BaseSettings):
    """Base configuration settings."""
    env: str = os.getenv("ENV", "dev")
    api: str = "/api"
    prefix: str = "/api/v1"
    project_name: str = "BoilerPlate"

    datetime_format: str = "%Y-%m-%dT%H:%M:%S"
    date_format: str = "%Y-%m-%d"

    project_root: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # AUTH
    secret_key: str = os.getenv("SECRET_KEY")
    access_token_expire: int = 60 * 24 * 30  # 60 minutes * 24 hours * 30 days = 30 days

    backend_cors_origins: List[str] = ["*"]

    # DATABASE
    engine: str = os.getenv("ENGINE")
    user: str = os.getenv("POSTGRES_USER")
    password: str = os.getenv("POSTGRES_PASSWORD")
    database_name: str = os.getenv("POSTGRES_DB")
    host: str = os.getenv("POSTGRES_HOST")
    port: str = os.getenv("POSTGRES_PORT")
    database_url: str = f"{engine}://{user}:{password}@{host}:{port}/{database_name}"

    # GOOGLE OAUTH
    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID")
    google_client_secret: str = os.getenv("GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str = os.getenv("GOOGLE_REDIRECT_URI")
    google_auth_url: str = os.getenv("GOOGLE_AUTH_URL")
    google_token_url: str = os.getenv("GOOGLE_TOKEN_URL")
    google_jwks_url: str = os.getenv("GOOGLE_JWKS_URL")

    # GITHUB OAUTH
    github_client_id: str = os.getenv("GITHUB_CLIENT_ID")
    github_client_secret: str = os.getenv("GITHUB_CLIENT_SECRET")
    github_redirect_uri: str = os.getenv("GITHUB_REDIRECT_URI")
    github_auth_url: str = os.getenv("GITHUB_AUTH_URL")
    github_token_url: str = os.getenv("GITHUB_TOKEN_URL")
    github_user_info_url: str = os.getenv("GITHUB_USER_INFO_URL")

    # FRONTEND
    frontend_url: str = os.getenv("FRONTEND_URL")

    model_config = SettingsConfigDict(env_prefix='my_prefix_')


class TestConfig(BaseConfig):
    """Test configuration settings."""
    env: str = "test"
    sqlite_file_name: str = "character.db"
    database_url: str = f"sqlite:///{sqlite_file_name}"


def get_settings() -> BaseConfig:
    env = os.getenv("ENV", "dev")
    if env == "test":
        return TestConfig()
    return BaseConfig()


settings = get_settings()