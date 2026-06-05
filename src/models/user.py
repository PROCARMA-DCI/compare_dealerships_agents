from sqlmodel import SQLModel, Field


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True, max_length=100)
    email: str = Field(unique=True, index=True, max_length=255)
    hashed_password: str
