"""Pytest fixtures"""

from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.sql import ClauseElement

from mediaapi.database import database, users_table
from mediaapi.main import app
from mediaapi.models.users import UserIn


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
async def db() -> AsyncGenerator:
    """Clearing all the stores information before each test"""
    await database.connect()
    yield
    # If "DB_FORCE_ROLL_BACK = True" the DB will rollback all the changed before disconnecting
    await database.disconnect()


@pytest.fixture
def client() -> Generator:
    yield TestClient(app)


@pytest.fixture()
async def async_client(client: Generator) -> AsyncGenerator:
    async with AsyncClient(app=app, base_url=client.base_url) as ac:
        yield ac


@pytest.fixture()
async def registered_user(async_client: AsyncClient) -> dict:
    """Fixture to create a user in the DB"""
    user_details = {"email": "test@example.net", "password": "1234"}
    await async_client.post("/register", json=user_details)

    # Get the user Id from the DB
    query: ClauseElement = users_table.select().where(
        users_table.c.email == user_details["email"]
    )  # type: ignore
    user: UserIn = await database.fetch_one(query)  # type: ignore
    user_details["id"] = user.id  # type: ignore
    return user_details


@pytest.fixture()
async def logged_in_token(async_client: AsyncClient, registered_user: dict) -> str:
    """Get a JWT from a registered user"""
    response = await async_client.post("/token", json=registered_user)
    return response.json()["access_token"]
