from agents import Agent
from agents import Runner

from src.schemas.weather_schema import WeatherReport

from src.agents.tools.weather_tool import (
    get_my_location,
    get_weather,
)

weather_agent = Agent(
    name="Weather Assistant",
    instructions="""
    You help users check weather.

    If user does not provide a city:
    1. Call get_my_location
    2. Extract city
    3. Call get_weather

    Return clean structured in md format.
    """,
    tools=[
        get_my_location,
        get_weather,
    ],
    # output_type=WeatherReport,
)


async def run_weather_agent(message: str):
    result = await Runner.run(
        weather_agent,
        message,
    )

    return result.final_output
