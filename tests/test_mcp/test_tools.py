import asyncio

import pytest

from app.mcp.tools import create_character, delete_character, get_character, list_characters, update_character
from core.schema.character_schema import UpdateCharacter
from container import Container
from core.security import get_password_hash
from db.database import BaseModel
from main import AppCreator


@pytest.fixture
def character_service():
    app_creator = AppCreator()
    asyncio.run(_reset_database(app_creator))
    service = app_creator.container.character_service()
    yield service
    asyncio.run(_reset_database(app_creator))


async def _reset_database(app_creator: AppCreator) -> None:
    async with app_creator.db._engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)
    await app_creator.db.create_database()


async def _seed_user(container: Container) -> int:
    from core.models.user import User

    async with container.db().session() as session:
        user = User(
            email="mcp@example.com",
            username="mcpuser",
            first_name="Test",
            last_name="User",
            password=get_password_hash("secret"),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user.id


@pytest.mark.asyncio
async def test_mcp_character_crud(character_service):
    container = AppCreator().container
    user_id = await _seed_user(container)

    created = await create_character(
        character_service,
        user_id=user_id,
        name="Han Solo",
        height=180.0,
        mass=80.0,
        hair_color="brown",
        skin_color="fair",
        eye_color="brown",
    )
    character_id = created["id"]

    listed = await list_characters(character_service, user_id=user_id)
    assert len(listed) == 1

    fetched = await get_character(character_service, user_id=user_id, character_id=character_id)
    assert fetched["name"] == "Han Solo"

    updated = await update_character(
        character_service,
        user_id=user_id,
        character_id=character_id,
        payload=UpdateCharacter(mass=81.0),
    )
    assert updated["mass"] == 81.0

    deleted = await delete_character(character_service, user_id=user_id, character_id=character_id)
    assert deleted == {"deleted": True, "id": character_id}
