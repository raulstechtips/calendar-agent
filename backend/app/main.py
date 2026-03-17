"""FastAPI application entry point with middleware and lifespan management."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.agents.router import router as agents_router
from app.auth.dependencies import close_google_transport
from app.auth.router import router as auth_router
from app.core.middleware import setup_middleware
from app.core.redis import close_redis, get_redis
from app.search.embeddings import close_embeddings_client, get_embeddings_client
from app.search.index import create_index
from app.search.service import close_search_client, get_search_client
from app.users.router import router as users_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup: eagerly create clients (connections are lazy on first command)
    get_redis()
    get_search_client()
    get_embeddings_client()
    # Ensure search index exists (idempotent — safe on every startup)
    await create_index()
    logger.info("Search index ready")
    yield
    # Shutdown: clean up connections (isolate exceptions so both always run)
    try:
        await close_redis()
    except Exception:
        logger.exception("Failed to close Redis client")
    try:
        await close_search_client()
    except Exception:
        logger.exception("Failed to close search client")
    try:
        close_embeddings_client()
    except Exception:
        logger.exception("Failed to close embeddings client")
    try:
        close_google_transport()
    except Exception:
        logger.exception("Failed to close Google auth transport")


app = FastAPI(title="AI Calendar Assistant", lifespan=lifespan)

setup_middleware(app)


app.include_router(agents_router)
app.include_router(auth_router)
app.include_router(users_router)


@app.get("/health")
async def health() -> JSONResponse:
    """Liveness probe — confirms the process can serve HTTP."""
    return JSONResponse(content={"status": "ok"})


@app.get("/ready")
async def readiness() -> JSONResponse:
    """Readiness probe — checks dependency connectivity."""
    try:
        await get_redis().ping()  # type: ignore[misc]
    except Exception:
        logger.warning("Readiness check failed: Redis unreachable", exc_info=True)
        return JSONResponse(
            content={"status": "not_ready", "redis": "error"},
            status_code=503,
        )
    return JSONResponse(content={"status": "ready", "redis": "ok"})
