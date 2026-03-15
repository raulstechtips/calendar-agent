"""Shared test fixtures for backend tests."""

import pytest

from app.users.schemas import UserResponse

TEST_USER_ID = "google-sub-test-123"
TEST_USER_EMAIL = "testuser@example.com"
TEST_USER_NAME = "Test User"
TEST_USER_PICTURE = "https://lh3.googleusercontent.com/test/photo.jpg"


@pytest.fixture
def google_claims() -> dict[str, str | int]:
    """Standard Google ID token claims for a test user."""
    return {
        "sub": TEST_USER_ID,
        "email": TEST_USER_EMAIL,
        "name": TEST_USER_NAME,
        "picture": TEST_USER_PICTURE,
        "aud": "test-google-client-id",
        "iss": "accounts.google.com",
        "exp": 9999999999,
        "iat": 1000000000,
    }


@pytest.fixture
def mock_user() -> UserResponse:
    """Expected UserResponse from standard google_claims."""
    return UserResponse(
        id=TEST_USER_ID,
        email=TEST_USER_EMAIL,
        name=TEST_USER_NAME,
        picture=TEST_USER_PICTURE,
        granted_scopes=[],
    )


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Authorization header with a test bearer token."""
    return {"Authorization": "Bearer test-id-token"}
