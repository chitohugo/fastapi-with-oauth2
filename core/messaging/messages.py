"""Normalized inbound message, independent of the chat provider."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class InboundMessage:
    """One inbound chat message after a provider has parsed its webhook."""

    message_id: str
    external_id: str
    text: Optional[str]
    message_type: str
