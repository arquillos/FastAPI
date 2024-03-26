from pydantic import BaseModel


class User(BaseModel):
    """Model for user data"""

    id: int | None = None  # When creating a user the ID is unknown
    email: str


class UserIn(User):
    """Model to output the data"""

    password: str
