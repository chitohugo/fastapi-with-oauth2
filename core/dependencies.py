from core.exceptions import AuthError, ForbiddenError
from core.models.user import User
from core.schema.auth_schema import Payload
from core.security import JWTBearer, decode_access_token_payload
from core.services.user_service import UserService
from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from pydantic import ValidationError

from container import Container


@inject
async def get_current_user(
    token: str = Depends(JWTBearer()),
    service: UserService = Depends(Provide[Container.user_service]),
) -> User:
    try:
        payload = decode_access_token_payload(token)
        token_data = Payload(**{k: v for k, v in payload.items() if k != "exp"})
    except ValidationError as exc:
        raise AuthError(message="Could not validate credentials") from exc

    current_user = await service.get_by_field("id", token_data.id)
    if not current_user:
        raise AuthError(message="User not found")

    return current_user


async def require_self(
    id: int,
    current_user: User = Depends(get_current_user),
) -> User:
    """Allow access only when the authenticated user matches the path ``id``."""
    if current_user.id != id:
        raise ForbiddenError(message="You can only access your own user profile")
    return current_user
