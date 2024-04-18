"""Tests for the user router"""
import pytest
from fastapi import Request, status
from httpx import AsyncClient
from pytest_mock import MockerFixture


async def register_user(async_client: AsyncClient, email: str, password: str):
    """Helper method to register a user"""
    return await async_client.post(
        "/register", json={"email": email, "password": password}
    )


@pytest.mark.anyio
async def test_confirm_email(async_client: AsyncClient, mocker: MockerFixture):
    """Checking clicking on the registration email link"""
    # Setup
    email = "test@email.com"

    # Get the arguments the request url_for was called with
    spy = mocker.spy(Request, "url_for")

    await register_user(
        async_client=async_client, email=email, password="1234"
    )

    confirmation_url = str(spy.spy_return)

    # Act
    response = await async_client.get(confirmation_url)

    # Assert
    assert response.status_code is status.HTTP_200_OK
    assert "User confirmed." == response.json()["detail"]


@pytest.mark.anyio
async def test_confirm_email_invalid_token(async_client: AsyncClient):
    """Checking clicking on the registration email link with a wrong link"""
    # Act
    response = await async_client.get("confirm/inalid_token")

    # Assert
    assert response.status_code is status.HTTP_401_UNAUTHORIZED
    assert "Could not validate credentials (JWT error)" == response.json()["detail"]


@pytest.mark.anyio
async def test_confirm_email_expired_token(async_client: AsyncClient, mocker: MockerFixture):
    """Checking clicking on the registration email link that has expires"""
    # Setup
    email = "test@email.com"

    # Expired token
    mocker.patch("mediaapi.security.confirm_token_expire_minutes", return_value=-1)
    # Get the arguments the request url_for was called with
    spy = mocker.spy(Request, "url_for")

    await register_user(
        async_client=async_client, email=email, password="1234"
    )

    confirmation_url = str(spy.spy_return)

    # Act
    response = await async_client.get(confirmation_url)

    # Assert
    assert response.status_code is status.HTTP_401_UNAUTHORIZED
    assert "Expired JWT token" == response.json()["detail"]