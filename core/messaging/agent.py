"""Language-model agent that turns a chat sentence into character tools."""

from typing import Protocol

from core.messaging.replies import OutboundReply


class MessagingAgent(Protocol):
    """Understand a free-text message and run the shared character tools."""

    async def respond(self, user_id: int, chat_id: str, text: str) -> OutboundReply:
        """Reply to ``text`` for ``user_id`` in ``chat_id``."""
