from pydantic import BaseModel, ConfigDict


class UserPostIn(BaseModel):
    body: str


class UserPost(UserPostIn):
    # Needed for sqlalchemy rows objects
    model_config = ConfigDict(from_attributes=True)

    id: int


class CommentIn(BaseModel):
    body: str
    post_id: int


class Comment(CommentIn):
    # Needed for sqlalchemy rows objects
    model_config = ConfigDict(from_attributes=True)

    id: int


class UserPostWithComments(BaseModel):
    post: UserPost
    comments: list[Comment]
