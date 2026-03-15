"""Tests for user endpoints and get_current_user auth dependency."""

from collections.abc import AsyncGenerator

import httpx
import pytest
from fastapi import HTTPException
from httpx import ASGITransport

from app.auth.dependencies import get_current_user
from app.main import app
from app.users.schemas import UserResponse


@pytest.fixture
async def client() -> AsyncGenerator[httpx.AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


class TestGetCurrentUser:
    async def test_should_return_user_from_valid_headers(self) -> None:
        user = await get_current_user(
            x_user_id="google-123",
            x_user_email="alice@example.com",
            x_user_name="Alice Smith",
        )
        assert user.id == "google-123"
        assert user.email == "alice@example.com"
        assert user.name == "Alice Smith"
        assert user.picture is None
        assert user.granted_scopes == []

    async def test_should_use_email_as_name_when_name_missing(self) -> None:
        user = await get_current_user(
            x_user_id="google-123",
            x_user_email="alice@example.com",
            x_user_name="",
        )
        assert user.name == "alice@example.com"

    async def test_should_strip_header_values(self) -> None:
        user = await get_current_user(
            x_user_id="  google-123  ",
            x_user_email="  alice@example.com  ",
            x_user_name="  Alice  ",
        )
        assert user.id == "google-123"
        assert user.email == "alice@example.com"
        assert user.name == "Alice"

    async def test_should_reject_empty_user_id(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                x_user_id="   ",
                x_user_email="alice@example.com",
                x_user_name="Alice",
            )
        assert exc_info.value.status_code == 401

    async def test_should_reject_empty_email(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                x_user_id="google-123",
                x_user_email="   ",
                x_user_name="Alice",
            )
        assert exc_info.value.status_code == 401


class TestGetMeEndpoint:
    async def test_should_return_user_profile(self, client: httpx.AsyncClient) -> None:
        response = await client.get(
            "/api/users/me",
            headers={
                "X-User-Id": "google-123",
                "X-User-Email": "alice@example.com",
                "X-User-Name": "Alice Smith",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "google-123"
        assert data["email"] == "alice@example.com"
        assert data["name"] == "Alice Smith"
        assert data["picture"] is None
        assert data["granted_scopes"] == []

    async def test_should_return_422_without_user_id_header(
        self, client: httpx.AsyncClient
    ) -> None:
        response = await client.get(
            "/api/users/me",
            headers={"X-User-Email": "alice@example.com"},
        )
        assert response.status_code == 422

    async def test_should_return_422_without_email_header(
        self, client: httpx.AsyncClient
    ) -> None:
        response = await client.get(
            "/api/users/me",
            headers={"X-User-Id": "google-123"},
        )
        assert response.status_code == 422

    async def test_should_return_401_with_whitespace_only_user_id(
        self, client: httpx.AsyncClient
    ) -> None:
        response = await client.get(
            "/api/users/me",
            headers={
                "X-User-Id": "   ",
                "X-User-Email": "alice@example.com",
            },
        )
        assert response.status_code == 401

    async def test_should_return_401_with_whitespace_only_email(
        self, client: httpx.AsyncClient
    ) -> None:
        response = await client.get(
            "/api/users/me",
            headers={
                "X-User-Id": "google-123",
                "X-User-Email": "   ",
            },
        )
        assert response.status_code == 401

    async def test_should_work_with_dependency_override(
        self, client: httpx.AsyncClient
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
