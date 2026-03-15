"""FastAPI application entry point with middleware and lifespan management."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.agents.router import router as agents_router
from app.auth.router import router as auth_router
from app.core.middleware import setup_middleware
from app.core.redis import close_redis, get_redis
from app.users.router import router as users_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup: eagerly create the Redis client (connection is lazy on first command)
    get_redis()
    yield
    # Shutdown: clean up Redis connection
    await close_redis()


app = FastAPI(title="AI Calendar Assistant", lifespan=lifespan)

setup_middleware(app)


app.include_router(agents_router)
app.include_router(auth_router)
app.include_router(users_router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Return service health status including Redis connectivity."""
    redis_status = "ok"
    try:
        await get_redis().ping()  # type: ignore[misc]
    except Exception:
        logger.warning("Redis health check failed", exc_info=True)
        redis_status = "error"
    return {"status": "ok", "redis": redis_status}
