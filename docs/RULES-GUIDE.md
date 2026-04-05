# Writing Rules Files

Guide for writing `.claude/rules/` files. Apply when creating or rewriting any rules file (stories #134, #135, #136).

## Philosophy

Rules files are **lean, best-practice-oriented backbone guidance** — not codebase documentation. They steer the AI toward production-quality code for things it cannot infer from reading the codebase.

If a current codebase pattern is wrong and you encode it as a rule, it gets amplified into every new file. Rules should be **forward-looking best practices**, not backward-looking pattern documentation.

## Target Size

- **60-80 lines, 3-5 KB** (~800-1200 tokens) for a path-scoped rules file
- Reference: `code-quality.md` (60 lines), `tdd.md` (52 lines) — good models
- Hard ceiling: ~130 lines (only justified for complex domains with skill orchestration, like `frontend.md`)

## The Litmus Test

Before including any rule, apply all three filters:

1. **Would the AI get this wrong without this rule?** If existing code demonstrates the pattern clearly, the AI will follow it via in-context learning. Remove.
2. **Is this discoverable by reading one file?** If yes, the AI can find it. Remove.
3. **Is this already in another rules file?** If `code-quality.md` or `tdd.md` covers it, don't repeat. Remove.

If a line fails any filter, it doesn't belong.

## What to Include

| Category | Example |
|----------|---------|
| **Architecture constraints** | "Service layers raise domain exceptions — never import HTTPException in service modules" |
| **Best practices the codebase should adopt** | Structlog over stdlib, base exception classes, explicit timeouts |
| **Non-obvious project-specific gotchas** | Which SDKs need `run_in_executor`, how locks are scoped |
| **Conventions that differ from defaults** | `asyncio_mode = "auto"`, `extra="forbid"` on request models |
| **Contracts the AI must preserve** | SSE event types, terminal event requirement |

## What to Exclude

| Category | Why |
|----------|-----|
| **Project layout trees** | Discoverable — the AI can `ls` or `Glob` |
| **Tables documenting existing code** (singletons, fixtures, status codes) | Discoverable — the AI can grep for patterns |
| **Code examples mirroring existing code** | The codebase IS the example — say "follow existing pattern" |
| **Migration/transitional notes** | Project context, not coding rules — belongs in specs or PRD |
| **Things the LLM already knows** | `asyncio.sleep` over `time.sleep`, HTTP status code meanings, standard Python conventions |
| **Rules from other files** | `code-quality.md` covers security, cleanup, dependencies, performance — don't duplicate |
| **Logging/naming conventions the LLM does correctly by default** | Only include if the project convention differs from standard practice |

## Structure Template

```markdown
---
description: [Stack] + [domain] conventions
paths:
  - "path/**"
---

# [Domain] Rules

## Architecture
[Layer boundaries, dependency direction, patterns that vary per project]

## [Domain-Specific Best Practices]
[Production patterns — forward-looking, not just current state]

## [Key Technical Area]
[Only non-obvious gotchas and project-specific constraints]

## Testing
[Only what differs from standard test framework behavior]
```

Each section: 5-15 lines of bullet points. Prefer prose rules over tables and code blocks — tables document what exists, prose rules guide what should be.

## Research Before Writing

Before writing or rewriting a rules file:

1. **Read the PRD** — understand what system you're building and its production concerns
2. **Research best practices** for the specific domain (not generic tutorials — production patterns for systems like this one)
3. **Read adjacent rules files** (`code-quality.md`, `tdd.md`, `workflow.md`) to know what's already covered
4. **Apply the litmus test** to every line before finalizing
