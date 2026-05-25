from fastapi import APIRouter

from src.agents.database_agent import run_database_agent
from src.agents.tools.db_tool import search_table_records
from src.schemas.database_schema import DatabaseChatRequest, DatabaseSearchRequest

router = APIRouter(
    prefix="/database",
    tags=["Database AI"],
)


@router.post("/chat")
async def database_chat(payload: DatabaseChatRequest):
    result = await run_database_agent(payload.message)
    return {
        "success": not result["blocked"],
        "data": result,
    }


@router.post("/search")
async def database_search(payload: DatabaseSearchRequest):
    result = search_table_records(payload.table_name, payload.search, payload.limit)
    return {
        "success": "error" not in result,
        "data": result,
    }
