from datetime import timedelta

from core.exceptions import AuthError, DuplicatedError
from core.repository.user_repository import UserRepository
from core.schema.auth_schema import Payload, SignIn, SignUp
from core.security import create_access_token, get_password_hash, verify_password
from config import settings


class AuthService:
    def __init__(self, user_repository: UserRepository):
        self.repository = user_repository

    async def sign_in(self, sign_in: SignIn):
        user = await self.repository.find_one("email", sign_in.email)
        if not user:
            raise AuthError(message="Incorrect email or password")

        if not user.password or not verify_password(sign_in.password, user.password):
            raise AuthError(message="Incorrect email or password")

        payload = Payload(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
        )
        token_lifespan = timedelta(minutes=settings.access_token_expire)
        access_token, _expiration = create_access_token(payload.model_dump(), token_lifespan)
        return {"access_token": access_token}

    async def sign_up(self, user: SignUp):
        existing_user = await self.repository.find_one("email", user.email)

        if existing_user:
            if not existing_user.password:
                user.password = get_password_hash(user.password)
                return await self.repository.update(existing_user.id, user)
            raise DuplicatedError(message="Email already registered")

        user.password = get_password_hash(user.password)
        return await self.repository.create(user)
