from typing import Any, Callable, Type

from core.exceptions import DuplicatedError, NotFoundError
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    def __init__(
        self,
        session_factory: Callable[..., Any],
        model: Type,
    ) -> None:
        self.session_factory = session_factory
        self.model = model

    async def read_by_field(self, field_name: str, value: Any):
        async with self.session_factory() as session:
            stmt = select(self.model).where(getattr(self.model, field_name) == value)
            result = await session.execute(stmt)
            entity = result.scalar_one_or_none()
            if not entity:
                raise NotFoundError(message=f"Not found {field_name} : {value}")
            return entity

    async def read(self):
        async with self.session_factory() as session:
            stmt = select(self.model)
            result = await session.scalars(stmt)
            return result.all()

    async def create(self, schema):
        async with self.session_factory() as session:
            try:
                entity = self.model(**schema.model_dump(), id=None)
                session.add(entity)
                await session.commit()
                await session.refresh(entity)
            except IntegrityError as exc:
                await session.rollback()
                raise DuplicatedError(message="The value already exists") from exc
            return entity

    async def update(self, id: int, schema):
        values = schema.model_dump(exclude_unset=True, exclude_none=True)
        if not values:
            return await self.read_by_field("id", id)
        async with self.session_factory() as session:
            stmt = update(self.model).where(self.model.id == id).values(**values)
            await session.execute(stmt)
            await session.commit()
        return await self.read_by_field("id", id)

    async def delete_by_id(self, id: int):
        async with self.session_factory() as session:
            stmt = select(self.model).where(self.model.id == id)
            result = await session.execute(stmt)
            entity = result.scalar_one_or_none()
            if not entity:
                raise NotFoundError(message=f"not found id : {id}")
            await session.delete(entity)
            await session.commit()

    async def find_one(self, field_name: str, value: Any):
        async with self.session_factory() as session:
            stmt = select(self.model).where(getattr(self.model, field_name) == value)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
