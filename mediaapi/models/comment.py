from pydantic import BaseModel, ConfigDict


class CommentIn(BaseModel):
    """Model to comment a post"""

    body: str
    post_id: int


class Comment(CommentIn):
    """Model to output the data"""

    # Needed for sqlalchemy rows objects
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int

