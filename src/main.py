from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routers import databaseRoute
from src.routers import weatherRoute

app = FastAPI(
    title="AI Weather Assistant",
    root_path="/api",
    version="1.0.1",
)

# Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
    ],  # or "*"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(weatherRoute.router)
app.include_router(databaseRoute.router)
