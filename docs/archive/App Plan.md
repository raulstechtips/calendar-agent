# Production AI calendar assistant: full stack specification reference

**Every component in this stack has a current stable release, well-documented best practices, and clear integration patterns.** This reference provides exact version numbers, pip/npm package names, and concrete recommendations for each of the 12 technology areas — ready for direct use in SPEC.md and CLAUDE.md documents. The stack centers on Next.js 16 + FastAPI + LangGraph on Azure Container Apps, with Azure OpenAI (GPT-4o) as the LLM backbone and Azure AI Search as the vector store.

---

## 1. Next.js 16 with App Router, Auth.js, and Docker

**Next.js latest stable: `16.1.6`** (released ~Feb 27, 2026). Next.js 16.0 shipped October 21, 2025, bringing Turbopack as the default bundler, React Compiler (stable), and React 19.2 support. The `proxy.ts` file replaces `middleware.ts` for network boundary concerns in v16.

**Auth.js / next-auth status is nuanced.** The npm package remains `next-auth`, and **v5 never reached a stable release** — the latest is `5.0.0-beta.30`. Auth.js was handed over to the Better Auth team in September 2025; v4 and v5-beta continue to receive security patches but are in maintenance mode. For new projects starting now, evaluate `better-auth` as the recommended successor. If continuing with next-auth v5 beta, install via `npm install next-auth@beta`.

Google OAuth configuration with Auth.js v5 requires setting `access_type: "offline"` and `prompt: "consent"` in the provider authorization params to obtain refresh tokens. Auth.js does **not** auto-refresh tokens — implement manual refresh in the `jwt` callback using Google's `https://oauth2.googleapis.com/token` endpoint. Environment variables use the `AUTH_` prefix in v5 (`AUTH_GOOGLE_ID`, `AUTH_GOOGLE_SECRET`, `AUTH_SECRET`).

**Node.js base image: use Node 24 LTS** (codename "Krypton", entered Active LTS October 28, 2025). Node 20 reaches EOL on April 30, 2026 — avoid it for new projects. Node 22 (Maintenance LTS until April 2027) is acceptable but not preferred. The official Next.js Docker example now uses `node:24-alpine`. Next.js 16.1 fixed a performance issue on musl-based distros by enabling mimalloc, making Alpine a strong production choice.

The standalone output mode requires `output: "standalone"` in `next.config.ts`. The production Dockerfile pattern is a three-stage build: **deps** (npm ci), **builder** (npm run build), **runner** (copy standalone + static assets, run as non-root user). Critical settings: `HOSTNAME="0.0.0.0"` to prevent loopback issues behind reverse proxies, and `NEXT_TELEMETRY_DISABLED=1`.

**Recommended App Router project structure** uses `src/` with route groups:

```
src/app/(auth)/          # Public auth pages
src/app/(main)/          # Authenticated app sections  
src/app/api/auth/[...nextauth]/route.ts
src/actions/             # Server Actions with "use server"
src/components/ui/       # Atomic components
src/lib/                 # Utilities, API clients, configs
auth.ts                  # Auth.js config at project root
proxy.ts                 # Next.js 16 proxy (replaces middleware.ts)
```

TypeScript config should use `"strict": true`, `"moduleResolution": "bundler"`, the `next` plugin for typed routes, and the `@/*` path alias pointing to `./src/*`.

---

## 2. FastAPI project structure and middleware stack

**FastAPI latest stable: `0.135.1`** (March 1, 2026). Install with `pip install "fastapi[standard]"` which includes uvicorn and the CLI. Requires **Python ≥ 3.10**; recommended Python version for new projects is **3.12 or 3.13**. Key dependencies are Starlette ≥0.46.0 and Pydantic ≥2.x.

The recommended project structure for a production app follows a **domain-module pattern** (inspired by Netflix Dispatch):

```
src/
├── auth/           # router.py, schemas.py, service.py, dependencies.py
├── users/          # router.py, schemas.py, service.py
├── context_ingestion/  # router.py, service.py, tasks.py
├── core/           # config.py (BaseSettings), security.py, redis.py, middleware.py
├── db/             # database.py, base.py
└── main.py         # App creation, router includes, middleware registration
```

Each domain module owns its `APIRouter`, Pydantic schemas, service layer, and dependencies. Routers handle HTTP concerns only; business logic lives in `service.py`. Use `Depends()` extensively for dependency injection.

**Middleware stack** (registered in reverse execution order in FastAPI): CORS → Request ID tracing → Rate limiting → Custom logging. For CORS with a Next.js frontend, **never use `allow_origins=["*"]` with `allow_credentials=True`** — these are mutually exclusive. Use `asgi-correlation-id` (`pip install asgi-correlation-id`) for request ID tracing, which auto-generates UUID4 and injects into log records. Use `slowapi` (`pip install slowapi`) for Redis-backed rate limiting with per-endpoint decorators like `@limiter.limit("5/minute")`.

**Background tasks for context ingestion on login**: For I/O-bound pipelines under 5 seconds, use FastAPI's built-in `BackgroundTasks`. For longer-running tasks needing retries and status tracking, use **ARQ** (`pip install arq`) — it's async-native, uses Redis as broker, and fits naturally with FastAPI. Avoid `asyncio.create_task` in production (tasks silently lost on crash). Celery is overkill unless you need enterprise-grade distributed processing.

---

## 3. LangGraph for stateful multi-tool agents

**LangGraph latest stable: `1.1.0`** (March 10, 2026). The 1.0.0 milestone shipped October 17, 2025. Install `pip install langgraph` plus `langgraph-prebuilt` (v1.0.8) for high-level agent APIs.

Build agents using `StateGraph` with `TypedDict` state (preferred over Pydantic for LangGraph — lighter weight, works natively with `Annotated` reducers). The core state pattern uses `Annotated[list, add_messages]` for message accumulation. Define tools with the `@tool` decorator from `langchain_core.tools`, where **the docstring is critical** — agents use it to decide when to invoke each tool.

The **recommended ReAct agent pattern** uses `create_react_agent` from `langgraph.prebuilt`:

```python
from langgraph.prebuilt import create_react_agent
app = create_react_agent(model, tools, checkpointer=checkpointer)
```

For more control, build a custom StateGraph with an "agent" node (LLM with bound tools), a "tools" node (`ToolNode`), and a conditional edge routing to tools when tool_calls exist or to END otherwise.

**Checkpointing for production: use `PostgresSaver`** from `langgraph-checkpoint-postgres`. Use `InMemorySaver` only for development. Structure `thread_id` values meaningfully: `f"tenant-{tenant_id}:user-{user_id}:session-{session_id}"`.

---

## 4. Azure OpenAI with GPT-4o via LangChain

**`langchain-openai` latest: `1.1.10`** (February 17, 2026). The **latest GA Azure OpenAI API version is `2024-10-21`**; the latest preview is `2025-04-01-preview`. A new v1 API (GA since August 2025) eliminates the `api-version` parameter entirely and allows using `ChatOpenAI` directly with Azure endpoints at `https://YOUR-RESOURCE.openai.azure.com/openai/v1/`.

Configure `AzureChatOpenAI` with four key parameters: `azure_deployment` (your deployment name, e.g., "gpt-4o"), `azure_endpoint`, `api_version`, and `api_key` (or `azure_ad_token_provider` for Entra ID auth). For production, **use Entra ID authentication** via `DefaultAzureCredential` with the `https://cognitiveservices.azure.com/.default` scope rather than API keys.

**System prompt hardening against prompt injection** should use a structured sandwich defense with clear delimiters separating system instructions from user input, an explicit instruction hierarchy (system > user > document content), output constraints via structured output (JSON schema), and a system reminder block after the user input section. Embed canary tokens in the system prompt to detect extraction attempts. Gate sensitive operations (sending emails, modifying calendar) behind human-in-the-loop confirmation.

---

## 5. Azure AI Search as a per-user vector store

**`azure-search-documents` latest stable: `11.6.0`** (October 9, 2025). Uses API version `2024-07-01`.

For per-user isolation, **use a single shared index with a filterable `user_id` field** (filter-by-user-id pattern). This is Microsoft's recommended approach for most multi-tenant apps — it's the simplest to manage and most cost-efficient. Apply `filter=f"user_id eq '{current_user_id}'"` on every query. Index-per-user is only justified when tenants need different schemas or strict physical isolation; the 200-index limit on S3 tier makes this impractical at scale.

The LangChain integration uses `AzureSearch` from `langchain_community.vectorstores.azuresearch`:

```python
from langchain_community.vectorstores.azuresearch import AzureSearch
from langchain_openai import AzureOpenAIEmbeddings

embeddings = AzureOpenAIEmbeddings(
    azure_deployment="text-embedding-3-small",
    openai_api_version="2024-02-01",
    azure_endpoint="https://<resource>.openai.azure.com/"
)
vector_store = AzureSearch(
    azure_search_endpoint="https://<search>.search.windows.net",
    azure_search_key="<key>",
    index_name="calendar-context",
    embedding_function=embeddings.embed_query,
    search_type="hybrid",
)
```

Use **`text-embedding-3-small`** (1536 dimensions) over the older `text-embedding-ada-002` for better performance. The `search_type="hybrid"` mode combines vector similarity with BM25 keyword matching for best retrieval quality.

---

## 6. Azure API Management policies and identity forwarding

APIM sits in front of Azure Container Apps to handle rate limiting, JWT validation, and CORS at the gateway layer. Set the backend URL to the Container App's internal FQDN.

**Rate limiting** uses three policy types. `<rate-limit>` enforces per-subscription limits (e.g., `calls="1000" renewal-period="60"`). `<rate-limit-by-key>` allows custom keys — extract user identity from JWT claims for per-user limiting:

```xml
<rate-limit-by-key calls="100" renewal-period="60"
  counter-key="@(context.Request.Headers.GetValueOrDefault(
    \"Authorization\",\"\").AsJwt()?.Subject)" />
```

`<quota>` enforces long-term caps (e.g., 10,000 calls/day). Rate-limit returns **429**; quota returns **403**. Note: `rate-limit-by-key` is not available on the Consumption tier.

**To forward authenticated user identity to the backend**, use `<validate-azure-ad-token>` (for Entra ID) or `<validate-jwt>` (generic), storing the validated token in `output-token-variable-name="jwt"`, then extract claims into headers with `<set-header>`:

```xml
<set-header name="X-User-Id" exists-action="override">
  <value>@(((Jwt)context.Variables["jwt"]).Subject)</value>
</set-header>
```

The backend FastAPI service reads `X-User-Id` from request headers, trusting APIM to have validated the JWT.

---

## 7. Azure Container Apps architecture and Terraform

Deploy Next.js (external ingress, port 3000) and FastAPI (internal ingress, port 8000) as **separate Container Apps in the same Container Apps Environment**. Internal apps are accessible only within the environment. For service-to-service calls, use `http://backend-app-name` directly (TLS encrypted automatically).

**FastAPI Dockerfile** uses a two-stage build: a `python:3.12-slim` builder stage that creates a venv and installs dependencies, and a slim runner stage that copies only the venv and application code. Run as non-root user with `PYTHONDONTWRITEBYTECODE=1` and `PYTHONUNBUFFERED=1`. Production command: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4`.

**Terraform uses `azurerm` provider v4.64.0** (March 2026) with **Terraform CLI v1.14.7**. Key resources: `azurerm_container_app_environment`, `azurerm_container_app` (one per service), `azurerm_container_registry`, `azurerm_api_management`, `azurerm_redis_cache`, `azurerm_search_service`, `azurerm_cognitive_account` (kind = "OpenAI"), and `azurerm_key_vault`.

Structure Terraform with **separate root modules per environment** (`environments/dev/`, `environments/prod/`) calling shared child modules (`modules/container-apps/`, `modules/redis/`, `modules/ai-services/`, etc.). State backend uses Azure Storage with Entra ID auth (`use_azuread_auth = true`), blob versioning enabled, and separate state keys per environment. Use `enable_rbac_authorization = true` on Key Vault. For Container App secrets, use Key Vault references with User-Assigned Managed Identity rather than inline values.

---

## 8. Redis for rate limiting and secure token storage

**`redis` (redis-py) latest: `7.1.1`** (February 9, 2026). **Always install `redis[hiredis]`** — the hiredis C parser provides up to **10x speed improvement** with zero code changes. The `aioredis` package is abandoned and was merged into redis-py as `redis.asyncio` since v4.2.0 — never install aioredis separately.

For async Redis in FastAPI:
```python
from redis.asyncio import Redis
redis = Redis.from_url("rediss://host:6380", password="...", decode_responses=True)
```

**Token bucket rate limiting** is recommended over sliding window for API rate limiting — it tolerates bursts while maintaining average rate. Use `slowapi` with `storage_uri="redis://..."` for distributed rate limiting across multiple FastAPI workers.

**Store Google OAuth tokens encrypted** using Fernet symmetric encryption from the `cryptography` package. Encrypt the token JSON before storing in Redis; use key pattern `oauth_token:{user_id}:google` with a Redis Hash. Set TTL on access tokens to `expires_in - 300` seconds (buffer before expiry). Azure Cache for Redis provides TLS encryption in transit on port 6380 by default.

---

## 9. Google OAuth scopes for Calendar, Gmail, and People

The exact scopes needed, from narrowest to broadest:

- **Read calendar events**: `https://www.googleapis.com/auth/calendar.events.readonly` (Sensitive)
- **Create/modify events**: `https://www.googleapis.com/auth/calendar.events` (Sensitive) — or `calendar.events.owned` for only user-owned calendars
- **Read Gmail threads**: `https://www.googleapis.com/auth/gmail.readonly` (**Restricted** — requires annual third-party security assessment)
- **Read contacts**: `https://www.googleapis.com/auth/contacts.readonly` (**Restricted**)

Restricted scopes require full OAuth App Verification plus an **annual CASA/LODA security assessment** by a Google-approved assessor. If you only need email metadata (subjects, senders, dates) without message body, `gmail.metadata` is Sensitive rather than Restricted and has a lighter verification path.

**Incremental consent** is essential: request only `openid`, `userinfo.email`, `userinfo.profile` at sign-in. Request Calendar scopes when the user first accesses calendar features; request Gmail scopes when they enable email integration. Use `include_granted_scopes=true` in the authorization request to merge new scopes with previously granted ones into a single token. Always check which scopes were actually granted — users can deny individual scopes via granular permissions.

---

## 10. LangChain Google tools vs MCP servers vs direct API calls

**`langchain-google-community` v3.0.5** provides native LangChain tool interfaces for Google Calendar and Gmail. Install with extras: `pip install langchain-google-community[gmail,calendar]`. This is the **recommended approach for LangGraph agents** — tools integrate directly with `ToolNode` and `create_react_agent`.

**No official Google or Anthropic MCP servers exist** for Google Calendar/Gmail. Several community MCP servers are available (notably `nspady/google-calendar-mcp` and `ngs/google-mcp-server`), and LangChain's `langchain-mcp-adapters` package can bridge MCP tools into LangGraph. However, MCP adds infrastructure complexity (a separate server process) with limited benefit for this use case.

**Direct Google API calls wrapped as `@tool` functions** give maximum control and are the best choice when `langchain-google-community` doesn't expose the specific API operations you need (e.g., advanced Calendar queries, batch operations, or fine-grained Gmail thread handling). For a calendar assistant, a hybrid approach works well: use `langchain-google-community` for standard operations and wrap custom Google API calls as LangGraph tools for anything beyond its capabilities.

---

## 11. Prompt injection defense with Azure AI Content Safety

The defense-in-depth strategy uses multiple layers. **Input validation** applies regex pattern matching for known injection phrases ("ignore previous instructions," "you are now," "reveal system prompt"), detects Base64/URL-encoded payloads, and enforces input length limits. **System prompt hardening** uses the sandwich defense pattern — system instructions, delimited user input, then a system reminder — with clear instruction hierarchy and output constraints via structured output schemas.

**Azure AI Content Safety** (`pip install azure-ai-contentsafety==1.0.0`) provides two key capabilities. The standard `analyze_text` endpoint checks four harm categories (Hate, SelfHarm, Sexual, Violence) with severity scores. The **Prompt Shields API** (`/contentsafety/text:shieldPrompt?api-version=2024-09-01`) specifically detects prompt injection, identifying both direct user prompt attacks and indirect injection via documents.

Integrate these as **pre- and post-generation guardrail nodes** in your LangGraph pipeline: an `input_guard` node runs Prompt Shields and content safety checks before the LLM call, and an `output_guard` node validates the LLM's response. Block the request entirely if injection is detected; filter or regenerate if output contains harmful content.

Additional defenses include canary tokens (embed secret strings in the system prompt and monitor for leakage), human-in-the-loop gates for high-risk actions (sending emails, creating events), and least-privilege tool access (use read-only scopes where possible, escalate only when the user explicitly requests a write action).

---

## 12. Complete version reference table

| Component | Package | Version | Install |
|---|---|---|---|
| Next.js | `next` | **16.1.6** | `npm install next@latest` |
| next-auth (v5 beta) | `next-auth` | **5.0.0-beta.30** | `npm install next-auth@beta` |
| Node.js (Docker) | `node:24-alpine` | **24 LTS** | Base image |
| FastAPI | `fastapi[standard]` | **0.135.1** | `pip install "fastapi[standard]==0.135.1"` |
| LangGraph | `langgraph` | **1.1.0** | `pip install langgraph` |
| LangGraph Prebuilt | `langgraph-prebuilt` | **1.0.8** | `pip install langgraph-prebuilt` |
| LangChain Core | `langchain-core` | **1.2.19** | `pip install langchain-core` |
| LangChain OpenAI | `langchain-openai` | **1.1.10** | `pip install langchain-openai` |
| LangChain Google | `langchain-google-community[gmail,calendar]` | **3.0.5** | `pip install langchain-google-community[gmail,calendar]` |
| Azure OpenAI API | — | **2024-10-21** (GA) | API version string |
| Azure AI Search SDK | `azure-search-documents` | **11.6.0** | `pip install azure-search-documents` |
| Azure AI Content Safety | `azure-ai-contentsafety` | **1.0.0** | `pip install azure-ai-contentsafety` |
| Redis (redis-py) | `redis[hiredis]` | **7.1.1** | `pip install "redis[hiredis]==7.1.1"` |
| SlowAPI | `slowapi` | **≥0.1.9** | `pip install slowapi` |
| ASGI Correlation ID | `asgi-correlation-id` | **≥4.3.0** | `pip install asgi-correlation-id` |
| Terraform CLI | `terraform` | **1.14.7** | Binary install |
| Terraform azurerm | `hashicorp/azurerm` | **4.64.0** | `version = "~> 4.64"` |
| Python | — | **3.12 or 3.13** | Base image `python:3.12-slim` |

## Conclusion

Three decisions stand out as particularly consequential for this stack. First, **the Auth.js situation requires a deliberate choice**: next-auth v5 beta works but is in maintenance mode following the Better Auth handover — evaluate `better-auth` for long-term support, or accept v5 beta's stability for now and plan migration later. Second, **Gmail readonly is a Restricted scope** requiring annual third-party security assessment — this has real cost and timeline implications for production launch. Consider starting with `gmail.metadata` (Sensitive) if full message body access isn't immediately needed. Third, **filter-by-user-id beats index-per-user** for Azure AI Search multi-tenancy in nearly all scenarios — the operational simplicity and cost efficiency far outweigh the marginal isolation benefits of separate indexes unless you have regulatory requirements demanding physical data separation.

The LangGraph ecosystem has matured significantly with the 1.0 release (October 2025), and `create_react_agent` from `langgraph-prebuilt` is now the idiomatic way to build tool-calling agents. Combined with `langchain-google-community[gmail,calendar]` for Google API tools and `AzureChatOpenAI` for the LLM backend, the integration path is well-paved. Use PostgresSaver for production checkpointing, Azure AI Content Safety Prompt Shields for injection defense, and the sandwich prompt pattern for system prompt hardening.