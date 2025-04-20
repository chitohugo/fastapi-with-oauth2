from httpx import AsyncClient

from config import settings
from core.repository.user_repository import UserRepository
from core.services.auth_service import AuthService
from core.services.character_service import CharacterService
from core.services.oauth_service import GoogleOAuthService, GitHubOAuthService
from core.services.user_service import UserService
from core.repository.character_repository import CharacterRepository
from dependency_injector import containers, providers
from db.database import Database


class Container(containers.DeclarativeContainer):
    config = providers.Configuration(pydantic_settings=[settings])

    wiring_config = containers.WiringConfiguration(
        modules=[
            "app.api.endpoints.auth",
            "app.api.endpoints.users",
            "app.api.endpoints.characters",
            "core.dependencies"
        ]
    )
    db = providers.Singleton(Database, db_url=config.database_url)

    user_repository = providers.Factory(UserRepository, session_factory=db.provided.session)
    character_repository = providers.Factory(CharacterRepository, session_factory=db.provided.session)

    auth_service = providers.Factory(AuthService, user_repository=user_repository)
    user_service = providers.Factory(UserService, user_repository=user_repository)
    character_service = providers.Factory(CharacterService, character_repository=character_repository)

    http_client = providers.Singleton(AsyncClient)

    google_oauth_service = providers.Factory(
        GoogleOAuthService,
        client_id=config.google_client_id,
        client_secret=config.google_client_secret,
        redirect_uri=config.google_redirect_uri,
        auth_url=config.google_auth_url,
        token_url=config.google_token_url,
        jwks_url=config.google_jwks_url,
        access_token_expire=config.access_token_expire,
        user_repository=user_repository,
        http_client=http_client,
    )

    github_oauth_service = providers.Factory(
        GitHubOAuthService,
        client_id=config.github_client_id,
        client_secret=config.github_client_secret,
        redirect_uri=config.github_redirect_uri,
        auth_url=config.github_auth_url,
        token_url=config.github_token_url,
        access_token_expire=config.access_token_expire,
        user_repository=user_repository,
        http_client=http_client,
        user_info_url=config.github_user_info_url
    )