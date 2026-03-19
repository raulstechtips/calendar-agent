# SDLC Skill Suite — Future Ideas

Captured during the v2 design brainstorm (2026-03-19). These are lower-priority improvements to revisit after the core suite is built and validated.

## Ideas

### Priority: HIGH — Build Before Other Future Ideas

### 1. `sdlc:audit` — Technical Verification Audit
A deep technical audit skill that verifies what was built matches what was specified. This is fundamentally different from `sdlc:retro` (which focuses on process outcomes) and from the existing `code-reviewer` agent (which reviews individual PRs during development).

**What it does:**
- Runs BEFORE `sdlc:retro` — its findings feed into the retrospective as evidence
- Dispatches a recursive subagent chain that audits across multiple domains
- Each subagent specializes in a different layer of verification:
  - PRD compliance: does the shipped code satisfy the product requirements?
  - PI completion: were the planned epics/features delivered as scoped?
  - Epic-level: were success criteria met? Compare code against epic's stated goals
  - Feature-level: do the implemented features match feature descriptions?
  - Story-level: were acceptance criteria met? Does file scope match what was listed?
- Subagents report back to a coordinator that synthesizes findings
- Produces an audit document at `.claude/audits/<scope>-<date>.md`

**Why it's separate from sdlc:retro:**
- Retro = "Did we follow a good process?" (lightweight, fast)
- Audit = "Did we build what we said we'd build?" (heavy, recursive, context-intensive)
- Audit requires loading PRD, PI, every epic/feature/story, AND the actual codebase — massive context
- Each domain subagent needs focused context (e.g., the story AC + the actual file changes)
- This is too complex to bundle into retro without degrading both skills

**Why it's separate from the existing code-reviewer:**
- Code-reviewer operates on individual PRs during development (tactical, per-story)
- Audit operates across the full PI scope (strategic, cross-cutting)
- Audit compares against the SDLC artifacts (PRD, epics, features), not just code quality
- Different subagent architecture: code-reviewer is a single pass, audit is recursive/hierarchical

**Pipeline:** `sdlc:audit` → `sdlc:retro` (reads audit findings) → `sdlc:define pi` (reads retro)

**Design considerations:**
- Recursive subagent chain needs careful context engineering — each subagent gets only what it needs
- Coordinator subagent synthesizes findings without re-reading everything
- Could be scoped: `sdlc:audit pi` (full PI) or `sdlc:audit epic #40` (single epic)
- Token cost will be significant — consider caching and incremental audits
- May need custom reviewer prompt templates (similar to how superpowers has spec-reviewer-prompt.md)
- Should support both "did we build the right thing" (spec compliance) and "did we build it right" (quality)

**Feasibility assessment:**
- HIGH feasibility for the subagent dispatch pattern — superpowers already proves this works with implementer/reviewer subagents
- MEDIUM feasibility for the recursive chain — needs careful prompt engineering to prevent context explosion
- The main risk is token cost for large PIs (30+ stories = 30+ subagent invocations minimum)
- Mitigation: allow scoped audits (per-epic, per-feature) and incremental runs
- Should be designed and tested thoroughly — this is the most complex skill in the suite

**Depends on:** Core SDLC suite being built first (sdlc:define, sdlc:create, sdlc:update, sdlc:retro) since audit reads the artifacts these skills produce.

### 2. PI Changelog — Skill Invocation Tracking
A lightweight changelog mechanism that enables richer retrospective metrics.

**What it does:**
- Adds a file at `.claude/pi/changelog.md` that persists for the duration of a PI
- `sdlc:update` and `sdlc:define` (in reshape mode) append an entry every time they make a change
- Each entry records: date, what changed, which artifact, which skill, depth level (DIRECT/LIGHT/STANDARD/DEEP)
- `sdlc:retro` reads this log to produce accurate process metrics

**Example format:**
```markdown
- 2026-03-15: Updated story #52 — added blocker #48 (via sdlc:update, DIRECT)
- 2026-03-16: Reshaped epic #40 — split into two epics (via sdlc:define, DEEP)
- 2026-03-17: Added feature #70 to PI (via sdlc:define, STANDARD)
```

**Why this is needed:**
- Without it, `sdlc:retro` cannot reliably know how many scope changes happened during a PI
- The agent has no session history across conversations — each invocation is stateless
- Git log and GitHub API can infer some changes but it's fragile and indirect
- This is the simplest mechanism: append-only log, one line per change, read by retro

**Metrics it unlocks for sdlc:retro:**
- Scope change frequency (how many times was the PI modified?)
- Update pattern analysis (were changes clustered or spread out?)
- Depth distribution (how often did updates require full brainstorming vs direct edits?)
- Per-epic/feature change count (which areas were most volatile?)

**Implementation notes:**
- Append-only — skills never edit or delete entries, only add
- Archived alongside PI.md when PI closes (moved to `.claude/pi/completed/`)
- Low overhead — one line per change, no complex format
- Should be added to `sdlc:update` and `sdlc:define` as a post-execution step

**Depends on:** Core SDLC suite (sdlc:define, sdlc:update) being built first. This is an enhancement to those skills, not a new skill.

**Priority:** HIGH — prerequisite for enhanced `sdlc:retro` process metrics. Without this, retro is limited to what GitHub API and git log can provide.

### 3. GitHub Projects Integration — Native Project Management
Replace label-based state management with GitHub Projects for richer sprint tracking, custom fields, and board views.

**What it changes:**
- Status tracking moves from labels (`status:todo`, `status:in-progress`) to a native Project Status field
- Priority becomes a Project custom field instead of labels (`priority:high`)
- Sprint/PI tracking uses Project Iterations instead of PI.md dates
- Area grouping uses Project custom field instead of labels (`area:auth`)
- Board and table views become available for visual overview

**What stays the same:**
- Issue hierarchy via body content (epic → feature → story parent links)
- Dependency mapping via body sections (`Blocked by` / `Blocks`)
- Labels for type classification (`type:epic`, `type:story`) — these are fundamental to querying

**Why this matters:**
- Projects give us custom fields with validation (single-select, iteration, number)
- Project views provide visual kanban boards and timeline views the CLI can't replicate
- Iterations have start/end dates natively — maps perfectly to PI concept
- Status field changes are trackable via the Projects API
- GitHub's built-in automations can auto-update status (e.g., when PR merges → status = Done)

**Impact on skills:**
- `sdlc:create` — sets Project fields in addition to (or instead of) labels
- `sdlc:update` — modifies Project fields via `gh project item-edit`
- `sdlc:status` — queries Project for richer status data, iteration progress
- `sdlc:reconcile` — audits Project field consistency
- `sdlc:retro` — uses Project iteration boundaries for sprint metrics

**Design decision needed:**
- Option A: Projects replaces labels entirely (cleaner, but requires Project for all repos)
- Option B: Projects supplements labels (richer data, but dual state management)
- Option C: Projects is primary, labels are kept as fallback for repos without Projects

**Depends on:** Core SDLC suite being built first. This is a v2 enhancement that adds richness on top of the working v1.

**Research available:** See `gh-cli-research/01-github-projects.md` for complete CLI command reference.

**Priority:** HIGH — this is the biggest quality-of-life improvement for the suite and could fundamentally change how status tracking works.

### 4. `sdlc:resume` — Context Switching Support
A "where was I?" command for solo developers who context-switch frequently.
- Shows: last modified story, its status, uncommitted git changes, suggested next action
- High value for returning to a project after a break or switching between features
- Could read git log + open issues with `status:in-progress` to reconstruct context

### 5. Burn-Down Awareness in `sdlc:status`
Add time-awareness to the status briefing.
- If PI.md has start and target dates, calculate % time elapsed vs % stories completed
- Show a simple "on track / at risk / behind" indicator
- Keep it lightweight — one sentence, not a chart
- Helps solo devs who are bad at self-managing pace

### 6. Local Index File (`.claude/sdlc-index.json`)
Cache the issue hierarchy, dependency graph, and label state locally.
- Updated whenever any sdlc skill runs
- Makes `sdlc:status` and `sdlc:reconcile` faster (no full GitHub re-fetch)
- Provides a reliable structured query layer instead of parsing issue body markdown every time
- Trade-off: another file to keep in sync, potential for stale data

### 7. Rollback Output from `sdlc:create`
After creating issues, output a rollback command block.
- List of `gh issue close` commands the developer can run to undo
- Do NOT auto-rollback — just make it easy to undo manually
- Especially useful for epic/feature creation which generates stub children (one create = many issues)

---

*Source: Audit by review subagent during SDLC v2 design session*
