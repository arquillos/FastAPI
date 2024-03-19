"""Module to Login a user"""

import datetime
import logging
from typing import Annotated, Optional

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
    """To simplify testing (create_access_token)"""
    return 30


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
    jwt_data = {"sub": email, "exp": expire}
    encoded_jwt = jwt.encode(
        claims=jwt_data, key=config.SECRET_KEY, algorithm=config.ALGORITHM
    )
    return encoded_jwt


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
            detail="User does not exist",
        )
    if not verify_password(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            # detail="User does not exist (incorrect password)",
            detail="User does not exist",
        )
    return user


async def get_user_from_a_jwt(
    token: Annotated[str, Depends(oaut2_scheme)]
) -> Optional[UserIn]:
    """Get the user if is exists in the DB
    @param: token: FastAPI Dependency injection
    """
    try:
        payload = jwt.decode(
            token=token, key=config.SECRET_KEY, algorithms=[config.ALGORITHM]
        )
        email = payload["sub"]
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Empty email after decoding the JWT",
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
    return await get_user(email)
