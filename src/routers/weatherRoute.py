from fastapi import APIRouter

from src.schemas.weather_schema import ChatRequest

from src.agents.weather_agent import run_weather_agent

router = APIRouter(
    prefix="/weather",
    tags=["Weather AI"],
)


@router.post("/chat")
async def weather_chat(payload: ChatRequest):
    result = await run_weather_agent(payload.message)
    return {
        "success": True,
        "data": result,
    }
