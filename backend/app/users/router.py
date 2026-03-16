"""User API endpoints."""

from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user
from app.users.schemas import (
    UpdatePreferencesRequest,
    UserPreferencesResponse,
    UserResponse,
)
from app.users.service import (
    get_user_preferences,
    get_user_profile,
    update_user_preferences,
)

router = APIRouter()


@router.get("/api/users/me", response_model=UserResponse)
async def get_me(
    user: UserResponse = Depends(get_current_user),  # noqa: B008
) -> UserResponse:
    """Return the authenticated user's profile."""
    return await get_user_profile(user)


@router.get("/api/users/me/preferences", response_model=UserPreferencesResponse)
async def get_preferences(
    user: UserResponse = Depends(get_current_user),  # noqa: B008
) -> UserPreferencesResponse:
    """Return the authenticated user's preferences."""
    return await get_user_preferences(user.id)


@router.patch("/api/users/me/preferences", response_model=UserPreferencesResponse)
async def patch_preferences(
    body: UpdatePreferencesRequest,
    user: UserResponse = Depends(get_current_user),  # noqa: B008
) -> UserPreferencesResponse:
    """Update the authenticated user's preferences."""
    return await update_user_preferences(user.id, body)
