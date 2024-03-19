"""Tests for the user router"""
import pytest
from fastapi import status
from httpx import AsyncClient, Response


async def register_user(async_client: AsyncClient, email: str, password: str):
    """Helper method to register a user"""
    return await async_client.post(
        "/register", json={"email": email, "password": password}
    )


@pytest.mark.anyio
async def test_register_user(async_client: AsyncClient):
    """Checking a register user"""
    # Act
    response = await register_user(
        async_client=async_client, email="test@email.com", password="1234"
    )

    # Assert
    assert response.status_code is status.HTTP_201_CREATED


@pytest.mark.anyio
async def test_register_user_no_email(async_client: AsyncClient):
    """Checking registering a user with no email"""
    # Act
    response: Response = await register_user(
        async_client=async_client, email="", password="1234"
    )

    # Assert
    assert response.status_code is status.HTTP_400_BAD_REQUEST
    assert "Missing email value" == response.json()["detail"]


@pytest.mark.anyio
async def test_register_user_no_password(async_client: AsyncClient):
    """Checking registering a user with no password"""
    # Act
    response: Response = await register_user(
        async_client=async_client, email="exmaple@email.com", password=""
    )

    # Assert
    assert response.status_code is status.HTTP_400_BAD_REQUEST
    assert "Missing password value" == response.json()["detail"]


@pytest.mark.anyio
async def test_register_user_email_exist(async_client: AsyncClient):
    """Checking registering a user with a registered email"""
    # Setup
    email = "test@email.com"

    # Act
    response = await register_user(
        async_client=async_client, email=email, password="1234"
    )
    # Second user with the same email
    response = await register_user(
        async_client=async_client, email=email, password="5678"
    )

    # Assert
    assert response.status_code is status.HTTP_400_BAD_REQUEST
    assert f"The user with email {email} already exists" == response.json()["detail"]


@pytest.mark.anyio
async def test_register_user_same_password(async_client: AsyncClient):
    """Checking registering a user with the same password as other user"""
    # Setup
    password = "1234"

    # Act
    response = await register_user(
        async_client=async_client, email="test@email.com", password=password
    )
    # Second user with the same email
    response = await register_user(
        async_client=async_client, email="test_2@email.com", password=password
    )

    # Assert
    assert response.status_code is status.HTTP_201_CREATED


@pytest.mark.anyio
async def test_token_user_exists(async_client: AsyncClient, registered_user: dict):
    """Checking JWT generation for a registered user"""
    # Act
    response = await async_client.post(
        "/token",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.anyio
async def test_token_user_not_exists(async_client: AsyncClient):
    """Checking JWT generation for a non registered user"""
    # Act
    response = await async_client.post(
        "/token", json={"email": "test@email.com", "password": "1234"}
    )

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "User does not exist" == response.json()["detail"]


@pytest.mark.anyio
async def test_token_incorrect_password(
    async_client: AsyncClient, registered_user: dict
):
    """Checking JWT generation for a user with incorrect password"""
    # Act
    response = await async_client.post(
        "/token", json={"email": registered_user["email"], "password": "2"}
    )

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "User does not exist" == response.json()["detail"]


@pytest.mark.anyio
async def test_token_empty_user(async_client: AsyncClient, registered_user: dict):
    """Checking JWT generation for a user with empty email"""
    # Act
    response = await async_client.post(
        "/token",
        json={
            "email": "",
            "password": registered_user["password"],
        },
    )

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "The email value can not be empty" == response.json()["detail"]


@pytest.mark.anyio
async def test_token_empty_password(async_client: AsyncClient, registered_user: dict):
    """Checking JWT generation for a user with empty password"""
    # Act
    response = await async_client.post(
        "/token", json={"email": registered_user["email"], "password": ""}
    )

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "User does not exist" == response.json()["detail"]


@pytest.mark.anyio
async def test_token_missing_email_field(
    async_client: AsyncClient, registered_user: dict
):
    """Checking JWT generation for a user with no email field"""
    # Act
    response = await async_client.post(
        "/token",
        json={
            "password": registered_user["password"],
        },
    )

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.anyio
async def test_token_missing_password_field(
    async_client: AsyncClient, registered_user: dict
):
    """Checking JWT generation for a user with no password field"""
    # Act
    response = await async_client.post(
        "/token", json={"email": registered_user["email"]}
    )

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
