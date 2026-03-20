# SDLC Plugin Guide

How to use the v2 SDLC plugin to plan, decompose, execute, and close sprints.

---

## Key Concepts

| Concept | What it is | Where it lives |
|---------|-----------|----------------|
| **PRD** | Product Requirements Document — the stable "what and why" (architecture, data models, API contracts, security constraints, decisions) | `.claude/sdlc/prd/PRD.md` |
| **PI Plan** | Program Increment Plan — the "what and when" for the current sprint (epics, features, dependency graph, worktree strategy) | `.claude/sdlc/pi/PI.md` |
| **Epic** | A large initiative spanning multiple features | GitHub Issue with `type:epic` label |
| **Feature** | A deliverable capability under an epic | GitHub Issue with `type:feature` label |
| **Story** | The smallest implementable unit of work | GitHub Issue with `type:story` label |

**Source of truth split:** The PRD owns product requirements. The PI Plan owns sprint structure. GitHub Issues own the detailed work items (acceptance criteria, file scope, dependencies).

---

## The Full Lifecycle

```
sdlc:define pi  ──►  sdlc:define epic  ──►  sdlc:define feature  ──►  sdlc:define story
       │                                                                       │
       │                                                                       ▼
  sdlc:retro pi  ◄──────────────────────────────────  sdlc:status  →  work  →  sdlc:reconcile
```

### Phase 1: Plan the Sprint

```
sdlc:define pi
```

This skill:
- Reviews the PRD Roadmap for available workstreams
- Asks you which workstreams go into this sprint
- Decomposes each workstream into epics with features (titles only)
- Builds a dependency graph and proposes a worktree strategy
- Writes a local draft at `.claude/sdlc/drafts/pi.md` with `#TBD` placeholders

Then push to GitHub:
```
sdlc:create pi
```

If a previous PI exists, run `sdlc:retro pi` for the retrospective, then `sdlc:create pi` archives the old PI and creates the new one.

### Phase 2: Decompose Into Work Items

Work top-down: epic → feature → story. Each level creates stub issues for the next level down.

**Step 1 — Detail each epic:**
```
sdlc:define epic "UI Overhaul"
sdlc:create epic
```
Creates a detailed GitHub Issue for the epic + stub feature issues (title + parent link only). Updates PI.md with real issue numbers.

**Step 2 — Detail each feature:**
```
sdlc:define feature #125
sdlc:create feature
```
Takes a stub feature issue, fleshes it out with a full description and story breakdown. Creates stub story issues (title + parent links only).

**Step 3 — Detail each story:**
```
sdlc:define story #130
sdlc:create story
```
Takes a stub story issue and adds the full detail: acceptance criteria, file scope, technical notes, verified dependencies.

### Phase 3: Execute

```
sdlc:status api
```

Presents an ordered list of unblocked stories by priority (optionally filtered by area). Checks all dependencies, traces root blockers, identifies parallelization opportunities. You decide which story to pick up — the `status:in-progress` label transition is your responsibility.

After completing a story, the agent creates a PR. Then run `sdlc:status` again for the next one.

### Phase 4: Monitor & Adjust

**Check project health:**
```
sdlc:reconcile
```
Audits the full issue hierarchy — fixes stale labels, validates dependencies, detects orphaned references and circular deps, reports status.

**When scope changes mid-sprint:**
```
sdlc:update pi "split UI Overhaul into two epics"
sdlc:update epic #123
sdlc:update feature #125
sdlc:update story #130
```

**When a design decision is made:**
```
sdlc:update prd "Use Redis for session persistence instead of Postgres"
```
Records the decision in the PRD Decision Log. Decisions are baked into the PRD body when the PI closes.

### Phase 5: Close the Sprint

**Step 1 — Run the retrospective:**
```
sdlc:retro pi
```
Produces an analysis document at `.claude/sdlc/retros/`. Does NOT modify issues, labels, or artifacts.

**Step 2 — Archive and start fresh:**
```
sdlc:create pi
```
When run with an existing PI, bakes decisions into PRD, wipes decision log, bumps PRD version, archives PI to `.claude/sdlc/pi/completed/PI-N.md`, creates git tag `pi-N-complete`.

Then run `sdlc:define pi` to start the next sprint.

---

## Quick Reference

### All Skills

| Skill | Purpose |
|-------|---------|
| `sdlc:define prd` | Guided interview to draft a new PRD |
| `sdlc:create prd` | Push PRD draft to git |
| `sdlc:update prd` | Record a decision or update a PRD section |
| `sdlc:define pi` | Draft a new Program Increment plan |
| `sdlc:create pi` | Push PI draft to GitHub |
| `sdlc:update pi` | Update PI Plan when scope changes mid-sprint |
| `sdlc:retro pi` | Process retrospective with metrics |
| `sdlc:define epic` | Draft epic details |
| `sdlc:create epic` | Create epic + stub feature issues on GitHub |
| `sdlc:define feature` | Draft feature details |
| `sdlc:create feature` | Create feature + stub story issues on GitHub |
| `sdlc:define story` | Draft story with full AC and file scope |
| `sdlc:create story` | Create story issue on GitHub |
| `sdlc:update` | Surgical edits to any existing artifact or issue |
| `sdlc:status` | Find next unblocked story; project health briefing |
| `sdlc:reconcile` | Audit hierarchy, fix labels, validate deps |
| `sdlc:capture` | Quick-capture idea as triage issue |
| `sdlc:init` | Bootstrap labels, directories, and project setup |

### Label Taxonomy

| Category | Labels |
|----------|--------|
| Type | `type:epic`, `type:feature`, `type:story`, `type:spike`, `type:bug`, `type:chore` |
| Status | `status:todo`, `status:in-progress`, `status:done`, `status:blocked` |
| Priority | `priority:critical`, `priority:high`, `priority:medium`, `priority:low` |
| Area | `area:auth`, `area:api`, `area:agent`, `area:ui`, `area:infra`, `area:search` |
| Triage | `triage` |

### Dependency Rules

A dependency is **satisfied** if: the issue has `status:done` label OR is `CLOSED`.

Stories with unmet blockers get `status:blocked` automatically. `sdlc:status` and `sdlc:reconcile` both enforce this.

### GitHub Issue Templates

**Epic:** Overview, Success Criteria, Features checklist, Non-goals, Dependencies

**Feature:** Description, Stories checklist, Non-goals, Dependencies, Parent (Epic)

**Story:** Description, Acceptance Criteria, File Scope (new + modified files), Technical Notes, Dependencies, Parent (Epic + Feature)

---

## File Structure

```
.claude/
├── sdlc/
│   ├── prd/
│   │   ├── PRD.md                 ← product requirements (git-versioned)
│   │   └── completed/
│   ├── pi/
│   │   ├── PI.md                  ← current sprint plan
│   │   └── completed/
│   │       └── PI-1.md            ← archived sprints
│   ├── drafts/                    ← local working drafts (gitignored)
│   └── retros/                    ← retrospective notes
└── plugins/
    └── sdlc/                      ← SDLC plugin (commands, skills, hooks)
```

---

## Plugin Loading

Load the SDLC plugin when starting a session:

```bash
claude --plugin-dir .claude/plugins/sdlc
```

Or set an alias for convenience:

```bash
alias cc='claude --plugin-dir .claude/plugins/sdlc'
```

---

## Getting Started (First-Time Setup)

Before using SDLC skills on a new project, create the required GitHub labels:

```bash
# Type labels
gh label create "type:epic"    --color "#7057ff" --force
gh label create "type:feature" --color "#0075ca" --force
gh label create "type:story"   --color "#cfd3d7" --force
gh label create "type:spike"   --color "#e4e669" --force
gh label create "type:bug"     --color "#d73a4a" --force
gh label create "type:chore"   --color "#fef2c0" --force

# Status labels
gh label create "status:todo"        --color "#ededed" --force
gh label create "status:in-progress" --color "#0075ca" --force
gh label create "status:done"        --color "#0e8a16" --force
gh label create "status:blocked"     --color "#e11d48" --force

# Priority labels
gh label create "priority:critical" --color "#b60205" --force
gh label create "priority:high"     --color "#d93f0b" --force
gh label create "priority:medium"   --color "#fbca04" --force
gh label create "priority:low"      --color "#0e8a16" --force

# Triage label
gh label create "triage" --color "#bfd4f2" --force
```

Area labels are project-specific. Use `sdlc:init` to create them for your project.

---

## Skill Arguments

Skills accept arguments via the `$ARGUMENTS` placeholder. This lets you pass context directly in the slash command:

```
sdlc:define story #130
sdlc:status api
sdlc:update prd "Switch from Postgres to Redis for sessions"
sdlc:capture "users need dark mode"
```

The text after the skill name is passed as `$ARGUMENTS` and used by the skill to determine the target artifact, issue number, or free-form instruction.

---

## Common Workflows

### Starting a brand new project
```
sdlc:define prd          → guided interview, creates PRD draft
sdlc:create prd          → commits PRD.md to git
sdlc:init               → creates GitHub labels from PRD
sdlc:define pi "MVP"     → creates PI-1 draft from PRD Roadmap
sdlc:create pi           → pushes PI-1 to GitHub
sdlc:define epic "Auth"  → drafts epic
sdlc:create epic         → creates epic + stub features on GitHub
sdlc:define feature #10  → details feature + stub stories
sdlc:create feature      → creates feature + stub stories on GitHub
sdlc:define story #15    → adds full AC, file scope, deps
sdlc:create story        → creates story issue on GitHub
sdlc:status              → start coding
```

### Starting a new sprint on an existing project
```
sdlc:retro pi            → produces retrospective analysis
sdlc:create pi           → archives PI-1, then prompts for PI-2 scope
sdlc:define pi "Phase 2" → drafts PI-2
sdlc:create pi           → pushes PI-2 to GitHub
sdlc:define epic "Session Persistence"
sdlc:create epic
sdlc:define feature #125
sdlc:create feature
sdlc:define story #130
sdlc:create story
sdlc:status
```

### Mid-sprint scope change
```
sdlc:update prd "Switch from Postgres to Redis for sessions"
sdlc:update pi "add Redis checkpointer story to Session Persistence"
sdlc:update feature #125    → add the new story
sdlc:define story #135      → flesh out the new story
sdlc:create story
sdlc:reconcile              → verify dependency graph is consistent
```

### End of day check
```
sdlc:reconcile             → fix stale labels, see what's blocked
sdlc:status                → what's next?
```
