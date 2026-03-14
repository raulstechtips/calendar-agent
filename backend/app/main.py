"""FastAPI application entry point with middleware and lifespan management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.agents.router import router as agents_router
from app.core.middleware import setup_middleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup: initialize shared resources here (Redis, HTTP clients)
    yield
    # Shutdown: clean up shared resources here


app = FastAPI(title="AI Calendar Assistant", lifespan=lifespan)

setup_middleware(app)


app.include_router(agents_router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Return service health status."""
    return {"status": "ok"}
