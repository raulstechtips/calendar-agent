# 06 - GitHub Issues vs Projects: Definitive Analysis for SDLC Skills

> **Decision document.** Where should each data point live in our SDLC skill suite?
>
> **Author:** Claude Code analysis based on verified CLI research (01-04)
> **Date:** 2026-03-19
> **Status:** RECOMMENDATION — Labels-only (Option A)

---

## Executive Summary

**Recommendation: Option A — Labels-only. Do not adopt GitHub Projects.**

The killer constraint is the Timeline API. Our `sdlc:retro` skill computes
time-in-status metrics by reading `labeled`/`unlabeled` events from the immutable
Timeline API. Project field changes are NOT recorded in the Timeline API, and the
GraphQL alternative (`ProjectV2ItemFieldValueEvent`) is in preview, poorly
documented, and has no `gh` CLI support. Moving status to a Project field would
destroy our ability to measure process metrics — the core value proposition of
`sdlc:retro`.

Projects add complexity (dual-entity model, ID resolution dance, extra OAuth
scope) without solving any problem that labels don't already solve for a
CLI-first, single-repo, solo/small-team workflow.

---

## Table of Contents

1. [The Dual-Entity Model Explained](#1-the-dual-entity-model-explained)
2. [Data Point Analysis](#2-data-point-analysis)
3. [The Timeline API Blocker](#3-the-timeline-api-blocker)
4. [Option A: Labels-Only](#4-option-a-labels-only)
5. [Option B: Projects-Only](#5-option-b-projects-only)
6. [Option C: Hybrid](#6-option-c-hybrid)
7. [Recommendation and Rationale](#7-recommendation-and-rationale)
8. [Labels-Only Implementation Spec](#8-labels-only-implementation-spec)
9. [What We Lose (and Why It Doesn't Matter)](#9-what-we-lose-and-why-it-doesnt-matter)

---

## 1. The Dual-Entity Model Explained

When you add an issue to a GitHub Project, GitHub creates a **Project Item** that
wraps the Issue. This creates two separate entities:

```
┌─────────────────────────────────┐
│ GitHub Issue #42                │
│ ├── title, body, state          │
│ ├── labels: [status:todo, ...]  │  ← Lives on the Issue
│ ├── assignees, milestone        │
│ └── timeline events (immutable) │
└─────────────────────────────────┘
         │
         │  item-add
         ▼
┌─────────────────────────────────┐
│ Project Item PVTI_xxx           │
│ ├── Status: "Todo"              │  ← Lives on the Project Item
│ ├── Priority: "P0"              │  ← Lives on the Project Item
│ ├── Sprint: "Sprint 1"         │  ← Lives on the Project Item
│ └── (no audit trail for REST)   │
└─────────────────────────────────┘
```

**Key facts verified from our research:**

1. **Complete independence.** Changing a Project field does NOT affect Issue labels. Adding a label does NOT affect Project fields. (01-github-projects.md §16)
2. **Data loss on removal.** If you remove an issue from the Project, all Project field values are lost. The Issue itself is unaffected. (01-github-projects.md §11)
3. **No Timeline events for Projects v2.** The `moved_columns_in_project` timeline event only fires for **classic (v1) projects**, not ProjectsV2. Project field changes are invisible to the REST Timeline API. (03-timeline-and-metrics.md §12, lines 1126-1133)
4. **Extra OAuth scope.** `gh project` commands require the `project` scope, not included in default `gh auth login`. (01-github-projects.md §1)
5. **ID resolution overhead.** Every Project field write requires looking up Item ID, Field ID, and Option ID first — the "two-step dance." (01-github-projects.md §8)

---

## 2. Data Point Analysis

### Status (Todo, In Progress, Done, Blocked)

| Criterion | Labels | Projects |
|---|---|---|
| **Queryability** | `gh issue list --label "status:todo"` — one command, zero setup | `gh project item-list 1 --owner X --query 'status:"Todo"'` — requires project to exist, `project` scope |
| **Visibility** | Visible on every issue view, in search results, in notifications | Only visible in the Project board context |
| **Automation** | `gh issue edit N --add-label X --remove-label Y` — atomic swap | Two-step: look up Item ID + Option ID, then `item-edit` |
| **Portability** | Survives repo transfers, project deletion, fork | Lost if issue removed from project or project deleted |
| **Audit trail** | `labeled`/`unlabeled` events in Timeline API with exact timestamps | **NO REST API audit trail.** `ProjectV2ItemFieldValueEvent` is GraphQL-only, preview, poorly documented |
| **Dual-state risk** | N/A (single source of truth) | If tracked in both, drift is guaranteed |

**Verdict: Labels.** The Timeline API audit trail for time-in-status is non-negotiable for `sdlc:retro`.

### Priority (Critical, High, Medium, Low)

| Criterion | Labels | Projects |
|---|---|---|
| **Queryability** | `gh issue list --label "priority:critical"` | `gh project item-list --query 'priority:"P0"'` |
| **Visibility** | Visible on issue | Only in project context |
| **Automation** | `gh issue edit N --add-label "priority:high" --remove-label "priority:medium"` | Two-step ID dance |
| **Portability** | Survives everything | Lost with project |
| **Audit trail** | Timeline records label changes with timestamps | No REST audit trail |
| **Batch ops** | `gh issue edit 1 2 3 --add-label X` — native batch | Must loop, one `item-edit` per item |

**Verdict: Labels.** Priority changes are tracked in timeline events, useful for retro analysis (priority inflation detection). Batch label operations are natively supported.

### Area (Auth, API, Agents, UI, Infra, Search)

| Criterion | Labels | Projects |
|---|---|---|
| **Queryability** | `gh issue list --label "area:auth"` — first-class filter | `gh project item-list --query 'area:"auth"'` |
| **Visibility** | Color-coded on every issue | Project board only |
| **Automation** | Set at creation, rarely changes | Same overhead as other fields |
| **Portability** | Permanent | Lost with project |
| **Use pattern** | Set once at creation, almost never changes | Same |

**Verdict: Labels.** Area is static metadata, perfect for labels. It's used in `gh issue list --label "area:X"` queries across every skill.

### Type (Epic, Feature, Story)

| Criterion | Labels | Projects |
|---|---|---|
| **Queryability** | `gh issue list --label "type:epic"` | `gh project item-list --query 'type:"Epic"'` |
| **Visibility** | Immediately visible on issue | Project context only |
| **Structural role** | Used to drive hierarchy logic in `sdlc:create`, `sdlc:reconcile`, `sdlc:status` | Same data, different location |
| **Portability** | Permanent | Lost with project |
| **Mutability** | Never changes after creation | Same |

**Verdict: Labels.** Type is the most structural label — every skill uses `--label "type:X"` for filtering. It never changes, so there's zero drift risk.

### Sprint/Iteration (PI-1, Sprint-1, etc.)

| Criterion | Labels | Projects |
|---|---|---|
| **Queryability** | `gh issue list --label "sprint:1"` | `gh project item-list --query 'iteration:"Sprint 1"'` — native iteration support |
| **Automation** | `gh issue edit N --add-label "sprint:1"` | `item-edit --iteration-id X` — requires iteration ID lookup |
| **Date awareness** | None — labels are just strings | Iterations have start/end dates, duration, breaks |
| **Burndown** | Must compute from label events + close dates | Projects Insights has built-in burndown (web UI only) |
| **Timeline audit** | Yes — `labeled`/`unlabeled` events tracked | No REST audit trail |

**Verdict: Labels.** The date-aware iteration field is the one genuinely useful Project feature. But:
- We track sprints via PI plans in local git files (our source of truth for sprint dates)
- We don't need GitHub to compute burndown — `sdlc:retro` does it from timeline events
- Iteration fields cannot be created via CLI (requires web UI or GraphQL)
- The timeline audit trail for sprint transitions matters for retro

If we ever need date-aware iterations, we can add a `sprint:N` label AND set the Project iteration field (write-only), but the label remains the source of truth.

### Dependencies (Blocked by / Blocks)

| Criterion | Labels | Projects |
|---|---|---|
| **Current approach** | Issue body sections: `Blocked by: #45, #46` / `Blocks: #52` | No native field for this |
| **Native GitHub** | GraphQL `blockedBy` / `blocking` fields (newer feature) | Not a project field |
| **Queryability** | Parse from body with jq regex | Not applicable |

**Verdict: Issue body (current approach).** Dependencies are relationships between issues, not metadata on a single issue. Neither labels nor project fields model this well. Our body-section convention + native sub-issues API is the right approach.

### Parent-Child Hierarchy

| Criterion | Labels | Projects |
|---|---|---|
| **Current approach** | Body convention: `Parent: Epic #40` + native sub-issues API | Projects v2 has Tracks/Tracked-by fields (auto-populated) |
| **Queryability** | GraphQL `parent` / `subIssues` fields | Projects show it in board UI |
| **Automation** | `addSubIssue` / `removeSubIssue` GraphQL mutations | Auto-populated from sub-issues |

**Verdict: Native sub-issues API + body convention (current approach).** The hierarchy lives on the Issue, not on labels or project fields. Projects' Tracks/Tracked-by fields are read-only mirrors of the native sub-issues relationship.

### Triage Flag

| Criterion | Labels | Projects |
|---|---|---|
| **Queryability** | `gh issue list --label "triage"` | Could be a boolean field, but overkill |
| **Automation** | `gh issue edit N --add-label "triage"` / `--remove-label "triage"` | Two-step dance |
| **Lifecycle** | Applied on capture, removed when triaged | Same |

**Verdict: Labels.** Triage is a simple flag. A label is the simplest possible implementation.

---

## 3. The Timeline API Blocker

This is the decisive technical constraint. Let me be specific.

### What the Timeline API gives us (labels)

```bash
gh api repos/raulstechtips/calendar-agent/issues/100/timeline \
  --jq '[.[] | select(.event == "labeled" or .event == "unlabeled") |
  {event, label: .label.name, at: .created_at}]'
```

**Verified output from our repo:**
```json
[
  {"created_at":"2026-03-17T08:19:06Z","event":"labeled","label":"type:bug"},
  {"created_at":"2026-03-17T08:19:06Z","event":"labeled","label":"priority:critical"},
  {"created_at":"2026-03-17T08:19:07Z","event":"labeled","label":"area:api"},
  {"created_at":"2026-03-17T08:19:07Z","event":"labeled","label":"area:agents"},
  {"created_at":"2026-03-17T18:10:55Z","event":"labeled","label":"status:done"}
]
```

Every label add/remove is an **immutable, timestamped event** that persists forever. The `sdlc:retro` skill pairs `labeled`/`unlabeled` events to compute:
- Time in todo (queue time)
- Time in progress (coding time)
- Time blocked (waste)
- Cycle time (first status change to done)

### What the Timeline API gives us for Project field changes

**Nothing.** Verified findings:

1. `moved_columns_in_project`, `added_to_project`, `removed_from_project` — these events exist in the Timeline API but **only fire for classic (v1) Projects**, not ProjectsV2. (03-timeline-and-metrics.md §12)

2. There is no `project_field_changed` or equivalent event in the REST Timeline API for ProjectsV2.

3. The GraphQL `ProjectV2ItemFieldValueEvent` type exists in preview but:
   - It's accessed via `projectV2ItemChanges` on the ProjectV2Item, not via the Issue timeline
   - It's not available via any `gh` CLI command
   - It's poorly documented and the schema is unstable
   - It requires the `project` OAuth scope on top of standard scopes

4. The repo-wide events endpoint (`/repos/{owner}/{repo}/issues/events`) also does NOT include ProjectsV2 field change events.

### Consequence

If we move `status:todo` / `status:in-progress` / `status:done` from labels to a Project Status field:

- `sdlc:retro` **cannot compute time-in-status** using the Timeline API
- We would need to build a custom event log (comment on the issue? write to a file?) to reconstruct status transitions — reinventing what the Timeline API already gives us for free
- OR we would need to use the preview GraphQL API, adding fragile, undocumented, scope-requiring code

**This alone kills the Projects approach for status tracking.** Time-in-status is the highest-value metric in `sdlc:retro`.

---

## 4. Option A: Labels-Only

### What we keep

Every data point on labels, exactly as we have today:

| Label prefix | Values | Used for |
|---|---|---|
| `type:` | `epic`, `feature`, `story`, `bug`, `spike`, `chore` | Hierarchy, filtering |
| `status:` | `todo`, `in-progress`, `done`, `blocked` | Workflow state, time-in-status metrics |
| `priority:` | `critical`, `high`, `medium`, `low` | Prioritization, pick-task ordering |
| `area:` | `auth`, `api`, `agents`, `ui`, `infra`, `search` | Domain filtering, area-based dashboards |
| `sprint:` | `pi1-s1`, `pi1-s2`, etc. | Sprint assignment, velocity tracking |
| `triage` | (no prefix) | Incoming issue flag |

### What we gain

- **Zero additional infrastructure.** No project to create, no fields to configure, no OAuth scope to add, no ID resolution cache to maintain.
- **Full Timeline API coverage.** Every status/priority/sprint change is an immutable, timestamped event. `sdlc:retro` works out of the box.
- **Portable.** Labels survive repo transfers, forks, and are visible everywhere — GitHub UI, mobile, notifications, email, and any third-party tool that reads issues.
- **Simple CLI operations.** Every operation is a single `gh issue` command. No "two-step dance."
- **Batch operations.** `gh issue edit 1 2 3 --add-label X --remove-label Y` — native batch support for label swaps.
- **Searchable.** `gh issue list --label "status:todo" --label "area:auth"` — AND filtering works natively.
- **No dual-state drift.** One system, one source of truth, zero reconciliation needed between labels and project fields.

### What we lose

- **No board visualization in GitHub UI.** Cannot get a kanban board without Projects.
- **No iteration date awareness.** Sprint labels are strings, not date ranges.
- **No burndown chart.** Projects Insights (web UI) has built-in burndown; we don't get that.
- **No "Views" feature.** Cannot save filtered/grouped views in the GitHub UI.

---

## 5. Option B: Projects-Only

### What it means

Move Status, Priority, Area, Type, and Sprint from labels to Project fields. Keep only `triage` as a label.

### What we gain

- **Board visualization.** Kanban board in GitHub UI, drag-and-drop column moves.
- **Iteration fields with dates.** Sprint has start/end dates, duration.
- **Views.** Save custom filtered/sorted views (Table, Board, Roadmap).
- **Built-in automations.** Auto-set Status to Done on issue close.

### What we lose — BLOCKERS

1. **Time-in-status metrics.** `sdlc:retro` cannot compute time-in-status. **BLOCKER.**
2. **`gh issue list --label` filtering.** Every skill that queries issues by status, priority, or area would need to switch to `gh project item-list --query` — which only works if the issue is IN the project. Issues not yet added to the project are invisible.
3. **Portability.** Delete or close the project, and all field values are gone. Orphaned issues lose their metadata.
4. **Extra OAuth scope.** Every user/CI environment needs `gh auth refresh -s project`.
5. **ID resolution overhead.** Every field write requires Item ID + Field ID + Option ID lookup. The "two-step dance" adds 2-3 API calls per operation.
6. **No batch field updates.** Must loop over items one at a time. Labels support `gh issue edit 1 2 3 --add-label`.
7. **Invisible outside project context.** Issue metadata is only visible if you're looking at the Project board. `gh issue view 42` shows nothing about Priority or Status.

**Verdict: Non-viable.** The Timeline API blocker alone disqualifies this option. The usability regressions pile on top.

---

## 6. Option C: Hybrid with Clear Ownership

### The split

| Data point | Lives on | Rationale |
|---|---|---|
| Status | Label (`status:X`) | Timeline audit trail required |
| Priority | Label (`priority:X`) | Simple, queryable, auditable |
| Area | Label (`area:X`) | Static, set-once, queryable |
| Type | Label (`type:X`) | Structural, never changes |
| Triage | Label (`triage`) | Simple flag |
| Sprint | Project iteration field | Date awareness |
| Estimate | Project number field | Not a label concern |
| Board views | Project views | Visual only |

### Rules

- Labels are the **source of truth** for Status, Priority, Area, Type
- Project fields for Sprint and Estimate are **write-only additions** — never read by skills for decision-making
- If label and project field disagree, the label wins
- `sdlc:reconcile` syncs labels → project fields (one-way), never the reverse

### What we gain over Labels-only

- Kanban board visualization
- Sprint date awareness in the UI
- Estimate tracking in the UI

### What we lose vs Labels-only

- **Double the write operations.** Every status change must update both the label AND the project field.
- **Reconciliation complexity.** `sdlc:reconcile` must now check label ↔ project field consistency.
- **Setup overhead.** Must create the project, configure fields, add all issues, maintain the OAuth scope.
- **Cognitive overhead.** "Where does this data live?" now has a split answer.
- **Fragile.** If the dual-write fails halfway (label updated, project field not), we have drift until reconcile runs.

### The honest assessment

This works, but it's solving a problem we don't have. The board visualization is nice, but we're building CLI skills for Claude Code — the user never looks at the GitHub Project board. They ask `sdlc:status` and get a terminal report. The estimate field is useful, but we can add `estimate:S/M/L` labels if needed.

---

## 7. Recommendation and Rationale

### Decision: Option A — Labels-Only

**Reasoning, ranked by importance:**

1. **Timeline API audit trail is non-negotiable.** `sdlc:retro`'s time-in-status computation depends on `labeled`/`unlabeled` events. There is no equivalent for Project field changes in the REST API. This is a hard blocker for putting status in Projects.

2. **Simplicity for a CLI-first workflow.** Our users interact with issues through Claude Code skills, not the GitHub web UI. A kanban board adds zero value when the interface is `sdlc:status` printing a formatted table in the terminal.

3. **Single source of truth.** Labels are the one system. No dual-state, no sync, no reconciliation between labels and project fields. Every skill reads/writes one thing.

4. **Zero setup cost.** No project to create, no fields to configure, no OAuth scope to manage. `sdlc:create` bootstraps labels with `gh label create --force` and it's done.

5. **Battle-tested in this repo.** The existing `calendar-agent` workflow already uses these exact labels successfully. All 58 issues have consistent labeling. The research documents (01-04) validated every command against the real repo.

6. **Portability.** Labels are permanent metadata on the issue. They survive everything — project deletion, repo transfers, organization changes.

### When to revisit this decision

- If GitHub adds ProjectsV2 field change events to the REST Timeline API (watch the [GitHub Changelog](https://github.blog/changelog/))
- If we move to a multi-repo setup where cross-repo board visualization becomes essential
- If the team grows beyond 3 people and needs a shared visual board for standups

---

## 8. Labels-Only Implementation Spec

### 8.1 Label Taxonomy

```
TYPE LABELS (immutable after creation)
  type:epic        #7B68EE   Top-level initiative
  type:feature     #4169E1   Feature under an epic
  type:story       #6495ED   Implementable unit of work
  type:bug         #DC143C   Bug report
  type:spike       #FF8C00   Research/investigation task
  type:chore       #C0C0C0   Maintenance and cleanup task

STATUS LABELS (mutually exclusive — exactly one per issue)
  status:todo          #EEEEEE   Ready to be picked up
  status:in-progress   #FFFF00   Currently being worked on
  status:done          #2E8B57   Completed
  status:blocked       #FF4500   Blocked by dependency

PRIORITY LABELS (mutually exclusive — exactly one per issue)
  priority:critical   #8B0000   Must ship
  priority:high       #FF6347   Important for MVP
  priority:medium     #FFA07A   Nice to have
  priority:low        #FFD700   Post-MVP improvement

AREA LABELS (can have multiple — rare but valid)
  area:auth       #9370DB   Authentication & OAuth
  area:api        #20B2AA   FastAPI backend
  area:agents     #32CD32   LangGraph agent pipeline
  area:ui         #FF69B4   Frontend UI
  area:infra      #708090   Infrastructure & deployment
  area:search     #DAA520   Azure AI Search & vectors

SPRINT LABELS (mutually exclusive — one per issue per PI)
  sprint:pi1-s1   #B0C4DE   PI 1, Sprint 1
  sprint:pi1-s2   #87CEEB   PI 1, Sprint 2
  (add more as sprints are planned)

TRIAGE
  triage          #FFFFFF   Needs triage
```

### 8.2 Skill Interactions with Labels

#### `sdlc:define`
No label operations. Produces local draft files only.

#### `sdlc:create`

| Operation | Command |
|---|---|
| Bootstrap labels | `gh label create "type:story" -c "6495ED" -d "..." --force` (sequential, idempotent) |
| Create issue with labels | `gh issue create --title "..." --body-file ... --label "type:story" --label "status:todo" --label "priority:high" --label "area:auth"` |
| Add sprint label | `gh issue edit N --add-label "sprint:pi1-s1"` |
| Link sub-issues | `gh api graphql` with `addSubIssue` mutation |

#### `sdlc:update`

| Operation | Command |
|---|---|
| Transition status | `gh issue edit N --add-label "status:in-progress" --remove-label "status:todo"` |
| Change priority | `gh issue edit N --add-label "priority:high" --remove-label "priority:medium"` |
| Assign sprint | `gh issue edit N --add-label "sprint:pi1-s2" --remove-label "sprint:pi1-s1"` |
| Update body | Read with `gh issue view N --json body`, modify, write with `gh issue edit N --body-file -` |
| Assign | `gh issue edit N --add-assignee "@me"` |
| Close | `gh issue close N --reason completed` |

#### `sdlc:status`

| Operation | Command |
|---|---|
| List by status | `gh issue list --label "status:todo" --json number,title,labels,assignees` |
| List by area | `gh issue list --label "area:auth" --json number,title,labels` |
| Count by status | `gh issue list --state all --limit 500 --json labels` + jq grouping |
| Find blocked | `gh issue list --label "status:blocked" --json number,title,body` |
| Find unassigned todo | `gh issue list --label "status:todo" --search "no:assignee"` |
| Sprint scope | `gh issue list --label "sprint:pi1-s1" --json number,title,labels,state` |
| Epic progress | `gh api graphql` with `subIssuesSummary` |
| Dependency check | Parse `Blocked by:` from issue body, check if blockers are closed |
| Parallelizable | Filter `status:todo` issues whose `Blocked by` refs are all `status:done` |

#### `sdlc:reconcile`

| Operation | Command |
|---|---|
| Find issues without status | `gh issue list --state open --limit 500 --json number,labels` + jq filter for missing `status:` |
| Find issues without type | Same pattern, filter for missing `type:` |
| Find issues without priority | Same pattern, filter for missing `priority:` |
| Fix closed without `status:done` | `gh issue list --state closed --limit 500 --json number,labels` + find those without `status:done`, then `gh issue edit N --add-label "status:done"` |
| Fix open with `status:done` | `gh issue list --label "status:done" --state open --json number` + either close or remove label |
| Close completed parents | Query sub-issues via GraphQL, if all done, close parent with `gh issue close N --reason completed --comment "..."` |
| Find orphaned sub-issues | Issues with `Parent: #X` in body where #X is closed/deleted |
| Verify label taxonomy | `gh label list --json name` + compare against expected set |
| Create missing labels | `gh label create "name" --force` |

#### `sdlc:retro`

| Operation | Command |
|---|---|
| Get sprint issues | `gh issue list --label "sprint:pi1-s1" --state all --json number,title,labels,createdAt,closedAt` |
| Time-in-status per issue | `gh api repos/{owner}/{repo}/issues/N/timeline --paginate` + filter `labeled`/`unlabeled` events for `status:*` |
| Blocked duration | Same timeline query, filter for `status:blocked` |
| Bulk label events | `gh api repos/{owner}/{repo}/issues/events --paginate` + filter status label events |
| Merged PRs | `gh pr list --state merged --search "merged:YYYY-MM-DD..YYYY-MM-DD" --json number,mergedAt,createdAt,reviews,additions,deletions,closingIssuesReferences` |
| PR-to-issue mapping | `--json closingIssuesReferences` |
| Review turnaround | `--json reviews` + compute first non-PENDING review timestamp |
| Priority changes | Timeline `labeled`/`unlabeled` events for `priority:*` |
| Sprint transitions | Timeline `labeled`/`unlabeled` events for `sprint:*` |

Every metric `sdlc:retro` computes depends on label events in the Timeline API. Zero dependency on Projects.

#### `sdlc:capture`

| Operation | Command |
|---|---|
| Quick create | `gh issue create --title "..." --body "..." --label "triage"` |

### 8.3 Key `gh` Commands by Category

**Status transitions (atomic swap):**
```bash
# Todo → In Progress
gh issue edit 42 --add-label "status:in-progress" --remove-label "status:todo"

# In Progress → Blocked
gh issue edit 42 --add-label "status:blocked" --remove-label "status:in-progress"

# Blocked → In Progress (unblocked)
gh issue edit 42 --add-label "status:in-progress" --remove-label "status:blocked"

# In Progress → Done
gh issue edit 42 --add-label "status:done" --remove-label "status:in-progress"
```

**Batch status transitions:**
```bash
# Move multiple issues to in-progress
gh issue edit 42 43 44 --add-label "status:in-progress" --remove-label "status:todo"
```

**Filtering (used by every skill):**
```bash
# AND logic with multiple --label flags
gh issue list --label "type:story" --label "status:todo" --label "area:auth"

# With search qualifiers
gh issue list --label "type:story" --search "no:assignee sort:created-asc"

# Negation (find stories that aren't done)
gh issue list --label "type:story" --search "-label:status:done"
```

**Dashboard aggregation:**
```bash
gh issue list --state all --limit 500 --json number,labels \
  --jq 'group_by(
    .labels | map(.name) |
    if contains(["status:done"]) then "done"
    elif contains(["status:in-progress"]) then "in-progress"
    elif contains(["status:blocked"]) then "blocked"
    elif contains(["status:todo"]) then "todo"
    else "unlabeled" end
  ) | map({status: .[0].labels | map(.name) |
    if contains(["status:done"]) then "done"
    elif contains(["status:in-progress"]) then "in-progress"
    elif contains(["status:blocked"]) then "blocked"
    elif contains(["status:todo"]) then "todo"
    else "unlabeled" end,
    count: length
  })'
```

**Time-in-status (used by `sdlc:retro`):**
```bash
gh api repos/raulstechtips/calendar-agent/issues/42/timeline --paginate \
  --jq '[.[] | select(
    (.event == "labeled" or .event == "unlabeled") and
    (.label.name | startswith("status:"))
  ) | {event, label: .label.name, at: .created_at}]'
```

### 8.4 `sdlc:reconcile` — What "Hygiene" Means in Labels-Only

Reconcile checks for and fixes these categories of drift:

**1. Missing labels (incomplete metadata):**
- Open issue without a `status:` label → add `status:todo`
- Open issue without a `type:` label → flag for triage
- Open issue without a `priority:` label → flag for triage
- Open issue without an `area:` label → flag for triage

**2. Contradictory state:**
- Issue is `CLOSED` but has `status:todo` or `status:in-progress` → swap to `status:done`
- Issue is `OPEN` but has `status:done` → either reopen investigation or close it
- Issue has multiple `status:` labels → remove all but the most recent (check timeline)
- Issue has multiple `priority:` labels → remove all but the most recent

**3. Hierarchy consistency:**
- Parent (epic/feature) has all sub-issues in `status:done` → auto-close parent
- Parent is closed but has open sub-issues → flag for review
- Issue body says `Blocked by: #X` but #X is closed → suggest removing `status:blocked`

**4. Label taxonomy integrity:**
- Labels in the expected set exist → `gh label create --force` for each
- Unknown labels matching our patterns (e.g., `status:review`) → flag for review
- GitHub default labels (`bug`, `enhancement`) → optionally delete

**5. Sprint consistency:**
- Open issues with a past sprint label and no current sprint → flag for re-planning
- Issues in `status:done` without being closed → close them

### 8.5 `sdlc:retro` — How Metrics Work with Labels

All metrics use the same pattern: query Timeline API events, pair intervals, compute durations.

**Available metrics (all from label events):**

| Metric | Timeline Events Used | Computation |
|---|---|---|
| Queue time | `labeled status:todo` → `unlabeled status:todo` | Duration of todo interval |
| Coding time | `labeled status:in-progress` → `unlabeled status:in-progress` | Duration of in-progress interval |
| Blocked time | `labeled status:blocked` → `unlabeled status:blocked` | Duration of blocked interval |
| Cycle time | First `labeled status:in-progress` → `labeled status:done` | End-to-end active time |
| Lead time | Issue `createdAt` → `labeled status:done` | Full lifetime |
| Priority changes | Count `labeled priority:*` events after initial creation | Stability metric |
| Sprint carries | Count `unlabeled sprint:X` + `labeled sprint:Y` pairs | Delivery predictability |
| Rework | `unlabeled status:done` then `labeled status:in-progress` | Quality signal |

**Metrics from PR data (no label dependency):**

| Metric | Source | Computation |
|---|---|---|
| PR lead time | `gh pr view --json commits,mergedAt` | `mergedAt - first_commit_date` |
| Review turnaround | `gh pr view --json createdAt,reviews` | `first_review.submittedAt - createdAt` |
| Code churn | `gh pr view --json additions,deletions` | Sum per sprint |
| Review compliance | `gh pr list --json reviewDecision` | `approved / total * 100` |

---

## 9. What We Lose (and Why It Doesn't Matter)

### Kanban board visualization

**What we lose:** Cannot drag-and-drop issues across status columns in the GitHub UI.

**Why it doesn't matter:** Our user interface is Claude Code in the terminal. `sdlc:status` renders a text-based status dashboard. The human never needs to open github.com to see project status.

**If we ever want it:** We can create a Project and set up a one-way label → project field sync in `sdlc:reconcile`. Labels remain source of truth; the board is a read-only view.

### Iteration date awareness

**What we lose:** Sprint labels don't know when a sprint starts and ends.

**Why it doesn't matter:** Sprint dates live in the PI plan file (local git). `sdlc:retro` reads sprint dates from the plan, then queries issues by `sprint:pi1-s1` label. The label identifies which sprint; the plan file provides the dates.

### Burndown charts

**What we lose:** Projects Insights has a built-in burndown chart.

**Why it doesn't matter:** `sdlc:retro` can compute burndown from timeline events (label timestamps for done transitions within the sprint date range). A CLI-rendered burndown is more useful in our workflow than a web chart.

### Saved views

**What we lose:** Cannot save filtered/sorted views in the GitHub UI.

**Why it doesn't matter:** Our "views" are skill invocations: `sdlc:status area=auth status=blocked`. Each skill call is a parameterized view. More flexible than saved static views.

### Estimate tracking

**What we lose:** No numeric field for story points.

**Mitigation if needed:** Add `size:S`, `size:M`, `size:L` labels. Or add an `## Estimate` section in the issue body. Both are queryable and tracked in the timeline.

---

## Sources

- `01-github-projects.md` §16 — Projects vs Issue Labels independence
- `01-github-projects.md` §8 — The "two-step dance" for field updates
- `01-github-projects.md` §9 — Iteration field cannot be created via CLI
- `01-github-projects.md` §13 — Built-in automations (no CLI configuration)
- `02-issue-management.md` §4 — Atomic label swap: `--add-label X --remove-label Y`
- `02-issue-management.md` §10 — Batch: `gh issue edit 1 2 3 --add-label X`
- `03-timeline-and-metrics.md` §4 — Time-in-status from label events
- `03-timeline-and-metrics.md` §12 — "Project field changes are NOT available via the REST timeline API"
- `03-timeline-and-metrics.md` §12 — "`moved_columns_in_project` event only works with classic (v1) projects"
- Verified Timeline API output from `raulstechtips/calendar-agent` issue #100 (2026-03-19)
