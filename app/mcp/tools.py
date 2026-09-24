"""MCP tool definitions backed by CharacterService."""

from __future__ import annotations

from typing import Optional

from mcp.server.fastmcp import FastMCP

from app.mcp.bootstrap import get_character_service, resolve_user_id
from app.mcp.errors import invoke_service
from app.mcp.schemas import character_to_dict
from core.schema.character_schema import PostCharacter, UpdateCharacter
from core.services.character_service import CharacterService


async def create_character(
    service: CharacterService,
    user_id: int,
    name: str,
    height: float,
    mass: float,
    hair_color: str,
    skin_color: str,
    eye_color: str,
) -> dict:
    """Create a character owned by ``user_id``."""
    payload = PostCharacter(
        name=name,
        height=height,
        mass=mass,
        hair_color=hair_color,
        skin_color=skin_color,
        eye_color=eye_color,
        user_id=user_id,
    )
    character = await invoke_service(lambda: service.add(payload))
    return character_to_dict(character)


async def get_character(service: CharacterService, user_id: int, character_id: int) -> dict:
    """Fetch one character if it belongs to ``user_id``."""
    character = await invoke_service(lambda: service.get_for_user(character_id, user_id))
    return character_to_dict(character)


async def list_characters(service: CharacterService, user_id: int) -> list[dict]:
    """List characters owned by ``user_id``."""
    characters = await invoke_service(lambda: service.get_list_for_user(user_id))
    return [character_to_dict(item) for item in characters]


async def update_character(
    service: CharacterService,
    user_id: int,
    character_id: int,
    payload: UpdateCharacter,
) -> dict:
    """Update a character owned by ``user_id``."""
    character = await invoke_service(
        lambda: service.patch_for_user(character_id, user_id, payload)
    )
    return character_to_dict(character)


async def delete_character(service: CharacterService, user_id: int, character_id: int) -> dict:
    """Delete a character owned by ``user_id``."""
    await invoke_service(lambda: service.remove_for_user(character_id, user_id))
    return {"deleted": True, "id": character_id}


def register_tools(mcp: FastMCP) -> None:
    """Register character CRUD tools on the MCP server."""

    @mcp.tool(
        name="create_character",
        description=(
            "Create a Star Wars-style character for user_id (owner). "
            "Requires name, height, mass, hair_color, skin_color, eye_color."
        ),
    )
    async def create_character_tool(
        name: str,
        height: float,
        mass: float,
        hair_color: str,
        skin_color: str,
        eye_color: str,
        user_id: int | None = None,
    ) -> dict:
        resolved_user_id = resolve_user_id(user_id)
        service = get_character_service()
        return await create_character(
            service,
            resolved_user_id,
            name,
            height,
            mass,
            hair_color,
            skin_color,
            eye_color,
        )

    @mcp.tool(
        name="get_character",
        description="Get one character by id. Only the owner (user_id) can read it.",
    )
    async def get_character_tool(character_id: int, user_id: int | None = None) -> dict:
        resolved_user_id = resolve_user_id(user_id)
        service = get_character_service()
        return await get_character(service, resolved_user_id, character_id)

    @mcp.tool(
        name="list_characters",
        description="List all characters belonging to user_id.",
    )
    async def list_characters_tool(user_id: int | None = None) -> list[dict]:
        resolved_user_id = resolve_user_id(user_id)
        service = get_character_service()
        return await list_characters(service, resolved_user_id)

    @mcp.tool(
        name="update_character",
        description="Patch character fields (only set fields you pass). Owner only.",
    )
    async def update_character_tool(
        character_id: int,
        user_id: int | None = None,
        name: Optional[str] = None,
        height: Optional[float] = None,
        mass: Optional[float] = None,
        hair_color: Optional[str] = None,
        skin_color: Optional[str] = None,
        eye_color: Optional[str] = None,
    ) -> dict:
        resolved_user_id = resolve_user_id(user_id)
        payload = UpdateCharacter(
            name=name,
            height=height,
            mass=mass,
            hair_color=hair_color,
            skin_color=skin_color,
            eye_color=eye_color,
        )
        service = get_character_service()
        return await update_character(service, resolved_user_id, character_id, payload)

    @mcp.tool(
        name="delete_character",
        description="Permanently delete a character by id. Owner only.",
    )
    async def delete_character_tool(character_id: int, user_id: int | None = None) -> dict:
        resolved_user_id = resolve_user_id(user_id)
        service = get_character_service()
        return await delete_character(service, resolved_user_id, character_id)
