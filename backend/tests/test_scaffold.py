"""Tests for FastAPI scaffold: health endpoint, CORS, request ID, rate limiting."""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from httpx import ASGITransport
from pydantic import ValidationError
from starlette.requests import Request

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

    async def test_health_returns_ok_even_when_redis_down(
        self, client: httpx.AsyncClient
    ) -> None:
        mock_redis = AsyncMock()
        mock_redis.ping.side_effect = ConnectionError("Redis unavailable")
        with patch("app.main.get_redis", return_value=mock_redis):
            response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestGoogleTransportCleanup:
    def test_close_google_transport_closes_session(self) -> None:
        from unittest.mock import MagicMock

        from app.auth import dependencies

        # Ensure clean state (async fixture teardown from prior tests may interleave)
        dependencies._google_transport = None
        transport = dependencies._get_google_transport()
        mock_session = MagicMock()
        transport.session = mock_session
        dependencies.close_google_transport()
        # GoogleAuthRequest.__del__ also calls session.close(), so assert ≥1 call
        assert mock_session.close.called
        assert dependencies._google_transport is None

    def test_close_google_transport_resets_global(self) -> None:
        from app.auth import dependencies

        dependencies._get_google_transport()
        assert dependencies._google_transport is not None
        dependencies.close_google_transport()
        assert dependencies._google_transport is None

    def test_close_google_transport_noop_when_none(self) -> None:
        from app.auth import dependencies

        dependencies._google_transport = None
        dependencies.close_google_transport()
        assert dependencies._google_transport is None


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

    async def test_cors_allows_post_method(self, client: httpx.AsyncClient) -> None:
        response = await client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )
        allowed = response.headers.get("access-control-allow-methods", "")
        assert "POST" in allowed

    async def test_cors_rejects_put_method(self, client: httpx.AsyncClient) -> None:
        response = await client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "PUT",
            },
        )
        assert response.status_code == 400
        allowed = response.headers.get("access-control-allow-methods", "")
        assert "PUT" not in allowed

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

    def test_limiter_uses_user_based_key_func(self) -> None:
        from app.core.middleware import get_user_from_token, limiter

        assert limiter._key_func is get_user_from_token  # pyright: ignore[reportPrivateUsage]


class TestGetUserFromToken:
    """Unit tests for the JWT-based rate-limit key function."""

    def _make_jwt(self, payload: dict[str, str | int]) -> str:
        """Build a fake unsigned JWT with the given payload claims."""
        import base64
        import json as _json

        header = base64.urlsafe_b64encode(b'{"alg":"RS256"}').rstrip(b"=").decode()
        body = base64.urlsafe_b64encode(
            _json.dumps(payload).encode()
        ).rstrip(b"=").decode()
        sig = base64.urlsafe_b64encode(b"fakesig").rstrip(b"=").decode()
        return f"{header}.{body}.{sig}"

    def _make_request(self, headers: dict[str, str] | None = None) -> Request:
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/chat",
            "headers": [
                (k.lower().encode(), v.encode())
                for k, v in (headers or {}).items()
            ],
            "query_string": b"",
            "root_path": "",
            "server": ("127.0.0.1", 8000),
        }
        return Request(scope)

    def test_extracts_sub_from_valid_jwt(self) -> None:
        from app.core.middleware import get_user_from_token

        token = self._make_jwt({"sub": "google-user-123", "aud": "test"})
        request = self._make_request({"Authorization": f"Bearer {token}"})
        assert get_user_from_token(request) == "google-user-123"

    def test_falls_back_to_ip_on_missing_header(self) -> None:
        from app.core.middleware import get_user_from_token

        request = self._make_request()
        result = get_user_from_token(request)
        # Should return IP address, not a user sub
        assert result != ""
        assert "google" not in result

    def test_falls_back_to_ip_on_malformed_token(self) -> None:
        from app.core.middleware import get_user_from_token

        request = self._make_request({"Authorization": "Bearer not-a-jwt"})
        result = get_user_from_token(request)
        assert result != ""
        assert "google" not in result

    def test_falls_back_to_ip_on_missing_sub(self) -> None:
        from app.core.middleware import get_user_from_token

        token = self._make_jwt({"aud": "test", "iss": "accounts.google.com"})
        request = self._make_request({"Authorization": f"Bearer {token}"})
        result = get_user_from_token(request)
        assert "google" not in result

    def test_falls_back_to_ip_on_empty_sub(self) -> None:
        from app.core.middleware import get_user_from_token

        token = self._make_jwt({"sub": "", "aud": "test"})
        request = self._make_request({"Authorization": f"Bearer {token}"})
        result = get_user_from_token(request)
        assert result != ""
        assert "." in result or result.startswith("127")  # IP address, not a sub


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
