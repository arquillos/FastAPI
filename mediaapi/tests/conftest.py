from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from mediaapi.database import database
from mediaapi.main import app


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


# Clearing all the stores information before each test
@pytest.fixture(autouse=True)
async def db() -> AsyncGenerator:
    await database.connect()
    yield
    # If "DB_FORCE_ROLL_BACK = True" the DB will rollback all the changed before disconnecting
    await database.disconnect()


@pytest.fixture
def client() -> Generator:
    yield TestClient(app)


@pytest.fixture()
async def async_client(client) -> AsyncGenerator:
    async with AsyncClient(app=app, base_url=client.base_url) as ac:
        yield ac
