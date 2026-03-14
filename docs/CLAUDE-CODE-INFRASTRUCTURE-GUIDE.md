# Claude Code Infrastructure Setup Guide

A step-by-step guide for setting up a production-grade Claude Code development environment in any project. This document serves two audiences:

- **Humans**: Understanding what each component does, why it exists, and how to customize it
- **AI Agents**: Executing the setup by following the phases in order, filling in project-specific details

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [What You Need to Provide](#what-you-need-to-provide)
4. [Phase 1: Directory Structure](#phase-1-directory-structure)
5. [Phase 2: CLAUDE.md — Project Brain](#phase-2-claudemd--project-brain)
6. [Phase 3: SPEC.md — Source of Truth](#phase-3-specmd--source-of-truth)
7. [Phase 4: Rules — Code Standards](#phase-4-rules--code-standards)
8. [Phase 5: Agents — Specialized Bots](#phase-5-agents--specialized-bots)
9. [Phase 6: Hooks — Automated Enforcement](#phase-6-hooks--automated-enforcement)
10. [Phase 7: Skills — Custom Slash Commands](#phase-7-skills--custom-slash-commands)
11. [Phase 8: Settings — Permissions & Safety](#phase-8-settings--permissions--safety)
12. [Phase 9: GitHub Issues & Labels](#phase-9-github-issues--labels)
13. [Phase 10: External Skills](#phase-10-external-skills)
14. [Phase 11: Branch Protection & CODEOWNERS](#phase-11-branch-protection--codeowners)
15. [Phase 12: Human Workflow Documentation](#phase-12-human-workflow-documentation)
16. [Verification Checklist](#verification-checklist)
17. [Architecture Reference](#architecture-reference)

---

## Overview

This infrastructure turns Claude Code into an autonomous development team under human tech lead supervision. The system has five layers:

```text
┌─────────────────────────────────────────────────────────┐
│  CLAUDE.md          Always-loaded brief (~75 lines)     │
│                     Stack, commands, conventions         │
├─────────────────────────────────────────────────────────┤
│  SPEC.md            External memory (survives /compact) │
│                     Tech stack, architecture, decisions  │
├─────────────────────────────────────────────────────────┤
│  .claude/rules/     Always-on code standards            │
│                     Path-scoped per tech area            │
├─────────────────────────────────────────────────────────┤
│  .claude/agents/    Specialized subagents               │
│  .claude/skills/    Custom slash commands                │
│  .claude/hooks/     Automated enforcement gates          │
├─────────────────────────────────────────────────────────┤
│  GitHub Issues      Task tracking (external database)   │
│  Branch Protection  Merge gates (human approval)         │
└─────────────────────────────────────────────────────────┘
```

### Key Principle

**Context engineering beats prompt engineering.** The infrastructure ensures every Claude Code session — whether fresh, after `/compact`, or after `/clear` — has the full project context available in structured, version-controlled files. Decisions live in the repo, not in chat history.

---

## Prerequisites

- **Claude Code CLI** installed and authenticated
- **GitHub CLI** (`gh`) installed and authenticated (`gh auth login`)
- **Git** repository initialized with a remote on GitHub
- **Node.js** (for `pnpm dlx skills add` if installing external skills)
- **pnpm** (`npm install -g pnpm`) for frontend skill installation

---

## What You Need to Provide

Before an AI agent can set up the infrastructure, the human must provide:

### Required Information

| Item | Example | Used In |
|------|---------|---------|
| **Project name** | AI Calendar Assistant | CLAUDE.md, SPEC.md |
| **Tech stack** | Next.js 16, FastAPI, LangGraph | CLAUDE.md, rules, SPEC.md |
| **Repository structure** | `/frontend`, `/backend`, `/infra` | CLAUDE.md, rules |
| **Package managers** | pnpm (frontend), uv (backend) | CLAUDE.md, settings |
| **Build/test/lint commands** | `pnpm dev`, `uv run pytest` | CLAUDE.md, agents |
| **GitHub repo** | `owner/repo-name` | Issues, CODEOWNERS |
| **GitHub username** | `@owner` | CODEOWNERS |
| **Code conventions** | ES modules only, async Python | CLAUDE.md, rules |
| **Architecture decisions** | Auth approach, database choice | SPEC.md |
| **Feature list** | Auth, API, UI, Deploy | GitHub Issues |

### Optional Information

| Item | Default If Not Provided |
|------|------------------------|
| External skills to install | shadcn/ui + Vercel agent-skills |
| Custom formatters | Prettier (frontend), Ruff (backend) |
| CI/CD platform | GitHub Actions |
| Cloud provider | Azure (affects infra rules) |
| Sprint duration | 2 days |

---

## Phase 1: Directory Structure

Create the `.claude/` directory tree and update `.gitignore`.

### Directory Layout

```text
.claude/
├── agents/              # Specialized subagent definitions
├── hooks/               # Automated enforcement scripts
├── rules/               # Always-loaded code standards
├── skills/              # Custom slash commands
│   ├── pick-task/
│   ├── sync-issues/
│   └── update-decision/
├── specs/
│   ├── plans/           # Pending specs (future epics)
│   ├── in-progress/     # Active spec (current epic)
│   └── plans-executed/  # Completed specs (history)
├── settings.json        # Permissions & hooks (committed)
└── settings.local.json  # Local overrides (gitignored)

.github/
└── CODEOWNERS           # Review requirements

docs/
├── HUMAN-WORKFLOW.md    # Operational playbook
└── archive/             # Historical planning docs
```

### Commands

```bash
mkdir -p .claude/agents .claude/hooks .claude/rules .claude/skills
mkdir -p .claude/specs/plans .claude/specs/in-progress .claude/specs/plans-executed
mkdir -p .github docs docs/archive
```

### .gitignore Additions

Add these lines to your existing `.gitignore`:

```gitignore
# Claude Code
.claude/worktrees/
.claude/settings.local.json
.agents/

# Python (if applicable)
__pycache__/
*.py[cod]
.venv/

# IDE
.vscode/
.idea/
```

---

## Phase 2: CLAUDE.md — Project Brain

`CLAUDE.md` is loaded into every Claude Code session automatically. It must be concise (<100 lines) and follow the **WHAT / WHY / HOW** framework.

### Template

```markdown
# Project: {PROJECT_NAME}

{One-line description of the tech stack and deployment target.}

## Repository Structure

{Show the top-level directories and what each contains.}

## Commands

{List every build, test, lint, format, and dev command. Be exact — agents copy-paste these.}

- Frontend dev: `cd frontend && {PACKAGE_MANAGER} dev`
- Backend dev: `cd backend && {RUNNER} uvicorn app.main:app --reload`
- Frontend tests: `cd frontend && {PACKAGE_MANAGER} test`
- Backend tests: `cd backend && {RUNNER} pytest`
- Type check: `cd frontend && {PACKAGE_MANAGER} typecheck`
- Lint: `cd frontend && {PACKAGE_MANAGER} lint && cd ../backend && {RUNNER} ruff check .`
- Add frontend dep: `cd frontend && {PACKAGE_MANAGER} add <pkg>`
- Add backend dep: `cd backend && {BACKEND_ADD_CMD} <pkg>`

## Code Conventions

{5-8 rules that apply across the entire codebase. Use NEVER/ALWAYS for critical rules.}

- {Language-specific conventions}
- NEVER install new dependencies without asking first
- Conventional commits: `feat(scope):`, `fix(scope):`, etc.

## Workflow

IMPORTANT: Follow these rules strictly:

- ALWAYS read a file before editing it
- ALWAYS run tests after making changes
- ALWAYS run lint and typecheck before considering work done
- Before writing code, read the active spec in `.claude/specs/in-progress/`
- Track work via GitHub Issues — pick stories labeled `status:todo`
- Commit after each completed task with conventional commits referencing the issue number
- If uncertain about approach, ASK before proceeding
- When starting a session: `git log --oneline -10 && gh issue list --label "status:todo" --label "status:in-progress"`

## Architecture Decisions

{Key decisions that affect how code is written. Update via /update-decision.}

## Skills (Slash Commands)

- `/pick-task [area]` — Find the next unblocked story to work on
- `/sync-issues [area]` — Check issue status against actual code state
- `/update-decision` — Record a decision into SPEC.md and update affected issues

## Decision Workflow

When a decision is made (by the user or during implementation):
1. Update SPEC.md first — it is the source of truth
2. Update affected GitHub issues if scope changes
3. CLAUDE.md only changes for new conventions or commands

## Reference Docs

- SPEC.md (source of truth): `.claude/specs/in-progress/SPEC.md`
- Human workflow: `docs/HUMAN-WORKFLOW.md`
```

### Important Notes

- Keep under 100 lines — Claude Code's system prompt says CLAUDE.md content "may or may not be relevant" and can be ignored if too long
- Use `IMPORTANT:`, `NEVER`, `ALWAYS` for critical rules — these measurably improve adherence
- Don't embed file contents with `@path` — just reference paths as strings
- Architecture decisions belong here as a summary; details go in SPEC.md

---

## Phase 3: SPEC.md — Source of Truth

The SPEC lives at `.claude/specs/in-progress/SPEC.md` and is the external memory that survives `/compact` and `/clear`. It's the most important file for preventing hallucination.

### Required Sections

| Section | Purpose |
|---------|---------|
| **Overview** | One paragraph describing the product |
| **Technology Stack & Versions** | Pinned versions with install commands for every dependency |
| **Architecture** | Diagram showing how services connect |
| **Project Structure** | Full directory tree for each service |
| **Data Models** | Pydantic/TypeScript models with field types |
| **API Contracts** | Every endpoint with request/response shapes |
| **Environment Variables** | Complete list with descriptions |
| **Security Constraints** | NEVER/ALWAYS rules for security |
| **Implementation Phases** | Stories mapped to phases with dependency graph |
| **Acceptance Criteria** | Checkboxes with exact test commands |
| **Out of Scope** | What NOT to build (prevents scope creep) |
| **Decisions Log** | Table of date, decision, reason |

### Key Principles

- **Every dependency must have a pinned version and install command** — agents will hallucinate versions otherwise
- **Every endpoint must have request/response shapes** — agents need contracts to implement against
- **The decisions log is append-only** — mark old decisions as superseded, never delete
- **Implementation phases must reference GitHub Issue numbers** — this links the spec to the task tracker

### Lifecycle

```text
Epic starts → Write SPEC.md in specs/in-progress/
Epic completes → Move to specs/plans-executed/SPEC-v{N}-{name}.md
Next epic → Write new SPEC.md in specs/in-progress/
```

CLAUDE.md persists across epics. SPEC.md is per-epic.

---

## Phase 4: Rules — Code Standards

Rules live in `.claude/rules/` and are loaded automatically every session. Use YAML frontmatter with `paths:` for domain-specific rules that only load when Claude works on matching files.

### Universal Rules (always loaded)

| File | Purpose |
|------|---------|
| `workflow.md` | Step-by-step process per story (read → plan → TDD → verify → commit) |
| `tdd.md` | Red-Green-Refactor, test protection, coverage targets |
| `code-quality.md` | Anti-patterns, cleanup, security, performance |
| `git.md` | Conventional commits, branch naming, what not to commit |

### Path-Scoped Rules (loaded when working on matching files)

| File | `paths:` | Purpose |
|------|----------|---------|
| `frontend.md` | `frontend/**` | Framework-specific patterns (React, Vue, Svelte, etc.) |
| `backend.md` | `backend/**` | Server framework patterns (FastAPI, Express, Django, etc.) |
| `infra.md` | `infra/**` | IaC patterns (Terraform, Pulumi, CDK, etc.) |

### Rule File Format

```markdown
---
description: {What this rule file covers}
paths:                    # Optional — omit for universal rules
  - "frontend/**"
---

# {Title}

## {Section}

- Rule 1
- Rule 2
- NEVER {critical anti-pattern}
- ALWAYS {critical requirement}
```

### Customization Guide

**For a different frontend framework** (e.g., Vue 3 instead of Next.js):
- Replace `frontend.md` content with Vue-specific patterns (Composition API, Pinia, etc.)
- Keep the same frontmatter structure with `paths: ["frontend/**"]`

**For a different backend** (e.g., Express/Go instead of FastAPI):
- Replace `backend.md` with language/framework-specific patterns
- Update the test commands and dependency management references

**For a different cloud** (e.g., AWS instead of Azure):
- Replace `infra.md` with AWS naming conventions, CloudFormation/CDK patterns
- Update resource naming rules

---

## Phase 5: Agents — Specialized Bots

Agents run as subagents in isolated context windows. Define them in `.claude/agents/`.

### File Format

```markdown
---
name: {agent-name}
description: {When Claude should delegate to this agent. Be specific.}
model: {sonnet|opus|haiku}
tools: {comma-separated tool list}
maxTurns: {number}
---

# {Agent Name} Instructions

{Detailed instructions for the agent's task.}

## Process
{Step-by-step process the agent follows.}

## Output Format
{How the agent should report findings.}
```

### Recommended Agents

| Agent | Model | Tools | Purpose |
|-------|-------|-------|---------|
| `code-reviewer` | sonnet | Read, Grep, Glob, Bash | Post-feature security + quality review |
| `test-runner` | sonnet | Bash, Read, Grep, Glob | Run full test suite and report failures |
| `issue-tracker` | haiku | Bash, Read | Check/update GitHub Issues status |

### When to Use Each Model

- **haiku**: Fast, cheap — use for simple lookups, status checks, file searches
- **sonnet**: Balanced — use for code review, test analysis, moderate reasoning
- **opus**: Most capable — use for architecture decisions, complex debugging (expensive)

---

## Phase 6: Hooks — Automated Enforcement

Hooks are shell scripts triggered by Claude Code events. They provide **deterministic enforcement** — unlike rules (which are advisory), hooks can block actions.

### Hook Types

| Event | When It Fires | Use Case |
|-------|---------------|----------|
| `PreToolUse` | Before Edit/Write/Bash | Block test modifications, validate paths |
| `PostToolUse` | After Edit/Write | Auto-format code, run linters |
| `Stop` | Before Claude finishes | Remind to run tests, update issues |
| `SessionStart` | On session start/compact/clear | Inject context reminders |

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Allow — proceed normally |
| `2` | Block — stderr message shown to Claude as feedback |
| Other | Allow — stderr logged but action proceeds |

### Recommended Hooks

#### 1. Test Protection (`protect-tests.sh`)

Blocks modification of test files during implementation. This is the single most important hook for TDD enforcement.

```bash
#!/bin/bash
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)
[ -z "$FILE_PATH" ] && exit 0

case "$FILE_PATH" in
  test_*|*/test_*|*.test.*|*/*.test.*|*.spec.*|*/*.spec.*|__tests__/*|*/__tests__/*)
    if [ "${WRITING_TESTS:-0}" = "1" ]; then
      exit 0
    fi
    echo "BLOCKED: Cannot modify test file '$FILE_PATH' during implementation." >&2
    echo "If you need to write NEW tests, set WRITING_TESTS=1 first." >&2
    exit 2
    ;;
esac
exit 0
```

#### 2. Auto-Format (`auto-format.sh`)

Runs formatters after file edits. Customize the `case` block for your tech stack.

```bash
#!/bin/bash
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)
[ -z "$FILE_PATH" ] && exit 0
[ ! -f "$FILE_PATH" ] && exit 0

case "$FILE_PATH" in
  *.py)
    {PYTHON_FORMATTER} "$FILE_PATH" 2>/dev/null || true
    ;;
  *.ts|*.tsx|*.js|*.jsx|*.json|*.css)
    {JS_FORMATTER} "$FILE_PATH" 2>/dev/null || true
    ;;
esac
exit 0
```

#### 3. Pre-Stop Check (`pre-stop-check.sh`)

Non-blocking reminder before Claude finishes.

```bash
#!/bin/bash
echo "Before stopping, verify:" >&2
echo "  1. Tests pass ({TEST_COMMAND})" >&2
echo "  2. Linting clean ({LINT_COMMAND})" >&2
echo "  3. Related GitHub issue updated (gh issue edit)" >&2
exit 0
```

### Registering Hooks

Hooks are registered in `.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [{ "type": "command", "command": ".claude/hooks/pre-stop-check.sh" }]
      }
    ]
  }
}
```

Make all hooks executable: `chmod +x .claude/hooks/*.sh`

---

## Phase 7: Skills — Custom Slash Commands

Skills are markdown files in `.claude/skills/` that define reusable workflows invokable via `/skill-name`.

### File Format

```text
.claude/skills/{skill-name}/SKILL.md
```

```markdown
---
name: {skill-name}
description: {When to use this skill — Claude auto-triggers based on this.}
allowed-tools: Read, Bash, Grep, Glob
argument-hint: "[optional arguments]"
---

# {Skill Title}

{What this skill does.}

## Steps

1. **Step one**: {description}
   ```bash
   {exact command}
   ```

2. **Step two**: {description}

## Rules

- {constraint 1}
- {constraint 2}
```

### Recommended Skills

#### `/pick-task` — Find Next Story

Queries GitHub Issues for the highest-priority unblocked story.

#### `/sync-issues` — Progress Check

Compares GitHub Issue status labels against actual code state. Updates labels to reflect reality.

#### `/update-decision` — Record Decisions

When the human makes a decision, this skill:
1. Updates SPEC.md with the decision (what, why, what it replaces)
2. Finds and updates affected GitHub Issues
3. Summarizes what changed

### Skills vs. Agents vs. Rules

| Mechanism | Loaded When | Execution | Best For |
|-----------|-------------|-----------|----------|
| **Rules** | Every session | Inline (main context) | Conventions, standards |
| **Skills** | On trigger/invocation | Inline (main context) | Workflows, procedures |
| **Agents** | When delegated | Isolated context | Complex, verbose tasks |

---

## Phase 8: Settings — Permissions & Safety

### `.claude/settings.json` (committed to git)

Controls what Claude Code can and cannot do. Structure:

```json
{
  "permissions": {
    "allow": [
      "Bash({PACKAGE_MANAGER} *)",
      "Bash(git status*)",
      "Bash(git log*)",
      "Bash(git diff*)",
      "Bash(git add *)",
      "Bash(git commit *)",
      "Bash(gh issue *)",
      "Bash(gh pr *)",
      "Bash({TEST_RUNNER}*)",
      "Bash({LINTER}*)",
      "Read",
      "Edit",
      "Write",
      "Glob",
      "Grep"
    ],
    "deny": [
      "Bash(rm -rf *)",
      "Bash(git push --force*)",
      "Bash(git reset --hard*)",
      "Bash(git clean -f*)"
    ]
  },
  "hooks": {}
}
```

### Permission Pattern Syntax

| Pattern | Matches |
|---------|---------|
| `Bash(npm run *)` | Commands starting with `npm run` |
| `Bash(git *)` | Any git command |
| `Read(./.env)` | Specific file |
| `Read(/src/**)` | Recursive glob |

### What to Always Deny

```json
"deny": [
  "Bash(rm -rf *)",
  "Bash(git push --force*)",
  "Bash(git reset --hard*)",
  "Bash(git clean -f*)"
]
```

### `.claude/settings.local.json` (gitignored)

For personal overrides like allowing `git push`:

```json
{
  "permissions": {
    "allow": ["Bash(git push *)"]
  }
}
```

---

## Phase 9: GitHub Issues & Labels

### Label Taxonomy

Create these labels on your GitHub repo. Adjust area labels to match your project domains.

```bash
# Type labels
gh label create "type:epic" --color "7B68EE" --description "Top-level initiative"
gh label create "type:feature" --color "4169E1" --description "Feature under an epic"
gh label create "type:story" --color "6495ED" --description "Implementable unit of work"
gh label create "type:bug" --color "DC143C" --description "Bug report"
gh label create "type:spike" --color "FF8C00" --description "Research/investigation task"

# Status labels (mutually exclusive)
gh label create "status:todo" --color "EEEEEE" --description "Ready to be picked up"
gh label create "status:in-progress" --color "FFFF00" --description "Currently being worked on"
gh label create "status:blocked" --color "FF4500" --description "Blocked by dependency"
gh label create "status:done" --color "2E8B57" --description "Completed"

# Priority labels
gh label create "priority:critical" --color "8B0000" --description "Must ship"
gh label create "priority:high" --color "FF6347" --description "Important for MVP"
gh label create "priority:medium" --color "FFA07A" --description "Nice to have"

# Area labels (customize per project)
gh label create "area:{AREA1}" --color "{COLOR}" --description "{DESCRIPTION}"
gh label create "area:{AREA2}" --color "{COLOR}" --description "{DESCRIPTION}"

# Sprint labels (optional)
gh label create "sprint:day1" --color "1E90FF" --description "Day 1 of sprint"
gh label create "sprint:day2" --color "00CED1" --description "Day 2 of sprint"
```

### Issue Hierarchy

```text
EPIC (type:epic)
├── FEATURE (type:feature, area:*, sprint:*)
│   ├── STORY (type:story, status:todo, priority:*, area:*)
│   ├── STORY
│   └── STORY
└── FEATURE
    ├── STORY
    └── STORY
```

### Story Issue Template

Each story should have:
- **Description**: What and why
- **Acceptance Criteria**: Checkboxes with exact verification commands
- **File Scope**: Specific paths to create/modify
- **Dependencies**: References to blocking issues
- **Parent Feature**: `Closes part of #N`

---

## Phase 10: External Skills

Install community skills for your tech stack. These are downloaded to `.agents/` (gitignored) and symlinked into `.claude/skills/`.

### Installation

```bash
# UI/Design skills (for any frontend project)
pnpm dlx skills add shadcn/ui --yes
pnpm dlx skills add vercel-labs/agent-skills --yes
pnpm dlx skills add nextlevelbuilder/ui-ux-pro-max-skill --yes
```

### Cleanup Irrelevant Skills

After installation, remove skills not relevant to your project:

```bash
# Example: remove React Native skills for a web-only project
rm .claude/skills/{irrelevant-skill-name}
rm -rf .agents/skills/{irrelevant-skill-name}
```

### Context Window Impact

Each skill adds to Claude's context. Keep to 3-4 skill packs maximum. Prioritize:
1. **Framework-specific** (shadcn/ui, Vercel react-best-practices)
2. **Design** (ui-ux-pro-max for design system generation)
3. **Remove** anything not directly relevant to your stack

---

## Phase 11: Branch Protection & CODEOWNERS

### CODEOWNERS

Create `.github/CODEOWNERS`:

```text
# Global — all PRs require owner review
* @{GITHUB_USERNAME}

# Sensitive areas (customize per project)
{INFRA_DIR}/ @{GITHUB_USERNAME}
.github/ @{GITHUB_USERNAME}
CLAUDE.md @{GITHUB_USERNAME}
.claude/ @{GITHUB_USERNAME}
```

### Branch Protection via API

```bash
gh api repos/{OWNER}/{REPO}/branches/main/protection -X PUT --input - <<'EOF'
{
  "required_status_checks": null,
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true
  },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": true
}
EOF
```

### What This Enforces

| Rule | Effect |
|------|--------|
| PR required | No direct pushes to main |
| 1 approval from CODEOWNER | Human must review |
| Dismiss stale reviews | New pushes invalidate old approvals |
| Linear history | Squash/rebase only |
| Conversation resolution | All review threads must be resolved |
| No force pushes | History cannot be rewritten |
| No branch deletion | main cannot be deleted |

---

## Phase 12: Human Workflow Documentation

Create `docs/HUMAN-WORKFLOW.md` covering:

1. **Starting a session** — check git status, read spec, pick stories
2. **Launching parallel agents** — `claude --worktree <name>` in separate terminals
3. **Monitoring loop** — glance at panes every 10-15 minutes
4. **When to intervene** — agent loops, scope creep, architecture drift
5. **Code review** — diff worktree branches, use fresh Claude session for unbiased review
6. **Merging** — merge backend first, then agents, then frontend; after each story, not in batch
7. **Decisions** — what you decide vs. what AI decides
8. **End of session** — merge, push, update issues, document progress

See `docs/HUMAN-WORKFLOW.md` in this repository for a complete example.

---

## Verification Checklist

After completing all phases, verify:

```text
[ ] CLAUDE.md exists at project root and is under 100 lines
[ ] .claude/specs/in-progress/SPEC.md exists with all required sections
[ ] .claude/rules/ has workflow.md, tdd.md, code-quality.md, git.md
[ ] .claude/rules/ has path-scoped rules for each tech area
[ ] .claude/agents/ has at least code-reviewer.md and test-runner.md
[ ] .claude/hooks/ has protect-tests.sh (executable)
[ ] .claude/hooks/ has auto-format.sh (executable)
[ ] .claude/settings.json has allow and deny permissions
[ ] .claude/skills/ has pick-task, sync-issues, update-decision
[ ] .github/CODEOWNERS exists with correct owner
[ ] Branch protection enabled on main (gh api check)
[ ] GitHub labels created (type, status, priority, area)
[ ] GitHub issues created (epic → features → stories)
[ ] docs/HUMAN-WORKFLOW.md exists
[ ] .gitignore includes .claude/worktrees/, .claude/settings.local.json, .agents/
[ ] Start a fresh `claude` session — verify CLAUDE.md loads
[ ] Run /pick-task — verify it queries GitHub Issues
[ ] Run /sync-issues — verify it reports status
```

---

## Architecture Reference

### File Inventory

| Category | File | Committed | Purpose |
|----------|------|-----------|---------|
| Root | `CLAUDE.md` | Yes | Always-loaded project brain |
| Root | `skills-lock.json` | Yes | Pins external skill versions |
| Spec | `.claude/specs/in-progress/SPEC.md` | Yes | Technical source of truth |
| Settings | `.claude/settings.json` | Yes | Permissions and hooks |
| Settings | `.claude/settings.local.json` | No | Personal overrides |
| Rules | `.claude/rules/workflow.md` | Yes | Development process |
| Rules | `.claude/rules/tdd.md` | Yes | Test-driven development |
| Rules | `.claude/rules/code-quality.md` | Yes | Quality anti-patterns |
| Rules | `.claude/rules/git.md` | Yes | Commit conventions |
| Rules | `.claude/rules/{frontend}.md` | Yes | Framework-specific (path-scoped) |
| Rules | `.claude/rules/{backend}.md` | Yes | Server-specific (path-scoped) |
| Rules | `.claude/rules/{infra}.md` | Yes | IaC-specific (path-scoped) |
| Agents | `.claude/agents/code-reviewer.md` | Yes | Code review subagent |
| Agents | `.claude/agents/test-runner.md` | Yes | Test execution subagent |
| Agents | `.claude/agents/issue-tracker.md` | Yes | Issue management subagent |
| Hooks | `.claude/hooks/protect-tests.sh` | Yes | TDD enforcement gate |
| Hooks | `.claude/hooks/auto-format.sh` | Yes | Post-edit formatting |
| Hooks | `.claude/hooks/pre-stop-check.sh` | Yes | Exit reminder |
| Skills | `.claude/skills/pick-task/SKILL.md` | Yes | Task selection workflow |
| Skills | `.claude/skills/sync-issues/SKILL.md` | Yes | Issue status sync |
| Skills | `.claude/skills/update-decision/SKILL.md` | Yes | Decision recording |
| GitHub | `.github/CODEOWNERS` | Yes | Review requirements |
| Docs | `docs/HUMAN-WORKFLOW.md` | Yes | Operational playbook |
| External | `.agents/skills/*` | No | Downloaded skill packs |

### Context Loading Order

```text
1. Claude Code system prompt (~50 instruction slots)
2. CLAUDE.md (always loaded, ~75 lines)
3. .claude/rules/ (all non-path-scoped rules loaded)
4. .claude/rules/{scoped} (loaded when matching files are accessed)
5. Skills (loaded on trigger or auto-invocation)
6. MCP server tool definitions (if any configured)
7. Conversation history
```

### Source of Truth Hierarchy

```text
SPEC.md        → Technology decisions, architecture, API contracts
CLAUDE.md      → Conventions, commands, workflow rules
GitHub Issues  → Task status, acceptance criteria, scope
.claude/rules/ → Code standards enforcement
```

When information conflicts, higher in this list wins.

---

## For AI Agents: Setup Execution Checklist

If you are an AI agent tasked with setting up this infrastructure:

1. Ask the human to provide the information from [What You Need to Provide](#what-you-need-to-provide)
2. Execute phases 1-12 in order
3. For each template file, replace `{PLACEHOLDER}` values with project-specific details
4. After creating all files, run the [Verification Checklist](#verification-checklist)
5. Create a PR with the infrastructure setup for human review
6. After approval, the human follows `docs/HUMAN-WORKFLOW.md` to begin the sprint
