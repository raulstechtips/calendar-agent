"""Middleware stack: CORS, correlation ID tracing, and rate limiting."""

import base64
import json
import logging

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.core.config import settings

logger = logging.getLogger(__name__)


def get_user_from_token(request: Request) -> str:
    """Extract user ID from Bearer JWT for rate limiting, with IP fallback.

    Decodes the JWT payload without signature verification for performance.
    This is safe because rate limiting is best-effort — actual authentication
    happens in get_current_user. A forged sub claim only affects which rate-limit
    bucket is used, not access control.
    """
    try:
        auth = request.headers.get("authorization", "")
        if not auth.lower().startswith("bearer "):
            return get_remote_address(request)
        token = auth[7:]
        parts = token.split(".")
        if len(parts) != 3:
            return get_remote_address(request)
        payload = parts[1]
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += "=" * padding
        claims = json.loads(base64.urlsafe_b64decode(payload))
        sub = claims.get("sub")
        if isinstance(sub, str) and sub:
            return sub
    except Exception:
        pass
    return get_remote_address(request)


limiter = Limiter(key_func=get_user_from_token, default_limits=["60/minute"])


def setup_middleware(app: FastAPI) -> None:
    """Register middleware stack. Order is LIFO — last added = outermost."""
    # Rate limiting (innermost — applied last)
    app.state.limiter = limiter
    # slowapi's handler is typed for RateLimitExceeded, but Starlette expects Exception
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
    app.add_middleware(SlowAPIMiddleware)

    # Correlation ID (middle)
    app.add_middleware(
        CorrelationIdMiddleware,
        header_name="X-Request-ID",
    )

    # CORS (outermost — applied first)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )
