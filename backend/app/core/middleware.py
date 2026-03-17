"""Middleware stack: CORS, correlation ID tracing, and rate limiting."""

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.core.config import settings

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])


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
