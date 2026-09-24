from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import PyJWTError
from passlib.context import CryptContext

from config import settings
from core.exceptions import AuthError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"


def create_access_token(subject: dict, expires_delta: timedelta | None = None) -> tuple[str, str]:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire)
    payload = {"exp": int(expire.timestamp()), **subject}
    encoded_jwt = jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)
    expiration_datetime = expire.strftime(settings.datetime_format)
    return encoded_jwt, expiration_datetime


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def decode_access_token_payload(token: str) -> dict:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except PyJWTError as exc:
        raise AuthError(message="Could not validate credentials") from exc
    return payload


def decode_jwt(token: str) -> dict | None:
    try:
        return decode_access_token_payload(token)
    except AuthError:
        return None


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        if credentials:
            if credentials.scheme != "Bearer":
                raise AuthError(message="Invalid authentication scheme.")
            if not self.verify_jwt(credentials.credentials):
                raise AuthError(message="Invalid token or expired token.")
            return credentials.credentials
        raise AuthError(message="Invalid authorization code.")

    def verify_jwt(self, jwt_token: str) -> bool:
        return decode_jwt(jwt_token) is not None
