"""User business logic."""

from app.users.schemas import UserResponse


async def get_user_profile(user: UserResponse) -> UserResponse:
    """Return the user profile."""
    return user
