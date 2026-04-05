---
description: FastAPI + Python 3.12 + Pydantic v2 backend conventions
paths:
  - "backend/**"
---

# Backend Rules

## Architecture

- Thin routes, thick services: routes validate input and return responses — business logic lives in `service.py` modules
- Service layers raise domain exceptions (e.g., `TokenNotFoundError`) — never import `HTTPException` outside of route/dependency files
- Domain exceptions should carry `status_code: int` and `error_code: str` attributes for consistent HTTP mapping and machine-readable client responses
- All shared resources use the singleton getter pattern (`get_*()` / `close_*()`) — init eagerly in lifespan startup, clean up in shutdown with isolated `try/except` per resource
- One `Settings(BaseSettings)` instance in `core/config.py` — import it, never re-instantiate
- `Depends()` for dependency injection — `# noqa: B008` on default args (Ruff false positive)
- One-line docstring on every endpoint — it appears in auto-generated OpenAPI docs

## Error Handling

- Define a base `AppError(Exception)` in `core/exceptions.py` with `status_code`, `error_code`, and `message` — all domain exceptions inherit from it
- Register ONE global `@app.exception_handler(AppError)` that returns structured JSON: `{"error_code": "TOKEN_NOT_FOUND", "message": "...", "request_id": "..."}`
- Use `HTTPException` directly only in route/dependency files for auth failures (401/403) where there is no domain concept to model
- Never let unhandled exceptions leak stack traces — catch-all handler logs full traceback, returns generic 500

## Async Patterns

- `run_in_executor` is an escape hatch for sync-only SDKs (Google OAuth, Calendar API) — prefer async-native libraries (httpx) for new code
- Set explicit timeouts on EVERY external call: `httpx.Timeout(connect=5, read=30)`, `Redis.from_url(..., socket_timeout=5, socket_connect_timeout=5)`, `asyncio.wait_for()` around `run_in_executor` calls
- Configure Redis for production: `retry_on_timeout=True`, `health_check_interval=30`, `socket_keepalive=True`
- `asyncio.TaskGroup` over `asyncio.gather` — structured concurrency with automatic cancellation on failure
- Scope `asyncio.Lock` per-user, not global — see the LRU-bounded lock pattern in `auth/google_credentials.py`
- `BackgroundTasks` for fire-and-forget post-response work — avoid `asyncio.create_task()` in request handlers (event loop holds weak references, untracked tasks get GC'd)
- All background task functions MUST catch and log all exceptions; re-raise `asyncio.CancelledError` after logging

## Pydantic v2

- Separate request and response models — never reuse one for both
- Request models: `ConfigDict(extra="forbid", str_strip_whitespace=True)` — rejects unknown fields, strips whitespace
- Response models: `ConfigDict(from_attributes=True, extra="forbid")`
- `Field(max_length=...)` on all string fields; `Field(gt=0)` on numeric bounds
- `model_dump(exclude_unset=True)` only for PATCH operations — never on response serialization
- Use `TypeAdapter` to validate non-model types (lists, dicts) at system boundaries instead of `json.loads()` + manual key access
- No docstrings on Pydantic models — field names, types, and `Field(description=...)` are the documentation

## Logging

- Use `structlog` with stdlib integration via `ProcessorFormatter` — all logs (structlog + uvicorn + FastAPI) produce identical structured output
- JSON output in production, `ConsoleRenderer` in development — controlled by one env var (`LOG_FORMAT=json|console`), configured once at startup
- Bind request-scoped context via `structlog.contextvars`: `clear_contextvars()` in middleware, then `bind_contextvars(request_id=..., user_id=...)` — never pass these as positional format args
- Use keyword arguments for structured data: `logger.info("ingest_complete", user_id=uid, event_count=n)` not `logger.info("Ingest complete for %s: %d", uid, n)`
- Integrate with existing `asgi-correlation-id` middleware — read the `X-Request-ID` header and bind it, don't generate a separate ID

## Type Checking

- `mypy --strict` and `pyright` must both pass — no exceptions
- Every `# type: ignore` MUST have a specific error code AND a comment explaining why: `# type: ignore[misc]  # redis-py returns Any for hgetall`
- Enable `warn_unused_ignores = true` so stale ignores fail the build
- Use `Protocol` for typing interfaces from untyped third-party libraries (e.g., Google Calendar service objects) — never leave them as `Any`
- Use `ParamSpec` + `Concatenate` for decorators wrapping async functions — preserves the decorated function's signature
- `TYPE_CHECKING` imports for cross-module type references — prevents circular imports and reduces startup time
- Never use `cast()` to silence a real type error — only for narrowing from a library's `Any` when you are certain of the runtime type

## SSE Streaming

- Async generator → `StreamingResponse(media_type="text/event-stream")` with JSON events using a `type` discriminator
- Always emit a terminal event (`done` or `error`) — clients rely on these to close the connection
- Wrap the entire generator body in `try/except` — catch `asyncio.CancelledError` BEFORE `Exception` (client disconnect is normal, log at info, don't yield further events)
- Never let exceptions propagate raw out of the generator — yield a structured error event, then done, then return

## Testing

- `asyncio_mode = "auto"` — no `@pytest.mark.asyncio` decorator needed
- `httpx.AsyncClient(transport=ASGITransport(app=app))` for endpoint tests
- Always `app.dependency_overrides.clear()` in fixture teardown — prevents leakage between tests
- `autouse` fixtures calling `reset_*()` for singleton isolation between tests
- Mock external APIs (Google OAuth, cloud services); test own endpoints and business logic real
- `monkeypatch` for settings; `unittest.mock.patch` + `AsyncMock` for function mocks
