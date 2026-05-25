from pydantic import BaseModel, Field


class WeatherReport(BaseModel):
    city: str
    temperature: float = Field(description="Current temperature in Celsius")
    feels_like: float = Field(description="Feels like temperature in Celsius")
    advice: str = Field(description="Short advice based on weather")


class ChatRequest(BaseModel):
    message: str
