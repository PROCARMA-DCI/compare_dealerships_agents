from pydantic import BaseModel, Field


class DatabaseChatRequest(BaseModel):
    message: str = Field(..., min_length=1)


class DatabaseSearchRequest(BaseModel):
    table_name: str = Field(..., description="Allowed table name, for example users or products")
    search: str = Field(default="", description="Search text")
    limit: int = Field(default=10, ge=1, le=25)
