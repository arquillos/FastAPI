import logging
from http import HTTPStatus

from fastapi import APIRouter, HTTPException
from sqlalchemy.sql import ClauseElement

from mediaapi.database import comments_table, database, post_table
from mediaapi.models.post import (
    Comment,
    CommentIn,
    UserPost,
    UserPostIn,
    UserPostWithComments,
)

router = APIRouter()

logger = logging.getLogger(__name__)


async def find_post(post_id: int):
    logger.info(f"Finding post with Id: {post_id}")
    query: ClauseElement = post_table.select().where(post_table.c.id == post_id)
    return await database.fetch_one(query)


@router.post("/post", response_model=UserPost, status_code=201)
async def create_post(post: UserPostIn):
    logger.info(f"Creating a post: {post}")
    data = post.model_dump()
    query: ClauseElement = post_table.insert().values(data)
    logger.debug(query)

    last_record_id: int = await database.execute(query)
    return {**data, "id": last_record_id}


@router.get("/post", response_model=list[UserPost])
async def get_all_posts():
    logger.info("Getting all the posts")
    query = post_table.select()
    logger.debug(query)

    return await database.fetch_all(query)


@router.post("/comment", response_model=Comment, status_code=HTTPStatus.CREATED)
async def create_comment(comment: CommentIn):
    logger.info(f"Creating a comment ({comment})")
    post = await find_post(comment.post_id)
    if not post:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"Post with Id {comment.post_id} not found",
        )

    data = comment.model_dump()
    query: ClauseElement = comments_table.insert().values(data)
    logger.debug(query)

    last_record_id: int = await database.execute(query)
    return {**data, "id": last_record_id}


@router.get("/post/{post_id}/comments", response_model=list[Comment])
async def get_comments_on_post(post_id: int):
    logger.info(f"Getting the comments from a post (Id: {post_id})")
    query: ClauseElement = comments_table.select().where(
        comments_table.c.post_id == post_id
    )
    logger.debug(query)

    return await database.fetch_all(query)


@router.get("/post/{post_id}", response_model=UserPostWithComments)
async def get_post_with_comments(post_id: int):
    logger.info(f"Getting the post and comments (Post Id: {post_id})")
    post = await find_post(post_id)
    if not post:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail=f"Post with Id {post_id} not found"
        )
    else:
        logger.info("Unbexpected post found!")
    return {
        "post": post,
        "comments": await get_comments_on_post(post_id),
    }
