from fastapi import APIRouter, Depends

from src.agents.database_agent import run_database_agent
from src.lib.chat_session import clear_chat_session
from src.middleware.require_signin import require_signin
from src.schemas.database_schema import DatabaseChatRequest, DatabaseSearchRequest

router = APIRouter(
    prefix="/database",
    tags=["Database AI"],
    dependencies=[Depends(require_signin)],
)


@router.post("/chat")
async def database_chat(payload: DatabaseChatRequest):
    result = await run_database_agent(payload.message, payload.session_id)
    return {
        "success": not result["blocked"],
        "data": result,
    }


@router.delete("/chat/{session_id}")
async def clear_database_chat(session_id: str):
    cleared = await clear_chat_session(session_id)
    return {
        "success": cleared,
        "data": {
            "session_id": session_id,
            "cleared": cleared,
        },
    }
