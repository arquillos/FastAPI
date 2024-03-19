from pydantic import BaseModel


class User(BaseModel):
    id: int | None = None  # When creating a user the ID is unknown
    email: str


class UserIn(User):
    password: str
