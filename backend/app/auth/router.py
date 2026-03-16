"""Auth router — token sync, refresh, and revocation endpoints."""

from fastapi import APIRouter, Depends, Response

from app.auth.dependencies import get_current_user
from app.auth.schemas import TokenRefreshResponse, TokenSyncRequest
from app.auth.service import refresh_user_token, revoke_user_token, sync_token
from app.users.schemas import UserResponse

router = APIRouter()


@router.post("/api/auth/callback", status_code=204)
async def auth_callback(
    body: TokenSyncRequest,
    user: UserResponse = Depends(get_current_user),  # noqa: B008
) -> Response:
    """Store OAuth tokens in Redis after frontend sign-in or refresh."""
    await sync_token(user.id, body)
    return Response(status_code=204)


@router.post("/api/auth/refresh", response_model=TokenRefreshResponse)
async def auth_refresh(
    user: UserResponse = Depends(get_current_user),  # noqa: B008
) -> TokenRefreshResponse:
    """Refresh the stored Google access token using the stored refresh token."""
    return await refresh_user_token(user.id)


@router.delete("/api/auth/revoke", status_code=204)
async def auth_revoke(
    user: UserResponse = Depends(get_current_user),  # noqa: B008
) -> Response:
    """Revoke the Google token and clear it from Redis."""
    await revoke_user_token(user.id)
    return Response(status_code=204)
