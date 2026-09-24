"""Serialization helpers for MCP tool responses."""

from core.models.character import Character as CharacterModel
from core.schema.character_schema import Character as CharacterSchema


def character_to_dict(character: CharacterModel) -> dict:
    """Serialize a character ORM instance for MCP clients.

    Args:
        character: SQLAlchemy character row.

    Returns:
        JSON-serializable character payload.
    """
    return CharacterSchema.model_validate(character).model_dump(mode="json")
