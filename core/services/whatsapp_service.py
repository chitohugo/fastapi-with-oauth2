"""Turn WhatsApp messages into character operations."""

import logging
from collections import OrderedDict
from typing import Optional

from core.exceptions import DuplicatedError, ForbiddenError, NotFoundError
from core.models.whatsapp_contact import WhatsAppContact
from core.repository.whatsapp_contact_repository import WhatsAppContactRepository
from core.services.character_service import CharacterService
from core.services.whatsapp_client import WhatsAppClient
from core.services.whatsapp_commands import (
    HELP_TEXT,
    UNLINKED_TEXT,
    CommandError,
    format_character,
    parse_command,
)
from core.services.whatsapp_protocol import InboundMessage, parse_inbound_messages

logger = logging.getLogger("client-ai")

_SEEN_LIMIT = 1000
_seen_message_ids: OrderedDict[str, None] = OrderedDict()


def clear_seen_messages() -> None:
    """Forget processed WhatsApp message ids (tests)."""
    _seen_message_ids.clear()


class WhatsAppService:
    """Webhook handling and phone linking for the character app."""

    def __init__(
        self,
        character_service: CharacterService,
        contact_repository: WhatsAppContactRepository,
        client: WhatsAppClient,
        default_user_id: Optional[int] = None,
    ):
        self.characters = character_service
        self.contacts = contact_repository
        self.client = client
        self.default_user_id = default_user_id

    async def link_current_user(self, user_id: int, phone: str) -> WhatsAppContact:
        """Bind a normalized phone to the authenticated user."""
        return await self.contacts.link(phone, user_id)

    async def get_link(self, user_id: int) -> WhatsAppContact:
        """Return the current user's WhatsApp link."""
        contact = await self.contacts.find_by_user_id(user_id)
        if contact is None:
            raise NotFoundError(message="WhatsApp number is not linked")
        return contact

    async def unlink(self, user_id: int) -> None:
        """Remove the current user's WhatsApp link."""
        removed = await self.contacts.unlink_user(user_id)
        if not removed:
            raise NotFoundError(message="WhatsApp number is not linked")

    async def handle_payload(self, payload: dict) -> None:
        """Reply to each inbound message in a Cloud API webhook body."""
        for message in parse_inbound_messages(payload):
            if _already_seen(message.message_id):
                logger.info("Skipping duplicate WhatsApp message %s", message.message_id)
                continue
            _remember(message.message_id)
            reply = await self._reply(message)
            await self.client.send_text(message.phone, reply)

    async def _reply(self, message: InboundMessage) -> str:
        if not message.text:
            return "Solo puedo leer mensajes de texto. Escribí ayuda."
        try:
            user_id = await self._resolve_user_id(message.phone)
            if user_id is None:
                return UNLINKED_TEXT.format(phone=message.phone)
            return await self._execute(user_id, message.text)
        except CommandError as exc:
            return exc.message
        except NotFoundError:
            return "No encontré ese personaje."
        except ForbiddenError:
            return "Ese personaje no es tuyo."
        except DuplicatedError:
            return "Ya existe un personaje con ese nombre."
        except Exception:
            logger.exception("WhatsApp command failed for %s", message.phone)
            return "No pude completar la acción. Escribí ayuda para ver los comandos."

    async def _resolve_user_id(self, phone: str) -> Optional[int]:
        contact = await self.contacts.find_by_phone(phone)
        if contact is not None:
            return contact.user_id
        return self.default_user_id

    async def _execute(self, user_id: int, text: str) -> str:
        command = parse_command(text)
        if command.kind == "help":
            return HELP_TEXT
        if command.kind == "list":
            rows = await self.characters.get_list_for_user(user_id)
            if not rows:
                return (
                    "No tenés personajes todavía. "
                    "Creá uno con: crear Nombre | altura | masa | pelo | piel | ojos"
                )
            return "\n\n".join(format_character(row) for row in rows)
        if command.kind == "get":
            character = await self.characters.get_for_user(command.character_id, user_id)
            return format_character(character)
        if command.kind == "create":
            command.payload.user_id = user_id
            character = await self.characters.add(command.payload)
            return "Personaje creado.\n" + format_character(character)
        if command.kind == "update":
            character = await self.characters.patch_for_user(
                command.character_id,
                user_id,
                command.payload,
            )
            return "Personaje actualizado.\n" + format_character(character)
        await self.characters.remove_for_user(command.character_id, user_id)
        return f"Eliminé el personaje #{command.character_id}."


def _already_seen(message_id: str) -> bool:
    if not message_id:
        return False
    return message_id in _seen_message_ids


def _remember(message_id: str) -> None:
    if not message_id:
        return
    _seen_message_ids[message_id] = None
    while len(_seen_message_ids) > _SEEN_LIMIT:
        _seen_message_ids.popitem(last=False)
