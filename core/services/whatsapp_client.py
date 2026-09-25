"""WhatsApp Cloud API client."""

import logging

from httpx import AsyncClient

from core.services.whatsapp_protocol import outbound_phone

logger = logging.getLogger("client-ai")

_MAX_BODY = 4096


class WhatsAppClient:
    """Send text replies through the WhatsApp Cloud API."""

    def __init__(
        self,
        access_token: str,
        phone_number_id: str,
        http_client: AsyncClient,
        api_version: str = "v22.0",
        graph_url: str = "https://graph.facebook.com",
    ):
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.http_client = http_client
        self.api_version = api_version
        self.graph_url = graph_url.rstrip("/")

    async def send_text(self, to: str, body: str) -> None:
        """Deliver a text message. Missing credentials are logged and skipped."""
        to = outbound_phone(to)
        text = body if len(body) <= _MAX_BODY else body[: _MAX_BODY - 1] + "…"
        if not self.access_token or not self.phone_number_id:
            logger.warning(
                "WhatsApp API is not configured. Reply to %s was not sent: %s",
                to,
                text,
            )
            return

        url = f"{self.graph_url}/{self.api_version}/{self.phone_number_id}/messages"
        try:
            response = await self.http_client.post(
                url,
                headers={"Authorization": f"Bearer {self.access_token}"},
                json={
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": to,
                    "type": "text",
                    "text": {"preview_url": False, "body": text},
                },
                timeout=15.0,
            )
            if response.is_error:
                logger.error(
                    "WhatsApp send failed for %s: %s %s",
                    to,
                    response.status_code,
                    response.text,
                )
                return
        except Exception:
            logger.exception("WhatsApp send failed for %s", to)
