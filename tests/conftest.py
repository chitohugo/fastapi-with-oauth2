import asyncio
import os

os.environ["ENV"] = "test"
os.environ["WHATSAPP_VERIFY_TOKEN"] = "test-verify-token"
os.environ["WHATSAPP_APP_SECRET"] = "test-app-secret"
os.environ["WHATSAPP_ACCESS_TOKEN"] = ""
os.environ["WHATSAPP_PHONE_NUMBER_ID"] = ""
os.environ["WHATSAPP_DEFAULT_USER_ID"] = ""
os.environ["LLM_API_KEY"] = ""

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from config import settings
from core.models.user import User
from core.rate_limit import limiter
from core.security import get_password_hash
from db.database import BaseModel
from main import AppCreator


async def _reset_app_database(app_creator: AppCreator) -> None:
    async with app_creator.db._engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)
    await app_creator.db.create_database()


@pytest_asyncio.fixture(scope="function")
async def session():
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

    async with AsyncSession(engine, expire_on_commit=False) as db_session:
        try:
            yield db_session
        finally:
            await db_session.rollback()

    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
def client():
    limiter.reset()
    AppCreator.reset_for_tests()
    app_creator = AppCreator()
    app = app_creator.app
    asyncio.run(_reset_app_database(app_creator))

    with TestClient(app) as test_client:
        yield test_client

    asyncio.run(_reset_app_database(app_creator))


@pytest_asyncio.fixture
async def create_user(session):
    data = {
        "email": "julian.clark@gmail.com",
        "username": "delicatesilk",
        "first_name": "Julian",
        "last_name": "Clark",
        "password": get_password_hash("dolor"),
    }
    instance = User(**data)
    session.add(instance)
    await session.commit()
    await session.refresh(instance)
    yield instance


@pytest.fixture
def auth_token(client):
    signup = {
        "email": "julian.clark@gmail.com",
        "username": "delicatesilk",
        "first_name": "Julian",
        "last_name": "Clark",
        "password": "dolor",
    }
    client.post("/api/v1/auth/signup", json=signup)
    response = client.post(
        "/api/v1/auth/signin",
        json={"email": signup["email"], "password": signup["password"]},
    )
    assert response.status_code == 200
    return response.json().get("access_token")


@pytest.fixture
def req(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    client.headers.update(headers)
    return client
