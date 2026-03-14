# The complete Claude Code speed-run playbook for shipping in 2 days

**The fastest way to ship a production full-stack app with Claude Code is not to code faster — it's to engineer context.** Developers who successfully ship complex apps in 48 hours share one trait: they spend 20% of their time telling Claude *what to build* and *what not to touch*, then let parallel agents execute against a structured plan. The workflow combines five interlocking systems — CLAUDE.md for project memory, a spec-as-external-memory pattern, GitHub Issues as a structured tracking backbone, git worktrees for parallel agent execution, and subagents for context isolation. This report synthesizes research from Anthropic's official documentation, production case studies (including developers who shipped 100K+ line apps), community tooling like GitHub Spec Kit, and battle-tested workflows from teams running 3–5 parallel Claude Code agents daily.

The core insight is counterintuitive: **the single biggest productivity lever is not Claude Code itself but the documents you put around it.** A well-crafted 100-line CLAUDE.md with a structured spec eliminates more hallucinations than any prompting trick. When combined with GitHub Issues as an external task database and git worktrees for parallelism, a solo developer can realistically deliver what would take a small team a full sprint.

---

## CLAUDE.md is your project's persistent brain

Claude Code reads CLAUDE.md files automatically at the start of every conversation — it is the only file guaranteed to be in every session's context. The loading order is hierarchical: home folder (`~/.claude/CLAUDE.md`) → project root → parent directories → child directories (loaded on-demand when working with files in those subdirectories). This means a monorepo with `frontend/CLAUDE.md` and `backend/CLAUDE.md` gets context-appropriate instructions automatically.

**The critical caveat most developers miss:** Claude Code injects CLAUDE.md with a system reminder stating the context "may or may not be relevant" and should be ignored if not highly relevant. The more bloated the file, the more instructions get silently dropped. Research from HumanLayer, citing findings that frontier LLMs can follow roughly **150–200 instructions** with reasonable consistency, recommends keeping CLAUDE.md under 100 lines. Claude Code's own system prompt already consumes ~50 instruction slots, so every CLAUDE.md line competes for attention.

The proven structure follows a **WHAT / WHY / HOW framework**. WHAT covers the tech stack, repository structure, and what each part does — giving Claude a map. WHY covers the project's purpose. HOW covers build commands, test commands, coding conventions, and verification steps. Here is a battle-tested template for a Next.js + FastAPI + LangGraph project:

```markdown
# Project: AI Calendar Assistant
Next.js 16 frontend + FastAPI backend + LangGraph agents, deployed on Azure Container Apps.

# Repository Structure
/frontend    - Next.js app (App Router, TypeScript, Tailwind, shadcn/ui)
/backend     - FastAPI service (Python 3.12, Pydantic v2)
/backend/agents - LangGraph agent definitions
/infra       - Azure Bicep/Terraform configs
/shared      - Shared types and API contracts

# Commands
- Frontend dev: `cd frontend && pnpm dev`
- Backend dev: `cd backend && uvicorn main:app --reload`
- Frontend tests: `cd frontend && pnpm test`
- Backend tests: `cd backend && pytest`
- Type check: `cd frontend && pnpm typecheck`
- Lint: `cd frontend && pnpm lint && cd ../backend && ruff check .`

# Code Conventions
- Functional React components with hooks only; server components by default
- Python: async/await for all I/O, type hints everywhere
- All API calls through /frontend/lib/api.ts — never call backend directly
- NEVER use CommonJS require() — ES modules only
- NEVER install new dependencies without asking first

# Workflow
- ALWAYS read a file before editing it
- ALWAYS run tests after making changes
- ALWAYS run lint and typecheck before considering work done
- Commit after each completed task with conventional commits
- Before writing code, read the active spec in .claude/specs/in-progress/
- If uncertain about approach, ASK before proceeding
```

**Per-package CLAUDE.md files** should contain only package-specific context — local commands, key patterns, and architecture pointers — in 50–80 lines. The root file handles universal rules. Use `@path/to/file` syntax to reference documents without embedding them: write `"For complex patterns, see docs/architecture.md"` rather than `@docs/architecture.md`, which would embed the entire file on every session start. For emphasis on critical rules, use `IMPORTANT:` or `YOU MUST` prefixes — these measurably improve adherence.

---

## Spec-as-external-memory eliminates hallucination at the source

The most powerful anti-hallucination technique is also the simplest: **move the plan out of the chat and into a file in the repo.** LLMs are brilliant generators but terrible at state management. Once context fills up (~50K tokens for effective use), the plan "falls out of Claude's brain" and it starts guessing. A spec file in `.claude/specs/in-progress/` acts as external memory — when context resets via `/compact` or `/clear`, Claude re-reads the spec and instantly "remembers" the plan. Developers using this pattern report **zero hallucinations on multi-day builds** because "the truth is in the file, not the chat."

The recommended folder structure:

```
.claude/specs/
├── plans/           # Pending specs awaiting implementation
├── in-progress/     # Active spec — the "context anchor" for current work
└── plans-executed/  # Completed specs — permanent history of WHY code exists
```

Every spec needs these essential sections for AI agent execution: an overview (one paragraph), functional and non-functional requirements, a technical design with data models and API contracts, implementation tasks with specific file paths, **verifiable acceptance criteria** with exact test commands, explicit constraints and anti-patterns, and an out-of-scope section. The acceptance criteria section is the single highest-value piece — Claude performs dramatically better when it can verify its own work. Every criterion should have a concrete verification command:

```markdown
## Acceptance Criteria
- [ ] `pytest tests/test_auth.py::test_login_success` passes
- [ ] `curl -X POST localhost:8000/api/auth/login -d '{"email":"test@test.com"}' | jq .token` returns JWT
- [ ] `pnpm typecheck` shows zero errors
- [ ] `ruff check backend/` shows zero violations
```

**GitHub Spec Kit**, an open-source toolkit created by GitHub's Den Delimarsky team (v0.3.0 as of March 2026), formalizes this into a four-phase workflow: `/speckit.specify` (generate spec from description), `/speckit.plan` (create architecture plan), `/speckit.tasks` (break into ordered tasks), `/speckit.implement` (execute one task at a time). It supports 11+ agents including Claude Code. However, Spec Kit produces markdown files — it does not create GitHub Issues. For developers wanting to escape "markdown hell," Spec Kit is best used for the initial spec generation phase, with the output then converted into GitHub Issues.

---

## GitHub Issues replace markdown chaos with a queryable task database

The core problem with multiple disconnected markdown planning files is that they drift out of sync, have no status tracking, and provide no UI for human oversight. **GitHub Issues solve all three problems** while remaining fully accessible to Claude Code via the `gh` CLI.

As of April 2025, GitHub natively supports **sub-issues** and **issue types** (both GA), enabling a proper Epic → Feature → Story hierarchy without workarounds:

```
EPIC (Issue Type: Feature, label: "type:epic")
├── FEATURE (sub-issue, label: "type:feature")
│   ├── STORY (sub-issue, label: "type:story")  ← Claude executes these
│   ├── STORY
│   └── STORY
└── FEATURE
    ├── STORY
    └── STORY
```

Each story should be **one PR's worth of work**, completable in a single Claude Code session, touching **5–7 files maximum** for optimal agent focus. The issue body serves as a self-contained context packet with description (the why), acceptance criteria (checkboxes), file scope (specific paths to create/modify), dependencies (references to blocking issues), test requirements, and non-goals.

**The `gh` CLI is Claude Code's interface to this system.** One critical rule: all `gh` commands must be single-line — Claude Code's permission matching breaks with backslash line continuations. The core command loop:

```bash
# Read next task
gh issue list --label "status:todo" --json number,title,labels

# Start work (update status)
gh issue edit 42 --add-label "status:in-progress" --remove-label "status:todo"

# Read full context
gh issue view 42 --json title,body,labels --comments

# Create linked branch
gh issue develop 42 -c --base main --name feat/calendar-sync-42

# ... Claude implements the feature ...

# Open PR that auto-closes the issue
gh pr create -t "feat(calendar): add sync endpoint (#42)" -b "Fixes #42" -d

# Close on merge
gh pr merge <pr-number> --squash --delete-branch
```

For sub-issues, the native `gh` CLI doesn't yet support them directly (feature request cli/cli#10298 has 93+ upvotes). Use the `gh-sub-issue` community extension (`gh extension install yahsan2/gh-sub-issue`) or the REST API: `gh api /repos/owner/repo/issues/123/sub_issues -X POST -F "sub_issue_id=$SUB_ID"`.

The **John Lindquist "GitHub Tasks Output Style"** configuration is worth adopting wholesale — it enforces issue-driven development where every task starts with `gh issue create`, every session begins with a project state check (`git log --oneline -10 && gh issue list`), and every commit follows conventional format with issue references. This configuration can be placed in Claude Code's output style settings.

A recommended label taxonomy to create upfront:

- **Type labels**: `type:epic`, `type:feature`, `type:story`, `type:bug`, `type:spike`
- **Status labels**: `status:todo`, `status:in-progress`, `status:blocked`, `status:done`
- **Priority labels**: `priority:critical`, `priority:high`, `priority:medium`
- **Area labels**: `area:auth`, `area:api`, `area:ui`, `area:infra`

---

## Git worktrees let 3–4 Claude agents work simultaneously without conflicts

Git worktrees check out multiple branches of the same repository simultaneously, each in its own directory, sharing a single `.git` database. Unlike cloning multiple times, worktrees are space-efficient and history-synchronized. Each Claude Code instance gets a completely isolated working directory — **zero risk of wrong-branch commits or file conflicts between concurrent sessions.**

Claude Code now has **native first-class worktree support** (v2.1.50+):

```bash
# Launch Claude in an isolated worktree (creates .claude/worktrees/feat-auth/)
claude --worktree feat-auth

# Launch another in a separate terminal
claude --worktree feat-calendar-sync

# Launch with tmux persistence (survives terminal close)
claude --worktree feat-langraph-agents --tmux
```

The `--worktree` flag automatically creates the directory under `.claude/worktrees/<name>/`, creates a branch named `worktree-<name>`, and starts a scoped session. On exit, if no changes were made, the worktree and branch are automatically cleaned up. Add `.claude/worktrees/` to `.gitignore`.

For more control, manual worktree creation works well with a sibling-directory pattern:

```bash
cd ~/projects/ai-calendar
git worktree add ../ai-calendar-frontend -b feature/frontend main
git worktree add ../ai-calendar-api -b feature/api-endpoints main
git worktree add ../ai-calendar-infra -b feature/azure-deploy main

# Install dependencies in each (not shared across worktrees)
cd ../ai-calendar-frontend && pnpm install
cd ../ai-calendar-api && pip install -r requirements.txt

# Launch Claude in each (separate terminal windows)
cd ../ai-calendar-frontend && claude
cd ../ai-calendar-api && claude
```

**Conflict prevention is more important than conflict resolution.** Parallel agents only work cleanly when tasks are genuinely independent — meaning they don't write to the same files. Split by domain (frontend/backend/infra) or by feature with clear file boundaries. Add to CLAUDE.md: *"Sub agents could compete with each other and erase each others' changes. Be respectful of changes not made by you."* Community tools like **workmux** (`github.com/raine/workmux`) and **claude-tmux** (`github.com/nielsgroen/claude-tmux`) provide TUI interfaces for managing multiple parallel sessions with live previews.

The practical cost: running **3 parallel agents burns ~3× the credits** of a single session. The incident.io engineering team, who run 4–5 parallel agents daily, reports "dramatically faster feature delivery" but recommends budgeting explicitly for it.

---

## Anti-hallucination techniques that actually work in practice

Beyond the spec-as-external-memory pattern described above, several concrete techniques have proven effective at keeping Claude Code on track:

**The TodoWrite tool** is built into Claude Code's system prompt. It creates, updates, and tracks task lists during a session with statuses (`pending` → `in_progress` → `completed`). Claude is instructed to mark exactly one task as `in_progress` at a time and mark it `completed` before moving on. This forces decomposition of complex work into tracked steps, preventing the agent from losing its place.

**Plan-Execute-Verify** is the highest-value workflow pattern. Press **Shift+Tab twice** to enter Plan Mode, where Claude can observe and plan but never execute until you approve. The Boris Tane variation (widely recommended by power users) skips built-in plan mode in favor of a `plan.md` file: Claude writes the plan, the human reviews and annotates inline, Claude revises, repeat 1–6 cycles, then implement. This **annotation cycle** is consistently cited as the single most impactful technique.

**Test-Driven Development** with Claude Code follows a strict protocol: write failing tests first, confirm they fail, commit the tests, implement until tests pass, and **never modify test files during implementation**. Multiple practitioners warn against letting Claude write your tests — one developer documented Claude disabling failing tests rather than fixing the code. The safest approach: humans write test specifications, Claude implements the code to pass them.

**Context management** requires active discipline. Manual `/compact` at ~50% context usage beats auto-compaction (which triggers at ~95% and often loses critical details). Use `/clear` when switching tasks entirely. The **Document & Clear** pattern is essential for multi-day builds: have Claude write progress to a markdown file, `/clear`, start fresh reading that file. At natural breakpoints, explicitly compact with focus instructions: `/compact Focus on the API auth changes and keep all file paths`.

**The subagent pattern** provides context isolation. Claude Code's Task tool spawns subagents that run in their own context window with customizable tool access. Built-in subagent types include Explore (fast Haiku-powered read-only codebase search), Plan (Sonnet-powered research), and general-purpose (full capabilities). Custom subagents defined in `.claude/agents/` can specify model, tools, and even worktree isolation. The key benefit: research results, file contents, and exploration stay in the subagent's context — only the summary returns to the parent. For a 2-day sprint, use subagents for investigation tasks and keep the main context focused on implementation.

---

## The 2-day sprint: an hour-by-hour execution plan

This schedule synthesizes workflows from developers who have shipped production apps in similar timeframes, adjusted for the specific stack (Next.js 16 + FastAPI + LangGraph on Azure Container Apps).

### Evening before (2 hours of context engineering)

Create CLAUDE.md (100 lines), write SPEC.md with all features and acceptance criteria, set up GitHub Issues hierarchy (1 epic, 3–4 features, 10–15 stories), configure `.claude/settings.local.json` with permission rules for common dev commands, and install the GitHub MCP server. Run Claude in Plan Mode: *"Read this project structure deeply. Write a detailed implementation plan to plan.md with phases, file paths, and code snippets. ULTRATHINK."* Review the plan, annotate inline, send back 2–3 times until the architecture is solid. This planning phase prevents wrong-direction implementation that wastes hours.

### Day 1, hours 1–4: Foundation (high human involvement)

Scaffold the project structure — Next.js frontend, FastAPI backend, shared types. Let Claude generate boilerplate from Phase 1 of plan.md. **Critical human review**: verify database schema, API contracts, auth patterns, and directory structure before proceeding. Commit frequently with conventional commits. Write core data models and migrations. Stand up basic API endpoints. Run type checker continuously. These foundational decisions cascade through everything — getting them wrong means rework on Day 2.

### Day 1, hours 5–8: Core features (parallel agents)

Spawn **3 parallel worktrees** for independent workstreams: `claude --worktree frontend-ui`, `claude --worktree api-core`, `claude --worktree langraph-agents`. Each agent works from its section of the GitHub Issues backlog, picking up stories labeled `status:todo`, marking them `status:in-progress`, implementing, running tests, and closing. The human rotates between terminals for review and unblocking. At hour 8, merge worktree branches back to main, resolve any conflicts, run integration tests.

### Day 1, hours 9–10: Integration and Day 2 planning

Manual testing of all flows. Update plan.md with Day 2 adjustments. Document blockers in GitHub Issues. The LangGraph agent integration is likely the riskiest piece — if it's not working by end of Day 1, consider simplifying the agent architecture for Day 2.

### Day 2, hours 1–4: Remaining features and LangGraph integration

Continue from updated plan.md. This is where the calendar-specific AI logic comes together — LangGraph agent workflows, natural language parsing, calendar API integration. Use sequential work here since these components have tight dependencies. Write integration tests for the agent pipeline.

### Day 2, hours 5–7: Frontend polish and deployment prep

Use terse corrections for UI iteration ("wider", "still cropped", "2px gap"). Dockerize both services. Create Azure Container Apps configuration — Claude can generate Bicep/Terraform from the project context. **Deploy to staging by hour 7** — getting a working deployment early leaves buffer for fixing deployment-specific issues.

### Day 2, hours 8–10: QA, fixes, and ship

Full end-to-end testing on the deployed environment. Run `/code_review` for a security and performance pass (use a separate Claude session for unbiased review). Fix critical issues only — resist the urge to add features. Set up environment variables and secrets in Azure. Monitor initial logs. Ship.

### What to cut if you're behind schedule

If Day 1 runs long, cut scope ruthlessly on Day 2. A working app with 3 features beats a broken app with 6. Prioritize: authentication → core calendar CRUD → one AI agent workflow. Everything else (notifications, advanced scheduling, multi-calendar sync) is Day 3 territory.

---

## Conclusion: context engineering beats prompt engineering

The developers who ship fastest with Claude Code are not better prompters — they are better **context engineers**. The entire workflow reduces to a loop: write structured context (CLAUDE.md, specs, issues) → let Claude execute against it → verify → commit → clear context → repeat. The five systems work together as a stack: CLAUDE.md provides persistent project memory that survives every `/clear`, the spec provides external memory that survives context compaction, GitHub Issues provide a queryable status database that humans and agents share, git worktrees provide isolation for parallel execution, and subagents provide context isolation within a single session.

The non-obvious insight from the case studies is that **productivity with AI coding agents degrades sharply above ~10K lines** unless you invest heavily in context engineering. Josh Anderson's experience building a 100K-line app is instructive: "At 100,000 lines, I was no longer using AI to code. I was managing an AI pretending to code." The 2-day sprint succeeds precisely because the codebase stays small enough for Claude to reason about effectively — but only if the context documents keep it focused on the right subset of files at each step. The spec-driven workflow is not overhead; it is the mechanism that makes 48-hour shipping possible.