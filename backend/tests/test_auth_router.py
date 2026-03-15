"""Tests for auth router endpoints and service layer."""

import time
from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import requests
from httpx import ASGITransport

from app.auth.dependencies import get_current_user
from app.auth.token_storage import (
    StoredToken,
    TokenEncryptionError,
    TokenNotFoundError,
)
from app.main import app
from app.users.schemas import UserResponse
from tests.conftest import TEST_USER_EMAIL, TEST_USER_ID, TEST_USER_NAME


@pytest.fixture
def mock_user() -> UserResponse:
    return UserResponse(
        id=TEST_USER_ID,
        email=TEST_USER_EMAIL,
        name=TEST_USER_NAME,
        picture=None,
        granted_scopes=[],
    )


@pytest.fixture
def valid_sync_body() -> dict[str, object]:
    return {
        "access_token": "ya29.test-access-token",
        "refresh_token": "1//test-refresh-token",
        "expires_at": int(time.time()) + 3600,
        "scopes": ["openid", "email", "profile"],
    }


@pytest.fixture
async def client() -> AsyncGenerator[httpx.AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


def _override_user(user: UserResponse) -> None:
    async def _override() -> UserResponse:
        return user

    app.dependency_overrides[get_current_user] = _override


def _google_refresh_response(
    access_token: str = "new-access-token",
    expires_in: int = 3600,
    refresh_token: str | None = None,
) -> MagicMock:
    data: dict[str, Any] = {
        "access_token": access_token,
        "expires_in": expires_in,
    }
    if refresh_token is not None:
        data["refresh_token"] = refresh_token
    resp = MagicMock()
    resp.ok = True
    resp.status_code = 200
    resp.json.return_value = data
    return resp


def _google_error_response(status: int = 400) -> MagicMock:
    resp = MagicMock()
    resp.ok = False
    resp.status_code = status
    resp.text = '{"error": "invalid_grant"}'
    return resp


def _google_revoke_response(ok: bool = True) -> MagicMock:
    resp = MagicMock()
    resp.ok = ok
    resp.status_code = 200 if ok else 400
    return resp


def _sample_stored_token() -> StoredToken:
    return StoredToken(
        access_token="ya29.stored-access-token",
        refresh_token="1//stored-refresh-token",
        expires_at=int(time.time()) + 3600,
        scopes=["openid", "email", "profile"],
    )


class TestAuthCallbackEndpoint:
    async def test_should_return_204_on_valid_token_sync(
        self,
        client: httpx.AsyncClient,
        mock_user: UserResponse,
        valid_sync_body: dict[str, object],
    ) -> None:
        _override_user(mock_user)

        with patch(
            "app.auth.service.store_token", new_callable=AsyncMock
        ) as mock_store:
            response = await client.post("/api/auth/callback", json=valid_sync_body)

        assert response.status_code == 204
        mock_store.assert_awaited_once()
        call_args = mock_store.call_args
        assert call_args[0][0] == TEST_USER_ID
        stored: StoredToken = call_args[0][1]
        assert stored.access_token == valid_sync_body["access_token"]
        assert stored.refresh_token == valid_sync_body["refresh_token"]
        assert stored.expires_at == valid_sync_body["expires_at"]
        assert stored.scopes == valid_sync_body["scopes"]

    async def test_should_return_401_without_authorization(
        self,
        client: httpx.AsyncClient,
        valid_sync_body: dict[str, object],
    ) -> None:
        response = await client.post("/api/auth/callback", json=valid_sync_body)
        assert response.status_code == 401

    async def test_should_return_422_with_missing_fields(
        self,
        client: httpx.AsyncClient,
        mock_user: UserResponse,
    ) -> None:
        _override_user(mock_user)
        response = await client.post(
            "/api/auth/callback",
            json={"access_token": "ya29.test"},
        )
        assert response.status_code == 422

    async def test_should_return_500_on_encryption_failure(
        self,
        client: httpx.AsyncClient,
        mock_user: UserResponse,
        valid_sync_body: dict[str, object],
    ) -> None:
        _override_user(mock_user)

        with patch(
            "app.auth.service.store_token",
            new_callable=AsyncMock,
            side_effect=TokenEncryptionError("bad key"),
        ):
            response = await client.post("/api/auth/callback", json=valid_sync_body)

        assert response.status_code == 500


class TestAuthRefreshEndpoint:
    async def test_should_return_200_with_new_expires_at(
        self,
        client: httpx.AsyncClient,
        mock_user: UserResponse,
    ) -> None:
        _override_user(mock_user)
        now = int(time.time())

        with (
            patch(
                "app.auth.service.get_token",
                new_callable=AsyncMock,
                return_value=_sample_stored_token(),
            ),
            patch(
                "app.auth.service.requests.post",
                return_value=_google_refresh_response(),
            ),
            patch("app.auth.service.store_token", new_callable=AsyncMock),
        ):
            response = await client.post("/api/auth/refresh")

        assert response.status_code == 200
        data = response.json()
        assert data["expires_at"] >= now + 3500

    async def test_should_return_401_without_authorization(
        self,
        client: httpx.AsyncClient,
    ) -> None:
        response = await client.post("/api/auth/refresh")
        assert response.status_code == 401

    async def test_should_return_404_when_no_token_in_redis(
        self,
        client: httpx.AsyncClient,
        mock_user: UserResponse,
    ) -> None:
        _override_user(mock_user)

        with patch(
            "app.auth.service.get_token",
            new_callable=AsyncMock,
            side_effect=TokenNotFoundError("not found"),
        ):
            response = await client.post("/api/auth/refresh")

        assert response.status_code == 404

    async def test_should_return_502_when_google_refresh_fails(
        self,
        client: httpx.AsyncClient,
        mock_user: UserResponse,
    ) -> None:
        _override_user(mock_user)

        with (
            patch(
                "app.auth.service.get_token",
                new_callable=AsyncMock,
                return_value=_sample_stored_token(),
            ),
            patch(
                "app.auth.service.requests.post",
                return_value=_google_error_response(),
            ),
        ):
            response = await client.post("/api/auth/refresh")

        assert response.status_code == 502

    async def test_should_return_502_on_network_error(
        self,
        client: httpx.AsyncClient,
        mock_user: UserResponse,
    ) -> None:
        _override_user(mock_user)

        with (
            patch(
                "app.auth.service.get_token",
                new_callable=AsyncMock,
                return_value=_sample_stored_token(),
            ),
            patch(
                "app.auth.service.requests.post",
                side_effect=requests.RequestException("timeout"),
            ),
        ):
            response = await client.post("/api/auth/refresh")

        assert response.status_code == 502

    async def test_should_return_502_when_google_returns_invalid_json(
        self,
        client: httpx.AsyncClient,
        mock_user: UserResponse,
    ) -> None:
        _override_user(mock_user)

        bad_json_resp = MagicMock()
        bad_json_resp.ok = True
        bad_json_resp.status_code = 200
        bad_json_resp.json.side_effect = ValueError("invalid json")

        with (
            patch(
                "app.auth.service.get_token",
                new_callable=AsyncMock,
                return_value=_sample_stored_token(),
            ),
            patch("app.auth.service.requests.post", return_value=bad_json_resp),
        ):
            response = await client.post("/api/auth/refresh")

        assert response.status_code == 502

    async def test_should_store_updated_token_after_refresh(
        self,
        client: httpx.AsyncClient,
        mock_user: UserResponse,
    ) -> None:
        _override_user(mock_user)

        with (
            patch(
                "app.auth.service.get_token",
                new_callable=AsyncMock,
                return_value=_sample_stored_token(),
            ),
            patch(
                "app.auth.service.requests.post",
                return_value=_google_refresh_response(
                    access_token="refreshed-access-token",
                ),
            ),
            patch("app.auth.service.store_token", new_callable=AsyncMock) as mock_store,
        ):
            response = await client.post("/api/auth/refresh")

        assert response.status_code == 200
        mock_store.assert_awaited_once()
        stored: StoredToken = mock_store.call_args[0][1]
        assert stored.access_token == "refreshed-access-token"

    async def test_should_store_rotated_refresh_token(
        self,
        client: httpx.AsyncClient,
        mock_user: UserResponse,
    ) -> None:
        _override_user(mock_user)

        with (
            patch(
                "app.auth.service.get_token",
                new_callable=AsyncMock,
                return_value=_sample_stored_token(),
            ),
            patch(
                "app.auth.service.requests.post",
                return_value=_google_refresh_response(
                    refresh_token="rotated-refresh-token",
                ),
            ),
            patch("app.auth.service.store_token", new_callable=AsyncMock) as mock_store,
        ):
            response = await client.post("/api/auth/refresh")

        assert response.status_code == 200
        stored: StoredToken = mock_store.call_args[0][1]
        assert stored.refresh_token == "rotated-refresh-token"

    async def test_should_return_500_on_decryption_failure(
        self,
        client: httpx.AsyncClient,
        mock_user: UserResponse,
    ) -> None:
        _override_user(mock_user)

        with patch(
            "app.auth.service.get_token",
            new_callable=AsyncMock,
            side_effect=TokenEncryptionError("corrupted"),
        ):
            response = await client.post("/api/auth/refresh")

        assert response.status_code == 500


class TestAuthRevokeEndpoint:
    async def test_should_return_204_on_successful_revoke(
        self,
        client: httpx.AsyncClient,
        mock_user: UserResponse,
    ) -> None:
        _override_user(mock_user)

        with (
            patch(
                "app.auth.service.get_token",
                new_callable=AsyncMock,
                return_value=_sample_stored_token(),
            ),
            patch(
                "app.auth.service.requests.post",
                return_value=_google_revoke_response(),
            ),
            patch(
                "app.auth.service.delete_token", new_callable=AsyncMock
            ) as mock_delete,
        ):
            response = await client.delete("/api/auth/revoke")

        assert response.status_code == 204
        mock_delete.assert_awaited_once_with(TEST_USER_ID)

    async def test_should_return_401_without_authorization(
        self,
        client: httpx.AsyncClient,
    ) -> None:
        response = await client.delete("/api/auth/revoke")
        assert response.status_code == 401

    async def test_should_return_404_when_no_token_in_redis(
        self,
        client: httpx.AsyncClient,
        mock_user: UserResponse,
    ) -> None:
        _override_user(mock_user)

        with patch(
            "app.auth.service.get_token",
            new_callable=AsyncMock,
            side_effect=TokenNotFoundError("not found"),
        ):
            response = await client.delete("/api/auth/revoke")

        assert response.status_code == 404

    async def test_should_return_500_on_decryption_failure(
        self,
        client: httpx.AsyncClient,
        mock_user: UserResponse,
    ) -> None:
        _override_user(mock_user)

        with patch(
            "app.auth.service.get_token",
            new_callable=AsyncMock,
            side_effect=TokenEncryptionError("corrupted"),
        ):
            response = await client.delete("/api/auth/revoke")

        assert response.status_code == 500

    async def test_should_delete_from_redis_even_if_google_revoke_fails(
        self,
        client: httpx.AsyncClient,
        mock_user: UserResponse,
    ) -> None:
        _override_user(mock_user)

        with (
            patch(
                "app.auth.service.get_token",
                new_callable=AsyncMock,
                return_value=_sample_stored_token(),
            ),
            patch(
                "app.auth.service.requests.post",
                return_value=_google_revoke_response(ok=False),
            ),
            patch(
                "app.auth.service.delete_token", new_callable=AsyncMock
            ) as mock_delete,
        ):
            response = await client.delete("/api/auth/revoke")

        assert response.status_code == 204
        mock_delete.assert_awaited_once_with(TEST_USER_ID)
