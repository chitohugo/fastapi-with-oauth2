"""WhatsApp adapter for the generic messaging service."""

from core.messaging.messages import InboundMessage
from core.messaging.provider import MessagingProvider
from core.messaging.replies import CharacterSnapshot, OutboundReply
from core.services.whatsapp_client import WhatsAppClient
from core.services.whatsapp_protocol import normalize_phone, parse_inbound_messages

_UNLINKED = (
    "Este número ({external_id}) no está vinculado a un usuario.\n"
    "Con tu JWT, llamá a PUT /api/v1/whatsapp/me con "
    '{{"phone": "{external_id}"}} y volvé a escribir.'
)


class WhatsAppProvider(MessagingProvider):
    """Cloud API webhook parsing and replies. Commands live in MessagingService."""

    key = "whatsapp"

    def __init__(self, client: WhatsAppClient):
        self.client = client

    def parse_inbound(self, payload: dict) -> list[InboundMessage]:
        """Extract text and non-text messages from a Cloud API payload."""
        return parse_inbound_messages(payload)

    def normalize_external_id(self, value: str) -> str:
        """Store the digits Meta sends in ``from``."""
        return normalize_phone(value)

    def unlinked_reply(self, external_id: str) -> str:
        """Explain how to bind this phone with the WhatsApp link endpoint."""
        return _UNLINKED.format(external_id=external_id)

    async def send(self, external_id: str, reply: OutboundReply) -> None:
        """Send a text reply. Character data is bold, without buttons."""
        if reply.kind == "character" and reply.character is not None:
            await self.client.send_text(
                external_id,
                _character_card(reply.headline, reply.character),
            )
            return
        if reply.kind == "list" and reply.characters:
            cards = [_character_card("", character) for character in reply.characters]
            body = reply.body + "\n\n" + "\n\n".join(cards)
            await self.client.send_text(external_id, body)
            return
        await self.client.send_text(external_id, reply.body)


def _character_card(headline: str, character: CharacterSnapshot) -> str:
    """Bold character card. WhatsApp treats ``*...*`` as bold."""
    name = _plain(character.name) or f"#{character.id}"
    lines = [f"*{name}*", f"#{character.id}"]
    lines.append(f"*Altura* {character.height:g}")
    lines.append(f"*Masa* {character.mass:g}")
    lines.append(f"*Pelo* {_plain(character.hair_color)}")
    lines.append(f"*Piel* {_plain(character.skin_color)}")
    lines.append(f"*Ojos* {_plain(character.eye_color)}")
    if headline:
        return headline + "\n\n" + "\n".join(lines)
    return "\n".join(lines)


def _plain(value: str) -> str:
    """Drop WhatsApp markup characters from user-provided text."""
    return " ".join(str(value).replace("*", "").replace("_", "").replace("~", "").split())
