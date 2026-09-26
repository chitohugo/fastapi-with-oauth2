import json
import logging

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse, PlainTextResponse, Response

from config import settings
from container import Container
from core.dependencies import get_current_user
from core.models.user import User
from core.schema.base_schema import Blank
from core.messaging.service import MessagingService
from core.schema.whatsapp_schema import LinkWhatsApp, WhatsAppLink
from core.security import JWTBearer
from core.services.whatsapp_protocol import signature_is_valid, verify_subscription
from core.services.whatsapp_provider import WhatsAppProvider

logger = logging.getLogger("client-ai")

webhook_router = APIRouter(prefix="/webhooks/whatsapp", tags=["whatsapp"])
link_router = APIRouter(
    prefix="/whatsapp",
    tags=["whatsapp"],
    dependencies=[Depends(JWTBearer())],
)


@webhook_router.get("")
async def verify_whatsapp_webhook(
    mode: str = Query(alias="hub.mode"),
    token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge"),
):
    """Meta subscription handshake. Echo the challenge when the verify token matches."""
    if not verify_subscription(mode, token, settings.whatsapp_verify_token):
        return Response(status_code=403)
    return PlainTextResponse(content=challenge)


@webhook_router.post("")
@inject
async def receive_whatsapp_webhook(
    request: Request,
    service: MessagingService = Depends(Provide[Container.messaging_service]),
    provider: WhatsAppProvider = Depends(Provide[Container.whatsapp_provider]),
):
    """Receive WhatsApp messages and reply with character commands."""
    body = await request.body()
    header = request.headers.get("x-hub-signature-256")
    if not signature_is_valid(body, header, settings.whatsapp_app_secret, settings.env):
        logger.info("Rejected WhatsApp webhook with an invalid signature")
        return Response(status_code=403)
    try:
        payload = json.loads(body) if body else {}
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content={"message": "Invalid JSON"})
    if not isinstance(payload, dict):
        return JSONResponse(status_code=400, content={"message": "Invalid JSON"})
    await service.handle(provider, payload, default_user_id=settings.whatsapp_default_user_id)
    return {"status": "ok"}


@link_router.put("/me", response_model=WhatsAppLink)
@inject
async def link_whatsapp(
    payload: LinkWhatsApp,
    current_user: User = Depends(get_current_user),
    service: MessagingService = Depends(Provide[Container.messaging_service]),
    provider: WhatsAppProvider = Depends(Provide[Container.whatsapp_provider]),
):
    """Bind the authenticated user to a WhatsApp phone number."""
    contact = await service.link(provider, current_user.id, payload.phone)
    return WhatsAppLink(phone=contact.external_id, user_id=contact.user_id)


@link_router.get("/me", response_model=WhatsAppLink)
@inject
async def get_whatsapp_link(
    current_user: User = Depends(get_current_user),
    service: MessagingService = Depends(Provide[Container.messaging_service]),
    provider: WhatsAppProvider = Depends(Provide[Container.whatsapp_provider]),
):
    """Return the WhatsApp number linked to the authenticated user."""
    contact = await service.get_link(provider, current_user.id)
    return WhatsAppLink(phone=contact.external_id, user_id=contact.user_id)


@link_router.delete("/me", response_model=Blank)
@inject
async def unlink_whatsapp(
    current_user: User = Depends(get_current_user),
    service: MessagingService = Depends(Provide[Container.messaging_service]),
    provider: WhatsAppProvider = Depends(Provide[Container.whatsapp_provider]),
):
    """Remove the WhatsApp number linked to the authenticated user."""
    await service.unlink(provider, current_user.id)
    return Blank()
