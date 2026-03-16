"""Tests for user endpoints and get_current_user auth dependency."""

from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi import HTTPException
from google.auth.exceptions import GoogleAuthError, TransportError
from httpx import ASGITransport

from app.auth.dependencies import get_current_user
from app.auth.token_storage import (
    StoredToken,
    TokenEncryptionError,
    TokenNotFoundError,
)
from app.main import app
from app.users.schemas import UserResponse
from tests.conftest import (
    TEST_USER_EMAIL,
    TEST_USER_ID,
    TEST_USER_NAME,
    TEST_USER_PICTURE,
)


@pytest.fixture
async def client() -> AsyncGenerator[httpx.AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


class TestGetCurrentUser:
    """Unit tests for get_current_user dependency (token verification)."""

    @pytest.fixture(autouse=True)
    def _mock_google_client_id(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "app.auth.dependencies.settings.google_client_id",
            "test-google-client-id",
        )

    async def test_should_return_user_from_valid_google_id_token(
        self,
        google_claims: dict[str, Any],
    ) -> None:
        mock_creds = AsyncMock()
        mock_creds.credentials = "valid-id-token"

        with patch(
            "app.auth.dependencies.verify_oauth2_token",
            return_value=google_claims,
        ):
            user = await get_current_user(credentials=mock_creds)

        assert user.id == TEST_USER_ID
        assert user.email == TEST_USER_EMAIL
        assert user.name == TEST_USER_NAME
        assert user.picture == TEST_USER_PICTURE
        assert user.granted_scopes == []

    async def test_should_use_email_as_name_when_name_claim_missing(
        self,
        google_claims: dict[str, Any],
    ) -> None:
        claims_without_name = {k: v for k, v in google_claims.items() if k != "name"}
        mock_creds = AsyncMock()
        mock_creds.credentials = "valid-id-token"

        with patch(
            "app.auth.dependencies.verify_oauth2_token",
            return_value=claims_without_name,
        ):
            user = await get_current_user(credentials=mock_creds)

        assert user.name == TEST_USER_EMAIL

    async def test_should_handle_missing_picture_claim(
        self,
        google_claims: dict[str, Any],
    ) -> None:
        claims_without_picture = {
            k: v for k, v in google_claims.items() if k != "picture"
        }
        mock_creds = AsyncMock()
        mock_creds.credentials = "valid-id-token"

        with patch(
            "app.auth.dependencies.verify_oauth2_token",
            return_value=claims_without_picture,
        ):
            user = await get_current_user(credentials=mock_creds)

        assert user.picture is None

    async def test_should_reject_missing_authorization_header(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=None)
        assert exc_info.value.status_code == 401
        assert "authorization" in exc_info.value.detail.lower()

    async def test_should_reject_invalid_token(self) -> None:
        mock_creds = AsyncMock()
        mock_creds.credentials = "invalid-token"

        with (
            patch(
                "app.auth.dependencies.verify_oauth2_token",
                side_effect=ValueError("Token is not valid"),
            ),
            pytest.raises(HTTPException) as exc_info,
        ):
            await get_current_user(credentials=mock_creds)

        assert exc_info.value.status_code == 401

    async def test_should_reject_expired_token(self) -> None:
        mock_creds = AsyncMock()
        mock_creds.credentials = "expired-token"

        with (
            patch(
                "app.auth.dependencies.verify_oauth2_token",
                side_effect=ValueError("Token expired"),
            ),
            pytest.raises(HTTPException) as exc_info,
        ):
            await get_current_user(credentials=mock_creds)

        assert exc_info.value.status_code == 401

    async def test_should_reject_wrong_issuer(self) -> None:
        mock_creds = AsyncMock()
        mock_creds.credentials = "wrong-issuer-token"

        with (
            patch(
                "app.auth.dependencies.verify_oauth2_token",
                side_effect=GoogleAuthError("Wrong issuer"),  # type: ignore[no-untyped-call]
            ),
            pytest.raises(HTTPException) as exc_info,
        ):
            await get_current_user(credentials=mock_creds)

        assert exc_info.value.status_code == 401

    async def test_should_pass_google_client_id_as_audience(
        self,
        google_claims: dict[str, Any],
    ) -> None:
        mock_creds = AsyncMock()
        mock_creds.credentials = "valid-id-token"

        with (
            patch(
                "app.auth.dependencies.verify_oauth2_token",
                return_value=google_claims,
            ) as mock_verify,
            patch(
                "app.auth.dependencies.settings",
            ) as mock_settings,
        ):
            mock_settings.google_client_id = "my-real-client-id"
            await get_current_user(credentials=mock_creds)

        mock_verify.assert_called_once()
        _, kwargs = mock_verify.call_args
        assert kwargs["audience"] == "my-real-client-id"

    async def test_should_return_500_when_google_client_id_not_configured(
        self,
    ) -> None:
        mock_creds = AsyncMock()
        mock_creds.credentials = "valid-id-token"

        with (
            patch("app.auth.dependencies.settings") as mock_settings,
            pytest.raises(HTTPException) as exc_info,
        ):
            mock_settings.google_client_id = ""
            await get_current_user(credentials=mock_creds)

        assert exc_info.value.status_code == 500

    async def test_should_return_502_on_transport_error(self) -> None:
        mock_creds = AsyncMock()
        mock_creds.credentials = "valid-id-token"

        with (
            patch(
                "app.auth.dependencies.verify_oauth2_token",
                side_effect=TransportError("Could not fetch certificates"),  # type: ignore[no-untyped-call]
            ),
            pytest.raises(HTTPException) as exc_info,
        ):
            await get_current_user(credentials=mock_creds)

        assert exc_info.value.status_code == 502

    async def test_should_return_401_for_missing_required_claims(self) -> None:
        mock_creds = AsyncMock()
        mock_creds.credentials = "valid-id-token"
        claims_missing_sub = {"email": "test@example.com", "iss": "accounts.google.com"}

        with (
            patch(
                "app.auth.dependencies.verify_oauth2_token",
                return_value=claims_missing_sub,
            ),
            pytest.raises(HTTPException) as exc_info,
        ):
            await get_current_user(credentials=mock_creds)

        assert exc_info.value.status_code == 401


class TestGetMeEndpoint:
    """Integration tests for GET /api/users/me."""

    @pytest.fixture(autouse=True)
    def _mock_google_client_id(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "app.auth.dependencies.settings.google_client_id",
            "test-google-client-id",
        )

    async def test_should_return_user_profile_with_valid_token(
        self,
        client: httpx.AsyncClient,
        google_claims: dict[str, Any],
        auth_headers: dict[str, str],
    ) -> None:
        with (
            patch(
                "app.auth.dependencies.verify_oauth2_token",
                return_value=google_claims,
            ),
            patch(
                "app.users.service.get_token",
                side_effect=TokenNotFoundError("No token"),
            ),
        ):
            response = await client.get("/api/users/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == TEST_USER_ID
        assert data["email"] == TEST_USER_EMAIL
        assert data["name"] == TEST_USER_NAME
        assert data["picture"] == TEST_USER_PICTURE
        assert data["granted_scopes"] == []

    async def test_should_return_401_without_authorization_header(
        self,
        client: httpx.AsyncClient,
    ) -> None:
        response = await client.get("/api/users/me")
        assert response.status_code == 401

    async def test_should_return_401_with_invalid_token(
        self,
        client: httpx.AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        with patch(
            "app.auth.dependencies.verify_oauth2_token",
            side_effect=ValueError("Invalid token"),
        ):
            response = await client.get("/api/users/me", headers=auth_headers)

        assert response.status_code == 401

    async def test_should_work_with_dependency_override(
        self,
        client: httpx.AsyncClient,
    ) -> None:
        mock_user = UserResponse(
            id="override-user",
            email="override@example.com",
            name="Override User",
            picture="https://example.com/photo.jpg",
            granted_scopes=["calendar.events"],
        )

        async def override_user() -> UserResponse:
            return mock_user

        app.dependency_overrides[get_current_user] = override_user

        with patch(
            "app.users.service.get_token",
            side_effect=TokenNotFoundError("No token"),
        ):
            response = await client.get("/api/users/me")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "override-user"
        assert data["email"] == "override@example.com"


def _override_user(user: UserResponse) -> None:
    """Set a dependency override for get_current_user."""

    async def _override() -> UserResponse:
        return user

    app.dependency_overrides[get_current_user] = _override


class TestGetMeWithScopes:
    """Tests for scope enrichment via Redis token storage."""

    async def test_should_return_granted_scopes_from_redis(
        self,
        client: httpx.AsyncClient,
        mock_user: UserResponse,
    ) -> None:
        _override_user(mock_user)
        stored = StoredToken(
            access_token="enc-access",
            refresh_token="enc-refresh",
            expires_at=9999999999,
            scopes=[
                "openid",
                "email",
                "profile",
                "https://www.googleapis.com/auth/calendar.events",
            ],
        )

        with patch("app.users.service.get_token", return_value=stored):
            response = await client.get("/api/users/me")

        assert response.status_code == 200
        data = response.json()
        assert data["granted_scopes"] == [
            "openid",
            "email",
            "profile",
            "https://www.googleapis.com/auth/calendar.events",
        ]

    async def test_should_return_empty_scopes_when_no_token_in_redis(
        self,
        client: httpx.AsyncClient,
        mock_user: UserResponse,
    ) -> None:
        _override_user(mock_user)

        with patch(
            "app.users.service.get_token",
            side_effect=TokenNotFoundError("No token found"),
        ):
            response = await client.get("/api/users/me")

        assert response.status_code == 200
        data = response.json()
        assert data["granted_scopes"] == []

    async def test_should_return_empty_scopes_on_token_decryption_error(
        self,
        client: httpx.AsyncClient,
        mock_user: UserResponse,
    ) -> None:
        _override_user(mock_user)

        with patch(
            "app.users.service.get_token",
            side_effect=TokenEncryptionError("Decryption failed"),
        ):
            response = await client.get("/api/users/me")

        assert response.status_code == 200
        data = response.json()
        assert data["granted_scopes"] == []


class TestPreferencesEndpoints:
    """Tests for GET/PATCH /api/users/me/preferences."""

    @pytest.fixture(autouse=True)
    def _setup_user(self, mock_user: UserResponse) -> None:
        _override_user(mock_user)

    async def test_should_return_default_preferences(
        self,
        client: httpx.AsyncClient,
    ) -> None:
        with patch("app.users.service.get_redis") as mock_redis:
            mock_redis.return_value = AsyncMock()
            mock_redis.return_value.hgetall = AsyncMock(return_value={})
            response = await client.get("/api/users/me/preferences")

        assert response.status_code == 200
        data = response.json()
        assert data["timezone"] == "UTC"
        assert data["default_calendar"] == "primary"

    async def test_should_update_timezone(
        self,
        client: httpx.AsyncClient,
    ) -> None:
        store: dict[str, str] = {}

        async def fake_hset(_key: str, mapping: dict[str, str]) -> int:
            store.update(mapping)
            return len(mapping)

        async def fake_hgetall(_key: str) -> dict[str, str]:
            return dict(store)

        mock_redis_instance = AsyncMock()
        mock_redis_instance.hset = fake_hset
        mock_redis_instance.hgetall = fake_hgetall

        with patch("app.users.service.get_redis", return_value=mock_redis_instance):
            response = await client.patch(
                "/api/users/me/preferences",
                json={"timezone": "America/New_York"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["timezone"] == "America/New_York"
        assert data["default_calendar"] == "primary"

    async def test_should_update_partial_fields(
        self,
        client: httpx.AsyncClient,
    ) -> None:
        store: dict[str, str] = {
            "timezone": "Europe/London",
            "default_calendar": "work",
        }

        async def fake_hset(_key: str, mapping: dict[str, str]) -> int:
            store.update(mapping)
            return len(mapping)

        async def fake_hgetall(_key: str) -> dict[str, str]:
            return dict(store)

        mock_redis_instance = AsyncMock()
        mock_redis_instance.hset = fake_hset
        mock_redis_instance.hgetall = fake_hgetall

        with patch("app.users.service.get_redis", return_value=mock_redis_instance):
            response = await client.patch(
                "/api/users/me/preferences",
                json={"default_calendar": "personal"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["default_calendar"] == "personal"
        assert data["timezone"] == "Europe/London"

    async def test_should_reject_oversized_input(
        self,
        client: httpx.AsyncClient,
    ) -> None:
        response = await client.patch(
            "/api/users/me/preferences",
            json={"timezone": "x" * 200},
        )
        assert response.status_code == 422

    async def test_should_return_401_unauthenticated(
        self,
        client: httpx.AsyncClient,
    ) -> None:
        app.dependency_overrides.clear()
        response = await client.get("/api/users/me/preferences")
        assert response.status_code == 401
