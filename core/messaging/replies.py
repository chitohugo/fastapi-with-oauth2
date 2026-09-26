"""Channel-neutral reply. Each provider decides how to render it."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CharacterSnapshot:
    """Character fields a provider can lay out without touching the database."""

    id: int
    name: str
    height: float
    mass: float
    hair_color: str
    skin_color: str
    eye_color: str


@dataclass(frozen=True)
class OutboundReply:
    """What MessagingService wants the channel to show."""

    body: str
    kind: str = "text"
    headline: str = ""
    character: Optional[CharacterSnapshot] = None
    characters: tuple[CharacterSnapshot, ...] = ()
