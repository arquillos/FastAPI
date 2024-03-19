import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.sql import ClauseElement

from mediaapi.database import comments_table, database, post_table
from mediaapi.models.post import (
    Comment,
    CommentIn,
    UserPost,
    UserPostIn,
    UserPostWithComments,
)
from mediaapi.models.users import User
from mediaapi.security import get_user_from_a_jwt

router = APIRouter()

logger = logging.getLogger(__name__)


async def find_post(post_id: int):
    logger.info(f"Finding post with Id: {post_id}")
    query: ClauseElement = post_table.select().where(post_table.c.id == post_id)  # type: ignore
    return await database.fetch_one(query)


@router.post("/post", response_model=UserPost, status_code=201)
async def create_post(
    post: UserPostIn, current_user: Annotated[User, Depends(get_user_from_a_jwt)]
):
    """
    @param post: User post to add to the DB
    @param current_user: FastAPI Dependency injection, protecting the endpoint: First we authenticate the user
    """
    logger.info(f"Creating a post: {post}")

    # Then we insert the post into the DB
    data = {**post.model_dump(), "user_id": current_user.id}
    query: ClauseElement = post_table.insert().values(data)
    logger.debug(query)

    # We return the inserted record with the record ID
    last_record_id: int = await database.execute(query)
    return {**data, "id": last_record_id}


@router.get("/post", response_model=list[UserPost])
async def get_all_posts():
    logger.info("Getting all the posts")
    query = post_table.select()
    logger.debug(query)

    return await database.fetch_all(query)


@router.post("/comment", response_model=Comment, status_code=status.HTTP_201_CREATED)
async def create_comment(
    comment: CommentIn, current_user: Annotated[User, Depends(get_user_from_a_jwt)]
):
    """
    @param comment: Comment to add to a post
    @param current_user: FastAPI Dependency injection, protecting the endpoint: First we authenticate the user
    """
    logger.info(f"Creating a comment ({comment})")

    # Then we find the post in the DB
    post = await find_post(comment.post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with Id {comment.post_id} not found",
        )

    # And insert the comment into the DB
    data = {**comment.model_dump(), "user_id": current_user.id}
    query: ClauseElement = comments_table.insert().values(data)
    logger.debug(query)

    last_record_id: int = await database.execute(query)
    return {**data, "id": last_record_id}


@router.get("/post/{post_id}/comments", response_model=list[Comment])
async def get_comments_on_post(post_id: int):
    logger.info(f"Getting the comments from a post (Id: {post_id})")
    query: ClauseElement = comments_table.select().where(
        comments_table.c.post_id == post_id
    )  # type: ignore
    logger.debug(query)

    return await database.fetch_all(query)


@router.get("/post/{post_id}", response_model=UserPostWithComments)
async def get_post_with_comments(post_id: int):
    logger.info(f"Getting the post and comments (Post Id: {post_id})")
    post = await find_post(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with Id {post_id} not found",
        )
    else:
        logger.info("Unbexpected post found!")
    return {
        "post": post,
        "comments": await get_comments_on_post(post_id),
    }
