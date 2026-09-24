from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse

from config import settings
from container import Container
from core.rate_limit import limiter
from core.schema.auth_schema import SignIn, SignInResponse, SignUp
from core.schema.user_schema import User
from core.services.auth_service import AuthService
from core.services.oauth_service import GoogleOAuthService, GitHubOAuthService

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post("/signin", response_model=SignInResponse)
@limiter.limit(settings.rate_limit_signin)
@inject
async def sign_in(
    request: Request,
    payload: SignIn,
    service: AuthService = Depends(Provide[Container.auth_service]),
):
    return await service.sign_in(payload)


@router.post("/signup", response_model=User)
@limiter.limit(settings.rate_limit_signin)
@inject
async def sign_up(
    request: Request,
    payload: SignUp,
    service: AuthService = Depends(Provide[Container.auth_service]),
):
    return await service.sign_up(payload)


@router.get("/google/oauth")
@inject
async def oauth_google(service: GoogleOAuthService = Depends(Provide[Container.google_oauth_service])):
    auth_url = await service.get_login_url()
    return RedirectResponse(auth_url)


@router.get("/google/callback", response_model=SignInResponse, include_in_schema=False)
@inject
async def auth_callback_google(
    code: str = None,
    error: str = None,
    service: GoogleOAuthService = Depends(Provide[Container.google_oauth_service]),
):
    if error:
        raise HTTPException(status_code=400, detail=f"Error de autenticación de Google: {error}")
    return await service.process_callback(code)


@router.get("/github/oauth")
@inject
async def oauth_github(service: GitHubOAuthService = Depends(Provide[Container.github_oauth_service])):
    auth_url = await service.get_login_url()
    return RedirectResponse(auth_url)


@router.get("/github/callback", response_model=SignInResponse, include_in_schema=False)
@inject
async def auth_callback_github(
    code: str = None,
    error: str = None,
    service: GitHubOAuthService = Depends(Provide[Container.github_oauth_service]),
):
    if error:
        raise HTTPException(status_code=400, detail=f"Error de autenticación de GitHub: {error}")
    return await service.process_callback(code)
