# SDLC Skill Suite Guide

How to use the project management skills to plan, decompose, execute, and close sprints.

---

## Key Concepts

| Concept | What it is | Where it lives |
|---------|-----------|----------------|
| **PRD** | Product Requirements Document — the stable "what and why" (architecture, data models, API contracts, security constraints, decisions) | `.claude/prd/PRD.md` |
| **PI Plan** | Program Increment Plan — the "what and when" for the current sprint (epics, features, dependency graph, worktree strategy) | `.claude/pi/PI.md` |
| **Epic** | A large initiative spanning multiple features | GitHub Issue with `type:epic` label |
| **Feature** | A deliverable capability under an epic | GitHub Issue with `type:feature` label |
| **Story** | The smallest implementable unit of work | GitHub Issue with `type:story` label |

**Source of truth split:** The PRD owns product requirements. The PI Plan owns sprint structure. GitHub Issues own the detailed work items (acceptance criteria, file scope, dependencies).

---

## The Full Lifecycle

```
/plan-increment  ──►  /create-epic  ──►  /create-feature  ──►  /detail-story
       │                                                              │
       │                                                              ▼
  /close-pi  ◄──────────────────────────────────  /pick-task  →  work  →  /sync-issues
```

### Phase 1: Plan the Sprint

```
/plan-increment "Enhancement & Polish"
```

This skill:
- Reviews the PRD Roadmap for available workstreams
- Asks you which workstreams go into this sprint
- Decomposes each workstream into epics with features (titles only)
- Builds a dependency graph and proposes a worktree strategy
- Writes `.claude/pi/PI.md` with `#TBD` placeholders

If a previous PI exists, it closes it first (runs `/close-pi` automatically).

### Phase 2: Decompose Into Work Items

Work top-down: epic → feature → story. Each level creates stub issues for the next level down.

**Step 1 — Detail each epic:**
```
/create-epic "UI Overhaul"
```
Creates a detailed GitHub Issue for the epic + stub feature issues (title + parent link only). Updates PI.md with real issue numbers.

**Step 2 — Detail each feature:**
```
/create-feature #125
```
Takes a stub feature issue, fleshes it out with a full description and story breakdown. Creates stub story issues (title + parent links only).

**Step 3 — Detail each story:**
```
/detail-story #130
```
Takes a stub story issue and adds the full detail: acceptance criteria, file scope, technical notes, verified dependencies.

### Phase 3: Execute

```
/pick-task api
```

Finds the highest-priority unblocked story (optionally filtered by area). Checks all dependencies, fixes any mismatched labels, presents a recommendation. On confirmation, marks it `status:in-progress` and you start coding.

After completing a story, the agent creates a PR. Then run `/pick-task` again for the next one.

### Phase 4: Monitor & Adjust

**Check project health:**
```
/sync-issues
```
Audits the full issue hierarchy — fixes stale labels, validates dependencies, detects orphaned references and circular deps, reports status.

**When scope changes mid-sprint:**
```
/update-pi "split UI Overhaul into two epics"
/update-epic #123
/update-feature #125
/update-story #130
```

**When a design decision is made:**
```
/update-prd "Use Redis for session persistence instead of Postgres"
```
Records the decision in the PRD Decision Log. Decisions are baked into the PRD body when the PI closes.

### Phase 5: Close the Sprint

```
/close-pi
```

This skill:
- Summarizes what shipped vs what's still open (from GitHub Issues)
- Verifies the PRD Decision Log is complete
- Bakes decision log entries into the relevant PRD sections
- Wipes the decision log for the next sprint
- Bumps the PRD version
- Archives the PI Plan to `.claude/pi/completed/PI-N.md`
- Creates a git tag `pi-N-complete`

Then run `/plan-increment` to start the next sprint.

---

## Quick Reference

### All Skills

| Skill | Purpose |
|-------|---------|
| `/create-prd` | Bootstrap a new PRD (new repos only) |
| `/update-prd` | Record a decision or update a PRD section |
| `/plan-increment` | Close previous PI + plan the next sprint |
| `/update-pi` | Update PI Plan when scope changes mid-sprint |
| `/close-pi` | Archive current PI, bake decisions, tag |
| `/create-epic` | Detail epic + create stub feature issues |
| `/create-feature` | Detail feature + create stub story issues |
| `/detail-story` | Add full AC, file scope, deps to a story |
| `/update-epic` | Modify epic scope, add/remove features |
| `/update-feature` | Modify feature, add/remove stories |
| `/update-story` | Modify story AC, deps, file scope |
| `/pick-task` | Find next unblocked story |
| `/sync-issues` | Audit hierarchy, fix labels, validate deps |

### Label Taxonomy

| Category | Labels |
|----------|--------|
| Type | `type:epic`, `type:feature`, `type:story`, `type:spike`, `type:bug`, `type:chore` |
| Status | `status:todo`, `status:in-progress`, `status:done`, `status:blocked` |
| Priority | `priority:critical`, `priority:high`, `priority:medium`, `priority:low` |
| Area | `area:auth`, `area:api`, `area:agents`, `area:ui`, `area:infra`, `area:search` |

### Dependency Rules

A dependency is **satisfied** if: the issue has `status:done` label OR is `CLOSED`.

Stories with unmet blockers get `status:blocked` automatically. `/pick-task` and `/sync-issues` both enforce this.

### GitHub Issue Templates

**Epic:** Overview, Success Criteria, Features checklist, Non-goals, Dependencies

**Feature:** Description, Stories checklist, Non-goals, Dependencies, Parent (Epic)

**Story:** Description, Acceptance Criteria, File Scope (new + modified files), Technical Notes, Dependencies, Parent (Epic + Feature)

---

## File Structure

```
.claude/
├── prd/
│   └── PRD.md                 ← product requirements (git-versioned)
├── pi/
│   ├── PI.md                  ← current sprint plan
│   └── completed/
│       └── PI-1.md            ← archived sprints
└── skills/
    ├── create-prd/            ← PRD management
    ├── update-prd/
    ├── plan-increment/        ← PI lifecycle
    ├── update-pi/
    ├── close-pi/
    ├── create-epic/           ← work decomposition
    ├── create-feature/
    ├── detail-story/
    ├── update-epic/           ← work updates
    ├── update-feature/
    ├── update-story/
    ├── pick-task/             ← execution
    └── sync-issues/
```

---

## Common Workflows

### Starting a brand new project
```
/create-prd                    → guided interview, creates PRD.md
/plan-increment "MVP"          → creates PI-1 from PRD Roadmap
/create-epic "Auth"            → creates epic + stub features
/create-feature #10            → details feature + stub stories
/detail-story #15              → adds full AC, file scope, deps
/pick-task                     → start coding
```

### Starting a new sprint on an existing project
```
/plan-increment "Phase 2"     → closes PI-1, creates PI-2
/create-epic "Session Persistence"
/create-feature #125
/detail-story #130
/pick-task
```

### Mid-sprint scope change
```
/update-prd "Switch from Postgres to Redis for sessions"
/update-pi "add Redis checkpointer story to Session Persistence"
/update-feature #125           → add the new story
/detail-story #135             → flesh out the new story
/sync-issues                   → verify dependency graph is consistent
```

### End of day check
```
/sync-issues                   → fix stale labels, see what's blocked
/pick-task                     → what's next?
```
