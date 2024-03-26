"""API endpoints for user posts"""
import logging
from enum import Enum
from typing import Annotated

import sqlalchemy
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.sql import ClauseElement

from mediaapi.database import comments_table, database, like_table, post_table
from mediaapi.models.comment import Comment, CommentIn
from mediaapi.models.like import PostLike, PostLikeIn
from mediaapi.models.post import (
    UserPost,
    UserPostIn,
    UserPostWithComments,
    UserPostWithLikes,
)
from mediaapi.models.users import User
from mediaapi.security import get_user_from_a_jwt

router = APIRouter()

logger = logging.getLogger(__name__)


# Query result: A row that has all th post data plus the number of likes
# label("likes") -> The model expect "likes" when doing the validation (UserPostWithLikes)
select_post_and_likes: ClauseElement = (
    sqlalchemy.select(post_table, sqlalchemy.func.count(like_table.c.id).label("likes"))
    .select_from(post_table.outerjoin(like_table))
    .group_by(post_table.c.id)
)

async def find_post(post_id: int):
    """
    @param post_id: The Id for the post in the post_table
    """
    logger.info("Finding post with Id: %d", post_id)
    query: ClauseElement = post_table.select().where(post_table.c.id == post_id)
    return await database.fetch_one(query)


@router.post(
    "/post",
    response_model=UserPost,
    status_code=status.HTTP_201_CREATED,
)
async def create_post(
    post: UserPostIn, current_user: Annotated[User, Depends(get_user_from_a_jwt)]
):
    """
    @param post: User post to add to the DB
    @param current_user: FastAPI Dependency injection, protecting the endpoint: First we authenticate the user
    """
    logger.info("Creating a post: %s", post)

    # Then we insert the post into the DB
    data = {**post.model_dump(), "user_id": current_user.id}
    query: ClauseElement = post_table.insert().values(data)
    logger.debug(query)

    # We return the inserted record with the record ID
    last_record_id: int = await database.execute(query)
    return {**data, "id": last_record_id}


class PostSorting(str, Enum):
    """Available sorting methods"""
    NEW = "new"
    OLD = "old"
    MOSTLIKES = "most_likes"


@router.get(
    "/post",
    response_model=list[UserPostWithLikes],
    status_code=status.HTTP_200_OK,
)
async def get_all_posts(sorting: PostSorting = PostSorting.NEW):  # http://.../post?sorting=most_files
    """Get all the post with their likes sorted by the number of likes"""
    logger.info("Getting all the posts")

    match(sorting):
        case PostSorting.NEW:
            query = select_post_and_likes.order_by(post_table.c.id.desc())
        case PostSorting.OLD:
            query = select_post_and_likes.order_by(post_table.c.id.asc())
        case PostSorting.MOSTLIKES:
            query = select_post_and_likes.order_by(sqlalchemy.desc("likes"))

    logger.debug(query)

    return await database.fetch_all(query)


@router.post(
    "/comment",
    response_model=Comment,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    comment: CommentIn, current_user: Annotated[User, Depends(get_user_from_a_jwt)]
):
    """
    @param comment: Comment to add to a post
    @param current_user: FastAPI Dependency injection, protecting the endpoint: First we authenticate the user
    """
    logger.info("Creating a comment (%s)", comment)

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


@router.get(
    "/post/{post_id}/comments",
    response_model=list[Comment],
    status_code=status.HTTP_200_OK,
)
async def get_comments_on_post(post_id: int):
    """
    @param post_id: The Id for the post in the post_table
    """
    logger.info("Getting the comments from a post (Id: %d)", post_id)
    query: ClauseElement = comments_table.select().where(
        comments_table.c.post_id == post_id
    )
    logger.debug(query)

    return await database.fetch_all(query)


@router.get(
    "/post/{post_id}",
    response_model=UserPostWithComments,
    status_code=status.HTTP_200_OK,
)
async def get_post_with_comments(post_id: int):
    """
    @param post_id: The Id for the post in the post_table
    """
    logger.info("Getting the post and comments (Post Id: %d)", post_id)

    query: ClauseElement = select_post_and_likes.where(post_table.c.id == post_id)
    logger.debug(query)

    post = await database.fetch_one(query)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with Id {post_id} not found",
        )

    return {
        "post": post,
        "comments": await get_comments_on_post(post_id),
    }


@router.post(
    "/like",
    response_model=PostLike,
    status_code=status.HTTP_201_CREATED,
)
async def like_post(
    like: PostLikeIn, current_user: Annotated[User, Depends(get_user_from_a_jwt)]
):
    """
    @param like: Like to add to a post
    @param current_user: FastAPI Dependency injection, protecting the endpoint: First we authenticate the user
    """
    logger.info("Creating a like (%d)", like)

    # Then we find the post in the DB
    post = await find_post(like.post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with Id {like.post_id} not found",
        )

    # And insert the like into the DB
    data = {**like.model_dump(), "user_id": current_user.id}
    query: ClauseElement = like_table.insert().values(data)
    logger.debug(query)

    last_record_id: int = await database.execute(query)
    return {**data, "id": last_record_id}
