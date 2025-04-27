from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Coroutine

from fastapi import HTTPException
from jwt import PyJWTError, algorithms, decode, get_unverified_header
from starlette.responses import RedirectResponse

from config import settings
from core.services.base_oauth_service import BaseOAuthService


class OAuthService(ABC):
    @abstractmethod
    async def get_login_url(self) -> str:
        pass

    @abstractmethod
    async def process_callback(self, code: str) -> Dict[str, Any]:
        pass


class GoogleOAuthService(OAuthService, BaseOAuthService):
    def __init__(self, auth_url: str, jwks_url: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auth_url = auth_url
        self.jwks_url = jwks_url

    async def get_login_url(self) -> str:
        return (
            f"{self.auth_url}?"
            f"client_id={self.client_id}&"
            f"redirect_uri={self.redirect_uri}&"
            f"response_type=code&"
            f"scope=openid profile email"
        )

    async def process_callback(self, code: str) -> RedirectResponse:
        if not code:
            raise HTTPException(status_code=400, detail="Código de autorización no recibido.")

        response = await self._exchange_code_for_tokens(code)
        id_token = response.get("id_token")
        access_token = response.get("access_token")

        if not id_token:
            raise HTTPException(status_code=401, detail="ID Token no recibido.")

        payload = await self._verify_id_token(id_token, access_token)
        response = await self.handle_oauth_user_login(
            payload["email"],
            username=payload["email"].split("@")[0],
            first_name=payload.get("given_name"),
            last_name=payload.get("family_name")
        )

        return RedirectResponse(url=f"{settings.frontend_url}/oauth/callback?access_token={response['access_token']}")

    async def _verify_id_token(self, id_token: str, access_token: str) -> Dict[str, Any]:
        jwks = (await self.http_client.get(self.jwks_url)).json()
        public_keys = {key["kid"]: algorithms.RSAAlgorithm.from_jwk(key) for key in jwks["keys"]}
        headers = get_unverified_header(id_token)
        key = public_keys.get(headers["kid"])

        if not key:
            raise HTTPException(status_code=401, detail="Clave pública no encontrada.")

        try:
            return decode(
                id_token,
                key=key,
                algorithms=["RS256"],
                audience=self.client_id,
                access_token=access_token
            )
        except PyJWTError:
            raise HTTPException(status_code=401, detail="Token inválido o expirado.")


class GitHubOAuthService(OAuthService, BaseOAuthService):
    def __init__(self, auth_url: str, user_info_url: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auth_url = auth_url
        self.user_info_url = user_info_url

    async def get_login_url(self) -> str:
        return f"{self.auth_url}?client_id={self.client_id}&redirect_uri={self.redirect_uri}&scope=user:email"

    async def process_callback(self, code: str) -> RedirectResponse:
        if not code:
            raise HTTPException(status_code=400, detail="Código de autorización no recibido.")

        tokens = await self._exchange_code_for_tokens(code, headers={"Accept": "application/json"})
        access_token = tokens.get("access_token")

        if not access_token:
            raise HTTPException(status_code=401, detail="Access token no recibido.")

        user_info = await self._get_user_info(access_token)
        email = user_info.get("email") or await self._get_primary_email(access_token)

        response = await self.handle_oauth_user_login(
            email,
            username=user_info.get("login"),
            first_name=(user_info.get("name") or "").split(" ")[0],
            last_name=" ".join((user_info.get("name") or "").split(" ")[1:])
        )

        return RedirectResponse(url=f"{settings.frontend_url}/oauth/callback?access_token={response['access_token']}")

    async def _get_user_info(self, token: str) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        response = await self.http_client.get(self.user_info_url, headers=headers)
        response.raise_for_status()
        return response.json()

    async def _get_primary_email(self, token: str) -> Optional[str]:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        response = await self.http_client.get(f"{self.user_info_url}/emails", headers=headers)
        response.raise_for_status()
        emails = response.json()
        primary = next((e for e in emails if e.get("primary") and e.get("verified")), None)
        return primary.get("email") if primary else None
