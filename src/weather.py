# Refrences

# https://openai.github.io/openai-agents-python/tools/
# https://openai.github.io/openai-agents-python/agents/#output-types

from pydantic import BaseModel, Field
import requests

from config import OPEN_WEATHER_API_KEY

from agents import Agent, Runner, function_tool


class WeatherReport(BaseModel):
    city: str
    temperature: float = Field(description="Current temperature in Celsius")
    feels_like: float = Field(description="Feels like temperature in Celsius")
    advice: str = Field(description="Short advice based on weather eg. carry umbrella")


@function_tool
def get_my_location() -> dict:
    """Detects the user's current city based on their IP address."""
    response = requests.get("http://ip-api.com/json/")
    data = response.json()

    if data.get("status") != "success":
        return {"error": "Could not detect location"}

    return data


@function_tool
def get_weather(city: str):
    api_key = OPEN_WEATHER_API_KEY

    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

    response = requests.get(url)
    data = response.json()

    if response.status_code != 200:
        return {"error": "City not found"}

    return {
        "city": data["name"],
        "temperature": data["main"]["temp"],
        "feels_like": data["main"]["feels_like"],
        "humidity": data["main"]["humidity"],
        "description": data["weather"][0]["description"],
    }


agent = Agent(
    name="Weather Assistant",
    instructions="""You help users check the weather.
    If the user doesn't specify a city, use get_my_location to detect their city first,
    then call get_weather with that city.""",
    tools=[get_my_location, get_weather],
    output_type=WeatherReport,
)

# result = Runner.run_sync(
#     agent, "What's the weather in Lahore, Islamabad, New York, Mumbai?"
# )
result = Runner.run_sync(agent, "What's the weather in my city?")

print(result.final_output)
