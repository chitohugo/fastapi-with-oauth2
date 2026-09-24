import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declared_attr
from sqlalchemy.orm import as_declarative


def _to_async_database_url(db_url: str) -> str:
    if db_url.startswith("postgresql+psycopg2"):
        return db_url.replace("postgresql+psycopg2", "postgresql+asyncpg", 1)
    if db_url.startswith("postgresql://"):
        return db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if db_url.startswith("sqlite:///"):
        return db_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    return db_url


@as_declarative()
class BaseModel:
    id: int
    __name__: str

    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()


class Database:
    def __init__(self, db_url: str) -> None:
        async_url = _to_async_database_url(db_url)
        echo = os.getenv("SQLALCHEMY_ECHO", "false").lower() in ("1", "true", "yes")
        connect_args: dict = {}
        if async_url.startswith("postgresql+asyncpg"):
            connect_args["timeout"] = int(os.getenv("DB_CONNECT_TIMEOUT", "10"))
        engine_kwargs: dict = {"echo": echo, "pool_pre_ping": True}
        if connect_args:
            engine_kwargs["connect_args"] = connect_args
        self._engine = create_async_engine(async_url, **engine_kwargs)
        self._session_factory = async_sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self._engine,
            expire_on_commit=False,
        )

    async def create_database(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(BaseModel.metadata.create_all)

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        session: AsyncSession = self._session_factory()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
