"""API endpoints for user login"""

import logging

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy.sql import ClauseElement

from mediaapi.database import database, users_table
from mediaapi.models.users import UserIn
from mediaapi.security import (
    JwtTypes,
    authenticate_user,
    create_access_token,
    create_confirmation_token,
    get_password,
    get_subject_for_token_type,
    get_user,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserIn, request: Request):
    """Register a new user"""
    if user.email == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Missing email value"
        )
    if user.password == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Missing password value"
        )
    logger.info("Registering user: %s", user)
    # First we check if the user already exists
    if await get_user(user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The user with email {user.email} already exists",
        )

    # The user does not exist, we create the new user
    hash_password: str = get_password(user.password)
    query: ClauseElement = users_table.insert().values(
        email=user.email, password=hash_password
    )
    logger.debug(query)

    await database.execute(query)

    # The user should receive an email with the /confirm/<JWT> to click
    # and confirm the user
    return {
        "detail": "User created. Pleae confirm your email",
        "confirmation_url": request.url_for(
            "confirm_email",
            token=create_confirmation_token(user.email)
        )
    }


@router.post("/token")
async def login(user: UserIn) -> dict:
    """If the user exists, returns a JWT"""
    auth_user: UserIn = await authenticate_user(user.email, user.password)  # type: ignore
    # If the user does not exists and HTTPException is raised by the security module
    return {
        "access_token": create_access_token(auth_user.email),
        "token_type": "bearer",
    }

# It needs to be GET. The endpoint is call by clicking a email button. The browser can only do a
# GET request.
# The token is in the URL for the same reason (Browser limitation)
@router.get("/confirm/{token}")
async def confirm_email(token: str):
    """Confirm a new user"""
    email = get_subject_for_token_type(token, JwtTypes.CONFIRMATION.value)

    # Update the "Users" table info
    query: ClauseElement = (
        users_table.update().where(users_table.c.email == email).values(confirmed=True)
    )
    logger.debug(query)
    await database.execute(query)

    return {"detail": "User confirmed."}
