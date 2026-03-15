"""Auth dependencies for FastAPI endpoint injection."""

from fastapi import Header, HTTPException

from app.users.schemas import UserResponse


async def get_current_user(
    x_user_id: str = Header(..., max_length=255),  # noqa: B008
    x_user_email: str = Header(..., max_length=255),  # noqa: B008
    x_user_name: str = Header("", max_length=255),  # noqa: B008
) -> UserResponse:
    """Extract the current user from request headers.

    Raises:
        HTTPException: 401 if required headers are missing or empty.
    """
    if not x_user_id.strip():
        raise HTTPException(status_code=401, detail="Missing user ID")
    if not x_user_email.strip():
        raise HTTPException(status_code=401, detail="Missing user email")

    return UserResponse(
        id=x_user_id.strip(),
        email=x_user_email.strip(),
        name=x_user_name.strip() if x_user_name.strip() else x_user_email.strip(),
        picture=None,
        granted_scopes=[],
    )
