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

---

## 2. Ingestion Sync Lock — None vs Distributed

**Date:** 2026-03-16
**Issue:** #92 (Embedding Pipeline Batching)
**File:** `backend/app/context_ingestion/tasks.py`

### The problem

When a user logs in, `run_ingestion()` is enqueued as a FastAPI BackgroundTask. If the same user logs in from two browser tabs simultaneously, both tasks pass the cooldown check (which reads Redis but doesn't lock) and both call `full_ingest()` — doubling the embedding API calls and TPM consumption.

### What we built (MVP)

No lock. The cooldown check in `run_ingestion()` uses `get_sync_metadata()` to read the last-ingested timestamp from Redis, but the check-then-act sequence is not atomic. Two concurrent tasks can both see "cooldown elapsed" and proceed.

### Why this is sufficient for now

- Upsert semantics (`merge_or_upload_documents`) make concurrent writes safe — whichever finishes last simply overwrites with the same data
- No data corruption or orphaned documents
- The only cost is redundant Azure OpenAI embedding calls (TPM waste)
- With the new batching + exponential backoff (#92), even redundant calls complete gracefully instead of crashing

### When this breaks

- High-traffic periods where many users log in simultaneously
- Multiple backend replicas (each runs its own background tasks)
- Low TPM quotas where redundant calls cause cascading 429 retries

### The upgrade path — Redis distributed lock

Same pattern as the token refresh lock (Tradeoff #1):

```python
lock_key = f"lock:ingestion:{user_id}"
acquired = await redis.set(lock_key, "1", nx=True, ex=600)  # 10min TTL
if acquired:
    try:
        await full_ingest(user_id)
    finally:
        await redis.delete(lock_key)
else:
    logger.info("Ingestion already running for user %s, skipping", user_id)
```

Key details:
- `ex=600` — TTL matches max expected full ingest duration (10 minutes for 500+ events at 10K TPM)
- If the holder crashes, the lock auto-releases after TTL
- Skipping (not queuing) is the right behavior — next login will trigger a delta sync

### Trigger to upgrade

- Observing duplicate `"Starting full ingest for user X"` logs at the same timestamp
- Scaling to 2+ backend replicas
- Frequent 429 retries in logs when TPM quota is tight

---

## 3. Embedding Token Budget Tracking — Reactive vs Proactive

**Date:** 2026-03-16
**Issue:** #92 (Embedding Pipeline Batching)
**File:** `backend/app/search/embeddings.py`

### The problem

The embedding pipeline has no visibility into how many tokens it consumes per batch. It only learns about TPM limits when Azure returns a 429 error, then reacts with exponential backoff. This is wasteful — each 429 response adds 1-60 seconds of retry delay.

### What we built (MVP)

Reactive rate limit handling:
- Batch events into groups of 50 (configurable)
- 1-second delay between batches (configurable)
- Exponential backoff with retry on 429 (respects `Retry-After` header)
- Progress logging per batch

### Why this is sufficient for now

- 10K TPM allows ~2.5 batches/minute of 50 short events (~80 tokens each)
- The `Retry-After` header tells us exactly when to retry
- Full ingest for a typical user (200-300 events) completes in 2-5 minutes
- Backoff adds latency but doesn't cause data loss (background task, idempotent)

### When this breaks

- Events with long descriptions (meeting transcripts, agendas) consume 300-500 tokens each — 50-event batch could hit 25K tokens, exhausting 10K TPM in one call
- Multiple users ingesting simultaneously share the same TPM quota
- Users notice slow first-login experience due to repeated 429 retries

### The upgrade path — Proactive token estimation

Estimate tokens before sending each batch and pace requests to stay within budget:

```python
# chars/4 is a reasonable heuristic for English text → tokens
estimated_tokens = sum(len(text) for text in batch_texts) // 4
tokens_per_minute = settings.azure_openai_tpm_limit  # e.g. 10_000

# Track cumulative usage in a sliding window
if cumulative_tokens + estimated_tokens > tokens_per_minute:
    wait = 60 - elapsed_since_window_start
    await asyncio.sleep(wait)
    reset_window()
```

Key details:
- `chars/4` heuristic is ~80% accurate for English text
- Sliding window tracks tokens consumed in the current minute
- Proactive delay avoids 429 entirely — no wasted retry cycles
- Could also use `tiktoken` for exact counts (adds ~1ms per batch)

### Trigger to upgrade

- Frequent 429 retries visible in batch progress logs (e.g., `"retrying in 30.0s"`)
- User complaints about slow first-login experience
- TPM quota increase is not an option (cost or policy constraint)
