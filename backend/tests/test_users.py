"""Tests for user endpoints and get_current_user auth dependency."""

from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi import HTTPException
from google.auth.exceptions import GoogleAuthError
from httpx import ASGITransport

from app.auth.dependencies import get_current_user
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
        with patch(
            "app.auth.dependencies.verify_oauth2_token",
            return_value=google_claims,
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

        response = await client.get("/api/users/me")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "override-user"
        assert data["email"] == "override@example.com"
        assert data["granted_scopes"] == ["calendar.events"]
