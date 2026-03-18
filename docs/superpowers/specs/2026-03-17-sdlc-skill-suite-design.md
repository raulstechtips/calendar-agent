# SDLC Skill Suite — Design Spec

## Problem

The project has outgrown its current tooling. SPEC.md serves double duty as product requirements AND implementation plan. Issue creation is entirely manual. There's no structured way to start a new sprint, decompose work, or close one out. The existing skills (`/pick-task`, `/sync-issues`, `/update-decision`) work but don't form a cohesive lifecycle.

## Solution

Rename and restructure artifacts to use proper SDLC conventions. Replace SPEC.md with two purpose-built documents (PRD + PI Plan). Build a suite of 13 skills that cover the full lifecycle: PRD management, PI planning, work decomposition, execution, and sprint close.

---

## Artifact Definitions

### PRD (Product Requirements Document)

The **what and why**. Stable across PIs. Git-versioned at a single path — no archive files, use `git log` and tags for history.

**Path:** `.claude/prd/PRD.md`

**Format:**

```markdown
---
name: AI Calendar Assistant
version: 1.0
created: 2026-03-14
---

# AI Calendar Assistant — Product Requirements Document

## Overview
[Product vision and purpose]

## Technology Stack & Versions
[Pinned versions table — frontend, backend, infrastructure]

## Architecture
[VNet diagram, service communication, identity strategy, network security]

## Data Models
[Pydantic models, Redis schemas, search document schema]

## API Contracts
[Endpoint signatures, request/response formats, SSE event types]

## Security Constraints
[Hard rules that apply across all PIs — e.g., never store unencrypted tokens]

## Roadmap
[High-level workstreams not yet planned into a PI]

## Acceptance Criteria
[What "done" means for the current state of the product]

## Out of Scope
[Explicit boundaries]

## Decision Log
| Date | Decision | Reason | Affects |
|------|----------|--------|---------|

[Accumulates during a PI. At PI close, entries are baked into the relevant
body sections (e.g., a decision about auth gets folded into the Architecture
section), then the log is wiped clean for the next PI.]
```

**What does NOT go in the PRD:**
- Implementation phases, issue numbers, worktree assignments (that's PI Plan)
- Sprint timelines or scheduling
- Detailed acceptance criteria per story (that's GitHub Issues)

**Versioning lifecycle:**
1. During a PI: decision log accumulates, body sections may be updated
2. At PI close: `/close-pi` bakes decision log entries into body sections, wipes the log, bumps the version number, commits with message `chore(prd): bump to vX.Y after PI-N`
3. Git tag `pi-N-complete` marks the boundary
4. Next PI starts with a clean decision log and updated body

### PI Plan (Program Increment Plan)

The **what and when**. Created fresh each sprint. The "map" — high-level structure, dependency graph, worktree strategy. Points to GitHub Issues for detail.

**Current PI path:** `.claude/pi/PI.md`
**Archived PIs:** `.claude/pi/completed/PI-N.md`

**Format:**

```markdown
---
name: PI-2
theme: "Enhancement & Polish"
started: 2026-03-18
target: 2026-03-25
status: active
---

# PI-2: Enhancement & Polish

## Goals
[2-3 sentences: what does this PI deliver and why now]

## Epics

### Epic: UI Overhaul (#TBD → #123 after /create-epic)
**Features:**
- [ ] Modern chat interface (#TBD)
- [ ] Responsive layout (#TBD)
- [ ] Dark mode (#TBD)
- [ ] Conversation sidebar (#TBD)

### Epic: Session Persistence (#TBD)
**Features:**
- [ ] Redis checkpointer swap (#TBD)
- [ ] Session history API (#TBD)
- [ ] Session metadata (#TBD)

## Dependency Graph
[High-level: which epics/features block others]
- Session Persistence → blocks Conversation Sidebar (needs thread list API)
- Redis checkpointer → blocks Session History API
- UI Overhaul and Session Persistence can start in parallel

## Worktree Strategy
- Worktree A (Frontend): UI Overhaul features — chat interface, responsive, dark mode
- Worktree B (Backend): Session Persistence — checkpointer, history API, metadata
- Sequential: Conversation Sidebar starts after Session History API merges
```

**`#TBD` lifecycle:** Placeholders are filled with real issue numbers as `/create-epic` and `/create-feature` run. PI.md tracks epics and features only — story-level issue numbers live on GitHub (in the feature issue's Stories checklist), not in PI.md. This keeps the map high-level.

**Status values:** `active`, `completed`

---

## Dependency Model

Dependencies are the backbone of the system. They exist at three levels and every skill that creates or modifies work items must maintain them.

### Level 1: PI-level (in PI.md)

High-level, expressed in plain language in the `## Dependency Graph` section:
- Epic-to-epic: "Session Persistence → blocks Conversation Sidebar"
- Cross-epic feature deps: "Redis checkpointer → blocks Session History API"

Purpose: inform worktree strategy and phasing decisions.

### Level 2: GitHub Issue-level (in issue bodies)

Every epic, feature, and story issue gets a structured section:

```markdown
## Dependencies
- Blocked by: #45, #46
- Blocks: #48, #52
```

Additionally, stories and features link to their parent:

```markdown
## Parent
- Epic: #40
- Feature: #43
```

Labels enforce status:
- If all blockers are `status:done` or `CLOSED` → issue can be `status:todo`
- If any blocker is not done → issue should be `status:blocked`

### Level 3: Skill enforcement

Each skill that touches work items is responsible for:

| Skill | Dependency responsibility |
|-------|--------------------------|
| `/plan-increment` | Build high-level dependency graph in PI Plan. Identify cross-epic blocking relationships. |
| `/update-pi` | Re-evaluate dependency graph and worktree strategy when PI scope changes. |
| `/create-epic` | Set cross-epic deps in PI Plan. When creating stub features, ask if any depend on other epics' features. |
| `/create-feature` | Set feature-to-feature deps. When creating stub stories, set intra-feature ordering. |
| `/detail-story` | Set story-level deps (Blocked by / Blocks). Verify no circular deps (see shared detection approach). Apply `status:blocked` if blockers aren't met (see shared satisfaction criteria). |
| `/update-epic` | Recalculate downstream: if epic scope changes, check if dependent epics/features need updating. Update PI Plan. |
| `/update-feature` | Recalculate: if feature scope changes, check dependent stories. Update PI Plan. |
| `/update-story` | Recalculate: if story deps change, verify graph integrity. If story is added mid-sprint, inject into dependency chain correctly. |
| `/pick-task` | Traverse dependency graph: parse `Blocked by` from issue body, verify each blocker is done (see shared satisfaction criteria). Rank by priority then creation order. |
| `/sync-issues` | Audit full graph: detect orphaned deps, circular deps (see shared detection approach), issues labeled `status:todo` with unmet blockers, stale labels on closed issues. |

### Blocker Satisfaction Criteria (shared across all skills)

A dependency is **satisfied** if ANY of:
- The issue has the `status:done` label
- The issue state is `CLOSED` (treated as done even if label wasn't updated)

A dependency is **unmet** if BOTH:
- The issue is `OPEN`
- The issue does NOT have `status:done` label

This definition is used by every skill that checks blockers: `/detail-story`, `/update-story`, `/pick-task`, `/sync-issues`, and the update-* skills.

**Cross-type blocking rules:**
- Story can be blocked by: stories, features (rare — usually means "all stories in this feature must complete")
- Feature can be blocked by: features, epics (rare)
- Epic can be blocked by: epics
- Epics do NOT carry `status:*` labels — their completion is determined by whether all child features are done. Skills that check epic blockers must traverse the feature list.

### Circular Dependency Detection (shared approach)

Used by `/detail-story`, `/update-story`, `/update-feature`, `/update-epic`, and `/sync-issues`:

1. Fetch all open issues with their `Blocked by` lists
2. Build an adjacency list: `{issue_number: [blocker_numbers]}`
3. For each issue, walk the blocker chain (DFS). If you encounter the starting issue, there's a cycle.
4. For small repos (<100 issues): simple path-tracking DFS is sufficient
5. Report cycles as: `Circular dependency detected: #A → #B → #C → #A`
6. Skills that CREATE deps (detail-story, update-*) must check BEFORE writing. Skills that AUDIT (sync-issues) check after the fact.

### Mid-sprint story injection

When a bug or new requirement surfaces mid-sprint:
1. `/update-feature` or `/update-epic` adds the new work item to the PI Plan
2. `/detail-story` (or `/update-story`) creates the issue with correct `Blocked by` / `Blocks`
3. The skill checks: does this new story block anything already in progress? If so, flag it
4. The skill checks: should any existing `status:todo` stories now be `status:blocked` by this new story?

---

## Skill Definitions (13 skills)

### PRD Skills

#### `/create-prd`
**Purpose:** Bootstrap a new PRD for a new repo.
**Trigger:** New project with no `.claude/prd/PRD.md`.
**Flow:**
1. Guided interview: project name, vision, tech stack, architecture decisions
2. Generate PRD.md with all sections populated
3. Create `.claude/prd/` directory if needed
4. Commit: `docs(prd): create initial PRD v1.0`

**Allowed tools:** Read, Write, Bash, Grep, Glob

#### `/update-prd [section|decision]`
**Purpose:** Record a design change or update a PRD section. Replaces `/update-decision`.
**Flow:**
1. If argument is "decision" or describes a decision:
   - Add entry to Decision Log with date, decision, reason, and which section it affects
   - Do NOT modify the body section yet (that happens at PI close)
2. If argument describes a section update (e.g., "update API contracts"):
   - Read current section
   - Present proposed change
   - On approval, update the section
   - If this changes scope, flag which GitHub Issues may be affected
3. Commit: `docs(prd): [description of change]`

**Allowed tools:** Read, Write, Edit, Bash, Grep, Glob

### PI Skills

#### `/plan-increment [theme]`
**Purpose:** Plan the next PI. Handles both first-ever PI and subsequent PIs.
**Flow — first PI (no `pi/PI.md` exists):**
1. Read PRD.md — specifically the Roadmap section
2. Ask: which workstreams go into this PI?
3. For each selected workstream, collaborate on high-level epic decomposition
4. Under each epic, list features (titles + 1-line descriptions)
5. Under each feature, list rough stories (titles only)
6. Build dependency graph across epics/features
7. Propose worktree strategy based on dependency graph
8. Write PI.md with frontmatter, all sections populated, #TBD placeholders
9. Commit: `docs(pi): create PI-1 plan`

**Flow — subsequent PI (`pi/PI.md` exists with `status: active`):**
1. Read current PI.md and PRD.md
2. Query GitHub Issues to assess current PI state:
   - What shipped (closed issues from current PI's epics)
   - What's still open (incomplete work)
   - Any bugs or decisions that affect planning
3. Present retrospective summary to user
4. Run the `/close-pi` flow (do not duplicate — invoke the same logic)
5. Then run the "first PI" flow for the next increment (steps 1-9 above)

**Allowed tools:** Read, Write, Edit, Bash, Grep, Glob

#### `/update-pi [description]`
**Purpose:** Update PI Plan when reality diverges mid-sprint.
**Flow:**
1. Read current PI.md
2. Based on description, identify what changed (epic split, feature moved, story added/removed, dependency change)
3. Update the relevant section of PI.md
4. If dependency graph changed, re-evaluate worktree strategy
5. Verify decision log in PRD is consistent (if this change was driven by a decision, ensure it's logged)
6. Commit: `docs(pi): [description of change]`

**Allowed tools:** Read, Write, Edit, Bash, Grep, Glob

#### `/close-pi`
**Purpose:** Explicitly close the current PI without planning the next one.
**Flow:**
1. Read PI.md and PRD.md
2. Query GitHub Issues — summarize what shipped vs what's open
3. Verify decision log completeness: for each decision, confirm it's reflected in PI state
4. Bake decision log entries into PRD body sections
5. Wipe decision log
6. Bump PRD version
7. Set PI status to `completed`, move to `pi/completed/PI-N.md`
8. Git tag: `pi-N-complete` (local only — remind user to push tag if desired)
9. Commit: `chore(pi): close PI-N` and `chore(prd): bump to vX.Y after PI-N`

**Allowed tools:** Read, Write, Edit, Bash, Grep, Glob

### Work Skills

#### `/create-epic [name]`
**Purpose:** Take a high-level epic from the PI Plan, create a detailed GitHub Issue, create stub feature issues.
**Flow:**
1. Read PI.md — find the epic by name or let user select
2. Collaborate on epic detail: description, success criteria, non-goals
3. Create epic issue on GitHub:
   ```bash
   gh issue create --title "EPIC: [Name]" --body "..." \
     --label "type:epic" --label "priority:..." --label "area:..." --label "status:todo"
   ```
4. For each feature listed under the epic in PI.md:
   - Create a stub feature issue (title + parent epic link only):
     ```bash
     gh issue create --title "FEATURE: [Name]" --body "## Parent\n- Epic: #N\n\n## Dependencies\n- Blocked by: \n- Blocks: " \
       --label "type:feature" --label "area:..." --label "status:todo"
     ```
   - Ask if this feature has cross-epic dependencies, set them
5. Update PI.md — replace `#TBD` with actual issue numbers
6. Commit: `docs(pi): add issue numbers for epic [name]`

**Allowed tools:** Read, Write, Edit, Bash, Grep, Glob

#### `/create-feature [#issue]`
**Purpose:** Take a stub feature issue, flesh it out, create stub story issues.
**Flow:**
1. Read the feature issue from GitHub: `gh issue view <number>`
2. Read the parent epic for context: `gh issue view <epic_number>`
3. Read PRD.md for architecture/data model context relevant to this feature
4. Collaborate on feature detail: description, story breakdown, non-goals, dependencies
5. Update the feature issue body on GitHub with full detail:
   ```bash
   gh issue edit <number> --body "..."
   ```
6. For each story identified:
   - Create a stub story issue (title + parent links only):
     ```bash
     gh issue create --title "[Story title]" --body "## Parent\n- Epic: #N\n- Feature: #M\n\n## Dependencies\n- Blocked by: \n- Blocks: " \
       --label "type:story" --label "area:..." --label "status:todo"
     ```
   - Set intra-feature dependency ordering (story 2 depends on story 1, etc.)
   - Set cross-feature dependencies if any
7. Commit: (story numbers live on GitHub in the feature issue body, not in PI.md)

**Allowed tools:** Read, Write, Edit, Bash, Grep, Glob

#### `/detail-story [#issue]`
**Purpose:** Take a stub story issue, add full detail (acceptance criteria, file scope, technical notes, deps).
**Flow:**
1. Read the story issue from GitHub
2. Read parent feature and epic for context
3. Read PRD.md — specifically security constraints, data models, API contracts relevant to this story
4. Collaborate on story detail:
   - Acceptance criteria (testable checkboxes)
   - File scope (new files, modified files)
   - Technical notes (implementation guidance)
   - Dependencies (verify and finalize `Blocked by` / `Blocks`)
5. Verify dependency integrity (see Blocker Satisfaction Criteria and Circular Dependency Detection below)
6. Update the story issue body on GitHub
7. If PI.md needs updating (e.g., dependency graph changed), update it
8. Commit if files changed: `docs(pi): update deps for story #N`

**Allowed tools:** Read, Write, Edit, Bash, Grep, Glob

#### `/update-epic [#issue]`
**Purpose:** Modify an epic's scope — add/remove features, change description, update dependencies.
**Flow:**
1. Read current epic issue and its features from GitHub
2. Identify what's changing
3. Update the epic issue body
4. If features added/removed:
   - Create new stub feature issues or close removed ones
   - Update downstream dependency graph
5. Update PI.md to reflect changes
6. Flag any features/stories that may be impacted
7. Commit: `docs(pi): update epic #N scope`

**Allowed tools:** Read, Write, Edit, Bash, Grep, Glob

#### `/update-feature [#issue]`
**Purpose:** Modify a feature — add/remove stories, change description, update dependencies.
**Flow:**
1. Read current feature issue and its stories from GitHub
2. Identify what's changing
3. Update the feature issue body
4. If stories added/removed:
   - Create new stub story issues or close removed ones
   - Re-evaluate dependency chain
   - Check: does this new/removed story affect any `status:blocked` / `status:todo` labels?
5. Update PI.md if feature-level changes affect the high-level plan
6. Commit if PI.md changed: `docs(pi): update feature #N`

**Allowed tools:** Read, Write, Edit, Bash, Grep, Glob

#### `/update-story [#issue]`
**Purpose:** Modify a story's AC, file scope, deps, or technical notes.
**Flow:**
1. Read current story issue from GitHub
2. Identify what's changing
3. Update the story issue body
4. If dependencies changed:
   - Verify no circular deps
   - Check downstream: if this story now blocks something new, update that issue's `Blocked by`
   - Check upstream: if a new blocker was added, verify it's met or apply `status:blocked`
5. If this was driven by a bug/decision, remind user to run `/update-prd` if not already done
6. Commit if PI.md changed

**Allowed tools:** Read, Write, Edit, Bash, Grep, Glob

#### `/pick-task [area]`
**Purpose:** Find the next unblocked story to work on. Rewritten with robust dependency analysis.
**Flow:**
1. Read PI.md for current sprint context
2. Query open stories:
   ```bash
   gh issue list --state open --label "type:story" --label "status:todo" \
     --json number,title,body,labels
   ```
3. For each candidate, parse `## Dependencies` → `Blocked by` from issue body
4. For each blocker, check status:
   ```bash
   gh issue view <dep> --json state,labels
   ```
   Satisfied if: `status:done` label OR issue state is `CLOSED`
5. Filter to only unblocked stories
6. If area filter provided, narrow to that area label
7. Rank by: `priority:critical` > `priority:high` > `priority:medium`, then issue creation date (older first)
8. Present recommendation with: issue number, title, why it's next, key AC, file scope
9. On confirmation:
   ```bash
   gh issue edit <number> --add-label "status:in-progress" --remove-label "status:todo"
   ```

**Allowed tools:** Read, Bash, Grep, Glob

#### `/sync-issues [area]`
**Purpose:** Audit and fix the full issue hierarchy. Rewritten for dependency graph validation.
**Flow:**
1. Fetch all open issues with type labels (epic, feature, story)
2. Fetch all closed issues with stale status labels (in-progress, todo)
3. **Stale label fix:** Closed issues with `status:in-progress` or `status:todo` → update to `status:done`
4. **Dependency audit:** For each open story:
   - Parse `Blocked by` from issue body
   - Check each blocker's state
   - If all blockers met but issue is `status:blocked` → update to `status:todo`
   - If any blocker unmet but issue is `status:todo` → update to `status:blocked`
5. **Orphan detection:** Flag issues that reference non-existent issue numbers in deps
6. **Circular dep detection:** Build adjacency list, detect cycles, report them
7. **Hierarchy check:** Verify every story has a parent feature, every feature has a parent epic
8. **Report:**
   - Total: X epics, Y features, Z stories
   - Done: X | In Progress: X | Todo: X | Blocked: X
   - Stale labels fixed: X
   - Dependency issues found: X (list them)
   - Orphaned references: X
   - Next recommended stories

**Allowed tools:** Read, Bash, Grep, Glob

---

## Migration Plan

### File moves
1. `.claude/specs/in-progress/SPEC.md` → `.claude/prd/PRD.md`
   - Remove "Implementation Phases" section (becomes PI Plan)
   - Remove issue numbers from body
   - Add YAML frontmatter
   - Keep everything else as-is
2. Create `.claude/pi/` and `.claude/pi/completed/`
3. Create `.claude/pi/PI.md` from the "Implementation Phases" section of current SPEC
4. Remove `.claude/specs/` directory (empty after migration)

### Reference updates
- `CLAUDE.md`: all SPEC.md references → PRD.md, add new skill docs, update workflow section, update "Decision Workflow" section, fix Architecture Decisions (langchain-google-community → custom @tool)
- `.claude/rules/workflow.md`: "Read the spec" → "Read the PRD and PI Plan". Step 2 becomes: "Read PRD.md (security constraints, data models, API contracts) and PI.md (dependency context). Read the GitHub issue for detailed AC and file scope."
- `.claude/rules/git.md`: add `pi-N-complete` tag convention
- `.claude/agents/code-reviewer.md`: update "Compare implementation against `.claude/specs/in-progress/`" → `.claude/prd/PRD.md`
- `docs/HUMAN-WORKFLOW.md`: rewrite to reflect PRD/PI split, replace `/update-decision` references with `/update-prd`, update session start procedure and decision workflow sections
- Deprecate `/update-decision` → redirect to `/update-prd`

### Existing skill disposition
| Current | Action |
|---------|--------|
| `/pick-task` | Rewrite in place with new dependency model |
| `/sync-issues` | Rewrite in place with hierarchy validation |
| `/update-decision` | Deprecate, replace with `/update-prd` |
| `/review-coderabbit` | Keep as-is, no changes needed |

### New directories
```
.claude/
├── prd/
│   └── PRD.md
├── pi/
│   ├── PI.md
│   └── completed/
├── skills/
│   ├── create-prd/SKILL.md
│   ├── update-prd/SKILL.md
│   ├── plan-increment/SKILL.md
│   ├── update-pi/SKILL.md
│   ├── close-pi/SKILL.md
│   ├── create-epic/SKILL.md
│   ├── create-feature/SKILL.md
│   ├── detail-story/SKILL.md
│   ├── update-epic/SKILL.md
│   ├── update-feature/SKILL.md
│   ├── update-story/SKILL.md
│   ├── pick-task/SKILL.md        (rewritten)
│   ├── sync-issues/SKILL.md      (rewritten)
│   ├── review-coderabbit/SKILL.md (unchanged)
│   └── update-decision/SKILL.md   (deprecated redirect)
```

---

## Label Taxonomy (unchanged)

The existing GitHub label system is retained as-is:

**Type:** `type:epic`, `type:feature`, `type:story`, `type:spike`, `type:bug`, `type:chore`
**Status:** `status:todo`, `status:in-progress`, `status:done`, `status:blocked` (mutually exclusive)
**Priority:** `priority:critical`, `priority:high`, `priority:medium`, `priority:low`
**Area:** `area:auth`, `area:api`, `area:agents`, `area:ui`, `area:infra`, `area:search`
**Sprint:** `sprint:day1`, `sprint:day2` (may evolve to PI-based naming in future)

---

## GitHub Issue Templates

### Epic template
```markdown
## Overview
[What this epic delivers and why]

## Success Criteria
- [ ] [Measurable outcome 1]
- [ ] [Measurable outcome 2]

## Features
- [ ] #N — Feature name
- [ ] #M — Feature name

## Non-goals
[What this epic explicitly does NOT include]

## Dependencies
- Blocked by: [epic-level blockers, if any]
- Blocks: [what depends on this epic completing]
```

### Feature template
```markdown
## Description
[What this feature delivers]

## Stories
- [ ] #N — Story title
- [ ] #M — Story title

## Non-goals
[Boundaries]

## Dependencies
- Blocked by: #X, #Y
- Blocks: #Z

## Parent
- Epic: #N
```

### Story template
```markdown
## Description
[What needs to be built and why]

## Acceptance Criteria
- [ ] [Testable criterion 1]
- [ ] [Testable criterion 2]
- [ ] [Testable criterion 3]

## File Scope
**New files:**
- path/to/new/file.py

**Modified files:**
- path/to/existing/file.py

## Technical Notes
[Implementation guidance, patterns to follow, edge cases]

## Dependencies
- Blocked by: #X, #Y
- Blocks: #Z

## Parent
- Epic: #N
- Feature: #M
```

---

## Shared Skill Conventions

### GitHub CLI pagination
All `gh issue list` commands must use `--limit 200` to avoid default 30-result truncation.

### Dependency body parsing
When parsing `Blocked by: #45, #46` from issue bodies, handle formatting variations:
- With/without spaces after commas: `#45,#46` and `#45, #46`
- With/without leading `- `: both `- Blocked by:` and `Blocked by:` are valid
- Empty deps: `Blocked by:` with nothing after it means no blockers

### Partial failure handling
Skills that create multiple GitHub Issues in sequence (e.g., `/create-epic` creating stub features):
- If a step fails mid-flight, report what was created and what failed
- Do NOT attempt to roll back already-created issues — they exist on GitHub and the user can manage them
- Do NOT commit PI.md changes until all GitHub operations succeed
- The user decides whether to retry the failed step or clean up manually

### PI numbering
`/plan-increment` auto-detects the next PI number by scanning `pi/completed/` for existing `PI-N.md` files. If none exist, starts at PI-1.

---

## What This Design Does NOT Change

- TDD workflow (`.claude/rules/tdd.md`)
- Code quality rules (`.claude/rules/code-quality.md`)
- Git commit conventions (`.claude/rules/git.md`, except adding tag convention)
- Agent definitions (`code-reviewer`, `test-runner`, `issue-tracker`)
- Frontend/backend contextual skills (shadcn, vercel patterns)
- The actual codebase structure — this is purely SDLC tooling
