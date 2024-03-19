"""Tests for the security module"""

import pytest
from fastapi import HTTPException, status
from jose import jwt
from pytest_mock import MockerFixture

from mediaapi import security
from mediaapi.config import config
from mediaapi.models.users import UserIn


def test_access_token_expire_minutes():
    """Check the return value from the function. Not necessary"""
    # Assert
    assert security.access_token_expire_minutes() == 30


def test_create_access_token():
    """Check the jwt token created by the create_access_token function"""
    # Set
    email = "test@email.com"

    # Act
    token: str = security.create_access_token(email)

    # Assert
    expected_token = jwt.decode(
        token=token, key=config.SECRET_KEY, algorithms=[config.ALGORITHM]
    )
    assert {"sub": email}.items() <= expected_token.items()


def test_create_access_token_empty_email():
    """Check the jwt creation with no email"""
    # Act
    with pytest.raises(HTTPException) as exc_info:
        security.create_access_token("")

    # Assert
    assert exc_info.value.detail == "empty email"
    assert exc_info.value.status_code == 400


@pytest.mark.anyio
async def test_get_user(registered_user: dict):
    """Check the get_user function"""
    # Act
    user: UserIn = await security.get_user(registered_user["email"])  # type: ignore

    # Assert
    assert user.email == registered_user["email"]
    assert user.id == int(registered_user["id"])


@pytest.mark.anyio
async def test_get_user_not_found():
    """Check a non existent user"""
    # Act
    user: UserIn = await security.get_user("uknown email") # type: ignore

    # Assert
    assert user is None


@pytest.mark.anyio
async def test_get_user_unexpected_type():
    """Check a wrong user type"""
    # Act
    user: UserIn = await security.get_user(123) # type: ignore

    # Assert
    assert user is None


@pytest.mark.anyio
async def test_get_user_empty_email():
    """Check an empty user"""
    # Act
    with pytest.raises(security.HTTPException) as exec_info:
        await security.get_user("")

    # Assert
    assert exec_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exec_info.value.detail == "The email value can not be empty"


@pytest.mark.anyio
async def test_authenticate_user(registered_user: dict):
    """Check if a user exists in the DB"""
    # Act
    user: UserIn = await security.authenticate_user(registered_user["email"], registered_user["password"]) # type: ignore

    # Assert
    assert user.email == registered_user["email"]

@pytest.mark.anyio
async def test_authenticate_user_does_not_exists():
    """Check the function with a no registered user"""
    # Asct
    with pytest.raises(security.HTTPException) as exec_info:
        await security.authenticate_user("fake_user@email.com", "password")

    # Assert
    assert exec_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exec_info.value.detail == "User does not exist"


@pytest.mark.anyio
async def test_authenticate_user_wrong_password(registered_user: dict):
    """Check the function with a no wrong password"""
    # Asct
    with pytest.raises(security.HTTPException) as exec_info:
        await security.authenticate_user(registered_user["email"], "wrong password")

    # Assert
    assert exec_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exec_info.value.detail == "User does not exist"


@pytest.mark.anyio
async def test_get_user_from_a_jwt(registered_user: dict):
    """Check the user returned from a JWT is the expected one"""
    token: str = security.create_access_token(registered_user["email"])
    user: UserIn = await security.get_user_from_a_jwt(token) # type: ignore

    assert user.email == registered_user["email"]


@pytest.mark.anyio
async def test_get_user_from_a_jwt_invalid_token():
    """Check no user returned from a JWT is the expected one"""
    # Act
    with pytest.raises(security.HTTPException) as exec_info:
        await security.get_user_from_a_jwt("Inalid token")

    # Assert
    assert exec_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exec_info.value.detail == "Could not validate credentials (JWT error)"


@pytest.mark.anyio
async def test_get_user_from_a_jwt_expired_token(registered_user: dict, mocker: MockerFixture):
    """Check the user returned from a JWT is the expected one"""
    # Arrange
    # Patching the JWT expire time
    mocker.patch(
        'mediaapi.security.access_token_expire_minutes',
        return_value = -1
    )

    # Get an expired token
    expired_token: str = security.create_access_token(registered_user["email"])
    
    # Act
    with pytest.raises(HTTPException) as exec_info:
        await security.get_user_from_a_jwt(expired_token)

    # Assert
    assert exec_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exec_info.value.detail == "Expired JWT token"
