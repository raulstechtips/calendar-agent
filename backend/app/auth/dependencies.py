"""Auth dependencies for FastAPI endpoint injection."""

import asyncio
import logging
from collections.abc import Mapping
from functools import partial
from typing import Any

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2.id_token import verify_oauth2_token

from app.core.config import settings
from app.users.schemas import UserResponse

logger = logging.getLogger(__name__)

_bearer_scheme = HTTPBearer(auto_error=False)

# Reuse transport to benefit from requests.Session connection pooling.
_google_transport: GoogleAuthRequest | None = None


def _get_google_transport() -> GoogleAuthRequest:
    global _google_transport  # noqa: PLW0603
    if _google_transport is None:
        _google_transport = GoogleAuthRequest()
    return _google_transport


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),  # noqa: B008
) -> UserResponse:
    """Verify a Google ID token and return the authenticated user.

    Raises:
        HTTPException: 401 if the token is missing, invalid, or expired.
    """
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not settings.google_client_id:
        logger.error("GOOGLE_CLIENT_ID is not configured — cannot verify tokens")
        raise HTTPException(status_code=500, detail="Authentication is misconfigured")

    try:
        loop = asyncio.get_running_loop()
        id_info: Mapping[str, Any] = await loop.run_in_executor(
            None,
            partial(
                verify_oauth2_token,
                credentials.credentials,
                _get_google_transport(),
                audience=settings.google_client_id,
            ),
        )
    except (ValueError, GoogleAuthError) as exc:
        logger.info("Token verification failed: %s", exc)
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired Google ID token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return UserResponse(
        id=id_info["sub"],
        email=id_info["email"],
        name=id_info.get("name", id_info["email"]),
        picture=id_info.get("picture"),
        granted_scopes=[],
    )
