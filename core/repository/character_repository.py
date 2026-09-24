from typing import Any, Callable, List

from core.models.character import Character
from core.repository.base_repository import BaseRepository
from sqlalchemy import select


class CharacterRepository(BaseRepository):
    def __init__(self, session_factory: Callable[..., Any]):
        super().__init__(session_factory, Character)

    async def read_by_user_id(self, user_id: int) -> List[Character]:
        async with self.session_factory() as session:
            stmt = select(Character).where(Character.user_id == user_id)
            result = await session.scalars(stmt)
            return list(result.all())
