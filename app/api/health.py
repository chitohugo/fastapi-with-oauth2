from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text

from config import settings
from container import Container

router = APIRouter(tags=["health"])


def _get_database():
    return Container().db()


@router.get("/health")
async def health():
    """Liveness probe."""
    return {"status": "ok", "service": settings.project_name}


@router.get("/ready")
async def ready(database: Any = Depends(_get_database)):
    """Readiness probe (includes database connectivity)."""
    async with database.session() as session:
        await session.execute(text("SELECT 1"))
    return {"status": "ready", "database": "connected"}
