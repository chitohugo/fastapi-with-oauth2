"""Application bootstrap for the MCP server process."""

from __future__ import annotations

import os
from functools import lru_cache

from container import Container
from core.services.character_service import CharacterService
from mcp.server.fastmcp.exceptions import ToolError


@lru_cache
def get_container() -> Container:
    """Return a process-wide dependency-injector container."""
    return Container()


def get_character_service() -> CharacterService:
    """Build a CharacterService instance from the shared container."""
    return get_container().character_service()


def resolve_user_id(user_id: int | None) -> int:
    """Resolve the acting user for MCP tool calls.

    Args:
        user_id: Explicit user id from the tool invocation.

    Returns:
        The resolved user id.

    Raises:
        ToolError: If neither ``user_id`` nor ``MCP_DEFAULT_USER_ID`` is set.
    """
    if user_id is not None:
        return user_id

    default = os.getenv("MCP_DEFAULT_USER_ID")
    if default is not None and default != "":
        try:
            return int(default)
        except ValueError as exc:
            raise ToolError("MCP_DEFAULT_USER_ID must be an integer") from exc

    raise ToolError(
        "user_id is required: pass it to the tool or set MCP_DEFAULT_USER_ID in the environment"
    )
