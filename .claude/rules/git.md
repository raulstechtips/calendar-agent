---
description: Git workflow and commit conventions
---

# Git Rules

## Conventional commits

Format: `<type>(<scope>): <description>`

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `ci`, `perf`

Scopes: `auth`, `api`, `agent`, `calendar`, `search`, `chat`, `ui`, `infra`, `deps`

Examples:
- `feat(auth): add Google OAuth with refresh token support (#9)`
- `fix(agent): handle expired token in calendar tool (#17)`
- `test(api): add integration tests for user endpoints (#13)`

## Commit rules

- Subject line: imperative mood, lowercase, no period, max 72 characters
- Body: explain WHY, not WHAT — the diff shows what changed
- Reference issue: `Closes #NNN` or `Refs #NNN` in footer
- Each commit MUST leave the codebase buildable with tests passing
- Never commit with failing tests or lint violations
- Never combine unrelated changes in one commit

## What to NEVER commit

- `.env` files (only `.env.example`)
- Secrets, API keys, passwords, tokens
- `node_modules/`, `__pycache__/`, `.venv/`
- `terraform.tfstate`, `terraform.tfstate.backup`
- `*.tfvars` with real values
- Debug statements, console.log, print()
- Large binary files

## Branch naming (for worktrees)

Format: `<type>/<issue-number>-<short-description>`
Example: `feat/8-auth-setup`, `fix/42-token-refresh`, `chore/29-project-init`

## PI tags

When a Program Increment (sprint) is closed, tag the commit:
- Format: `pi-N-complete` (e.g., `pi-1-complete`, `pi-2-complete`)
- Created by the `/close-pi` skill
- Local only by default — push with `git push origin pi-N-complete` if desired
