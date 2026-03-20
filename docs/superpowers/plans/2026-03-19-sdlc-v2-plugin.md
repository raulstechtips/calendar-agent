# SDLC v2 Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `sdlc` Claude Code plugin with 7 skills that replace the v1 suite of 13 local skills.

**Architecture:** A Claude Code plugin at `.claude/plugins/sdlc/` providing namespaced skills (`sdlc:define`, `sdlc:create`, etc.). Skills use progressive disclosure — SKILL.md contains the core flow under 500 lines, with level-specific content in `reference/` subdirectories. All local artifacts live under `.claude/sdlc/`.

**Tech Stack:** Claude Code plugin system (plugin.json manifest, skills/ directory, agents/ directory), GitHub CLI (`gh`), git.

**Spec:** `docs/superpowers/specs/2026-03-19-sdlc-v2-skill-suite-design.md`

**CLI Research:** `gh-cli-research/02-issue-management.md`, `gh-cli-research/03-timeline-and-metrics.md`, `gh-cli-research/04-git-analytics.md`, `gh-cli-research/05-plugin-architecture.md`

---

## File Structure

```
.claude/plugins/sdlc/
├── plugin.json
├── skills/
│   ├── define/
│   │   ├── SKILL.md
│   │   └── reference/
│   │       ├── prd-guide.md
│   │       ├── pi-guide.md
│   │       ├── epic-guide.md
│   │       ├── feature-guide.md
│   │       └── story-guide.md
│   ├── create/
│   │   ├── SKILL.md
│   │   └── reference/
│   │       ├── prd-execution.md
│   │       ├── pi-execution.md
│   │       ├── epic-execution.md
│   │       ├── feature-execution.md
│   │       └── story-execution.md
│   ├── update/
│   │   ├── SKILL.md
│   │   └── reference/
│   │       ├── prd-update.md
│   │       ├── pi-update.md
│   │       ├── epic-update.md
│   │       ├── feature-update.md
│   │       └── story-update.md
│   ├── status/
│   │   └── SKILL.md
│   ├── reconcile/
│   │   └── SKILL.md
│   ├── retro/
│   │   └── SKILL.md
│   └── capture/
│       └── SKILL.md
└── agents/
    (defined in future tasks)

.claude/sdlc/
├── prd/
│   └── (PRD.md created by sdlc:create prd)
├── pi/
│   ├── (PI.md created by sdlc:create pi)
│   └── completed/
├── drafts/
└── retros/
```

**Files to remove** (v1 skills — after plugin is verified working):
```
.claude/skills/create-prd/
.claude/skills/update-prd/
.claude/skills/plan-increment/
.claude/skills/update-pi/
.claude/skills/close-pi/
.claude/skills/create-epic/
.claude/skills/create-feature/
.claude/skills/detail-story/
.claude/skills/update-epic/
.claude/skills/update-feature/
.claude/skills/update-story/
.claude/skills/pick-task/
.claude/skills/sync-issues/
.claude/skills/update-decision/
```

**Files to modify:**
- `CLAUDE.md` — update Skills section, workflow references, artifact paths
- `docs/SDLC-GUIDE.md` — update to reflect v2 plugin commands

---

### Task 1: Plugin Scaffold + Capture Skill

The simplest task — creates the plugin manifest, directory structure, and the capture skill (smallest skill, validates the plugin loads correctly).

**Files:**
- Create: `.claude/plugins/sdlc/plugin.json`
- Create: `.claude/plugins/sdlc/skills/capture/SKILL.md`
- Create: `.claude/sdlc/prd/.gitkeep`
- Create: `.claude/sdlc/pi/completed/.gitkeep`
- Create: `.claude/sdlc/drafts/.gitkeep`
- Create: `.claude/sdlc/retros/.gitkeep`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p .claude/plugins/sdlc/skills/capture
mkdir -p .claude/plugins/sdlc/agents
mkdir -p .claude/sdlc/prd
mkdir -p .claude/sdlc/pi/completed
mkdir -p .claude/sdlc/drafts
mkdir -p .claude/sdlc/retros
```

- [ ] **Step 2: Create plugin.json**

Write `.claude/plugins/sdlc/plugin.json`:

```json
{
  "name": "sdlc",
  "description": "Software Development Lifecycle plugin — define, create, update, track, and retrospect on work items using GitHub Issues and git-versioned artifacts.",
  "version": "2.0.0"
}
```

- [ ] **Step 3: Create sdlc:capture SKILL.md**

Write `.claude/plugins/sdlc/skills/capture/SKILL.md`.

This skill is fire-and-forget: one-liner input → GitHub issue with `triage` label. No context loading, no brainstorming phases. Read the spec section "sdlc:capture — Quick Capture" (lines 649-670) for the exact behavior.

Key requirements:
- Frontmatter: name `capture`, description starts with "Use when", argument-hint `"<one-line description>"`
- No context loading — explicitly state this
- Creates issue via `gh issue create --title "$ARGUMENTS" --label "triage" --body "..."`
- Reports the issue number
- Mentions that `sdlc:reconcile` flags triage issues older than 14 days

- [ ] **Step 4: Create .gitkeep files for artifact directories**

```bash
touch .claude/sdlc/prd/.gitkeep
touch .claude/sdlc/pi/completed/.gitkeep
touch .claude/sdlc/drafts/.gitkeep
touch .claude/sdlc/retros/.gitkeep
```

- [ ] **Step 5: Verify plugin loads**

```bash
claude --plugin-dir .claude/plugins/sdlc --print-plugins 2>&1 | head -20
```

If `--print-plugins` doesn't exist, try: `claude --plugin-dir .claude/plugins/sdlc -p "list your available skills that start with sdlc"` to verify the skill appears.

- [ ] **Step 6: Commit**

```bash
git add .claude/plugins/sdlc/ .claude/sdlc/
git commit -m "feat(sdlc): scaffold plugin structure and capture skill

Create the sdlc plugin with plugin.json manifest and the simplest
skill (sdlc:capture) to validate the plugin loads correctly.
Also create .claude/sdlc/ artifact directory structure.

Refs #121"
```

---

### Task 2: `sdlc:define` — Core SKILL.md

The brainstorming engine. This is the most complex skill — it has the 5-phase flow, scope assessment criteria, post-discovery gate, and support for both new artifacts and reshaping existing ones.

**Files:**
- Create: `.claude/plugins/sdlc/skills/define/SKILL.md`

- [ ] **Step 1: Create skill directory**

```bash
mkdir -p .claude/plugins/sdlc/skills/define/reference
```

- [ ] **Step 2: Write SKILL.md**

Write `.claude/plugins/sdlc/skills/define/SKILL.md`.

Read the spec section "sdlc:define — The Brainstorming Engine" (lines 132-254) for the complete flow definition.

Key requirements for the SKILL.md (must stay under 500 lines):
- Frontmatter: name `define`, description "Use when defining new SDLC artifacts (PRD, PI, epic, feature, story) or reshaping existing ones through collaborative brainstorming", allowed-tools "Read, Edit, Write, Bash, Grep, Glob, Agent", argument-hint `"[level] [identifier]"`
- **Phase 0: Context Loading** — parse level from argument, load reference guide via `Read ${CLAUDE_PLUGIN_ROOT}/skills/define/reference/<level>-guide.md`, read upstream artifacts per level
- **Phase 1: Scope Assessment** — state that criteria are in the reference guide, output assessment visibly (LIGHT/STANDARD/DEEP)
- **Phase 2: Discovery** — depth-specific question counts, subagent dispatch for DEEP
- **Post-Discovery Gate** — re-evaluate scope, upgrade only up, max one upgrade
- **Phase 3: Approaches** — depth-specific option counts
- **Phase 4: Draft** — produce file at `.claude/sdlc/drafts/<level>-<name>.md`, include frontmatter format, mention `## Changes` section for reshapes
- **Phase 5: Review** — present, iterate, different prompts for new vs reshape
- **Red Flags table** — anti-rationalization (like superpowers skills)
- **Feature level is optional** — ask when defining an epic

The SKILL.md should NOT contain the level-specific scope criteria, question templates, or draft body templates — those go in the reference files (Task 3).

- [ ] **Step 3: Verify file is under 500 lines**

```bash
wc -l .claude/plugins/sdlc/skills/define/SKILL.md
```

- [ ] **Step 4: Commit**

```bash
git add .claude/plugins/sdlc/skills/define/SKILL.md
git commit -m "feat(sdlc): add sdlc:define core skill

5-phase brainstorming flow with mandatory gates, variable depth
(LIGHT/STANDARD/DEEP), post-discovery scope upgrade, and
anti-rationalization tables.

Refs #121"
```

---

### Task 3: `sdlc:define` — Reference Guides (5 files)

The level-specific intelligence for each artifact type. Each reference guide contains: scope assessment criteria, question templates, draft body template, and greenfield/brownfield guidance where applicable.

**Files:**
- Create: `.claude/plugins/sdlc/skills/define/reference/prd-guide.md`
- Create: `.claude/plugins/sdlc/skills/define/reference/pi-guide.md`
- Create: `.claude/plugins/sdlc/skills/define/reference/epic-guide.md`
- Create: `.claude/plugins/sdlc/skills/define/reference/feature-guide.md`
- Create: `.claude/plugins/sdlc/skills/define/reference/story-guide.md`

- [ ] **Step 1: Write prd-guide.md**

Must contain:
- **Scope criteria** for PRD (LIGHT: minor section update; STANDARD: new section or major revision; DEEP: full PRD from scratch)
- **Greenfield detection**: check if `.claude/sdlc/prd/PRD.md` exists and if codebase has code
- **Greenfield interview questions** (10): project name, overview, tech stack, architecture, data models, API contracts, security constraints, roadmap, acceptance criteria, out of scope
- **Brownfield questions**: scan codebase first (package.json, pyproject.toml, directory structure), propose structure, ask targeted gaps
- **Draft body template**: PRD.md sections with YAML frontmatter (name, version, created)
- **Decision Log format**: date, decision, reason, affected section

- [ ] **Step 2: Write pi-guide.md**

Must contain:
- **Scope criteria** for PI (LIGHT: small PI with 1-2 epics; STANDARD: 3-4 epics; DEEP: large PI with complex dependencies)
- **Context to read**: PRD roadmap section, previous PI retro if available
- **Questions to ask**: which roadmap items for this PI, theme, target date, epics and their features
- **Draft body template**: PI.md with frontmatter (name: PI-N, theme, started, target, status: active), Goals, Epics section with features, Dependency Graph, Worktree Strategy
- **PI archival**: if active PI exists, note that `sdlc:create pi` will handle archiving

- [ ] **Step 3: Write epic-guide.md**

Must contain:
- **Scope criteria** (from spec lines 161-178): DEEP if 3+ areas, new patterns, cross-epic deps, 5+ features; STANDARD if 2-3 features; LIGHT if 1-2 features, existing patterns
- **Context to read**: PI.md, PRD.md
- **Questions**: overview, success criteria (measurable checkboxes), features breakdown, non-goals, priority, area labels, dependencies
- **Feature level optional**: if fewer than ~8 stories, ask if features are needed or flat stories under epic
- **Draft body template**: Overview, Success Criteria, Features (checklist with `#TBD`), Non-goals, Dependencies (Blocked by/Blocks), parent link

- [ ] **Step 4: Write feature-guide.md**

Must contain:
- **Scope criteria**: DEEP if 5+ stories, cross-feature deps, new patterns; STANDARD if 3-4 stories; LIGHT if 1-2 stories
- **Context to read**: parent epic issue, PI.md, PRD.md
- **Questions**: description (2-3 paragraphs), story breakdown, non-goals, dependencies
- **Draft body template**: Description, Stories (checklist with `#TBD`), Non-goals, Dependencies, Parent (Epic link)

- [ ] **Step 5: Write story-guide.md**

Must contain:
- **Scope criteria** (from spec lines 180-198): DEEP if 4+ files, new patterns, 3+ blockers, bug with unclear cause; STANDARD if 2-3 files; LIGHT if 1 file, clear pattern, 0 blockers
- **Context to read**: parent feature, parent epic, PRD (security constraints, data models, API contracts)
- **Questions**: description, acceptance criteria (3-7 testable checkboxes), file scope (new/modified files with exact paths), technical notes, dependencies
- **Draft body template**: Description, Acceptance Criteria, File Scope (New/Modify), Technical Notes, Dependencies (Blocked by/Blocks), Parent (Epic + Feature links)

- [ ] **Step 6: Commit**

```bash
git add .claude/plugins/sdlc/skills/define/reference/
git commit -m "feat(sdlc): add define reference guides for all 5 levels

Level-specific scope criteria, question templates, draft body
templates, and greenfield/brownfield guidance for PRD, PI, epic,
feature, and story.

Refs #121"
```

---

### Task 4: `sdlc:create` — Core SKILL.md + Reference Files

The execution engine. Reads drafts, validates, pushes to GitHub or git.

**Files:**
- Create: `.claude/plugins/sdlc/skills/create/SKILL.md`
- Create: `.claude/plugins/sdlc/skills/create/reference/prd-execution.md`
- Create: `.claude/plugins/sdlc/skills/create/reference/pi-execution.md`
- Create: `.claude/plugins/sdlc/skills/create/reference/epic-execution.md`
- Create: `.claude/plugins/sdlc/skills/create/reference/feature-execution.md`
- Create: `.claude/plugins/sdlc/skills/create/reference/story-execution.md`

- [ ] **Step 1: Create directories**

```bash
mkdir -p .claude/plugins/sdlc/skills/create/reference
```

- [ ] **Step 2: Write SKILL.md**

Read spec lines 258-326 for the complete flow.

Key requirements:
- Frontmatter: name `create`, description "Use when a draft from sdlc:define is ready to be pushed to GitHub or git", allowed-tools "Read, Bash, Grep, Glob", argument-hint `"[level] [name]"`
- Step 1: Locate draft in `.claude/sdlc/drafts/`, handle multiple drafts of same level
- Step 2: Validate with 3-tier routing (FIX INLINE / REOPEN DRAFT / ESCALATE TO DEFINE)
- Step 3: Execute — load level-specific reference via `Read ${CLAUDE_PLUGIN_ROOT}/skills/create/reference/<level>-execution.md`
- Step 4: Report & cleanup (ask to delete draft, mention stale draft flagging)
- Key property: never asks creative questions

- [ ] **Step 3: Write prd-execution.md**

Must contain:
- Required fields validation checklist for PRD draft
- Exact steps: write draft to `.claude/sdlc/prd/PRD.md`, git add, git commit with `docs(prd): create PRD v1.0`
- For updates: note version bump convention

- [ ] **Step 4: Write pi-execution.md**

Must contain:
- Required fields validation for PI draft
- **PI archival flow** (if active PI exists): read current PI, move to `.claude/sdlc/pi/completed/PI-N.md`, read PRD decision log, bake decisions into PRD body sections, bump PRD version, wipe decision log, commit PRD changes, commit PI archive, git tag `pi-N-complete`
- New PI creation: write to `.claude/sdlc/pi/PI.md`, git commit `docs(pi): create PI-N plan`

- [ ] **Step 5: Write epic-execution.md**

Must contain:
- Required fields validation for epic draft
- Exact `gh issue create` command with labels, body from draft. Reference `gh-cli-research/02-issue-management.md` for the heredoc/body-file pattern.
- Stub child creation: for each feature (or story if flat), create stub issues with minimal body, parent link, and `status:todo` label
- Bidirectional dep linking: if epic has `Blocked by`, update those issues' `Blocks` sections
- PI.md update: replace `#TBD` placeholders with real issue numbers
- Git commit for PI.md: `docs(pi): add issue numbers for epic [name]`

- [ ] **Step 6: Write feature-execution.md**

Similar to epic but:
- Creates feature issue with parent epic link
- Creates stub story issues under it
- Updates parent epic's Features checklist with real issue numbers

- [ ] **Step 7: Write story-execution.md**

Simplest execution:
- Creates single story issue with full body from draft
- No children to create
- Updates parent feature's Stories checklist
- Applies status labels based on blocker satisfaction check
- Bidirectional dep linking

- [ ] **Step 8: Verify all files under line limits and commit**

```bash
wc -l .claude/plugins/sdlc/skills/create/SKILL.md
git add .claude/plugins/sdlc/skills/create/
git commit -m "feat(sdlc): add sdlc:create skill with execution references

Execution engine that reads drafts and pushes to GitHub/git.
Includes validation routing, PI archival flow, stub child creation,
and bidirectional dependency linking.

Refs #121"
```

---

### Task 5: `sdlc:update` — Core SKILL.md + Reference Files

The surgical editor with smart routing.

**Files:**
- Create: `.claude/plugins/sdlc/skills/update/SKILL.md`
- Create: `.claude/plugins/sdlc/skills/update/reference/prd-update.md`
- Create: `.claude/plugins/sdlc/skills/update/reference/pi-update.md`
- Create: `.claude/plugins/sdlc/skills/update/reference/epic-update.md`
- Create: `.claude/plugins/sdlc/skills/update/reference/feature-update.md`
- Create: `.claude/plugins/sdlc/skills/update/reference/story-update.md`

- [ ] **Step 1: Create directories**

```bash
mkdir -p .claude/plugins/sdlc/skills/update/reference
```

- [ ] **Step 2: Write SKILL.md**

Read spec lines 330-402 for the complete flow.

Key requirements:
- Frontmatter: name `update`, description "Use when modifying existing SDLC artifacts on GitHub or in git — surgical edits for small changes, escalation to sdlc:define for large ones", allowed-tools "Read, Edit, Write, Bash, Grep, Glob", argument-hint `"[level] [identifier]"`
- Step 1: Load current state — check for reshape draft first, then fetch from GitHub/git
- Step 2: Understand the change (skip if reshape draft loaded)
- Step 3: Assess magnitude — TWO TIERS ONLY (DIRECT UPDATE / ESCALATE TO DEFINE), objective criteria
- Step 4: Execute — side-by-side diff for direct, invoke sdlc:define for escalation
- Step 5: Cascade logic — flag affected children/parents
- Anti-rationalization: "Two tiers only. No fuzzy middle ground."

- [ ] **Step 3: Write prd-update.md**

Must contain:
- **DIRECT criteria**: 1-2 sections changing (e.g., update a decision log entry, tweak a description)
- **ESCALATE criteria**: new section, structural rewrite, version bump
- **Edit pattern**: read `.claude/sdlc/prd/PRD.md`, make changes, git commit `docs(prd): [description]`
- **Decision log**: how to add a row (date, decision, reason, affected section)
- **Cascade**: flag if decision affects PI plan or open issues

- [ ] **Step 4: Write pi-update.md**

Must contain:
- **DIRECT criteria**: date change, status update, single epic/feature rename
- **ESCALATE criteria**: epic add/remove, dependency graph restructure, rescoping
- **Edit pattern**: read `.claude/sdlc/pi/PI.md`, make changes, git commit `docs(pi): [description]`
- **Cascade**: flag affected epics/features in GitHub Issues

- [ ] **Step 5: Write epic-update.md**

Must contain:
- **DIRECT criteria**: priority change, description tweak, single label change
- **ESCALATE criteria**: feature add/remove, scope change, success criteria rewrite
- **Edit pattern**: `gh issue view` to fetch body, modify section, `gh issue edit --body` with full body. Reference `gh-cli-research/02-issue-management.md` for the read-modify-write pattern.
- **Label commands**: `gh issue edit --add-label --remove-label` for status/priority changes
- **Cascade**: flag child features/stories, update PI.md if epic structure changed
- **Dep updates**: bidirectional `Blocked by`/`Blocks` maintenance, circular dep check

- [ ] **Step 6: Write feature-update.md**

Must contain:
- **DIRECT criteria**: description edit, single field change
- **ESCALATE criteria**: story add/remove, scope expansion
- **Edit pattern**: same read-modify-write as epic, `gh issue edit --body`
- **Cascade**: flag child stories, update parent epic's features checklist
- **Dep updates**: bidirectional linking, blocker satisfaction check

- [ ] **Step 7: Write story-update.md**

Must contain:
- **DIRECT criteria**: AC edit, priority change, technical notes update, file scope change
- **ESCALATE criteria**: scope expansion (new files/areas), fundamental rework
- **Edit pattern**: `gh issue edit --body` with read-modify-write
- **Dep updates**: bidirectional `Blocked by`/`Blocks`, circular dep detection (DFS walk), status label recalculation
- **Cascade**: update parent feature's story checklist if title changed

- [ ] **Step 8: Commit**

```bash
git add .claude/plugins/sdlc/skills/update/
git commit -m "feat(sdlc): add sdlc:update skill with surgical edit references

Smart routing: direct edits for 1-2 field changes, escalation to
sdlc:define for structural changes. Includes cascade logic and
bidirectional dependency maintenance.

Refs #121"
```

---

### Task 6: `sdlc:status` — Situational Awareness

**Files:**
- Create: `.claude/plugins/sdlc/skills/status/SKILL.md`

- [ ] **Step 1: Create directory**

```bash
mkdir -p .claude/plugins/sdlc/skills/status
```

- [ ] **Step 2: Write SKILL.md**

Read spec lines 406-475 for the complete flow.

Key requirements:
- Frontmatter: name `status`, description "Use to get a project status briefing — what's in progress, blocked, ready, and what can run in parallel", allowed-tools "Read, Bash, Grep, Glob", argument-hint `"[area or 'epic #N']"`
- Step 1: Determine scope (full PI / area filter / specific artifact)
- Step 2: Gather state — include exact `gh issue list` commands with `--json` and `--jq` filters from `gh-cli-research/02-issue-management.md`. Also scan `.claude/sdlc/drafts/` for stale drafts.
- Step 3: Analyze — in progress, blocked (with root blocker tracing), ready (ranked by priority), parallelization analysis, stale detection
- Step 4: Present briefing (include the example output format from the spec)
- Step 5: Offer next action
- This skill should have the exact `gh` commands baked in, not just references to research docs

- [ ] **Step 3: Commit**

```bash
git add .claude/plugins/sdlc/skills/status/
git commit -m "feat(sdlc): add sdlc:status situational awareness skill

Full project briefing with root blocker tracing, parallelization
analysis, stale draft detection, and priority-ranked recommendations.

Refs #121"
```

---

### Task 7: `sdlc:reconcile` — Label Hygiene

**Files:**
- Create: `.claude/plugins/sdlc/skills/reconcile/SKILL.md`

- [ ] **Step 1: Create directory**

```bash
mkdir -p .claude/plugins/sdlc/skills/reconcile
```

- [ ] **Step 2: Write SKILL.md**

Read spec lines 479-541 for the complete flow.

Key requirements:
- Frontmatter: name `reconcile`, description "Use to fix label drift in GitHub issues — stale labels, unclosed parents, orphaned references, circular dependencies", allowed-tools "Read, Bash, Grep, Glob", argument-hint `"[area]"`
- Step 1: Scan — exact `gh` commands for fetching all issues, building hierarchy
- Step 2: Detect problems by severity (CRITICAL/WARNING/INFO) — all categories from spec
- Parent completion rule: ALL children have `status:done` AND are `CLOSED`
- Step 3: Present findings (include example output format)
- Step 4: Execute on confirmation — individual parallel `gh issue edit` commands
- Step 5: Flag what it can't fix — redirect to sdlc:update
- Include the `triage` issues older than 14 days check

- [ ] **Step 3: Commit**

```bash
git add .claude/plugins/sdlc/skills/reconcile/
git commit -m "feat(sdlc): add sdlc:reconcile label hygiene skill

Scans issue hierarchy, detects circular deps, stale labels,
unclosed parents, blocker mismatches. Applies fixes as individual
parallel gh issue edit commands.

Refs #121"
```

---

### Task 8: `sdlc:retro` — Process Retrospective

**Files:**
- Create: `.claude/plugins/sdlc/skills/retro/SKILL.md`

- [ ] **Step 1: Create directory**

```bash
mkdir -p .claude/plugins/sdlc/skills/retro
```

- [ ] **Step 2: Write SKILL.md**

Read spec lines 545-644 for the complete flow.

Key requirements:
- Frontmatter: name `retro`, description "Use to run a process retrospective on a completed PI, epic, or feature — analyzes what went well and what needs improvement", allowed-tools "Read, Bash, Grep, Glob, Agent", argument-hint `"[pi | epic #N | feature #N]"`
- Early exit: if no closed stories in scope
- Step 2: Gather metrics — include exact commands from `gh-cli-research/03-timeline-and-metrics.md` and `gh-cli-research/04-git-analytics.md`. Key commands: `gh issue list` for planned vs delivered, `gh api` Timeline endpoint for label events (time-in-status), `gh pr view` for lead time and review compliance, `git log` for commit cadence and hotspots
- Step 3: Analyze patterns — flow efficiency, lead time outliers, dependency accuracy, hot areas, review discipline
- Step 4: Produce retro document at `.claude/sdlc/retros/<scope>-<date>.md` with the template from the spec
- Step 5: Offer next steps
- Note deferred metrics (scope change frequency, depth distribution, estimation accuracy)

- [ ] **Step 3: Commit**

```bash
git add .claude/plugins/sdlc/skills/retro/
git commit -m "feat(sdlc): add sdlc:retro process retrospective skill

Process-focused retrospective using GitHub Timeline API and git
analytics. Produces retro document with metrics, patterns, and
recommendations for next PI.

Refs #121"
```

---

### Task 9: Cleanup — Remove v1 Skills + Update Docs

**Files:**
- Remove: all 14 directories under `.claude/skills/` (v1 skills)
- Modify: `CLAUDE.md`
- Modify: `docs/SDLC-GUIDE.md`

- [ ] **Step 1: Remove v1 skill directories**

```bash
git rm -r .claude/skills/create-prd/
git rm -r .claude/skills/update-prd/
git rm -r .claude/skills/plan-increment/
git rm -r .claude/skills/update-pi/
git rm -r .claude/skills/close-pi/
git rm -r .claude/skills/create-epic/
git rm -r .claude/skills/create-feature/
git rm -r .claude/skills/detail-story/
git rm -r .claude/skills/update-epic/
git rm -r .claude/skills/update-feature/
git rm -r .claude/skills/update-story/
git rm -r .claude/skills/pick-task/
git rm -r .claude/skills/sync-issues/
git rm -r .claude/skills/update-decision/
```

Note: keep non-SDLC skills (if any exist in `.claude/skills/`).

- [ ] **Step 2: Update CLAUDE.md**

Read current `CLAUDE.md` and update:
- **Skills section**: replace v1 skill listing with v2 plugin skills (`sdlc:define`, `sdlc:create`, `sdlc:update`, `sdlc:status`, `sdlc:reconcile`, `sdlc:retro`, `sdlc:capture`)
- **Workflow section**: update "Read the spec" to "Read the PRD and PI Plan" with new paths (`.claude/sdlc/prd/PRD.md`, `.claude/sdlc/pi/PI.md`)
- **Reference Docs section**: update SPEC.md reference to PRD path
- **Decision Workflow section**: update to reference `sdlc:update prd`
- Add a "Plugin Loading" subsection under **Commands** with: `claude --plugin-dir .claude/plugins/sdlc` and the alias tip `alias cc='claude --plugin-dir .claude/plugins/sdlc'`

- [ ] **Step 3: Update docs/SDLC-GUIDE.md**

Read current guide and update all skill references from v1 to v2 names. See spec section "What This Replaces" (lines 709-724) for the exact v1 → v2 mapping. Update artifact paths from `.claude/prd/` to `.claude/sdlc/prd/`, `.claude/pi/` to `.claude/sdlc/pi/`, etc. Update the lifecycle flow diagram to use v2 skill names.

- [ ] **Step 4: Migrate existing artifacts if they exist**

If `.claude/prd/PRD.md` exists, move to `.claude/sdlc/prd/PRD.md`.
If `.claude/pi/PI.md` exists, move to `.claude/sdlc/pi/PI.md`.
If `.claude/pi/completed/` has files, move to `.claude/sdlc/pi/completed/`.

```bash
# Only run if files exist:
git mv .claude/prd/PRD.md .claude/sdlc/prd/PRD.md 2>/dev/null || true
git mv .claude/pi/PI.md .claude/sdlc/pi/PI.md 2>/dev/null || true
git mv .claude/pi/completed/ .claude/sdlc/pi/completed/ 2>/dev/null || true
```

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "refactor(sdlc): replace v1 skills with v2 plugin, update docs

Remove 14 v1 local skills, update CLAUDE.md and SDLC-GUIDE.md
to reference v2 plugin skills (sdlc:define, sdlc:create, etc.),
migrate artifacts to .claude/sdlc/.

Refs #121"
```

---

## Implementation Notes

### Skill Writing Guidelines

When writing each SKILL.md:

1. **Frontmatter**: `name`, `description` (starts with "Use when"), `allowed-tools`, `argument-hint`
2. **Announce at start**: "I'm using the sdlc:[name] skill to [action]."
3. **Use `${CLAUDE_PLUGIN_ROOT}`** for referencing files within the plugin
4. **Include a Red Flags table** for discipline-enforcing skills (define, create, update)
5. **Include exact `gh` commands** — don't say "query GitHub", say the exact command with `--json` fields and `--jq` filters
6. **Reference research docs** where the command is complex — "See gh-cli-research/02-issue-management.md section X for the full command"
7. **Anti-rationalization**: for each mandatory gate, include specific negations of rationalizations the LLM might use

### Dependency Model (shared across all skills)

Blocker satisfaction rule (copy into every skill that checks dependencies):
- Satisfied: issue has `status:done` label OR issue state is `CLOSED`
- Unmet: issue is `OPEN` without `status:done`

Circular dependency detection (copy into define, create, update, reconcile):
- Walk `Blocked by` chain via DFS
- If walk reaches original issue, flag cycle, do NOT save

### Label Taxonomy (for reference in create/update/reconcile)

```
type:epic, type:feature, type:story
status:todo, status:in-progress, status:done, status:blocked
priority:critical, priority:high, priority:medium, priority:low
area:auth, area:api, area:agents, area:ui, area:infra, area:search
triage
```

Status labels are mutually exclusive — always remove old status when adding new.

### Execution Order

Tasks should be executed in order (1-9). Each task produces a working increment:
- After Task 1: plugin loads, capture works
- After Tasks 2-3: define works (brainstorming)
- After Task 4: create works (full define → create flow)
- After Task 5: update works (surgical edits)
- After Tasks 6-8: status, reconcile, retro work
- After Task 9: v1 removed, docs updated, migration complete
