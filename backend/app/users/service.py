"""User business logic."""

import logging

from app.auth.token_storage import (
    TokenEncryptionError,
    TokenNotFoundError,
    get_token,
)
from app.core.redis import get_redis
from app.users.schemas import (
    UpdatePreferencesRequest,
    UserPreferencesResponse,
    UserResponse,
)

logger = logging.getLogger(__name__)

_PREFS_KEY_PREFIX = "user_prefs"


def _prefs_key(user_id: str) -> str:
    return f"{_PREFS_KEY_PREFIX}:{user_id}"


async def get_user_profile(user: UserResponse) -> UserResponse:
    """Return the user profile enriched with granted scopes from Redis."""
    try:
        stored = await get_token(user.id)
        scopes = stored.scopes
    except (TokenNotFoundError, TokenEncryptionError):
        scopes = []
    except Exception:
        logger.exception("Failed to read scopes for user %s", user.id)
        scopes = []

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        picture=user.picture,
        granted_scopes=scopes,
    )


async def get_user_preferences(user_id: str) -> UserPreferencesResponse:
    """Read user preferences from Redis, returning defaults if none stored."""
    redis = get_redis()
    data: dict[str, str] = await redis.hgetall(_prefs_key(user_id))  # type: ignore[misc]
    return UserPreferencesResponse(
        timezone=data.get("timezone") or "UTC",
        default_calendar=data.get("default_calendar") or "primary",
    )


async def update_user_preferences(
    user_id: str, updates: UpdatePreferencesRequest
) -> UserPreferencesResponse:
    """Update user preferences in Redis and return the merged result."""
    redis = get_redis()
    key = _prefs_key(user_id)

    fields = updates.model_dump(exclude_unset=True, exclude_none=True)
    if fields:
        await redis.hset(key, mapping=fields)  # type: ignore[misc]

    return await get_user_preferences(user_id)
