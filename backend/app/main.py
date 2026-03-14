from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.middleware import setup_middleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup: initialize shared resources here (Redis, HTTP clients)
    yield
    # Shutdown: clean up shared resources here


app = FastAPI(title="AI Calendar Assistant", lifespan=lifespan)

setup_middleware(app)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
