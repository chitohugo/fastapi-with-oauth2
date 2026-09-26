"""Base every chat provider implements."""

from abc import ABC, abstractmethod

from core.messaging.messages import InboundMessage
from core.messaging.replies import OutboundReply


class MessagingProvider(ABC):
    """Translate one channel's webhook and replies. Commands stay outside."""

    key: str

    @abstractmethod
    def parse_inbound(self, payload: dict) -> list[InboundMessage]:
        """Extract inbound messages. Status callbacks return an empty list."""

    @abstractmethod
    def normalize_external_id(self, value: str) -> str:
        """Canonical identity stored for this channel (phone, chat id, ...)."""

    @abstractmethod
    def unlinked_reply(self, external_id: str) -> str:
        """Tell the sender how to link this identity to a user."""

    @abstractmethod
    async def send(self, external_id: str, reply: OutboundReply) -> None:
        """Deliver ``reply`` to ``external_id`` in this channel's format."""
