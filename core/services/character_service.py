from core.exceptions import ForbiddenError
from core.repository.character_repository import CharacterRepository


class CharacterService:
    def __init__(self, character_repository: CharacterRepository):
        self.repository = character_repository

    async def get_list_for_user(self, user_id: int):
        return await self.repository.read_by_user_id(user_id)

    async def add(self, schema):
        return await self.repository.create(schema)

    async def get_for_user(self, character_id: int, user_id: int):
        character = await self.repository.read_by_field("id", character_id)
        if character.user_id != user_id:
            raise ForbiddenError(message="You do not own this character")
        return character

    async def patch_for_user(self, character_id: int, user_id: int, schema):
        await self.get_for_user(character_id, user_id)
        return await self.repository.update(character_id, schema)

    async def remove_for_user(self, character_id: int, user_id: int):
        await self.get_for_user(character_id, user_id)
        await self.repository.delete_by_id(character_id)
