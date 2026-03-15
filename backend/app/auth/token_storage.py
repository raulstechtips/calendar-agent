"""Fernet-encrypted OAuth token storage in Redis."""

import json
import time

from cryptography.fernet import Fernet, InvalidToken
from pydantic import BaseModel

from app.core.config import settings
from app.core.redis import get_redis


class TokenNotFoundError(Exception):
    """Raised when no token exists for a given user."""


class TokenEncryptionError(Exception):
    """Raised when Fernet key is missing/invalid or decryption fails."""


_FALLBACK_TTL = 60


class StoredToken(BaseModel):
    model_config = {"extra": "forbid"}

    access_token: str
    refresh_token: str
    expires_at: int
    scopes: list[str]


_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    """Return the singleton Fernet cipher, initializing from settings on first call."""
    global _fernet
    if _fernet is None:
        if not settings.fernet_key:
            raise TokenEncryptionError("FERNET_KEY not configured")
        try:
            _fernet = Fernet(settings.fernet_key.encode())
        except ValueError as e:
            raise TokenEncryptionError(f"Invalid FERNET_KEY: {e}") from e
    return _fernet


def reset_fernet() -> None:
    """Clear the singleton Fernet cipher. For test isolation only."""
    global _fernet
    _fernet = None


def _token_key(user_id: str) -> str:
    return f"oauth_token:{user_id}:google"


async def store_token(user_id: str, token_data: StoredToken) -> None:
    """Encrypt and store OAuth token in Redis with TTL."""
    fernet = _get_fernet()
    encrypted_access = fernet.encrypt(token_data.access_token.encode()).decode()
    encrypted_refresh = fernet.encrypt(token_data.refresh_token.encode()).decode()

    key = _token_key(user_id)
    redis = get_redis()

    mapping: dict[str, str] = {
        "access_token": encrypted_access,
        "refresh_token": encrypted_refresh,
        "expires_at": str(token_data.expires_at),
        "scopes": json.dumps(token_data.scopes),
    }

    await redis.hset(key, mapping=mapping)  # type: ignore[misc]

    ttl = token_data.expires_at - int(time.time()) - 300
    await redis.expire(key, ttl if ttl > 0 else _FALLBACK_TTL)


async def get_token(user_id: str) -> StoredToken:
    """Retrieve and decrypt OAuth token from Redis.

    Returns the token regardless of expiry — callers are responsible for
    checking ``expires_at`` and refreshing when needed.
    """
    key = _token_key(user_id)
    redis = get_redis()

    # decode_responses=True guarantees str values from Redis
    data: dict[str, str] = await redis.hgetall(key)  # type: ignore[misc]
    if not data:
        raise TokenNotFoundError(f"No token found for user {user_id}")

    fernet = _get_fernet()
    try:
        access_token = fernet.decrypt(data["access_token"].encode()).decode()
        refresh_token = fernet.decrypt(data["refresh_token"].encode()).decode()
        return StoredToken(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=int(data["expires_at"]),
            scopes=json.loads(data["scopes"]),
        )
    except (InvalidToken, KeyError, ValueError, json.JSONDecodeError) as e:
        raise TokenEncryptionError(
            f"Token decryption failed for user {user_id}"
        ) from e


async def delete_token(user_id: str) -> None:
    """Remove OAuth token from Redis."""
    redis = get_redis()
    await redis.delete(_token_key(user_id))
