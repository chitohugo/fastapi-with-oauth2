from typing import Dict, Any, Optional
from httpx import AsyncClient
from fastapi import HTTPException
from datetime import timedelta

from core.repository.user_repository import UserRepository
from core.schema.auth_schema import Payload
from core.schema.user_schema import User
from core.security import create_access_token



class BaseOAuthService:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str,
                 token_url: str, access_token_expire: int,
                 user_repository: UserRepository, http_client: AsyncClient):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.token_url = token_url
        self.access_token_expire = access_token_expire
        self.repository = user_repository
        self.http_client = http_client

    async def _exchange_code_for_tokens(self, code: str, headers: dict = None, extra_data: dict = None) -> Dict[
        str, Any]:
        data = {
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }
        if extra_data:
            data.update(extra_data)

        response = await self.http_client.post(self.token_url, headers=headers, data=data)
        response.raise_for_status()
        return response.json()

    async def _get_or_create_user_and_generate_token(self, email: str, username: str, first_name: Optional[str],
                                                     last_name: Optional[str]) -> Dict[str, str]:
        if not email:
            raise HTTPException(status_code=400, detail="Email no disponible o no verificado.")

        user = self.repository.find_one("email", email)
        if not user:
            user = User(email=email, username=username, first_name=first_name, last_name=last_name)
            user = self.repository.create(user)

        payload = Payload(id=user.id, email=user.email, first_name=user.first_name).model_dump()
        token_lifespan = timedelta(minutes=self.access_token_expire)
        access_token, _ = create_access_token(payload, token_lifespan)
        return {"access_token": access_token}