# SDLC v2 Skill Suite — Design Spec

## Overview

A 6-skill suite for managing the full software development lifecycle via Claude Code. Replaces the v1 suite (13 skills) with a cleaner architecture that separates brainstorming from execution, uses mandatory gates with variable depth, and follows the progressive disclosure pattern for skill files.

**Namespace:** `sdlc:`

**Core principle:** Define the work collaboratively (brainstorm → local draft), then execute deliberately (push to GitHub/git). Never skip the thinking phase, never surprise the user with mutations.

## Architecture Decisions

- **Skills are self-contained** — no shared conventions file. Patterns are repeated in each skill for clarity (follows superpowers plugin architecture).
- **SKILL.md stays under 500 lines** — level-specific content lives in `reference/` subdirectories, loaded on-demand (progressive disclosure).
- **Scope assessment uses objective criteria** — concrete signals (file count, dep count, area count), never "use your judgment."
- **All phases are mandatory** — depth varies (LIGHT/STANDARD/DEEP), phases are never skipped.
- **Anti-rationalization** — explicit criteria tables and red flag tables prevent the LLM from skipping phases.
- **Drafts are local files** until `sdlc:create` pushes them to their final destination.
- **`sdlc:update` handles surgical GitHub edits** — it has the toolset for precise `gh issue edit` operations.
- **`sdlc:reconcile` only touches labels and open/closed state** — never edits issue bodies.
- **GitHub CLI research documents** in `gh-cli-research/` are the command reference for implementation.

## Artifacts

| Artifact | Location | Managed By |
|----------|----------|------------|
| PRD | `.claude/prd/PRD.md` | `sdlc:define prd` → `sdlc:create prd` |
| PI Plan | `.claude/pi/PI.md` | `sdlc:define pi` → `sdlc:create pi` |
| Archived PIs | `.claude/pi/completed/PI-N.md` | `sdlc:create pi` (archives old PI when creating new) |
| Drafts | `.claude/drafts/<level>-<name>.md` | `sdlc:define` (creates) → `sdlc:create` (consumes + cleans up) |
| Retro documents | `.claude/retros/<scope>-<date>.md` | `sdlc:retro` (creates) |
| Epics | GitHub Issues (`type:epic`) | `sdlc:create epic` / `sdlc:update` |
| Features | GitHub Issues (`type:feature`) | `sdlc:create feature` / `sdlc:update` |
| Stories | GitHub Issues (`type:story`) | `sdlc:create story` / `sdlc:update` |

## Label Taxonomy

| Category | Labels |
|----------|--------|
| Type | `type:epic`, `type:feature`, `type:story` |
| Status | `status:todo`, `status:in-progress`, `status:done`, `status:blocked` |
| Priority | `priority:critical`, `priority:high`, `priority:medium`, `priority:low` |
| Area | `area:auth`, `area:api`, `area:agents`, `area:ui`, `area:infra`, `area:search` |
| Triage | `triage` (for quick-capture items not yet defined) |

Status labels are mutually exclusive. Type, priority, and area labels are set at creation and updated via `sdlc:update`.

## Dependency Model

### Three Levels

1. **PI Plan** (plain language in `.claude/pi/PI.md`) — high-level blocking relationships between epics/features. Informs worktree strategy and phasing.
2. **GitHub Issue body** (structured sections) — exact blocking relationships per issue:
   ```markdown
   ## Dependencies
   - Blocked by: #45, #46
   - Blocks: #48, #52

   ## Parent
   - Epic: #40
   - Feature: #43
   ```
3. **Label enforcement** — `status:blocked` applied when any blocker is unmet; `status:todo` when all blockers satisfied.

### Blocker Satisfaction Rule (shared across all skills)

A blocker is **satisfied** if:
- The issue has the `status:done` label, OR
- The issue state is `CLOSED`

A blocker is **unmet** if:
- The issue is `OPEN` without `status:done`

### Circular Dependency Detection

When adding a new blocker, walk the `Blocked by` chain via DFS. If the walk reaches the original issue, flag a cycle and do NOT save the dependency. Ask the user to resolve.

---

## Skill Definitions

### 1. `sdlc:define` — The Brainstorming Engine

**Description:** Use when defining new artifacts (PRD, PI, epic, feature, story) or reshaping existing ones. Collaborative brainstorming that produces a local draft.

**Invocation:** `/sdlc:define`, `/sdlc:define epic`, `/sdlc:define story #45`

**Supports levels:** `prd`, `pi`, `epic`, `feature`, `story`

**Allowed tools:** Read, Edit, Write, Bash, Grep, Glob, Agent

**File structure:**
```
.claude/skills/sdlc-define/
├── SKILL.md                    # Core 5-phase flow
└── reference/
    ├── prd-guide.md            # PRD-specific questions, templates, criteria
    ├── pi-guide.md             # PI planning guidance
    ├── epic-guide.md           # Epic definition guidance
    ├── feature-guide.md        # Feature definition guidance
    └── story-guide.md          # Story definition guidance
```

#### Phases

**Phase 0: Context Loading (mandatory)**
- Parse argument for level. If none provided, ask: "What are we defining?"
- Load `reference/<level>-guide.md` for level-specific intelligence
- Read upstream artifacts:
  - `prd` → scan codebase for greenfield/brownfield detection
  - `pi` → read PRD (roadmap section)
  - `epic` → read PI + PRD
  - `feature` → read parent epic + PI + PRD
  - `story` → read parent feature + parent epic + PRD
- If reshaping an existing artifact (invoked from `sdlc:update` escalation): load current state from GitHub/git as starting context

**Phase 1: Scope Assessment (mandatory, objective criteria)**

Each reference guide defines concrete signals per level. Examples:

Epic scope criteria:
```
DEEP if any:
  - Spans 3+ area labels
  - Introduces new architectural patterns
  - Has cross-epic dependencies
  - 5+ features

STANDARD if any:
  - 2-3 features
  - Follows existing patterns with some new ground
  - Has intra-epic dependencies

LIGHT if all:
  - 1-2 features
  - Purely follows existing patterns
  - No cross-epic dependencies
```

Story scope criteria:
```
DEEP if any:
  - Touches 4+ files across multiple areas
  - Requires new patterns not in codebase
  - Has 3+ blockers
  - Is a bug with unclear root cause

STANDARD if any:
  - 2-3 files
  - Extends existing patterns
  - Has 1-2 blockers

LIGHT if all:
  - 1 file
  - Clear pattern to follow
  - 0 blockers
  - Parent feature already has detailed context
```

Output the assessment visibly to the user.

**Phase 2: Discovery (mandatory, depth varies)**
- LIGHT: "Based on the parent context, here's what I understand. Does this match your intent?" — 0-1 follow-up questions
- STANDARD: 2-4 targeted questions, one at a time. May dispatch a research subagent for codebase exploration.
- DEEP: 4+ questions. Dispatches research subagents. Explores unknowns before asking the user.

**Post-Discovery Gate: Re-evaluate Scope**

After Phase 2 completes, re-evaluate the depth assessment using the same objective criteria. If discovery revealed more complexity than initially assessed:
- Upgrade depth (LIGHT → STANDARD, or STANDARD → DEEP). Depth can only go UP, never down.
- Re-run Phase 2 at the new depth.
- Announce the upgrade: "Discovery revealed this touches auth + api + search. Upgrading from LIGHT to STANDARD."
- Maximum one upgrade per run.

**Phase 3: Approaches (mandatory, depth varies)**
- LIGHT: "I'd approach it this way: [single approach]. Sound right?"
- STANDARD: "Two options — [A] or [B]. I'd recommend [A] because [reason]."
- DEEP: "Three approaches with trade-offs. Here's my analysis..."

**Phase 4: Draft (mandatory)**
- Produce a draft file at `.claude/drafts/<level>-<name-or-number>.md`
- If reshaping an existing artifact: draft starts as a copy of current state, with a `## Changes` section documenting what was modified
- Format defined by the reference guide (level-specific template). Each guide specifies the exact body sections for that level (e.g., epic: Overview, Success Criteria, Features, Non-goals, Dependencies; story: Description, Acceptance Criteria, File Scope, Technical Notes, Dependencies). These templates will be defined in the implementation plan.
- Draft includes all fields `sdlc:create` or `sdlc:update` will need

Draft frontmatter format:
```yaml
---
type: epic | feature | story | prd | pi
name: <artifact name>
priority: critical | high | medium | low
areas: [auth, api]
status: draft
parent-epic: <number or name, if applicable>
parent-feature: <number or name, if applicable>
---
```

**Phase 5: Review (mandatory)**
- Present the draft to the user in full
- Iterate: "Want to change anything?"
- Loop until user approves
- On approval for new artifact: "Draft saved. Run `/sdlc:create <level>` when ready."
- On approval for reshape: "Draft saved with changes documented. Run `/sdlc:update <level> <number>` to apply."

#### Greenfield vs Brownfield (PRD level)

- Greenfield: guided interview — overview, tech stack, architecture, data models, API contracts, security constraints, roadmap, acceptance criteria, out of scope
- Brownfield: scan codebase first (package.json, pyproject.toml, directory structure), propose PRD structure based on what exists, ask targeted questions to fill gaps
- Detection: check if `.claude/prd/PRD.md` exists and if codebase has existing code

#### Feature Level is Optional

Epics can contain stories directly when the epic is small (fewer than ~8 stories). The feature level is used when an epic needs sub-grouping. `sdlc:define epic` should ask: "This epic has [N] stories. Want to group them into features, or keep them flat under the epic?"

---

### 2. `sdlc:create` — The Execution Engine

**Description:** Use when a draft from `sdlc:define` is ready to be pushed to GitHub or git. Reads the draft, validates it, creates the artifacts, and cleans up.

**Invocation:** `/sdlc:create`, `/sdlc:create epic`, `/sdlc:create pi`

**Supports levels:** `prd`, `pi`, `epic`, `feature`, `story`

**Allowed tools:** Read, Bash, Grep, Glob

**File structure:**
```
.claude/skills/sdlc-create/
├── SKILL.md                    # Core execution flow
└── reference/
    ├── prd-execution.md        # Commit PRD to git
    ├── pi-execution.md         # Commit PI to git
    ├── epic-execution.md       # Create epic + stub features/stories
    ├── feature-execution.md    # Create feature + stub stories
    └── story-execution.md      # Create story issue
```

#### Steps

**Step 1: Locate Draft**
- Parse argument for level
- If none: scan `.claude/drafts/` and show available drafts
- If multiple drafts of the same level exist: list them and ask which one (e.g., "I see `epic-auth.md` and `epic-search.md`. Which one?")
- If no drafts exist: "No drafts found. Run `/sdlc:define <level>` first."
- Load `reference/<level>-execution.md`

**Step 2: Validate Draft**

Check required fields per level. On validation failure, route by severity:

```
FIX INLINE if:
  - 1 missing metadata field (priority, area, label)
  - Formatting/template issues only

REOPEN DRAFT if:
  - 1-2 content gaps (missing AC, wrong dep reference)
  - Fields that need user input but scope is unchanged

ESCALATE TO DEFINE if:
  - 3+ content gaps
  - Structural issues (wrong parent, scope mismatch)
  - Circular dependencies detected
```

For FIX INLINE: show the fix, apply it, continue.
For REOPEN DRAFT: show the problem, propose a fix, user approves, update draft, continue.
For ESCALATE: stop and redirect to `sdlc:define`.

**Step 3: Execute (level-specific)**

For file-based artifacts (PRD, PI):
- Write draft content to final location (`.claude/prd/PRD.md` or `.claude/pi/PI.md`)
- If creating a new PI and an active PI exists: archive old PI to `.claude/pi/completed/PI-N.md`, bake decision log into PRD, bump PRD version, git tag `pi-N-complete`
- Git commit with conventional commit message

For GitHub-based artifacts (epic, feature, story):
- Create primary GitHub issue via `gh issue create` with labels and full body
- Create stub child issues (epic → features or stories, feature → stories)
- Maintain bidirectional dependency links: if the new issue has `Blocked by: #48`, update #48 to add `Blocks: #<new>` in its body
- Update parent issue's checklist with real issue numbers
- Update `.claude/pi/PI.md` with real issue numbers (replacing `#TBD`)
- Apply status labels based on dependency state
- Git commit for PI.md changes

See `gh-cli-research/02-issue-management.md` for exact `gh` commands.

**Step 4: Report & Cleanup**
- Show what was created: issue numbers, links, labels applied
- Ask: "Delete `.claude/drafts/<file>`?" (default yes). If the user declines, the draft persists and will be flagged as a stale draft by `sdlc:status` after 7 days.

#### Key Property

This skill never asks creative questions. If the draft is incomplete, it points back to `sdlc:define`. One-way valve: draft in → artifacts out.

---

### 3. `sdlc:update` — The Surgical Editor

**Description:** Use when modifying existing artifacts on GitHub or in git. Smart routing: direct edits for small changes, escalation to `sdlc:define` for large changes.

**Invocation:** `/sdlc:update`, `/sdlc:update story #45`, `/sdlc:update prd`

**Supports levels:** `prd`, `pi`, `epic`, `feature`, `story`

**Allowed tools:** Read, Edit, Write, Bash, Grep, Glob

**File structure:**
```
.claude/skills/sdlc-update/
├── SKILL.md                    # Smart assessment + routing
└── reference/
    ├── prd-update.md
    ├── pi-update.md
    ├── epic-update.md
    ├── feature-update.md
    └── story-update.md
```

#### Steps

**Step 1: Load Current State**
- Parse argument for level + identifier
- If not provided, ask: "What are we updating?"
- Check `.claude/drafts/` for a reshape draft for this artifact (produced by `sdlc:define` escalation). If found, load it — the `## Changes` section is the change specification. Skip Step 2.
- If no draft: fetch current state:
  - PRD/PI → read file from git
  - Epic/feature/story → `gh issue view --json` (see `gh-cli-research/02-issue-management.md`)
- Load `reference/<level>-update.md`

**Step 2: Understand the Change**
- If a reshape draft was loaded in Step 1: skip this step — the draft's `## Changes` section defines what to change.
- Otherwise, ask: "What do you want to change?"
- Validate the request — challenge if needed ("Are you sure you want to remove this AC? It was there because of X.")

**Step 3: Assess Magnitude (objective criteria)**

```
DIRECT UPDATE if all:
  - 1-2 fields changing
  - No new children added/removed
  - No new dependencies
  - No scope expansion

ESCALATE TO DEFINE if any:
  - 3+ fields changing
  - Adding/removing children (features under epic, stories under feature)
  - New dependencies introduced
  - Scope change
  - User says "let's rethink this"
```

Two tiers only. No fuzzy middle ground.

**Step 4: Execute**

DIRECT UPDATE:
- Show current value and proposed change side by side
- User confirms
- For PRD/PI: edit file + git commit
- For epic/feature/story: apply via individual `gh issue edit` commands
- If dependency changed: update the other issue's `Blocked by`/`Blocks` section
- If status label affected: update labels

ESCALATE TO DEFINE:
- "This is a significant change. Let me pull the current state into a draft for reshaping."
- Invoke `sdlc:define <level>` with current artifact pre-loaded as context
- `sdlc:define` produces an updated draft with a `## Changes` section
- User reviews and approves the draft
- User invokes `sdlc:update <level> <number>` with the draft
- `sdlc:update` reads the `## Changes` section and applies each change surgically
- Cleanup: offer to delete the draft

**Step 5: Cascade Logic**
- When update affects children or parents, flag them:
  - "Features #12 and #14 may need updates. Want me to check?"
- User confirms before any cascade
- Each cascade change is its own surgical `gh issue edit`

See `gh-cli-research/02-issue-management.md` for exact edit commands and the read-modify-write pattern for body edits.

---

### 4. `sdlc:status` — Situational Awareness

**Description:** Use to get a full briefing on project state — what's in progress, what's blocked, what's ready, what can run in parallel. Read-only.

**Invocation:** `/sdlc:status`, `/sdlc:status auth`, `/sdlc:status epic #40`

**Allowed tools:** Read, Bash, Grep, Glob

**File structure:**
```
.claude/skills/sdlc-status/
└── SKILL.md
```

#### Steps

**Step 1: Determine Scope**
- No argument → full PI scope
- Area filter (`auth`, `api`) → issues with that area label
- Specific artifact (`epic #40`) → that epic and its children

**Step 2: Gather State**
- Fetch open issues grouped by status label via `gh issue list`
- Fetch recently closed issues (last 7 days)
- Read dependency chains from issue bodies
- Read `.claude/pi/PI.md` for planned structure
- Scan `.claude/drafts/` for stale drafts (older than 7 days)

See `gh-cli-research/02-issue-management.md` for query commands and jq filters.

**Step 3: Analyze**

- **In Progress:** active stories, how long (via `createdAt` or label timestamp), assigned to whom
- **Blocked:** what's stuck and why — trace root blockers through the chain, not just immediate blockers
- **Ready:** unblocked `status:todo` stories, ranked by priority
- **Parallelization:** which ready stories have no dependency relationship and can run simultaneously in separate worktrees
- **Stale detection:** anything `in-progress` for an unusually long time
- **Stale drafts:** drafts in `.claude/drafts/` older than 7 days

**Step 4: Present Briefing**

```
## Current PI: PI-1 — MVP Foundation

### In Progress (2)
- #48 Token encryption (auth) — 2 days
- #55 Chat UI scaffold (ui) — 1 day

### Blocked (3)
- #52 Session history API ← waiting on #48
- #60 Calendar tool ← waiting on #52 ← #48
  → Root blocker: #48 (in progress, unblocks 2 stories when done)
- #63 Search indexing ← waiting on #61 (not started)

### Ready to Pick Up (4, ranked)
1. #61 Vector store setup (search, priority:critical)
2. #57 Error boundary component (ui, priority:high)
3. #58 Loading states (ui, priority:medium)
4. #62 Rate limiter middleware (api, priority:medium)

### Can Parallelize
- Worktree A: #61 (search) — independent
- Worktree B: #57 or #58 (ui) — independent of #61

### Stale Drafts
- epic-auth.md (12 days old)

### Momentum
- 8 stories closed this PI, 12 remaining
- 3 stories closed in last 7 days
```

**Step 5: Offer Next Action**
- "Want to pick up one of these? I can start implementation or run `/sdlc:define story` if it needs more detail."

---

### 5. `sdlc:reconcile` — Label Hygiene

**Description:** Use to fix state drift in GitHub issues — stale labels, unclosed parents, orphaned references. Only touches labels and open/closed state, never edits issue bodies.

**Invocation:** `/sdlc:reconcile`, `/sdlc:reconcile auth`

**Allowed tools:** Read, Bash, Grep, Glob

**File structure:**
```
.claude/skills/sdlc-reconcile/
└── SKILL.md
```

#### Steps

**Step 1: Scan**
- Fetch all open and recently closed issues
- Build parent-child hierarchy
- Map all dependency chains
- Optional area filter

**Step 2: Detect Problems (by severity)**

CRITICAL:
- Circular dependencies (DFS walk on blocker chains)
- Broken hierarchy (story references nonexistent parent)

WARNING:
- Stale labels on closed issues (closed but still `status:in-progress` or `status:todo`)
- Completed parents not closed — a parent is "complete" when ALL its children have `status:done` label AND are in `CLOSED` state. If complete: close the parent issue and apply `status:done`.
- Blocker mismatch (`status:todo` but has unmet blocker → should be `status:blocked`)
- Unblocked but still blocked (`status:blocked` but all blockers satisfied → should be `status:todo`)

INFO:
- Orphaned references (issue in `Blocked by` doesn't link back in `Blocks`)
- Priority mismatch (story has higher priority than parent)
- `triage` issues older than 14 days (quick-capture items not yet defined)

**Step 3: Present Findings**

```
## Reconciliation Report

### CRITICAL (0)
No critical issues.

### WARNING (4)
1. #48 (closed) — status:in-progress → fix to status:done
2. #45 Feature: all 3 stories done → close feature, apply status:done
3. #52 Story: status:todo but blocked by #48 → fix to status:blocked
4. #60 Story: status:blocked but blocker done → fix to status:todo

### INFO (1)
1. #63 lists "Blocked by #61" but #61 doesn't list "Blocks #63"

Apply WARNING fixes? [y/n]
```

**Step 4: Execute (on confirmation)**
- Execute each fix as an individual `gh issue edit` command, run in parallel where independent
- Report results per-issue — which succeeded, which failed

**Step 5: Flag What It Can't Fix**
- CRITICAL items → "Run `/sdlc:update` to fix."
- INFO orphaned references → "Run `/sdlc:update story #63` to fix cross-reference."
- Content issues → "Out of scope. Use `/sdlc:update`."

---

### 6. `sdlc:retro` — Process Retrospective

**Description:** Use to analyze how work was done during a PI, epic, or feature. Produces a retrospective document for the human to review. Never mutates anything.

**Invocation:** `/sdlc:retro`, `/sdlc:retro pi`, `/sdlc:retro epic #40`

**Supports levels:** `pi`, `epic`, `feature`

**Allowed tools:** Read, Bash, Grep, Glob, Agent

**File structure:**
```
.claude/skills/sdlc-retro/
└── SKILL.md
```

#### Steps

**Step 1: Determine Scope**
- `sdlc:retro pi` → full PI analysis
- `sdlc:retro epic #40` → single epic and children

**Early Exit:** If the scope has no closed stories (e.g., PI just started), report: "This scope has no completed work yet. A retrospective will be more useful after some stories are done." and exit.

**Step 2: Gather Observable Metrics**

Only metrics with reliable data sources:

| Metric | Source | Reference |
|--------|--------|-----------|
| Planned vs delivered | PI.md + `gh issue list` | `gh-cli-research/02-issue-management.md` |
| Stories completed/carried | `gh issue list` by state + labels | `gh-cli-research/02-issue-management.md` |
| Time in-progress | Timeline API label events | `gh-cli-research/03-timeline-and-metrics.md` |
| Blocked duration | Timeline API `status:blocked` events | `gh-cli-research/03-timeline-and-metrics.md` |
| PR lead time | `gh pr view --json commits,mergedAt` | `gh-cli-research/03-timeline-and-metrics.md` |
| Code review compliance | `gh pr view --json reviewDecision` | `gh-cli-research/03-timeline-and-metrics.md` |
| Commit cadence | `git log --format='%ad' --date=short` | `gh-cli-research/04-git-analytics.md` |
| File hotspots | `git log --name-only` frequency | `gh-cli-research/04-git-analytics.md` |
| Commits per story | `git log --fixed-strings --grep="(#N)"` | `gh-cli-research/04-git-analytics.md` |

**Metrics explicitly deferred to v2** (requires PI Changelog — see `docs/sdlc-future-ideas.md`):
- Scope change frequency
- Depth distribution (LIGHT/STANDARD/DEEP)
- Estimation accuracy

**Step 3: Analyze Patterns**

Based on observable data:
- **Flow efficiency:** stories that moved `todo → in-progress → done` without bouncing vs stories with `blocked` periods (from label event timestamps)
- **Lead time outliers:** stories in-progress for significantly longer than average
- **Dependency accuracy:** was each blocker completed before the dependent story started? (compare `status:done` timestamp on blocker vs `status:in-progress` timestamp on dependent)
- **Hot areas:** file hotspots cross-referenced with area labels
- **Review discipline:** merged PRs without reviews

**Step 4: Produce Retrospective Document**

Saved to `.claude/retros/<scope>-<date>.md`:

```markdown
---
type: retro
scope: PI-1
date: 2026-03-19
audit-ref: (path to sdlc:audit output if available, or "not run" — placeholder for future sdlc:audit skill, see docs/sdlc-future-ideas.md)
---

## Summary
PI-1 planned 28 stories across 5 epics. 23 shipped, 5 carried over.

## What Went Well
- Auth epic completed, avg 1.5 days in-progress per story
- Dependency chain was accurate — no unexpected blockers
- 100% of PRs had code review

## What Caused Friction
- Story #52 blocked for 5 days (longest in PI)
- Search epic: 2 of 6 stories carried over
- Stories #60, #63: 4+ days in-progress without commits

## Process Metrics
| Metric | Value |
|--------|-------|
| Planned stories | 28 |
| Delivered | 23 (82%) |
| Carried over | 5 |
| Avg days in-progress | 1.8 |
| Longest blocked | 5 days (#52) |
| Dep predictions accurate | 19/22 (86%) |
| PRs with review | 23/23 (100%) |

## Recommendations for Next PI
- Carry-over stories as priority for PI-2
- Search area needs tighter scoping
- Build buffer for external dependencies

## Audit Reference
(If sdlc:audit was run: "See .claude/audits/ for technical findings")
(If not: "Consider running sdlc:audit for technical verification")
```

**Step 5: Present and Offer Next Steps**
- Show summary in terminal
- "Retrospective saved to `.claude/retros/<file>`. Ready to plan next increment? Run `/sdlc:define pi`."

---

## Additional Skills

### `sdlc:capture` — Quick Capture

**Description:** Use when you want to jot down an idea without going through the full define ceremony. Creates a minimal GitHub issue with `triage` label.

**Invocation:** `/sdlc:capture <one-line description>`

**Allowed tools:** Bash

**File structure:**
```
.claude/skills/sdlc-capture/
└── SKILL.md
```

**Behavior:**
- No context loading — this is a fire-and-forget skill. It does not read PI.md, PRD, or any upstream artifacts.
- Creates a GitHub issue with title from the argument, `triage` label, and minimal body:
  ```markdown
  ## Description
  <user's one-liner>

  ## Status
  Captured via sdlc:capture. Needs `/sdlc:define` to flesh out.
  ```
- Reports: "Captured as #N. Run `/sdlc:define <level>` when ready to detail it."
- `sdlc:reconcile` flags `triage` issues older than 14 days

---

## Lifecycle Flow

```
New project:
  sdlc:define prd → sdlc:create prd → sdlc:define pi → sdlc:create pi

Break down work:
  sdlc:define epic → sdlc:create epic
    sdlc:define feature → sdlc:create feature  (optional level)
      sdlc:define story → sdlc:create story

Execute:
  sdlc:status → pick a story → implement → PR → merge

Mid-sprint:
  sdlc:update (small change) or sdlc:define → sdlc:update (large change)
  sdlc:capture (quick idea)
  sdlc:reconcile (fix label drift)

Close sprint:
  sdlc:retro pi → review findings → sdlc:define pi (next cycle)
```

## Dependency on GitHub CLI Research

The following research documents inform the exact commands used in skill reference files:

| Document | Informs |
|----------|---------|
| `gh-cli-research/01-github-projects.md` | Future v2 enhancement (not used in v1) |
| `gh-cli-research/02-issue-management.md` | `sdlc:create`, `sdlc:update`, `sdlc:status`, `sdlc:reconcile` |
| `gh-cli-research/03-timeline-and-metrics.md` | `sdlc:retro` |
| `gh-cli-research/04-git-analytics.md` | `sdlc:retro`, `sdlc:status` |

## What This Replaces

The v1 suite (13 skills from PR #121):
- `create-prd` → `sdlc:define prd` + `sdlc:create prd`
- `update-prd` → `sdlc:update prd` or `sdlc:define prd` (reshape)
- `plan-increment` → `sdlc:define pi` + `sdlc:create pi`
- `update-pi` → `sdlc:update pi`
- `close-pi` → `sdlc:retro pi` + `sdlc:create pi` (archives old PI during next PI creation)
- `create-epic` → `sdlc:define epic` + `sdlc:create epic`
- `create-feature` → `sdlc:define feature` + `sdlc:create feature`
- `detail-story` → `sdlc:define story` + `sdlc:create story`
- `update-epic` → `sdlc:update epic`
- `update-feature` → `sdlc:update feature`
- `update-story` → `sdlc:update story`
- `pick-task` → `sdlc:status` (with richer analysis)
- `sync-issues` → `sdlc:reconcile` (focused on hygiene)
- `update-decision` → `sdlc:update prd` (decision log)

## Future Enhancements

See `docs/sdlc-future-ideas.md` for prioritized backlog:
1. `sdlc:audit` — technical verification audit (recursive subagent chain)
2. PI Changelog — skill invocation tracking for richer retro metrics
3. GitHub Projects integration — native project management fields
4. `sdlc:resume` — context switching support
5. Burn-down awareness in `sdlc:status`
6. Local index file for faster querying
7. Rollback output from `sdlc:create`
