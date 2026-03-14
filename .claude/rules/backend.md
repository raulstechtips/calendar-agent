---
description: FastAPI + Python 3.12 + Pydantic v2 + LangGraph conventions
paths:
  - "backend/**"
---

# Backend Rules (FastAPI + LangGraph)

## FastAPI Patterns

### Endpoints
- Use `async def` for all endpoints with I/O (Redis, HTTP, database)
- Never call blocking code inside `async def` — use `run_in_executor` if unavoidable
- Keep routes thin: validate input, call service, return response — business logic in `service.py`
- Use `Depends()` for dependency injection — chain small, focused dependencies
- Set `response_model=XResponse` on route decorators for automatic serialization

### Request/Response Models
- Separate models for request and response — never reuse one model for both
- Create `CreateX`, `UpdateX`, `XResponse` schemas per domain
- Set `Field(max_length=...)` on all string fields
- Use `model_config = ConfigDict(from_attributes=True, extra="forbid", str_strip_whitespace=True)`

### Exception Handling
- Use `HTTPException` for standard HTTP errors
- Register custom exception handlers via `@app.exception_handler`
- Always include a catch-all handler that logs context but returns generic 500
- In service layers, raise domain exceptions — let handlers translate to HTTP responses

### Middleware
- Middleware ordering is LIFO (last added = outermost)
- Register in order: CORS -> Correlation ID -> Rate Limiting
- Never use `allow_origins=["*"]` with `allow_credentials=True`

### Lifespan
- Use `lifespan` async context manager (not deprecated `@app.on_event`)
- Store shared resources (Redis pool, HTTP client) on `app.state`
- Always clean up resources in the shutdown phase

## Pydantic v2

- Use `field_validator(mode="before")` for pre-processing, `mode="after"` for business rules
- Use `model_validator(mode="after")` for cross-field validation
- Use discriminated unions with `Field(discriminator="type")` for polymorphic types
- Use `model_dump(exclude_unset=True)` for PATCH operations
- Use `@computed_field` on `@property` for derived values in API responses

## Docstrings

- Use Google-style docstrings (compatible with `parse_docstring=True` and Sphinx)
- One-line summary in imperative mood. Extended description only when the function does something non-obvious
- `Args:` only when parameter names + types aren't self-explanatory. `Returns:` only when the return type annotation isn't sufficient. `Raises:` when callers need to handle domain exceptions
- Pydantic models: do NOT add docstrings — field names, types, and `Field(description=...)` are the documentation. Only add a class-level docstring if the model's purpose isn't clear from its name
- FastAPI endpoints: add a one-line docstring (it appears in the auto-generated OpenAPI/Swagger docs)
- Test functions: do NOT add docstrings — the test name (`test_should_reject_expired_token`) is the documentation

## Python Async

- Use `asyncio.TaskGroup` (not `asyncio.gather`) for concurrent operations — structured concurrency
- Every resource opened in startup MUST be closed in shutdown
- Redis: `await redis.aclose()` explicitly — no async destructor magic
- HTTP clients: one `httpx.AsyncClient` per app in lifespan, not per request
- Use `async with` for transient connections
- Never use `time.sleep()` in async code — use `await asyncio.sleep()`

## LangGraph Agent

### State
- Use `TypedDict` with `Annotated` reducers — lighter than Pydantic for LangGraph
- Keep state serializable — no complex objects, connections, or file handles

### Tools
- Use `@tool(parse_docstring=True)` — LLM uses docstrings to decide when to call tools
- Full type hints on all tool parameters — these define the input schema
- Tools should do ONE action — no Swiss-army-knife tools
- Return error messages as strings, NEVER raise exceptions — raising stops the flow
- Wrap every external API call in try/except
- Use `InjectedState` to pass graph state without exposing it to the LLM

### Human-in-the-Loop
- Use `interrupt()` for write operations (create/update/delete events)
- Requires checkpointer and `thread_id` in config
- Emit structured SSE events before interrupting

## Type Checking

- `mypy --strict` and `pyright --strict` must both pass on the full backend project before considering work done
- Never use `# type: ignore` without a specific error code (e.g. `# type: ignore[arg-type]`)
- Never use `cast()` to paper over a real type error — fix the underlying issue
- Use `TYPE_CHECKING` imports to avoid circular imports and runtime overhead
- For third-party libraries without `py.typed`: add a per-module override in `[tool.mypy]`, never use blanket `ignore_missing_imports`

### Testing Agents
- Use `GenericFakeChatModel` for deterministic LLM mocking
- Unit test individual tools in isolation before testing the full graph
- Test the full chain: LLM decision -> tool params -> execution -> result -> response

## Testing

- Set `asyncio_mode = "auto"` in `pyproject.toml` — eliminates `@pytest.mark.asyncio` boilerplate
- Use `httpx.AsyncClient` with `ASGITransport(app=app)` for async endpoint tests
- Use `app.dependency_overrides` for swapping dependencies — FastAPI's built-in mechanism
- Mock: external APIs (Google, Azure). Test with real: Redis (use Docker), own endpoints
- Test YOUR business logic, not framework behavior (don't test that Pydantic validates types)
