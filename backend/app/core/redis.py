"""Async Redis client with connection pooling and TLS support."""

from redis.asyncio import Redis

from app.core.config import settings

_redis_client: Redis | None = None


def create_redis(url: str) -> Redis:
    """Create a new async Redis client from a URL."""
    return Redis.from_url(url, decode_responses=True)


def get_redis() -> Redis:
    """Return the singleton async Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = create_redis(settings.redis_url)
    return _redis_client


async def close_redis(client: Redis) -> None:
    """Close an async Redis client connection."""
    await client.aclose()
