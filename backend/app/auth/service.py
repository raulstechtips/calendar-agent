"""Business logic for auth token lifecycle — sync, refresh, revoke."""

import asyncio
import logging
import time
from functools import partial

import requests
from fastapi import HTTPException

from app.auth.schemas import TokenRefreshResponse, TokenSyncRequest
from app.auth.token_storage import (
    StoredToken,
    TokenEncryptionError,
    TokenNotFoundError,
    delete_token,
    get_token,
    store_token,
)
from app.core.config import settings

logger = logging.getLogger(__name__)

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"
_GOOGLE_TIMEOUT = 10


async def sync_token(user_id: str, body: TokenSyncRequest) -> None:
    """Store frontend OAuth tokens in Redis."""
    token_data = StoredToken(
        access_token=body.access_token,
        refresh_token=body.refresh_token,
        expires_at=body.expires_at,
        scopes=body.scopes,
    )
    try:
        await store_token(user_id, token_data)
    except TokenEncryptionError:
        logger.exception("Token encryption failed for user %s", user_id)
        raise HTTPException(status_code=500, detail="Token storage failed") from None


async def refresh_user_token(user_id: str) -> TokenRefreshResponse:
    """Read refresh_token from Redis, call Google, store updated tokens."""
    stored = await _get_stored_token(user_id)

    loop = asyncio.get_running_loop()
    try:
        response = await loop.run_in_executor(
            None,
            partial(
                requests.post,
                GOOGLE_TOKEN_URL,
                data={
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "grant_type": "refresh_token",
                    "refresh_token": stored.refresh_token,
                },
                timeout=_GOOGLE_TIMEOUT,
            ),
        )
    except requests.RequestException:
        logger.exception("Google token refresh network error for user %s", user_id)
        raise HTTPException(
            status_code=502, detail="Google token refresh failed"
        ) from None

    if not response.ok:
        logger.warning(
            "Google token refresh failed for user %s: %s %s",
            user_id,
            response.status_code,
            response.text[:200],
        )
        raise HTTPException(status_code=502, detail="Google token refresh failed")

    try:
        data = response.json()
    except ValueError:
        logger.warning(
            "Google token refresh returned invalid JSON for user %s", user_id
        )
        raise HTTPException(
            status_code=502, detail="Google token refresh failed"
        ) from None

    new_access_token = data.get("access_token")
    expires_in = data.get("expires_in")
    if not isinstance(new_access_token, str) or not isinstance(expires_in, int):
        raise HTTPException(status_code=502, detail="Google token refresh failed")

    new_expires_at = int(time.time()) + expires_in
    new_refresh_token = data.get("refresh_token")

    # Use scopes from Google's response when available (self-correcting);
    # fall back to stored scopes if Google omits the field.
    scope_str = data.get("scope")
    refreshed_scopes = (
        scope_str.split()
        if isinstance(scope_str, str) and scope_str
        else stored.scopes
    )

    updated = StoredToken(
        access_token=new_access_token,
        refresh_token=(
            new_refresh_token
            if isinstance(new_refresh_token, str)
            else stored.refresh_token
        ),
        expires_at=new_expires_at,
        scopes=refreshed_scopes,
    )

    try:
        await store_token(user_id, updated)
    except TokenEncryptionError:
        logger.exception("Token encryption failed during refresh for user %s", user_id)
        raise HTTPException(status_code=500, detail="Token storage failed") from None

    return TokenRefreshResponse(expires_at=new_expires_at)


async def revoke_user_token(user_id: str) -> None:
    """Revoke the token at Google, then delete from Redis."""
    stored = await _get_stored_token(user_id)

    loop = asyncio.get_running_loop()
    try:
        response = await loop.run_in_executor(
            None,
            partial(
                requests.post,
                GOOGLE_REVOKE_URL,
                data={"token": stored.refresh_token},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=_GOOGLE_TIMEOUT,
            ),
        )
        if not response.ok:
            logger.warning(
                "Google revoke returned %s for user %s",
                response.status_code,
                user_id,
            )
    except requests.RequestException:
        logger.warning(
            "Google revoke network error for user %s — clearing Redis anyway",
            user_id,
        )

    await delete_token(user_id)


async def _get_stored_token(user_id: str) -> StoredToken:
    """Retrieve token from Redis with standard error handling."""
    try:
        return await get_token(user_id)
    except TokenNotFoundError:
        raise HTTPException(status_code=404, detail="No token found for user") from None
    except TokenEncryptionError:
        logger.exception("Token decryption failed for user %s", user_id)
        raise HTTPException(status_code=500, detail="Token retrieval failed") from None
