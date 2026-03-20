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
- SDLC Plugin: `claude --plugin-dir .claude/plugins/sdlc` (or alias: `alias cc='claude --plugin-dir .claude/plugins/sdlc'`)

## Code Conventions

- Functional React components with hooks only; server components by default
- Python: async/await for all I/O, type hints everywhere, Pydantic v2 models
- All backend calls are server-side — the browser never contacts the backend directly. Regular API calls go through `api.ts`; SSE streams go through the Next.js route handler proxy at `/api/chat`; client-initiated mutations use Server Actions
- ES modules only — NEVER use CommonJS require()
- NEVER install new dependencies without asking first
- Conventional commits: `feat(scope):`, `fix(scope):`, `refactor(scope):`, etc.

## Workflow

IMPORTANT: Follow these rules strictly:

- ALWAYS read a file before editing it
- ALWAYS run tests after making changes
- ALWAYS run lint and typecheck before considering work done
- Before writing code, read the PRD at `.claude/sdlc/prd/PRD.md` and PI at `.claude/sdlc/pi/PI.md`
- Track work via GitHub Issues — pick stories labeled `status:todo`, mark `status:in-progress`; when done update label to `status:done` and create a PR (the issue closes automatically when the PR merges)
- Commit after each completed task with conventional commits referencing the issue number
- If uncertain about approach, ASK before proceeding
- When starting a session, check project state: `git log --oneline -10 && gh issue list --label "status:todo" --label "status:in-progress"`

## Architecture Decisions

- Auth: Auth.js v5 beta with Google OAuth, incremental consent, offline access for refresh tokens
- Vector store: Single shared Azure AI Search index with `user_id` filter (not index-per-user)
- Agent: LangGraph ReAct via `create_react_agent` + custom `@tool` functions (not langchain-google-community — incompatible with multi-user credentials)
- Gmail scope: Use `gmail.metadata` (Sensitive) not `gmail.readonly` (Restricted) to avoid annual security audit
- Tokens: Fernet-encrypted Google OAuth tokens stored in Redis with TTL
- Rate limiting: slowapi with Redis backend

## Skills (Slash Commands)

### SDLC Plugin (v2)
- `/sdlc:define [level]` — Collaborative brainstorming → local draft
- `/sdlc:create [level]` — Push draft to GitHub/git
- `/sdlc:update [level] [#N]` — Surgical edits to existing artifacts
- `/sdlc:status [area]` — Project status briefing
- `/sdlc:reconcile [area]` — Label hygiene and hierarchy audit
- `/sdlc:retro [scope]` — Process retrospective
- `/sdlc:capture <description>` — Quick-capture idea as triage issue

### Other Skills
- `/review-coderabbit [PR#]` — Fetch and triage CodeRabbit review comments

### Contextual Skills (Frontend)

Auto-available when working on `frontend/**`. See `.claude/rules/frontend.md` for usage guidance.

- `shadcn` — shadcn/ui component management
- `ui-ux-pro-max` — UI/UX design intelligence
- `vercel-react-best-practices` — React/Next.js performance patterns
- `vercel-composition-patterns` — React component architecture

## Decision Workflow

When a decision is made (by the user or during implementation):
1. Update PRD.md first — it is the source of truth. Use `sdlc:update prd` to record decisions.
2. Update the PI Plan if scope changes affect the current increment
3. Update affected GitHub issues if story/feature scope changes
4. CLAUDE.md only changes for new conventions or commands

## Reference Docs

- PRD (source of truth): `.claude/sdlc/prd/PRD.md` — tech stack, versions, architecture, API contracts, data models, decisions log
- PI Plan (current sprint): `.claude/sdlc/pi/PI.md` — epics, features, dependency graph, worktree strategy
- Human workflow: `docs/HUMAN-WORKFLOW.md` — how to launch agents, review, merge, manage the sprint
- Design spec: `docs/superpowers/specs/2026-03-17-sdlc-skill-suite-design.md` — SDLC skill suite design
