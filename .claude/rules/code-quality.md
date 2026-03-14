---
description: Code quality and anti-pattern rules
---

# Code Quality Rules

## Over-engineering (most common AI mistake)

- Do NOT create abstraction layers with only one implementation
- Do NOT build flexibility that was not requested (generic factories, plugin systems)
- Do NOT create utility files for one-off functions
- Do NOT add configuration options that aren't needed yet
- Rule of thumb: implement the simplest solution that satisfies the acceptance criteria

## Under-engineering

- Every external call (HTTP, Redis, Google API, Azure) MUST have error handling
- Every API endpoint MUST validate input at the boundary
- Every async resource MUST be properly cleaned up (async context managers, lifespan shutdown)

## Existing patterns

- Before creating any new file, search for existing patterns to follow
- Before adding a utility, check if one already exists
- Match the naming conventions, file structure, and code style of existing code exactly
- ALWAYS prefer editing an existing file over creating a new one

## Cleanup before commit

- Remove ALL `console.log`, `print()`, `debugger` statements
- Remove ALL `TODO` and `FIXME` comments referencing the current task
- Remove ALL commented-out code
- The only acceptable logging is structured production logging

## Dependencies

- Do NOT add any package not listed in the SPEC or already in package.json/pyproject.toml without asking first
- Before adding a dependency, check if the platform API or an existing dependency already handles it

## Performance

- Batch database and API calls — never make N+1 queries in a loop
- Never call blocking I/O inside `async def` functions
- Use connection pooling for Redis and HTTP clients (one client per app, not per request)

## Security

- Never log tokens, secrets, or API keys — not even at DEBUG level
- Never hardcode credentials — always use environment variables via BaseSettings
- Never trust user input — validate at every boundary with Pydantic or Zod
- Never use `allow_origins=["*"]` with `allow_credentials=True`
