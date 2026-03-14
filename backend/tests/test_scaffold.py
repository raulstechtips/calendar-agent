"""Tests for FastAPI scaffold: health endpoint, CORS, request ID, rate limiting."""

from collections.abc import AsyncGenerator

import httpx
import pytest
from httpx import ASGITransport
from pydantic import ValidationError

from app.main import app


@pytest.fixture
async def client() -> AsyncGenerator[httpx.AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestHealthEndpoint:
    async def test_health_returns_ok(self, client: httpx.AsyncClient) -> None:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    async def test_health_returns_json_content_type(
        self, client: httpx.AsyncClient
    ) -> None:
        response = await client.get("/health")
        assert "application/json" in response.headers["content-type"]


class TestCORS:
    async def test_cors_allows_configured_origin(
        self, client: httpx.AsyncClient
    ) -> None:
        response = await client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert (
            response.headers.get("access-control-allow-origin")
            == "http://localhost:3000"
        )

    async def test_cors_rejects_unconfigured_origin(
        self, client: httpx.AsyncClient
    ) -> None:
        response = await client.options(
            "/health",
            headers={
                "Origin": "http://evil.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.headers.get("access-control-allow-origin") != "http://evil.com"

    async def test_cors_allows_credentials(self, client: httpx.AsyncClient) -> None:
        response = await client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.headers.get("access-control-allow-credentials") == "true"


class TestRequestID:
    async def test_response_has_request_id_header(
        self, client: httpx.AsyncClient
    ) -> None:
        response = await client.get("/health")
        assert "x-request-id" in response.headers

    async def test_echoes_provided_request_id(self, client: httpx.AsyncClient) -> None:
        request_id = "550e8400-e29b-41d4-a716-446655440000"
        response = await client.get(
            "/health",
            headers={"X-Request-ID": request_id},
        )
        assert response.headers["x-request-id"] == request_id

    async def test_generates_request_id_when_not_provided(
        self, client: httpx.AsyncClient
    ) -> None:
        response = await client.get("/health")
        request_id = response.headers.get("x-request-id")
        assert request_id is not None
        assert len(request_id) > 0


class TestRateLimiting:
    def test_slowapi_middleware_registered(self) -> None:
        from slowapi.middleware import SlowAPIMiddleware

        middleware_classes = [m.cls for m in app.user_middleware]
        # Starlette types middleware.cls as _MiddlewareFactory, not the concrete class
        assert SlowAPIMiddleware in middleware_classes  # type: ignore[comparison-overlap]

    def test_limiter_configured_on_app_state(self) -> None:
        from slowapi import Limiter

        assert hasattr(app.state, "limiter")
        assert isinstance(app.state.limiter, Limiter)


class TestConfig:
    def test_config_loads_defaults(self) -> None:
        from app.core.config import Settings

        settings = Settings()
        assert settings.cors_origins == ["http://localhost:3000"]
        assert settings.redis_url == "redis://localhost:6379/0"

    def test_config_parses_multiple_cors_origins(self) -> None:
        from app.core.config import Settings

        # Testing Pydantic before-validator that parses str → list[str]
        settings = Settings(cors_origins="http://localhost:3000,http://localhost:8080")  # pyright: ignore[reportArgumentType]
        assert settings.cors_origins == [
            "http://localhost:3000",
            "http://localhost:8080",
        ]

    def test_config_rejects_wildcard_cors_origin(self) -> None:
        from app.core.config import Settings

        with pytest.raises(ValidationError, match="wildcard"):
            Settings(cors_origins="*")  # pyright: ignore[reportArgumentType]

    def test_config_strips_empty_cors_origins(self) -> None:
        from app.core.config import Settings

        settings = Settings(cors_origins="http://localhost:3000,,")  # pyright: ignore[reportArgumentType]
        assert settings.cors_origins == ["http://localhost:3000"]
