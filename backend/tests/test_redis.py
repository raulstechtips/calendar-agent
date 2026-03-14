"""Tests for async Redis client: connection, health check, and lifecycle."""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from httpx import ASGITransport

from app.main import app


@pytest.fixture
async def client() -> AsyncGenerator[httpx.AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestRedisClient:
    def test_get_redis_returns_async_client(self) -> None:
        from app.core.redis import get_redis

        client = get_redis()

        from redis.asyncio import Redis

        assert isinstance(client, Redis)

    def test_get_redis_returns_same_instance(self) -> None:
        from app.core.redis import get_redis

        assert get_redis() is get_redis()

    def test_redis_configured_with_decode_responses(self) -> None:
        from app.core.redis import get_redis

        client = get_redis()
        connection_kwargs = client.connection_pool.connection_kwargs
        assert connection_kwargs.get("decode_responses") is True

    def test_redis_supports_tls_url(self) -> None:
        from redis.asyncio.connection import SSLConnection

        from app.core.redis import create_redis

        tls_url = "rediss://:password@host:6380/0"
        client = create_redis(tls_url)
        assert client.connection_pool.connection_class is SSLConnection

    def test_redis_default_url_no_tls(self) -> None:
        from redis.asyncio.connection import Connection, SSLConnection

        from app.core.redis import get_redis

        client = get_redis()
        assert client.connection_pool.connection_class is not SSLConnection
        assert client.connection_pool.connection_class is Connection


class TestHealthEndpointWithRedis:
    async def test_health_includes_redis_status_ok(
        self, client: httpx.AsyncClient
    ) -> None:
        mock_redis = AsyncMock()
        mock_redis.ping.return_value = True

        with patch("app.main.get_redis", return_value=mock_redis):
            response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["redis"] == "ok"

    async def test_health_includes_redis_status_error(
        self, client: httpx.AsyncClient
    ) -> None:
        mock_redis = AsyncMock()
        mock_redis.ping.side_effect = ConnectionError("Connection refused")

        with patch("app.main.get_redis", return_value=mock_redis):
            response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["redis"] == "error"


class TestRedisLifecycle:
    async def test_close_redis_calls_aclose(self) -> None:
        from app.core.redis import close_redis, create_redis

        client = create_redis("redis://localhost:6379/0")
        with patch.object(client, "aclose", new_callable=AsyncMock) as mock_aclose:
            await close_redis(client)
            mock_aclose.assert_awaited_once()
