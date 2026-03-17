"""Tests for readiness probe endpoint."""

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


class TestReadinessEndpoint:
    async def test_ready_returns_200_when_redis_ok(
        self, client: httpx.AsyncClient
    ) -> None:
        mock_redis = AsyncMock()
        mock_redis.ping.return_value = True
        with patch("app.main.get_redis", return_value=mock_redis):
            response = await client.get("/ready")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ready"
        assert body["redis"] == "ok"

    async def test_ready_returns_503_when_redis_down(
        self, client: httpx.AsyncClient
    ) -> None:
        mock_redis = AsyncMock()
        mock_redis.ping.side_effect = ConnectionError("Redis unavailable")
        with patch("app.main.get_redis", return_value=mock_redis):
            response = await client.get("/ready")
        assert response.status_code == 503
        body = response.json()
        assert body["status"] == "not_ready"
        assert body["redis"] == "error"

    async def test_ready_returns_json_content_type(
        self, client: httpx.AsyncClient
    ) -> None:
        mock_redis = AsyncMock()
        mock_redis.ping.return_value = True
        with patch("app.main.get_redis", return_value=mock_redis):
            response = await client.get("/ready")
        assert "application/json" in response.headers["content-type"]
