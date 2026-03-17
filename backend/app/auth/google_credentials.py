"""Shared Google OAuth credential and Calendar service builder.

Provides public APIs for resolving per-user Google OAuth credentials from
Redis and constructing authenticated Google Calendar API service objects.
Used by both the LangGraph agent tools and the context ingestion pipeline.
"""

import asyncio
import logging
import time
from collections import OrderedDict
from functools import partial
from typing import Any

import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.auth.token_storage import (
    StoredToken,
    TokenEncryptionError,
    TokenNotFoundError,
    get_token,
    store_token,
)
from app.core.config import settings

logger = logging.getLogger(__name__)

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
CALENDAR_EVENTS_SCOPE = "https://www.googleapis.com/auth/calendar.events"
CALENDAR_READONLY_SCOPE = "https://www.googleapis.com/auth/calendar.readonly"
CALENDAR_SCOPES = frozenset({CALENDAR_EVENTS_SCOPE, CALENDAR_READONLY_SCOPE})
SCOPE_ERROR_SENTINEL = "##SCOPE_REQUIRED##calendar"
_GOOGLE_TIMEOUT = 10

# Per-user lock to prevent concurrent token refreshes (single-instance only;
# multi-instance deployments would need a Redis-based distributed lock).
# NOTE: If a lock is evicted while held (extremely unlikely at maxsize 1024),
# a concurrent refresh for the same user may run in parallel — harmless since
# the refresh operation is idempotent.
_REFRESH_LOCK_MAXSIZE = 1024
_refresh_locks: OrderedDict[str, asyncio.Lock] = OrderedDict()


def _get_refresh_lock(user_id: str) -> asyncio.Lock:
    """Return a per-user refresh lock, creating if needed. Bounded by LRU eviction."""
    if user_id in _refresh_locks:
        _refresh_locks.move_to_end(user_id)
        return _refresh_locks[user_id]
    if len(_refresh_locks) >= _REFRESH_LOCK_MAXSIZE:
        _refresh_locks.popitem(last=False)
    lock = asyncio.Lock()
    _refresh_locks[user_id] = lock
    return lock


async def _refresh_token_for_tool(
    user_id: str, stored: StoredToken
) -> StoredToken | str:
    """Refresh an expired Google OAuth token.

    Returns updated StoredToken on success, or an error message string on failure.
    Does NOT raise HTTPException — tools must return error strings.
    """
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
    except requests.RequestException as e:
        logger.warning("Token refresh network error for user %s: %s", user_id, e)
        return "Google token refresh failed — network error."

    if not response.ok:
        logger.warning(
            "Token refresh failed for user %s: %s %s",
            user_id,
            response.status_code,
            response.text[:200],
        )
        return "Google token refresh failed — please re-authenticate."

    try:
        data = response.json()
    except ValueError:
        return "Google token refresh returned invalid response."

    new_access_token = data.get("access_token")
    expires_in = data.get("expires_in")
    if not isinstance(new_access_token, str) or not isinstance(expires_in, int):
        return "Google token refresh returned unexpected data."

    new_expires_at = int(time.time()) + expires_in
    new_refresh_token = data.get("refresh_token")

    # Use scopes from Google's response when available (self-correcting);
    # fall back to stored scopes if Google omits the field.
    scope_str = data.get("scope")
    refreshed_scopes = (
        scope_str.split() if isinstance(scope_str, str) and scope_str else stored.scopes
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
        return "Failed to store refreshed token."

    return updated


async def get_google_credentials(user_id: str) -> Credentials | str:
    """Retrieve user's Google OAuth credentials, refreshing if expired.

    Returns google.oauth2.credentials.Credentials on success,
    or an error message string on failure.
    """
    try:
        stored = await get_token(user_id)
    except TokenNotFoundError:
        return "No Google token found — please sign in and grant calendar access."
    except TokenEncryptionError:
        return "Failed to retrieve Google token — please re-authenticate."

    # Refresh if expired (with 60s buffer), using a per-user lock
    # to prevent concurrent refreshes from racing on the same token
    if stored.expires_at < int(time.time()) + 60:
        async with _get_refresh_lock(user_id):
            # Re-check after acquiring lock — another coroutine may have refreshed
            try:
                stored = await get_token(user_id)
            except (TokenNotFoundError, TokenEncryptionError):
                return "Token became unavailable during refresh."
            if stored.expires_at < int(time.time()) + 60:
                result = await _refresh_token_for_tool(user_id, stored)
                if isinstance(result, str):
                    return result
                stored = result

    return Credentials(  # type: ignore[no-untyped-call]
        token=stored.access_token,
        refresh_token=stored.refresh_token,
        token_uri=GOOGLE_TOKEN_URL,
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
    )


async def build_calendar_service(user_id: str) -> Any | str:
    """Build a Google Calendar API Resource for the given user.

    Pre-checks that the stored token includes calendar scopes before
    attempting the Google API call. Returns the Resource on success,
    or an error message string on failure.
    """
    # Pre-check: verify calendar scope before making a doomed API call
    try:
        stored = await get_token(user_id)
        if CALENDAR_EVENTS_SCOPE not in stored.scopes:
            logger.warning(
                "User %s missing calendar scope. Stored scopes: %s",
                user_id,
                stored.scopes,
            )
            return SCOPE_ERROR_SENTINEL
    except (TokenNotFoundError, TokenEncryptionError):
        pass  # get_google_credentials will handle with a proper error message

    creds = await get_google_credentials(user_id)
    if isinstance(creds, str):
        return creds

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,
        partial(build, "calendar", "v3", credentials=creds),
    )
