# Project: AI Calendar Assistant

Next.js 16 frontend + FastAPI backend + LangGraph agents, deployed on Azure Container Apps.
Azure OpenAI (GPT-4o) as LLM backbone, Azure AI Search as vector store.

## Repository Structure

```
/frontend    - Next.js 16 app (App Router, TypeScript, Tailwind, shadcn/ui)
/backend     - FastAPI service (Python 3.12, Pydantic v2, async)
/backend/agents - LangGraph agent definitions and tools
/infra       - Terraform configs for Azure
/shared      - Shared types, API contracts, constants
```

## Commands

- Frontend dev: `cd frontend && pnpm dev`
- Backend dev: `cd backend && uv run uvicorn app.main:app --reload`
- Frontend tests: `cd frontend && pnpm test`
- Backend tests: `cd backend && uv run pytest`
- Type check frontend: `cd frontend && pnpm typecheck`
- Type check backend (mypy): `cd backend && uv run mypy .`
- Type check backend (pyright): `cd backend && uv run pyright`
- Lint frontend: `cd frontend && pnpm lint`
- Lint backend: `cd backend && uv run ruff check .`
- Format backend: `cd backend && uv run ruff format .`
- Add frontend dep: `cd frontend && pnpm add <pkg>`
- Add backend dep: `cd backend && uv add <pkg>`
- Add backend dev dep: `cd backend && uv add --group dev <pkg>`
- UI screenshots: `cd frontend && pnpm e2e:screenshots` (outputs to `frontend/e2e/screenshots/`)

## Code Conventions

- Functional React components with hooks only; server components by default
- Python: async/await for all I/O, type hints everywhere, Pydantic v2 models
- All backend calls are server-side — the browser never contacts the backend directly. Regular API calls go through `api.ts`; SSE streams go through the Next.js route handler proxy at `/api/chat`; client-initiated mutations use Server Actions
- ES modules only — NEVER use CommonJS require()
- NEVER depend on transitive dependencies — if you `import` a package in production code, it MUST be listed in `pyproject.toml` with a pinned version
- ALL dependencies MUST use exact version pins (`==`) — this is an application, not a library; upgrades must be explicit and intentional
- To upgrade a dependency: update the version in `pyproject.toml`, run `uv lock --upgrade-package <pkg>`, run tests, commit both files
- NEVER install new dependencies without asking the developer first
- Conventional commits: `feat(scope):`, `fix(scope):`, `refactor(scope):`, etc.

## Workflow

IMPORTANT: Follow these rules strictly:

- ALWAYS read a file before editing it
- ALWAYS run tests after making changes
- ALWAYS run lint and typecheck before considering work done
- NEVER commit `docs/superpowers/` files — they are local-only design artifacts and are gitignored

### Contextual Skills (Frontend)

Auto-available when working on `frontend/**`. See `.claude/rules/frontend.md` for usage guidance.

- `shadcn` — shadcn/ui component management
- `frontend-design` — Opinionated UI/UX design guidance (Anthropic official)
- `vercel-react-best-practices` — React/Next.js performance patterns
- `vercel-composition-patterns` — React component architecture
