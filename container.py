from typing import Optional

from dependency_injector import containers, providers
from httpx import AsyncClient

from app.messaging.llm_agent import LlmCharacterAgent
from config import get_settings, settings
from core.messaging.service import MessagingService
from core.repository.character_repository import CharacterRepository
from core.repository.messaging_contact_repository import MessagingContactRepository
from core.repository.user_repository import UserRepository
from core.services.auth_service import AuthService
from core.services.character_service import CharacterService
from core.services.oauth_service import GoogleOAuthService, GitHubOAuthService
from core.services.user_service import UserService
from core.services.whatsapp_client import WhatsAppClient
from core.services.whatsapp_provider import WhatsAppProvider
from db.database import Database


def build_llm_agent(
    character_service: CharacterService,
    http_client: AsyncClient,
) -> Optional[LlmCharacterAgent]:
    """Return the natural-language agent when an API key is configured."""
    if not settings.llm_api_key:
        return None
    return LlmCharacterAgent(
        character_service=character_service,
        http_client=http_client,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        base_url=settings.llm_base_url,
    )


class Container(containers.DeclarativeContainer):
    config = providers.Configuration(pydantic_settings=[settings])

    wiring_config = containers.WiringConfiguration(
        modules=[
            "app.api.endpoints.auth",
            "app.api.endpoints.users",
            "app.api.endpoints.characters",
            "app.api.endpoints.whatsapp",
            "core.dependencies",
        ]
    )
    db = providers.Singleton(Database, db_url=get_settings().database_url)

    user_repository = providers.Factory(
        UserRepository,
        session_factory=db.provided.session,
    )
    character_repository = providers.Factory(
        CharacterRepository,
        session_factory=db.provided.session,
    )

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

    messaging_contact_repository = providers.Factory(
        MessagingContactRepository,
        session_factory=db.provided.session,
    )

    whatsapp_client = providers.Singleton(
        WhatsAppClient,
        access_token=settings.whatsapp_access_token,
        phone_number_id=settings.whatsapp_phone_number_id,
        api_version=settings.whatsapp_api_version,
        graph_url=settings.whatsapp_graph_url,
        http_client=http_client,
    )

    whatsapp_provider = providers.Factory(WhatsAppProvider, client=whatsapp_client)

    llm_agent = providers.Singleton(
        build_llm_agent,
        character_service=character_service,
        http_client=http_client,
    )

    messaging_service = providers.Factory(
        MessagingService,
        character_service=character_service,
        contact_repository=messaging_contact_repository,
        agent=llm_agent,
    )
