import requests

from agents import function_tool

from src.config import OPEN_WEATHER_API_KEY


@function_tool
def get_my_location() -> dict:
    """Detect user's city using IP."""

    response = requests.get("http://ip-api.com/json/")
    data = response.json()

    if data.get("status") != "success":
        return {"error": "Could not detect location"}

    return data


@function_tool
def get_weather(city: str):
    """Get weather by city."""

    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={city}"
        f"&appid={OPEN_WEATHER_API_KEY}"
        f"&units=metric"
    )

    response = requests.get(url)
    data = response.json()

    if response.status_code != 200:
        return {"error": "City not found"}

    description = data["weather"][0]["description"]
    temp = data["main"]["temp"]

    advice = "Weather looks good."

    if "rain" in description.lower():
        advice = "Carry an umbrella."

    elif temp > 35:
        advice = "Stay hydrated."

    elif temp < 10:
        advice = "Wear warm clothes."

    return {
        "city": data["name"],
        "temperature": temp,
        "feels_like": data["main"]["feels_like"],
        "advice": advice,
    }
