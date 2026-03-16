# Tradeoffs & Deferred Decisions

Decisions where we chose the simpler MVP path with a known upgrade path for later.

---

## 1. Token Refresh Lock — In-Memory vs Distributed

**Date:** 2026-03-15
**Issue:** #17 (Calendar Tools)
**File:** `backend/app/agents/tools/calendar_tools.py`

### The problem

When a user's Google OAuth access token expires, the agent refreshes it before calling the Calendar API. If two concurrent tool calls for the same user both detect the expired token, both attempt a refresh — a race condition.

### What we built (MVP)

Per-user `asyncio.Lock` with a double-check pattern:

```python
_refresh_locks: dict[str, asyncio.Lock] = {}

async def _get_credentials(user_id):
    stored = await get_token(user_id)
    if stored.expires_at < time.time() + 60:
        async with _get_refresh_lock(user_id):
            # Re-check — another coroutine may have refreshed
            stored = await get_token(user_id)
            if stored.expires_at < time.time() + 60:
                stored = await _refresh_token_for_tool(user_id, stored)
```

### Why this is sufficient for now

- MVP runs a single Container App replica (one Python process)
- `asyncio.Lock` serializes all coroutines within that process
- Even without the lock, the race is benign — both refreshes succeed and whichever `store_token` runs last stores a valid token

### When this breaks

Multiple backend replicas (horizontal scaling). Each replica has its own memory, so Process 1's lock is invisible to Process 2:

```
Process 1: sees expired → acquires local lock → refreshes → stores
Process 2: sees expired → acquires local lock → refreshes → stores (overwrites)
```

Both succeed, but if Google rotates the refresh token, the overwritten token from Process 1 is lost. The stored token (from Process 2) is still valid, so no immediate failure — but it's wasteful and could cause subtle issues under high concurrency.

### The upgrade path — Redis distributed lock

Use Redis `SETNX` (atomic set-if-not-exists) as the coordination layer since Redis is already shared across all replicas:

```python
# Conceptual — would use redis.lock.Lock in practice
lock_key = f"lock:token_refresh:{user_id}"
acquired = await redis.set(lock_key, "1", nx=True, ex=10)  # 10s TTL
if acquired:
    try:
        # refresh token
    finally:
        await redis.delete(lock_key)
else:
    # wait briefly, then re-read token from Redis (now fresh)
```

Key details:
- `nx=True` — only one caller wins the lock
- `ex=10` — auto-release after 10s prevents deadlocks if the holder crashes
- `redis.lock.Lock` from the `redis` library handles this pattern with retry/backoff built in

### Trigger to upgrade

- Scaling to 2+ backend replicas
- Observing duplicate refresh calls in logs (`"Token refresh failed"` or `"Token refresh network error"` for the same user at the same timestamp)
