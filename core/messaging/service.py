"""Run character commands for any messaging provider."""

import logging
from collections import OrderedDict
from typing import Optional

from core.exceptions import DuplicatedError, ForbiddenError, NotFoundError
from core.messaging.agent import MessagingAgent
from core.messaging.commands import HELP_TEXT, CommandError, parse_command
from core.messaging.messages import InboundMessage
from core.messaging.provider import MessagingProvider
from core.messaging.replies import CharacterSnapshot, OutboundReply
from core.models.messaging_contact import MessagingContact
from core.repository.messaging_contact_repository import MessagingContactRepository
from core.services.character_service import CharacterService

logger = logging.getLogger("client-ai")

_SEEN_LIMIT = 1000
_seen_message_ids: OrderedDict[str, None] = OrderedDict()


def clear_seen_messages() -> None:
    """Forget processed message ids (tests)."""
    _seen_message_ids.clear()


class MessagingService:
    """Contact links and character commands shared by every channel."""

    def __init__(
        self,
        character_service: CharacterService,
        contact_repository: MessagingContactRepository,
        agent: Optional[MessagingAgent] = None,
    ):
        self.characters = character_service
        self.contacts = contact_repository
        self.agent = agent

    async def link(
        self,
        provider: MessagingProvider,
        user_id: int,
        external_id: str,
    ) -> MessagingContact:
        """Bind a channel identity to the authenticated user."""
        normalized = provider.normalize_external_id(external_id)
        return await self.contacts.link(provider.key, normalized, user_id)

    async def get_link(self, provider: MessagingProvider, user_id: int) -> MessagingContact:
        """Return the user's link for this channel."""
        contact = await self.contacts.find_by_user(provider.key, user_id)
        if contact is None:
            raise NotFoundError(message="Messaging contact is not linked")
        return contact

    async def unlink(self, provider: MessagingProvider, user_id: int) -> None:
        """Remove the user's link for this channel."""
        removed = await self.contacts.unlink(provider.key, user_id)
        if not removed:
            raise NotFoundError(message="Messaging contact is not linked")

    async def handle(
        self,
        provider: MessagingProvider,
        payload: dict,
        default_user_id: Optional[int] = None,
    ) -> None:
        """Reply to each inbound message using ``provider``."""
        for message in provider.parse_inbound(payload):
            seen_key = f"{provider.key}:{message.message_id}"
            if _already_seen(seen_key):
                logger.info("Skipping duplicate %s message %s", provider.key, message.message_id)
                continue
            _remember(seen_key)
            reply = await self._reply(provider, message, default_user_id)
            await provider.send(message.external_id, reply)

    async def _reply(
        self,
        provider: MessagingProvider,
        message: InboundMessage,
        default_user_id: Optional[int],
    ) -> OutboundReply:
        if not message.text:
            return OutboundReply("Solo puedo leer mensajes de texto. Escribí ayuda.")
        try:
            user_id = await self._resolve_user_id(provider, message.external_id, default_user_id)
            if user_id is None:
                return OutboundReply(provider.unlinked_reply(message.external_id))
            return await self._execute(user_id, message.text, message.external_id)
        except CommandError as exc:
            return OutboundReply(exc.message)
        except NotFoundError:
            return OutboundReply("No encontré ese personaje.")
        except ForbiddenError:
            return OutboundReply("Ese personaje no es tuyo.")
        except DuplicatedError:
            return OutboundReply("Ya existe un personaje con ese nombre.")
        except Exception:
            logger.exception("%s command failed for %s", provider.key, message.external_id)
            return OutboundReply(
                "No pude completar la acción. Escribí ayuda para ver los comandos."
            )

    async def _resolve_user_id(
        self,
        provider: MessagingProvider,
        external_id: str,
        default_user_id: Optional[int],
    ) -> Optional[int]:
        contact = await self.contacts.find_by_external_id(provider.key, external_id)
        if contact is not None:
            return contact.user_id
        return default_user_id

    async def _execute(self, user_id: int, text: str, external_id: str) -> OutboundReply:
        if self.agent is not None and not _structured_command(text):
            return await self.agent.respond(user_id, external_id, text)
        command = parse_command(text)
        if command.kind == "help":
            return OutboundReply(HELP_TEXT)
        if command.kind == "list":
            rows = await self.characters.get_list_for_user(user_id)
            if not rows:
                return OutboundReply(
                    "No tenés personajes todavía. "
                    "Pedime que cree uno y pasame nombre, altura, masa, pelo, piel y ojos."
                )
            shown = rows[:10]
            note = "Estos son tus personajes."
            if len(rows) > len(shown):
                note = f"Mostrando 10 de {len(rows)}."
            return OutboundReply(
                note,
                kind="list",
                characters=tuple(_snapshot(row) for row in shown),
            )
        if command.kind == "get":
            character = await self.characters.get_for_user(command.character_id, user_id)
            return _character_reply(character)
        if command.kind == "create":
            command.payload.user_id = user_id
            character = await self.characters.add(command.payload)
            return _character_reply(character, "Personaje creado.")
        if command.kind == "update":
            character = await self.characters.patch_for_user(
                command.character_id,
                user_id,
                command.payload,
            )
            return _character_reply(character, "Personaje actualizado.")
        await self.characters.remove_for_user(command.character_id, user_id)
        return OutboundReply(f"Eliminé el personaje #{command.character_id}.")


def _structured_command(text: str) -> bool:
    """True for an exact command, which skips the language model."""
    stripped = text.strip().lower()
    if stripped in {"listar", "lista", "list", "ayuda", "help", "hola", "start", "menu"}:
        return True
    head, _, tail = stripped.partition(" ")
    if head in {"ver", "get", "eliminar", "borrar", "delete"} and tail.isdigit():
        return True
    if head in {"actualizar", "update"}:
        character_id = tail.split(" ", 1)[0]
        return character_id.isdigit()
    return False


def _snapshot(character) -> CharacterSnapshot:
    """Copy the fields a chat card needs."""
    return CharacterSnapshot(
        id=character.id,
        name=character.name,
        height=character.height,
        mass=character.mass,
        hair_color=character.hair_color,
        skin_color=character.skin_color,
        eye_color=character.eye_color,
    )


def _character_reply(character, headline: str = "") -> OutboundReply:
    """Detail card for one character."""
    return OutboundReply(
        "",
        kind="character",
        headline=headline,
        character=_snapshot(character),
    )


def _already_seen(seen_key: str) -> bool:
    if seen_key.endswith(":"):
        return False
    return seen_key in _seen_message_ids


def _remember(seen_key: str) -> None:
    if seen_key.endswith(":"):
        return
    _seen_message_ids[seen_key] = None
    while len(_seen_message_ids) > _SEEN_LIMIT:
        _seen_message_ids.popitem(last=False)
