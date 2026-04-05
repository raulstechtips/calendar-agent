---
description: Development workflow — context gathering, planning, implementing, reviewing
---

# Development Workflow

## Context Gathering

Before writing code, read up the issue hierarchy to understand why this work exists:

- Read the current issue: `gh issue view <number>` — understand acceptance criteria
- Follow `## Parent` links upward through the hierarchy (story → feature → epic → PI → PRD)
- At each level, note goals, constraints, and scope boundaries
- Always read the PRD (`.claude/sdlc/prd/PRD.md`) for security constraints and architecture decisions
- Deeper context prevents coding to the letter of a story while missing broader product intent

## Planning

- List files to create/modify and identify existing patterns to follow
- Search for existing code that handles similar concerns — reuse over reinvent
- Cross-check the plan against applicable rules files — rules override plan defaults
- For each PRD security constraint relevant to this work, note how the implementation satisfies it
- If the plan touches multiple domains (frontend, backend, agents), verify it respects each domain's rules file

## Implementing

- Follow TDD red-green-refactor cycle (see `tdd.md`)
- Run the full verification suite for the area being changed:
  - Backend: `uv run pytest`, `uv run ruff check .`, `uv run mypy .`, `uv run pyright`
  - Frontend: `pnpm test`, `pnpm lint`, `pnpm typecheck`
- Commit at logical checkpoints — each passing test or completed sub-task, not one giant commit at the end

## Reviewing

- Re-read the acceptance criteria — confirm each is met
- Verify no regressions in adjacent code
- Run cleanup checks per `code-quality.md` (debug statements, TODOs, commented-out code)

## Decision Boundaries

**Ask the human when:**
- Behavior is ambiguous (not just implementation details)
- Multiple architecturally different approaches exist
- Changes affect files outside the story's scope
- Credentials or environment config is needed

**Decide autonomously when:**
- Fixing lint/type errors from the current change
- Implementation approach is clear from existing patterns

## Error Recovery

- Maximum 3 attempts to fix a failing test, then ask the human
- If a test fails for reasons outside the story's scope, report it and move on
