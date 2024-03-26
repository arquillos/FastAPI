from pydantic import BaseModel, ConfigDict

from mediaapi.models.comment import Comment


class UserPostIn(BaseModel):
    """Model for a post"""
    body: str


class UserPost(UserPostIn):
    """Model to output the data"""
    # Needed for sqlalchemy rows objects
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int


class UserPostWithLikes(UserPost):
    """Model for a post with the number of likes"""
    # Needed for sqlalchemy rows objects
    model_config = ConfigDict(from_attributes=True)

    likes: int


class UserPostWithComments(BaseModel):
    """Model for a post with the comments and the number of likes"""
    # Needed for sqlalchemy rows objects
    model_config = ConfigDict(from_attributes=True)

    post: UserPostWithLikes
    comments: list[Comment]
