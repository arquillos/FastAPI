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


def test_confirm_token_expire_minutes():
    """Check the return value from the function. Not necessary"""
    # Assert
    assert security.confirm_token_expire_minutes() == 1440


def test_create_access_token():
    """Check the jwt access token"""
    # Arrange
    email = "test@email.com"

    # Act
    token: str = security.create_access_token(email)

    # Assert
    expected_token = jwt.decode(
        token=token, key=config.SECRET_KEY, algorithms=[config.ALGORITHM]
    )
    assert {"sub": email, "type": security.JwtTypes.ACCESS.value}.items() <= expected_token.items()


def test_create_confirmation_token():
    """Check the jwt confirmation token"""
    # Arrange
    email = "test@email.com"

    # Act
    token: str = security.create_confirmation_token(email)

    # Assert
    expected_token = jwt.decode(
        token=token, key=config.SECRET_KEY, algorithms=[config.ALGORITHM]
    )
    assert {"sub": email, "type": security.JwtTypes.CONFIRMATION.value}.items() <= expected_token.items()


def test_create_confirmation_token_empty_email():
    """Check the jwt confirmation token with no email"""
    # Arrange
    email = ""

    # Act
    with pytest.raises(HTTPException) as exc_info:
        security.create_confirmation_token(email)

    # Assert
    assert exc_info.value.detail == "empty email"
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST


def test_get_subject_for_token_type_confirmation_token():
    """Check the email from a jwt confirmation token"""
    # Arrange
    email = "test@email.com"

    # Act
    token: str = security.create_confirmation_token(email)

    # Assert
    assert email == security.get_subject_for_token_type(
        token, security.JwtTypes.CONFIRMATION.value
        )


def test_get_subject_for_token_type_access_token():
    """Check the email from a jwt access token"""
    # Arrange
    email = "test@email.com"

    # Act
    token: str = security.create_access_token(email)

    # Assert
    assert email == security.get_subject_for_token_type(
        token, security.JwtTypes.ACCESS.value
        )


def test_get_subject_for_token_expired_token(mocker: MockerFixture):
    """Check the email from an expired jwt acess token"""
    # Arrange
    # Patching the JWT expire time
    mocker.patch(
        'mediaapi.security.access_token_expire_minutes',
        return_value = -1
    )
    email = "test@email.com"
    token: str = security.create_access_token(email)

    # Act
    with pytest.raises(HTTPException) as exc_info:
        security.get_subject_for_token_type(
            token, security.JwtTypes.ACCESS.value
        )
    
    # Assert
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Expired JWT token"


def test_get_subject_for_token_wrong_token():
    """Check the email from a wrong jwt token"""
    # Act
    with pytest.raises(HTTPException) as exec_info:
        security.get_subject_for_token_type(
            "WRONG TOKEN", security.JwtTypes.ACCESS.value
        )
    
    # Assert
    assert exec_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exec_info.value.detail == "Could not validate credentials (JWT error)"


def test_get_subject_for_token_missing_sub_field():
    """Check the email from a wrong jwt token (No sub)"""
    # Arrange
    email = "test@email.com"
    token: str = security.create_access_token(email)
    payload = jwt.decode(
        token=token, key=config.SECRET_KEY, algorithms=[config.ALGORITHM]
    )
    del payload["sub"]
    wrong_token = jwt.encode(
        claims=payload, key=config.SECRET_KEY, algorithm=config.ALGORITHM
    )

    # Act
    with pytest.raises(HTTPException) as exc_info:
        security.get_subject_for_token_type(
            wrong_token, security.JwtTypes.ACCESS.value
        )
    
    # Assert
    assert "Token is missing 'sub' field" == exc_info.value.detail


def test_get_subject_for_token_type_wrong_type_access():
    """Check the email from a jwt access token with a confirmation type"""
    # Arrange
    email = "test@email.com"
    token: str = security.create_confirmation_token(email)

    # Act
    with pytest.raises(HTTPException) as exc_info:
        security.get_subject_for_token_type(
        token, security.JwtTypes.ACCESS.value
        )
    
    # Assert
    assert "Invalid JWT type, expected: access" == exc_info.value.detail


def test_get_subject_for_token_type_wrong_type_confirmation():
    """Check the email from a jwt access token with a access type"""
    # Arrange
    email = "test@email.com"
    token: str = security.create_access_token(email)

    # Act
    with pytest.raises(HTTPException) as exc_info:
        security.get_subject_for_token_type(
        token, security.JwtTypes.CONFIRMATION.value
        )
    
    # Assert
    assert "Invalid JWT type, expected: confirmation" == exc_info.value.detail
    

def test_create_access_token_empty_email():
    """Check the jwt creation with no email"""
    # Act
    with pytest.raises(HTTPException) as exc_info:
        security.create_access_token("")

    # Assert
    assert exc_info.value.detail == "empty email"
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST


def test_create_access_token_wrong_type():
    """Check the jwt creation with a wrong type"""
    # Set
    email = "test@email.com"

    # Act
    token: str = security.create_confirmation_token(email)

    # Assert
    with pytest.raises(HTTPException) as exc_info:
        security.get_subject_for_token_type(
            token, "WRONG TYPE"
        )

    # Assert
    assert exc_info.value.detail == "Invalid JWT type, expected: WRONG TYPE"
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


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
async def test_authenticate_user(confirmed_user: dict):
    """Check if a user exists in the DB"""
    # Act
    user: UserIn = await security.authenticate_user(confirmed_user["email"], confirmed_user["password"]) # type: ignore

    # Assert
    assert user.email == confirmed_user["email"]


@pytest.mark.anyio
async def test_authenticate_user_does_not_exists():
    """Check the function with a no registered user"""
    # Asct
    with pytest.raises(security.HTTPException) as exec_info:
        await security.authenticate_user("fake_user@email.com", "password")

    # Assert
    assert exec_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exec_info.value.detail == "Invalid user or password"


@pytest.mark.anyio
async def test_authenticate_user_wrong_password(registered_user: dict):
    """Check the function with a no wrong password"""
    # Asct
    with pytest.raises(security.HTTPException) as exec_info:
        await security.authenticate_user(registered_user["email"], "wrong password")

    # Assert
    assert exec_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exec_info.value.detail == "Invalid user or password"


@pytest.mark.anyio
async def test_get_user_from_a_jwt(registered_user: dict):
    """Check the user returned from a JWT is the expected one"""
    token: str = security.create_access_token(registered_user["email"])
    user: UserIn = await security.get_user_from_a_jwt(token)

    assert user.email == registered_user["email"]


@pytest.mark.anyio
async def test_get_user_from_a_jwt_invalid_token():
    """Check no user returned from an invalid JWT"""
    # Act
    with pytest.raises(security.HTTPException) as exec_info:
        await security.get_user_from_a_jwt("Inalid token")

    # Assert
    assert exec_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exec_info.value.detail == "Could not validate credentials (JWT error)"


@pytest.mark.anyio
async def test_get_user_from_wrong_jwt_type(registered_user: dict):
    """Check no user returned from a JWT with the wrong type"""
    # Setup
    token = security.create_confirmation_token(registered_user["email"])

    # Act
    with pytest.raises(security.HTTPException) as exec_info:
        await security.get_user_from_a_jwt(token)

    # Assert
    assert exec_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exec_info.value.detail == "Invalid JWT type, expected: access"


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
