"""WhatsApp Cloud API payload parsing and webhook signature checks."""

import hashlib
import hmac
from dataclasses import dataclass
from typing import Optional


@dataclass
class InboundMessage:
    """One inbound WhatsApp message extracted from a webhook payload."""

    message_id: str
    phone: str
    text: Optional[str]
    message_type: str


def normalize_phone(value: str) -> str:
    """Keep digits from a phone string."""
    return "".join(character for character in value if character.isdigit())


def outbound_phone(value: str) -> str:
    """Return the number the Cloud API will accept as a recipient.

    WhatsApp reports Argentine mobiles as ``549...``. The test recipient list
    stores the same number without that extra ``9``.
    """
    digits = normalize_phone(value)
    if digits.startswith("549") and len(digits) >= 12:
        return "54" + digits[3:]
    return digits


def signature_is_valid(body: bytes, header: Optional[str], secret: str, env: str) -> bool:
    """Validate ``X-Hub-Signature-256``.

    An empty secret is accepted only in ``dev`` so a local tunnel can be tried
    before the Meta app secret is set. Any other environment rejects it.
    """
    if not secret:
        return env == "dev"
    if not header or not header.startswith("sha256="):
        return False
    provided = header.split("=", 1)[1].strip()
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, provided)


def verify_subscription(mode: str, token: str, expected_token: str) -> bool:
    """Return whether a Meta hub challenge should be accepted."""
    if mode != "subscribe" or not expected_token or not token:
        return False
    return hmac.compare_digest(token.encode("utf-8"), expected_token.encode("utf-8"))


def parse_inbound_messages(payload: dict) -> list[InboundMessage]:
    """Extract inbound messages. Status callbacks yield an empty list."""
    messages: list[InboundMessage] = []
    for entry in payload.get("entry") or []:
        for change in entry.get("changes") or []:
            value = change.get("value") or {}
            for raw in value.get("messages") or []:
                phone = normalize_phone(str(raw.get("from") or ""))
                if not phone:
                    continue
                message_type = str(raw.get("type") or "unknown")
                text = None
                if message_type == "text":
                    text = str((raw.get("text") or {}).get("body") or "").strip()
                messages.append(
                    InboundMessage(
                        message_id=str(raw.get("id") or ""),
                        phone=phone,
                        text=text,
                        message_type=message_type,
                    )
                )
    return messages
