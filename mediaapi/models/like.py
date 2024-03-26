from pydantic import BaseModel, ConfigDict


class PostLikeIn(BaseModel):
    """Model to like a post"""

    post_id: int


class PostLike(PostLikeIn):
    """Model to output the data"""

    # Needed for sqlalchemy rows objects
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int