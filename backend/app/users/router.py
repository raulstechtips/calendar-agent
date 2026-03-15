"""User API endpoints."""

from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user
from app.users.schemas import UserResponse
from app.users.service import get_user_profile

router = APIRouter()


@router.get("/api/users/me", response_model=UserResponse)
async def get_me(
    user: UserResponse = Depends(get_current_user),  # noqa: B008
) -> UserResponse:
    """Return the authenticated user's profile."""
    return await get_user_profile(user)
