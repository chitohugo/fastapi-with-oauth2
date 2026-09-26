"""WhatsApp Cloud API payload parsing and webhook signature checks."""

import hashlib
import hmac
from typing import Optional

from core.messaging.messages import InboundMessage


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


def _inbound_text(raw: dict, message_type: str) -> Optional[str]:
    """Text command from a text message or from a tapped button or list row."""
    if message_type == "text":
        body = str((raw.get("text") or {}).get("body") or "").strip()
        return body or None
    if message_type != "interactive":
        return None
    interactive = raw.get("interactive") or {}
    kind = str(interactive.get("type") or "")
    choice = interactive.get(kind) or {}
    if not isinstance(choice, dict):
        return None
    return command_from_choice(str(choice.get("id") or ""))


def command_from_choice(choice_id: str) -> Optional[str]:
    """Map a button or list id back to a chat command."""
    known = {"listar", "ayuda", "menu:crear", "menu:actualizar", "menu:eliminar"}
    if choice_id in known:
        return choice_id
    prefix, _, value = choice_id.partition(":")
    if prefix in {"ver", "eliminar"} and value.isdigit():
        return f"{prefix} {value}"
    return None


def parse_inbound_messages(payload: dict) -> list[InboundMessage]:
    """Extract inbound messages. Status callbacks yield an empty list."""
    messages: list[InboundMessage] = []
    for entry in payload.get("entry") or []:
        for change in entry.get("changes") or []:
            value = change.get("value") or {}
            for raw in value.get("messages") or []:
                external_id = normalize_phone(str(raw.get("from") or ""))
                if not external_id:
                    continue
                message_type = str(raw.get("type") or "unknown")
                text = _inbound_text(raw, message_type)
                messages.append(
                    InboundMessage(
                        message_id=str(raw.get("id") or ""),
                        external_id=external_id,
                        text=text,
                        message_type=message_type,
                    )
                )
    return messages
