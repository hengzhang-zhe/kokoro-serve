from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import router
from app.config import get_settings
from app.engine import get_engine

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = get_engine()
    engine.load()
    yield

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Self-hosted API service for official Kokoro inference.",
    lifespan=lifespan,
)

app.include_router(router)
