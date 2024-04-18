"""Module to Login a user"""

import datetime
import logging
from enum import Enum
from typing import Annotated, Literal, Optional

import bcrypt
from bcrypt import checkpw, hashpw
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError, jwt
from sqlalchemy.sql import ClauseElement, select

from mediaapi.config import config
from mediaapi.database import database, users_table
from mediaapi.models.users import UserIn

logger = logging.getLogger(__name__)

# Two goals:
# - To automatically populate the FastAPI doc
# - Let us grab the token
oaut2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def access_token_expire_minutes() -> int:
    """
    User token
    To simplify testing (create_access_token)
    """
    return 30  # 30 mins


def confirm_token_expire_minutes() -> int:
    """
    Register token
    To simplify testing (create_access_token)
    """
    return 1440  # 1 day


class JwtTypes(str, Enum):
    """JWT types"""
    ACCESS = "access"  # JWT for a registered user
    CONFIRMATION = "confirmation"  # JWT for a user to register


def create_access_token(email: str):
    """Create a JWT for a registered user"""
    if email == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="empty email"
        )

    logger.debug("Creating an access token for user: %s", email)
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=access_token_expire_minutes()
    )
    jwt_data = {
        "sub": email, 
        "exp": expire,
        "type": JwtTypes.ACCESS.value
        }
    encoded_jwt = jwt.encode(
        claims=jwt_data, key=config.SECRET_KEY, algorithm=config.ALGORITHM
    )
    return encoded_jwt


def create_confirmation_token(email: str):
    """Create a JWT for confirmation email"""
    if email == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="empty email"
        )

    logger.debug("Creating a confirmation token for user: %s", email)
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=confirm_token_expire_minutes()
    )
    jwt_data = {
        "sub": email, 
        "exp": expire,
        "type": JwtTypes.CONFIRMATION.value
        }
    encoded_jwt = jwt.encode(
        claims=jwt_data, key=config.SECRET_KEY, algorithm=config.ALGORITHM
    )
    return encoded_jwt


def get_subject_for_token_type(
    token: str, token_type: Literal[JwtTypes.ACCESS.value, JwtTypes.CONFIRMATION.value]
    ) -> str:
    """Get the email from a token. Checks for the expected token type"""
    try:
        payload: dict = jwt.decode(
            token=token, key=config.SECRET_KEY, algorithms=[config.ALGORITHM]
        )
    except ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Expired JWT token"
        ) from exc
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials (JWT error)",
        ) from exc

    email = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing 'sub' field",
        )
    payload_type = payload.get("type")
    if payload_type is None or payload_type != token_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid JWT type, expected: {token_type}",
        )

    return email


def get_password(password: str) -> str:
    """Hashing a password"""
    pwd_bytes = password.encode("utf-8")  # converting password to array of bytes
    return hashpw(pwd_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check if a password is the expected one"""
    user_bytes = plain_password.encode("utf-8")  # encoding user password
    hashed_bytes = hashed_password.encode("utf-8")
    return checkpw(user_bytes, hashed_bytes)


async def get_user(email: str) -> Optional[UserIn]:
    """Get the user if is exists in the DB"""
    if email:
        logger.debug("Fetching user with email: %s from the DB", email)
        query: ClauseElement = select(users_table).where(users_table.c.email == email)
        result: UserIn = await database.fetch_one(query)  # type: ignore
        if result:
            return result
        return None
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The email value can not be empty",
        )


async def authenticate_user(email: str, password: str) -> Optional[UserIn]:
    """Return the user from the DB if it already exist"""
    logger.debug("Authenticating user (email: %s)", email)
    user: UserIn = await get_user(email=email)  # type: ignore
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            # detail="Incorrect user",
            detail="Invalid user or password",
        )
    if not verify_password(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            # detail="Incorrect password",
            detail="Invalid user or password",
        )
    # Require a confirmed user before using any protected endpoint
    if not user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The user has not confirmed the email",
        )  
    return user


async def get_user_from_a_jwt(
    token: Annotated[str, Depends(oaut2_scheme)]
) -> Optional[UserIn]:
    """Get the user if is exists in the DB
    @param: token: FastAPI Dependency injection
    """
    email = get_subject_for_token_type(token, JwtTypes.ACCESS.value)
    user = await get_user(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not find user for this user",
        )  
    return user
