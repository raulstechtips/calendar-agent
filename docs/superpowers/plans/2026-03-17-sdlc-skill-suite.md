# SDLC Skill Suite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure project tooling from SPEC.md to PRD + PI Plan and build 13 skills covering the full SDLC lifecycle.

**Architecture:** All skills are markdown SKILL.md files in `.claude/skills/`. No code — pure process automation via Claude Code's skill system. Migration moves SPEC.md content to PRD.md + PI.md and updates all references.

**Tech Stack:** GitHub CLI (`gh`), git, markdown with YAML frontmatter.

**Spec:** `docs/superpowers/specs/2026-03-17-sdlc-skill-suite-design.md`

---

## File Structure

### New files to create
- `.claude/prd/PRD.md` — migrated from SPEC.md (product requirements only)
- `.claude/pi/PI.md` — migrated from SPEC.md (implementation phases only)
- `.claude/skills/create-prd/SKILL.md`
- `.claude/skills/update-prd/SKILL.md`
- `.claude/skills/plan-increment/SKILL.md`
- `.claude/skills/update-pi/SKILL.md`
- `.claude/skills/close-pi/SKILL.md`
- `.claude/skills/create-epic/SKILL.md`
- `.claude/skills/create-feature/SKILL.md`
- `.claude/skills/detail-story/SKILL.md`
- `.claude/skills/update-epic/SKILL.md`
- `.claude/skills/update-feature/SKILL.md`
- `.claude/skills/update-story/SKILL.md`

### Files to modify
- `.claude/skills/pick-task/SKILL.md` — rewrite with dependency model
- `.claude/skills/sync-issues/SKILL.md` — rewrite with hierarchy validation
- `.claude/skills/update-decision/SKILL.md` — deprecation redirect
- `CLAUDE.md` — update all SPEC references, skills section, decision workflow
- `.claude/rules/workflow.md` — update spec references
- `.claude/rules/git.md` — add tag convention
- `.claude/agents/code-reviewer.md` — update spec path

### Files to delete
- `.claude/specs/in-progress/SPEC.md` (after migration)
- `.claude/specs/` directory tree (after migration)

### Files NOT changed (out of scope)
- `docs/HUMAN-WORKFLOW.md` — needs a full rewrite, separate task
- `docs/CLAUDE-CODE-INFRASTRUCTURE-GUIDE.md` — archival doc, references are historical
- `docs/AUDIT-2026-03-17.md` — archival doc
- `docs/archive/*` — archived, no updates needed

---

## Task 1: Migrate SPEC.md → PRD.md

**Files:**
- Create: `.claude/prd/PRD.md`
- Source: `.claude/specs/in-progress/SPEC.md`

This is a content migration, not a rewrite. Take the existing SPEC.md, add YAML frontmatter, remove the "Implementation Phases" section (that becomes the PI Plan), and clean up.

- [ ] **Step 1: Create the prd directory**

```bash
mkdir -p .claude/prd
```

- [ ] **Step 2: Create PRD.md from SPEC.md**

Copy `.claude/specs/in-progress/SPEC.md` to `.claude/prd/PRD.md`. Then make these changes:

1. Add YAML frontmatter at the top:
```yaml
---
name: AI Calendar Assistant
version: 1.0
created: 2026-03-14
---
```

2. Change the title from "MVP Implementation Spec" to "Product Requirements Document"

3. Remove the entire "## Implementation Phases (mapped to GitHub Issues)" section (lines 565-633 of original SPEC.md) — this content moves to PI.md in Task 2

4. Remove the "## Phase 2: Enhancement (Roadmap)" header and rename it to just "## Roadmap" — keep the content (workstreams 2.1-2.5) but strip the "Phase 2:" prefix from the section heading

5. Rename the "## Decision Log" table — add the `Affects` column:
```markdown
## Decision Log
| Date | Decision | Reason | Affects |
|------|----------|--------|---------|
```
Keep all existing rows, add `Affects` value where obvious (e.g., "Architecture" for auth decisions), leave blank otherwise.

6. Update the "langchain-google-community" reference in the Architecture Decisions if it still appears in the body (the decision log already has the superseding entry, but if the agent tools table still references it, update to "custom @tool")

- [ ] **Step 3: Verify PRD.md**

```bash
head -5 .claude/prd/PRD.md  # should show frontmatter
grep -c "Implementation Phases" .claude/prd/PRD.md  # should be 0
grep -c "## Roadmap" .claude/prd/PRD.md  # should be 1
```

- [ ] **Step 4: Commit**

```bash
git add .claude/prd/PRD.md
git commit -m "docs(prd): migrate SPEC.md to PRD.md with frontmatter and cleanup"
```

---

## Task 2: Create PI.md from SPEC.md Implementation Phases

**Files:**
- Create: `.claude/pi/PI.md`
- Create: `.claude/pi/completed/` (empty directory)
- Source: `.claude/specs/in-progress/SPEC.md` lines 565-633

- [ ] **Step 1: Create directories**

```bash
mkdir -p .claude/pi/completed
```

- [ ] **Step 2: Create PI.md**

Create `.claude/pi/PI.md` with this structure. Pull the epic/feature/story structure from the "Implementation Phases" section of SPEC.md, but reformat to PI Plan format:

```markdown
---
name: PI-1
theme: "MVP — AI Calendar Assistant"
started: 2026-03-14
target: 2026-03-17
status: active
---

# PI-1: MVP — AI Calendar Assistant

## Goals
Ship a functional AI calendar assistant: Google OAuth, chat with LangGraph agent, calendar CRUD with human-in-the-loop confirmation, deployed to Azure Container Apps.

## Epics

### Epic: Auth & Google OAuth (#2)
**Features:**
- [ ] Google OAuth with refresh tokens (#2 → stories #8, #9, #10, #11, #13, #59, #67)

### Epic: FastAPI Backend Core (#3)
**Features:**
- [ ] Backend scaffold + middleware (#3 → stories #12, #14, #31)

### Epic: LangGraph Agent Pipeline (#4)
**Features:**
- [ ] Agent setup + calendar tools (#4 → stories #16, #17, #18, #19)

### Epic: Azure AI Search Integration (#5)
**Features:**
- [ ] Search index + embedding pipeline (#5 → stories #20, #21, #22)

### Epic: Frontend Chat & Calendar UI (#6)
**Features:**
- [ ] Chat UI + calendar view (#6 → stories #23, #24)

### Epic: Infrastructure & Deployment (#7)
**Features:**
- [ ] Terraform modules + Container Apps (#7 → stories #47, #48, #49, #50, #51, #64, #71)

## Dependency Graph
- Backend scaffold (#12) → blocks Redis (#14), agent setup (#16), user endpoints (#13), token storage (#10)
- Google OAuth (#9) → blocks auth proxy (#11), backend verification (#59)
- Backend verification (#59) → blocks calendar tools (#17), ingestion (#15)
- Search index (#20) → blocks embedding pipeline (#21) → blocks search tool (#22)
- Prompt defense (#18) → must precede content safety (#19)
- All code stories → block Dockerfiles (#26) → blocks Container Apps (#50)

## Worktree Strategy
- Worktree A (Frontend): #8 → #9 → #11 → #23, #24
- Worktree B (Backend): #12 → #14, #13 → #10 → #59
- Worktree C (Agent): #16 → #17, #18 → #19, #22
- Worktree D (Infra): #47 → #48, #64, #71 → #49 → #50 → #51
```

Note: This is a retroactive PI Plan — PI-1 is mostly complete. The exact issue numbers are already known. This establishes the pattern for future PIs.

- [ ] **Step 3: Verify**

```bash
head -7 .claude/pi/PI.md  # should show frontmatter with PI-1
grep "status: active" .claude/pi/PI.md  # should match
```

- [ ] **Step 4: Create .gitkeep and commit**

```bash
touch .claude/pi/completed/.gitkeep
git add .claude/pi/PI.md .claude/pi/completed/.gitkeep
git commit -m "docs(pi): create PI-1 plan from SPEC.md implementation phases"
```

---

## Task 3: Remove old specs directory

**Files:**
- Delete: `.claude/specs/in-progress/SPEC.md`
- Delete: `.claude/specs/` directory tree

- [ ] **Step 1: Remove old spec and stage deletion**

```bash
git rm -r .claude/specs/
```

This removes the files from the working tree AND stages the deletion in one step.

- [ ] **Step 2: Verify**

```bash
ls .claude/specs 2>&1  # should fail with "No such file or directory"
ls .claude/prd/PRD.md  # should succeed
ls .claude/pi/PI.md    # should succeed
```

- [ ] **Step 3: Commit**

```bash
git commit -m "chore: remove old specs directory (migrated to prd/ and pi/)"
```

---

## Task 4: Update CLAUDE.md references

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update workflow section**

Change:
```
- Before writing code, read the active spec in `.claude/specs/in-progress/`
```
To:
```
- Before writing code, read the PRD at `.claude/prd/PRD.md` and the PI Plan at `.claude/pi/PI.md`
```

- [ ] **Step 2: Update Architecture Decisions**

Change:
```
- Agent: LangGraph ReAct via `create_react_agent` + `langchain-google-community` tools
```
To:
```
- Agent: LangGraph ReAct via `create_react_agent` + custom `@tool` functions (not langchain-google-community — incompatible with multi-user credentials)
```

- [ ] **Step 3: Update Skills section**

Replace the entire Skills section with:
```markdown
## Skills (Slash Commands)

### PRD & PI Management
- `/create-prd` — Bootstrap a new PRD for a new repo
- `/update-prd [section|decision]` — Record a design change or update a PRD section
- `/plan-increment [theme]` — Close previous PI + plan the next one
- `/update-pi [description]` — Update PI Plan when scope changes mid-sprint
- `/close-pi` — Archive current PI, bake decisions into PRD, tag

### Work Decomposition
- `/create-epic [name]` — Create detailed epic + stub feature issues on GitHub
- `/create-feature [#issue]` — Detail a feature + create stub story issues
- `/detail-story [#issue]` — Add full acceptance criteria, file scope, deps to a story

### Work Updates
- `/update-epic [#issue]` — Modify epic scope, add/remove features
- `/update-feature [#issue]` — Modify feature, add/remove stories
- `/update-story [#issue]` — Modify story AC, deps, file scope

### Execution
- `/pick-task [area]` — Find the next unblocked story to work on
- `/sync-issues [area]` — Audit issue hierarchy, fix stale labels, validate deps
- `/review-coderabbit [PR#]` — Fetch and triage CodeRabbit review comments
```

- [ ] **Step 4: Update Decision Workflow section**

Replace:
```markdown
## Decision Workflow

When a decision is made (by the user or during implementation):
1. Update SPEC.md first — it is the source of truth
2. Update affected GitHub issues if scope changes
3. CLAUDE.md only changes for new conventions or commands
```
With:
```markdown
## Decision Workflow

When a decision is made (by the user or during implementation):
1. Update PRD.md first — it is the source of truth. Use `/update-prd` to record decisions.
2. Update the PI Plan if scope changes affect the current increment
3. Update affected GitHub issues if story/feature scope changes
4. CLAUDE.md only changes for new conventions or commands
```

- [ ] **Step 5: Update Reference Docs section**

Replace:
```markdown
## Reference Docs

- SPEC.md (source of truth): `.claude/specs/in-progress/SPEC.md` — tech stack, versions, architecture, API contracts, data models, decisions log
- Human workflow: `docs/HUMAN-WORKFLOW.md` — how to launch agents, review, merge, manage the sprint
```
With:
```markdown
## Reference Docs

- PRD (source of truth): `.claude/prd/PRD.md` — tech stack, versions, architecture, API contracts, data models, decisions log
- PI Plan (current sprint): `.claude/pi/PI.md` — epics, features, dependency graph, worktree strategy
- Human workflow: `docs/HUMAN-WORKFLOW.md` — how to launch agents, review, merge, manage the sprint
- Design spec: `docs/superpowers/specs/2026-03-17-sdlc-skill-suite-design.md` — SDLC skill suite design
```

- [ ] **Step 6: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md references from SPEC.md to PRD.md + PI.md"
```

---

## Task 5: Update rule files and agents

**Files:**
- Modify: `.claude/rules/workflow.md`
- Modify: `.claude/rules/git.md`
- Modify: `.claude/agents/code-reviewer.md`

- [ ] **Step 1: Update workflow.md step 2 (line 12)**

Change:
```
2. **Read the spec**: `.claude/specs/in-progress/SPEC.md` — understand architecture context
```
To:
```
2. **Read the PRD and PI Plan**: Read `.claude/prd/PRD.md` (security constraints, data models, API contracts) and `.claude/pi/PI.md` (dependency context). Read the GitHub issue for detailed AC and file scope.
```

- [ ] **Step 2: Update workflow.md step 4 (line 14)**

Change:
```
4. **Plan thoroughly**: list files to create/modify, patterns to follow, and review the SPEC's Security Constraints section — for each constraint that applies to this story, note how the implementation will satisfy it
```
To:
```
4. **Plan thoroughly**: list files to create/modify, patterns to follow, and review the PRD's Security Constraints section — for each constraint that applies to this story, note how the implementation will satisfy it
```

- [ ] **Step 3: Update workflow.md "When to ask" section (line 33)**

Change:
```
- A dependency not in the spec needs to be added
```
To:
```
- A dependency not in the PRD needs to be added
```

- [ ] **Step 4: Update workflow.md "When to decide" section (line 38)**

Change:
```
- Implementation approach is clear from spec + existing patterns
```
To:
```
- Implementation approach is clear from PRD + PI Plan + existing patterns
```

- [ ] **Step 5: Add tag convention to git.md**

After the "Branch naming" section (after line 42), add:

```markdown

## PI tags

When a Program Increment (sprint) is closed, tag the commit:
- Format: `pi-N-complete` (e.g., `pi-1-complete`, `pi-2-complete`)
- Created by the `/close-pi` skill
- Local only by default — push with `git push origin pi-N-complete` if desired
```

- [ ] **Step 6: Update code-reviewer.md (line 15)**

Change:
```
3. **Spec adherence**: Compare implementation against `.claude/specs/in-progress/` — flag deviations
```
To:
```
3. **PRD adherence**: Compare implementation against `.claude/prd/PRD.md` — flag deviations from architecture, data models, API contracts, and security constraints
```

- [ ] **Step 7: Commit**

```bash
git add .claude/rules/workflow.md .claude/rules/git.md .claude/agents/code-reviewer.md
git commit -m "docs: update rule files and code-reviewer agent for PRD/PI references"
```

---

## Task 6: Write PRD skills — `/create-prd` and `/update-prd`

**Files:**
- Create: `.claude/skills/create-prd/SKILL.md`
- Create: `.claude/skills/update-prd/SKILL.md`

- [ ] **Step 1: Create create-prd skill**

Create `.claude/skills/create-prd/SKILL.md`:

```markdown
---
name: create-prd
description: Bootstrap a new Product Requirements Document for a new repo. Use when starting a brand new project that has no .claude/prd/PRD.md.
allowed-tools: Read, Write, Bash, Grep, Glob
---

# Create PRD

Bootstrap a new Product Requirements Document through a guided interview.

## Preflight

1. Check if `.claude/prd/PRD.md` already exists:
   ```bash
   ls .claude/prd/PRD.md 2>/dev/null
   ```
   If it exists, STOP — inform the user and suggest `/update-prd` instead.

2. Create the directory if needed:
   ```bash
   mkdir -p .claude/prd
   ```

## Guided Interview

Ask the user these questions ONE AT A TIME:

1. **Project name** — what is this project called?
2. **Overview** — one paragraph describing the product vision and purpose
3. **Tech stack** — what languages, frameworks, databases, and infrastructure? (List with versions if known)
4. **Architecture** — how do the services communicate? Draw a high-level diagram if appropriate.
5. **Data models** — what are the core entities? (Can be rough — will be refined)
6. **API contracts** — what are the key endpoints? (Can be rough)
7. **Security constraints** — what are the hard rules that must never be violated?
8. **Roadmap** — what are the planned workstreams beyond the first increment?
9. **Acceptance criteria** — what does "done" look like for the initial product?
10. **Out of scope** — what is explicitly NOT being built?

## Generate PRD

After the interview, generate `.claude/prd/PRD.md` with this structure:

```markdown
---
name: [Project Name]
version: 1.0
created: [today's date YYYY-MM-DD]
---

# [Project Name] — Product Requirements Document

## Overview
[From interview]

## Technology Stack & Versions
[From interview — formatted as table]

## Architecture
[From interview — include diagrams if provided]

## Data Models
[From interview]

## API Contracts
[From interview]

## Security Constraints
[From interview — numbered hard rules]

## Roadmap
[From interview — high-level workstreams]

## Acceptance Criteria
[From interview — checkboxes]

## Out of Scope
[From interview — bullet list]

## Decision Log
| Date | Decision | Reason | Affects |
|------|----------|--------|---------|
```

## Commit

```bash
git add .claude/prd/PRD.md
git commit -m "docs(prd): create initial PRD v1.0"
```
```

- [ ] **Step 2: Create update-prd skill**

Create `.claude/skills/update-prd/SKILL.md`:

```markdown
---
name: update-prd
description: Record a design change or update a PRD section. Replaces /update-decision. Use when the user makes a decision about how something should be built, or when a PRD section needs updating.
allowed-tools: Read, Edit, Write, Bash, Grep, Glob
argument-hint: "[decision description or section name to update]"
---

# Update PRD

Record a design decision or update a section of the Product Requirements Document.

## Preflight

1. Read the current PRD:
   ```bash
   cat .claude/prd/PRD.md
   ```
   If it doesn't exist, STOP — suggest `/create-prd` first.

2. Read the current PI Plan for context (if it exists):
   ```bash
   cat .claude/pi/PI.md 2>/dev/null
   ```

## Mode Detection

Determine the type of update from the user's argument:

### Mode A: Record a Decision

If the argument describes a decision (architecture choice, tech change, scope change, approach change):

1. Add a new row to the Decision Log table:
   ```
   | [today's date] | [decision] | [reason] | [affected PRD section] |
   ```

2. Do NOT modify the affected body section yet — decisions are baked into body sections only at PI close (`/close-pi`). The Decision Log is the buffer.

3. If the decision changes scope, check which GitHub Issues may be affected:
   ```bash
   gh issue list --state open --label "type:story" --limit 200 --json number,title,body \
     --jq '.[] | select(.body | test("KEYWORD"; "i")) | "#\(.number) \(.title)"'
   ```
   Report affected issues to the user but do NOT auto-update them — suggest `/update-story`, `/update-feature`, or `/update-epic` as appropriate.

4. If the decision supersedes a previous decision in the log, mark the old one:
   ```
   | [old date] | ~~old decision~~ **Superseded [today]** | ~~old reason~~ | [section] |
   ```

### Mode B: Update a PRD Section

If the argument names a section (e.g., "update API contracts", "update data models"):

1. Read the current section content
2. Present the proposed change to the user
3. On approval, edit the section using the Edit tool
4. If this changes scope, flag affected GitHub Issues (same as Mode A step 3)

## Commit

```bash
git add .claude/prd/PRD.md
git commit -m "docs(prd): [concise description of the change]"
```

## Rules

- The PRD is the source of truth — always update it FIRST
- Never delete decision history — mark old decisions as superseded with date and strikethrough
- If a decision affects the PI Plan, remind the user to run `/update-pi`
- If a decision affects GitHub Issues, list which ones and suggest the appropriate update skill
```

- [ ] **Step 3: Deprecate update-decision**

Replace the contents of `.claude/skills/update-decision/SKILL.md` with:

```markdown
---
name: update-decision
description: "DEPRECATED: Use /update-prd instead. This skill redirects to /update-prd."
allowed-tools: Read
---

# Deprecated

This skill has been replaced by `/update-prd`.

Run `/update-prd` instead — it records decisions to the PRD's Decision Log and can also update PRD sections directly.
```

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/create-prd/SKILL.md .claude/skills/update-prd/SKILL.md .claude/skills/update-decision/SKILL.md
git commit -m "feat(skills): add create-prd and update-prd skills, deprecate update-decision"
```

---

## Task 7: Write PI skills — `/plan-increment`, `/update-pi`, `/close-pi`

**Files:**
- Create: `.claude/skills/plan-increment/SKILL.md`
- Create: `.claude/skills/update-pi/SKILL.md`
- Create: `.claude/skills/close-pi/SKILL.md`

- [ ] **Step 1: Create plan-increment skill**

Create `.claude/skills/plan-increment/SKILL.md`:

```markdown
---
name: plan-increment
description: Plan the next Program Increment (sprint). Closes the previous PI if one exists, then creates a new PI Plan from the PRD roadmap. Use at the start of a new sprint or when beginning a new project.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
argument-hint: "[optional: theme for the new PI]"
---

# Plan Increment

Plan the next Program Increment. Handles both first-ever PI and subsequent PIs.

## Preflight

1. Check if PRD exists:
   ```bash
   ls .claude/prd/PRD.md 2>/dev/null
   ```
   If not, STOP — suggest `/create-prd` first.

2. Check if an active PI exists:
   ```bash
   grep "status: active" .claude/pi/PI.md 2>/dev/null
   ```

## Flow A: First PI (no active PI.md)

1. Read `.claude/prd/PRD.md` — focus on the Roadmap section
2. Ask the user: **Which workstreams from the Roadmap go into this PI?**
3. For each selected workstream, collaborate on epic decomposition:
   - Epic name and 1-line description
   - Features under this epic (titles + 1-line descriptions)
   - Rough stories under each feature (titles only — detail comes later via `/detail-story`)
4. Check: did any workstream turn out to be larger than expected? Should it split into multiple epics? Confirm with user.
5. Build the dependency graph:
   - Which epics/features block others?
   - Which can run in parallel?
6. Propose a worktree strategy based on the dependency graph
7. Auto-detect PI number:
   ```bash
   ls .claude/pi/completed/PI-*.md 2>/dev/null | wc -l
   ```
   Next PI = count + 1. If no completed PIs exist, start at PI-1.
8. Write `.claude/pi/PI.md`:

```markdown
---
name: PI-[N]
theme: "[theme from argument or discussion]"
started: [today's date YYYY-MM-DD]
target: [user-provided or suggested date]
status: active
---

# PI-[N]: [Theme]

## Goals
[2-3 sentences from the discussion]

## Epics

### Epic: [Name] (#TBD)
**Features:**
- [ ] [Feature name] (#TBD)
- [ ] [Feature name] (#TBD)

[repeat for each epic]

## Dependency Graph
[From step 5 — plain language, one line per dependency]

## Worktree Strategy
[From step 6 — which worktree handles which features]
```

9. Create the pi directory if needed:
   ```bash
   mkdir -p .claude/pi/completed
   ```

10. Commit:
    ```bash
    git add .claude/pi/PI.md
    git commit -m "docs(pi): create PI-[N] plan"
    ```

## Flow B: Subsequent PI (active PI.md exists)

1. Read current `.claude/pi/PI.md` and `.claude/prd/PRD.md`
2. Query GitHub Issues to assess current PI state:
   ```bash
   gh issue list --state closed --limit 200 --json number,title,labels \
     --jq '.[] | "#\(.number) \(.title) [\([.labels[].name] | join(", "))]"'
   gh issue list --state open --limit 200 --json number,title,labels \
     --jq '.[] | "#\(.number) \(.title) [\([.labels[].name] | join(", "))]"'
   ```
3. Present a retrospective summary:
   - What shipped (closed issues from this PI's epics)
   - What's still open (incomplete work — will carry over or be dropped)
   - Key decisions made during the PI (from PRD decision log)
4. Ask the user: what carries over vs. what gets dropped?
5. Run the `/close-pi` flow to close the current PI
6. Then run Flow A (steps 1-10) to plan the next PI

## Rules

- Always read the PRD Roadmap — the next PI should pull from planned workstreams
- One epic per major workstream — if a workstream is too large, split it
- Features are the unit of deliverable capability — each should be independently valuable
- Stories are rough at this stage — just titles. Detail comes via `/create-epic` → `/create-feature` → `/detail-story`
- The dependency graph drives the worktree strategy — don't assign worktrees without understanding blocking relationships
```

- [ ] **Step 2: Create update-pi skill**

Create `.claude/skills/update-pi/SKILL.md`:

```markdown
---
name: update-pi
description: Update the PI Plan when reality diverges mid-sprint — epic splits, feature moves, dependency changes, scope adjustments. Use when the plan needs to change.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
argument-hint: "[description of what changed]"
---

# Update PI

Update the PI Plan when scope, dependencies, or structure changes mid-sprint.

## Preflight

1. Read current PI Plan:
   ```bash
   cat .claude/pi/PI.md
   ```
   If no active PI exists, STOP — suggest `/plan-increment` first.

2. Read PRD for context:
   ```bash
   cat .claude/prd/PRD.md
   ```

## Steps

1. Based on the user's description, identify what changed:
   - **Epic split**: one epic becoming two or more
   - **Feature moved**: feature moving between epics
   - **Story added/removed**: new work discovered or scope cut
   - **Dependency change**: blocking relationships shifted
   - **Worktree reassignment**: parallel strategy needs adjusting

2. Update the relevant section of PI.md:
   - If epic split: create new epic section, redistribute features, update issue numbers
   - If feature moved: move the feature line, update parent epic references
   - If dependency graph changed: update the `## Dependency Graph` section
   - If worktree strategy affected: update `## Worktree Strategy`

3. If dependency graph changed, re-evaluate worktree strategy:
   - Can the same worktrees still run in parallel?
   - Does a new sequential dependency exist?

4. Check PRD decision log consistency:
   - If this PI change was driven by a decision, verify it's logged in the PRD
   - If not, remind user to run `/update-prd` to record the decision

5. If GitHub Issues need updating (e.g., parent links changed, new stubs needed):
   - Suggest the appropriate skill: `/update-epic`, `/update-feature`, `/create-epic`, etc.
   - Do NOT auto-update GitHub Issues from this skill — that's the work skills' job

## Commit

```bash
git add .claude/pi/PI.md
git commit -m "docs(pi): [concise description of the change]"
```
```

- [ ] **Step 3: Create close-pi skill**

Create `.claude/skills/close-pi/SKILL.md`:

```markdown
---
name: close-pi
description: Close the current Program Increment — archive the PI Plan, bake decisions into PRD, bump version, git tag. Use at the end of a sprint.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

# Close PI

Archive the current PI and prepare the PRD for the next increment.

## Preflight

1. Read current PI Plan:
   ```bash
   cat .claude/pi/PI.md
   ```
   If no active PI exists, STOP — nothing to close.

2. Read PRD:
   ```bash
   cat .claude/prd/PRD.md
   ```

3. Extract PI number from frontmatter:
   ```bash
   grep "^name:" .claude/pi/PI.md | head -1
   ```

## Steps

### 1. Summarize PI State

Query GitHub Issues to see what shipped:
```bash
gh issue list --state closed --limit 200 --json number,title,labels \
  --jq '.[] | "#\(.number) \(.title) [\([.labels[].name] | join(", "))]"'
gh issue list --state open --limit 200 --json number,title,labels \
  --jq '.[] | "#\(.number) \(.title) [\([.labels[].name] | join(", "))]"'
```

Present summary: what shipped, what's still open.

### 2. Verify Decision Log Completeness

Read the PRD Decision Log. For each decision:
- Does it make sense given what was built?
- Are there decisions that were made but never recorded? (Check git log for hints)
- Ask the user if anything is missing.

### 3. Bake Decisions into PRD Body

For each decision in the Decision Log:
- Identify the `Affects` column value (which PRD section)
- Update that section to reflect the decision
- Example: if a decision says "Use custom @tool instead of langchain-google-community" and Affects = "Architecture", update the Architecture section's agent tools description

After baking all decisions, wipe the Decision Log table (keep the header):
```markdown
## Decision Log
| Date | Decision | Reason | Affects |
|------|----------|--------|---------|
```

### 4. Bump PRD Version

Update the frontmatter `version` field. Minor bump for incremental changes (1.0 → 1.1), major bump if architecture fundamentally changed (1.x → 2.0). Ask user if unsure.

### 5. Archive PI Plan

```bash
# Extract PI number
PI_NUM=$(grep "^name:" .claude/pi/PI.md | sed 's/name: PI-//')

# Update status in PI.md
# Change "status: active" to "status: completed" in the frontmatter

# Move to completed
cp .claude/pi/PI.md ".claude/pi/completed/PI-${PI_NUM}.md"
rm .claude/pi/PI.md
```

### 6. Commit and Tag

Two separate commits — one for the PRD update, one for the PI archive:

```bash
# Commit 1: PRD version bump with baked-in decisions
git add .claude/prd/PRD.md
git commit -m "chore(prd): bump to v[X.Y] after PI-${PI_NUM}"

# Commit 2: Archive the PI
git add .claude/pi/
git commit -m "chore(pi): close PI-${PI_NUM}"

# Tag the boundary
git tag "pi-${PI_NUM}-complete"
```

Remind user: "Tag `pi-${PI_NUM}-complete` created locally. Push with `git push origin pi-${PI_NUM}-complete` if desired."

## Rules

- Never skip the decision log verification — decisions are the reason the PRD evolves
- Always bake decisions into body sections BEFORE wiping the log
- The archived PI in `completed/` is a read-only historical record
- After closing, there is no active PI — user should run `/plan-increment` to start the next one
```

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/plan-increment/SKILL.md .claude/skills/update-pi/SKILL.md .claude/skills/close-pi/SKILL.md
git commit -m "feat(skills): add plan-increment, update-pi, and close-pi skills"
```

---

## Task 8: Write work creation skills — `/create-epic`, `/create-feature`, `/detail-story`

**Files:**
- Create: `.claude/skills/create-epic/SKILL.md`
- Create: `.claude/skills/create-feature/SKILL.md`
- Create: `.claude/skills/detail-story/SKILL.md`

- [ ] **Step 1: Create create-epic skill**

Create `.claude/skills/create-epic/SKILL.md`:

```markdown
---
name: create-epic
description: Create a detailed epic on GitHub with stub feature issues. Takes an epic from the PI Plan, creates the GitHub Issue with full detail, then creates stub feature issues with parent links and dependency placeholders.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
argument-hint: "[epic name from PI Plan]"
---

# Create Epic

Take a high-level epic from the PI Plan, create a detailed GitHub Issue, and create stub feature issues.

## Preflight

1. Read the PI Plan:
   ```bash
   cat .claude/pi/PI.md
   ```
2. Read the PRD for context:
   ```bash
   cat .claude/prd/PRD.md
   ```
3. Find the epic in PI.md by the argument name. If ambiguous, list available epics and ask user to select.

## Steps

### 1. Collaborate on Epic Detail

Using the PRD and PI Plan context, work with the user to define:
- **Overview**: What this epic delivers and why
- **Success criteria**: Measurable outcomes (checkboxes)
- **Non-goals**: What this epic explicitly does NOT include
- **Priority**: critical, high, medium, or low
- **Area labels**: which area(s) this epic spans

### 2. Create Epic Issue on GitHub

```bash
gh issue create \
  --title "EPIC: [Name]" \
  --body "$(cat <<'BODY'
## Overview
[from discussion]

## Success Criteria
- [ ] [criterion 1]
- [ ] [criterion 2]

## Features
[will be filled as stub features are created]

## Non-goals
[from discussion]

## Dependencies
- Blocked by: [epic-level blockers, if any]
- Blocks: [what depends on this epic]
BODY
)" \
  --label "type:epic" --label "priority:[level]" --label "area:[area]" --label "status:todo"
```

Note the epic issue number from the output.

### 3. Create Stub Feature Issues

For each feature listed under this epic in PI.md:

```bash
gh issue create \
  --title "FEATURE: [Feature Name]" \
  --body "$(cat <<'BODY'
## Description
[1-line from PI Plan]

## Stories
[to be added by /create-feature]

## Non-goals
[to be added by /create-feature]

## Dependencies
- Blocked by:
- Blocks:

## Parent
- Epic: #[epic_number]
BODY
)" \
  --label "type:feature" --label "area:[area]" --label "status:todo"
```

For each stub feature:
- Ask if it has cross-epic dependencies (blocked by features from other epics)
- If yes, add the blocker issue numbers to the `Blocked by` line
- If the blocker isn't met yet, also apply `status:blocked` label

### 4. Update Epic Issue with Feature List

After all features are created, update the epic's body to list them:

```bash
# Build the features list
FEATURES="- [ ] #F1 — Feature Name 1\n- [ ] #F2 — Feature Name 2\n..."

# Update the epic issue body (replace the Features section)
gh issue edit [epic_number] --body "[updated body with feature list]"
```

### 5. Update PI.md

Replace `#TBD` placeholders with actual issue numbers for this epic and its features.

### 6. Commit

```bash
git add .claude/pi/PI.md
git commit -m "docs(pi): add issue numbers for epic [name]"
```

## Partial Failure

If creating a stub feature fails mid-flight:
- Report what was created and what failed
- Do NOT roll back already-created issues
- Do NOT commit PI.md changes until all GitHub operations succeed
- User decides whether to retry or clean up
```

- [ ] **Step 2: Create create-feature skill**

Create `.claude/skills/create-feature/SKILL.md`:

```markdown
---
name: create-feature
description: Detail a stub feature issue and create stub story issues under it. Takes a feature issue number, fleshes out the description, then creates stub stories with parent links.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
argument-hint: "#[feature issue number]"
---

# Create Feature

Take a stub feature issue, flesh it out with full detail, and create stub story issues.

## Preflight

1. Read the feature issue:
   ```bash
   gh issue view [number] --json number,title,body,labels
   ```
2. Extract the parent epic number from the `## Parent` section of the issue body.
3. Read the parent epic:
   ```bash
   gh issue view [epic_number] --json number,title,body
   ```
4. Read the PRD for relevant context:
   ```bash
   cat .claude/prd/PRD.md
   ```
5. Read the PI Plan:
   ```bash
   cat .claude/pi/PI.md
   ```

## Steps

### 1. Collaborate on Feature Detail

Using the epic context and PRD, work with the user to define:
- **Description**: What this feature delivers (2-3 paragraphs)
- **Story breakdown**: List of stories needed to deliver this feature
- **Non-goals**: Explicit boundaries for this feature
- **Dependencies**: Does this feature depend on or block other features?

### 2. Update Feature Issue on GitHub

```bash
gh issue edit [number] --body "$(cat <<'BODY'
## Description
[from discussion]

## Stories
- [ ] #[TBD] — [Story title 1]
- [ ] #[TBD] — [Story title 2]
...

## Non-goals
[from discussion]

## Dependencies
- Blocked by: [verified blockers]
- Blocks: [what this feature unblocks]

## Parent
- Epic: #[epic_number]
BODY
)"
```

### 3. Create Stub Story Issues

For each story identified:

```bash
gh issue create \
  --title "[Story title]" \
  --body "$(cat <<'BODY'
## Description
[1-line summary]

## Acceptance Criteria
[to be added by /detail-story]

## File Scope
[to be added by /detail-story]

## Technical Notes
[to be added by /detail-story]

## Dependencies
- Blocked by:
- Blocks:

## Parent
- Epic: #[epic_number]
- Feature: #[feature_number]
BODY
)" \
  --label "type:story" --label "area:[area]" --label "status:todo"
```

For each story:
- Set intra-feature dependency ordering where applicable (e.g., story 2 depends on story 1 if they must be done in order)
- Set cross-feature dependencies if any
- If a blocker exists and isn't met, apply `status:blocked` label instead of `status:todo`

### 4. Update Feature Issue with Story Numbers

After all stories are created, update the feature issue's Stories section with actual issue numbers.

### 5. Verify Dependencies

For each story with blockers, verify using the shared blocker satisfaction criteria:
- Satisfied if: issue has `status:done` label OR issue state is `CLOSED`
- Unmet if: issue is `OPEN` without `status:done`

Apply `status:blocked` to any story with unmet blockers.

## Partial Failure

Same as `/create-epic`: report what was created, don't roll back, don't commit until all GitHub operations succeed.
```

- [ ] **Step 3: Create detail-story skill**

Create `.claude/skills/detail-story/SKILL.md`:

```markdown
---
name: detail-story
description: Add full detail to a stub story issue — acceptance criteria, file scope, technical notes, and verified dependencies. Takes a story issue number and enriches it with implementation-ready detail.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
argument-hint: "#[story issue number]"
---

# Detail Story

Take a stub story issue and add full implementation detail.

## Preflight

1. Read the story issue:
   ```bash
   gh issue view [number] --json number,title,body,labels
   ```
2. Extract parent epic and feature numbers from the `## Parent` section.
3. Read the parent feature and epic for context:
   ```bash
   gh issue view [feature_number] --json number,title,body
   gh issue view [epic_number] --json number,title,body
   ```
4. Read the PRD — focus on sections relevant to this story:
   ```bash
   cat .claude/prd/PRD.md
   ```
   Pay special attention to:
   - **Security Constraints** — which apply to this story?
   - **Data Models** — which models does this story touch?
   - **API Contracts** — which endpoints does this story implement or consume?

## Steps

### 1. Collaborate on Story Detail

Work with the user to define:

- **Description**: What needs to be built and why (2-3 sentences)
- **Acceptance Criteria**: Testable checkboxes — each criterion should be verifiable by a test or manual check. Aim for 3-7 criteria.
- **File Scope**:
  - New files to create (exact paths)
  - Existing files to modify (exact paths)
- **Technical Notes**: Implementation guidance — patterns to follow, edge cases, relevant existing code to reference
- **Dependencies**: Verify and finalize `Blocked by` and `Blocks` lists

### 2. Verify Dependency Integrity

**Blocker satisfaction check** — for each issue in `Blocked by`:
```bash
gh issue view [dep_number] --json state,labels \
  --jq '{state: .state, done: ([.labels[].name] | contains(["status:done"]))}'
```
Satisfied if: `status:done` label OR state is `CLOSED`.

**Circular dependency check** — if this story has new blockers:
1. Fetch all open issues this story is connected to (its blockers, and issues that list this story as a blocker)
2. Walk the blocker chain: if following `Blocked by` links leads back to this story, there's a cycle
3. If cycle detected: report it and do NOT save the dependency. Ask the user to resolve.

**Cross-issue updates** — if this story now blocks an issue that doesn't list it in `Blocked by`:
```bash
# Read the blocked issue and add this story to its Blocked by list
gh issue view [blocked_number] --json body
# Update the body to include this story in Blocked by
gh issue edit [blocked_number] --body "[updated body]"
```

### 3. Update Story Issue on GitHub

```bash
gh issue edit [number] --body "$(cat <<'BODY'
## Description
[from discussion]

## Acceptance Criteria
- [ ] [criterion 1]
- [ ] [criterion 2]
- [ ] [criterion 3]

## File Scope
**New files:**
- [path/to/new/file]

**Modified files:**
- [path/to/existing/file]

## Technical Notes
[from discussion]

## Dependencies
- Blocked by: #X, #Y
- Blocks: #Z

## Parent
- Epic: #[epic_number]
- Feature: #[feature_number]
BODY
)"
```

### 4. Apply Correct Status Label

If any blocker is unmet:
```bash
gh issue edit [number] --add-label "status:blocked" --remove-label "status:todo"
```

If all blockers are met (or no blockers):
```bash
gh issue edit [number] --add-label "status:todo" --remove-label "status:blocked"
```

### 5. Update PI.md if Needed

If the dependency graph in PI.md needs updating (e.g., a new cross-epic dependency was discovered):
```bash
# Edit .claude/pi/PI.md dependency graph section
git add .claude/pi/PI.md
git commit -m "docs(pi): update deps for story #[number]"
```
```

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/create-epic/SKILL.md .claude/skills/create-feature/SKILL.md .claude/skills/detail-story/SKILL.md
git commit -m "feat(skills): add create-epic, create-feature, and detail-story skills"
```

---

## Task 9: Write work update skills — `/update-epic`, `/update-feature`, `/update-story`

**Files:**
- Create: `.claude/skills/update-epic/SKILL.md`
- Create: `.claude/skills/update-feature/SKILL.md`
- Create: `.claude/skills/update-story/SKILL.md`

- [ ] **Step 1: Create update-epic skill**

Create `.claude/skills/update-epic/SKILL.md`:

```markdown
---
name: update-epic
description: Modify an epic's scope — add/remove features, change description, update dependencies. Use when an epic needs restructuring mid-sprint.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
argument-hint: "#[epic issue number]"
---

# Update Epic

Modify an epic's scope, features, or dependencies.

## Preflight

1. Read the epic issue:
   ```bash
   gh issue view [number] --json number,title,body,labels
   ```
2. List its child features (parse the `## Features` checklist from the body for issue numbers):
   ```bash
   # For each feature number found in the epic body:
   gh issue view [feature_number] --json number,title,body,labels
   ```
3. Read PI Plan:
   ```bash
   cat .claude/pi/PI.md
   ```

## Steps

1. Identify what's changing based on the user's request:
   - **Adding features**: new capability needed under this epic
   - **Removing features**: scope cut or moved to another epic
   - **Splitting epic**: this epic is too large, should become two
   - **Dependency change**: blocking relationships shifted
   - **Description update**: success criteria or overview changed

2. Make the changes:

   **Adding a feature:**
   - Create a stub feature issue (same as `/create-epic` step 3)
   - Update the epic issue's Features checklist to include it
   - Update PI.md to add the feature under this epic

   **Removing a feature:**
   - Close the feature issue with a comment explaining why
   - Close any child story issues
   - Update the epic issue's Features checklist
   - Update PI.md

   **Splitting an epic:**
   - Create a new epic issue for the split portion
   - Move relevant features to the new epic (update their Parent section)
   - Update PI.md with the new epic and redistributed features
   - Update the dependency graph

   **Dependency change:**
   - Update the epic issue's Dependencies section
   - Check downstream: do any features/stories need their deps updated?
   - Update PI.md dependency graph

3. Flag downstream impacts:
   - List features/stories that may need updating
   - Suggest running `/update-feature` or `/update-story` for affected issues

4. Commit:
   ```bash
   git add .claude/pi/PI.md
   git commit -m "docs(pi): update epic #[number] scope"
   ```
```

- [ ] **Step 2: Create update-feature skill**

Create `.claude/skills/update-feature/SKILL.md`:

```markdown
---
name: update-feature
description: Modify a feature — add/remove stories, change description, update dependencies. Use when a feature's scope changes mid-sprint.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
argument-hint: "#[feature issue number]"
---

# Update Feature

Modify a feature's scope, stories, or dependencies.

## Preflight

1. Read the feature issue:
   ```bash
   gh issue view [number] --json number,title,body,labels
   ```
2. List its child stories (parse the `## Stories` checklist):
   ```bash
   # For each story number found:
   gh issue view [story_number] --json number,title,body,labels
   ```
3. Read PI Plan and PRD for context.

## Steps

1. Identify what's changing:
   - **Adding stories**: new work discovered (bug, new requirement)
   - **Removing stories**: scope cut
   - **Dependency change**: feature now blocks/is blocked by something new
   - **Description/non-goals update**

2. Make the changes:

   **Adding a story:**
   - Create a stub story issue (same as `/create-feature` step 3)
   - Update the feature issue's Stories checklist
   - Check: does this new story block anything already in progress? Flag it.
   - Check: should any existing `status:todo` stories now depend on this new story?

   **Removing a story:**
   - Close the story issue with a comment
   - Update the feature issue's Stories checklist
   - Check: did any other story depend on the removed one? Update their deps.

   **Dependency change:**
   - Update the feature issue's Dependencies section
   - Re-evaluate: should any child stories have their status labels updated?
   - Apply `status:blocked` or `status:todo` as appropriate using shared blocker satisfaction criteria

3. Update PI.md if the feature-level plan changed:
   ```bash
   git add .claude/pi/PI.md
   git commit -m "docs(pi): update feature #[number]"
   ```
```

- [ ] **Step 3: Create update-story skill**

Create `.claude/skills/update-story/SKILL.md`:

```markdown
---
name: update-story
description: Modify a story's acceptance criteria, file scope, dependencies, or technical notes. Use when a story's requirements change.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
argument-hint: "#[story issue number]"
---

# Update Story

Modify a story's detail — acceptance criteria, file scope, deps, or technical notes.

## Preflight

1. Read the story issue:
   ```bash
   gh issue view [number] --json number,title,body,labels
   ```
2. Read parent feature and epic for context.

## Steps

1. Identify what's changing based on user's request.

2. Update the story issue body on GitHub:
   ```bash
   gh issue edit [number] --body "[updated body]"
   ```

3. If dependencies changed:

   **Circular dependency check:**
   - Fetch the blocker chain for this story
   - Walk `Blocked by` links from each blocker
   - If the chain leads back to this story, STOP and report the cycle

   **Downstream updates:**
   - If this story now blocks a new issue, update that issue's `Blocked by` section:
     ```bash
     gh issue view [blocked_number] --json body
     gh issue edit [blocked_number] --body "[add this story to Blocked by]"
     ```
   - If a blocker was removed, check if the previously blocked issue is now unblocked

   **Status label update:**
   - If a new blocker was added and it's unmet → apply `status:blocked`
   - If a blocker was removed and all remaining blockers are met → apply `status:todo`

4. If this change was driven by a bug or decision:
   - Remind user to run `/update-prd` if the decision isn't recorded yet
   - Remind user to run `/update-pi` if the PI Plan is affected

5. Commit only if PI.md was changed:
   ```bash
   git add .claude/pi/PI.md
   git commit -m "docs(pi): update deps for story #[number]"
   ```
```

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/update-epic/SKILL.md .claude/skills/update-feature/SKILL.md .claude/skills/update-story/SKILL.md
git commit -m "feat(skills): add update-epic, update-feature, and update-story skills"
```

---

## Task 10: Rewrite `/pick-task` and `/sync-issues`

**Files:**
- Modify: `.claude/skills/pick-task/SKILL.md`
- Modify: `.claude/skills/sync-issues/SKILL.md`

- [ ] **Step 1: Rewrite pick-task**

Replace the entire contents of `.claude/skills/pick-task/SKILL.md`:

```markdown
---
name: pick-task
description: Find the next unblocked story to work on from GitHub issues based on priority and dependency analysis. Use at the start of a coding session or after completing a story.
allowed-tools: Read, Bash, Grep, Glob
argument-hint: "[optional: area like 'auth', 'api', 'agents', 'ui', 'infra', 'search']"
---

# Pick Next Task

Find the highest-priority unblocked story to work on next.

## Steps

1. **Read context** — read the PI Plan for current sprint awareness:
   ```bash
   cat .claude/pi/PI.md
   ```

2. **Get candidate stories** — fetch all open stories labeled `status:todo`:
   ```bash
   gh issue list --state open --label "type:story" --label "status:todo" --limit 200 \
     --json number,title,body,labels,createdAt \
     --jq '.[] | {number, title, labels: [.labels[].name], createdAt, body}'
   ```

3. **Check dependencies** — for each candidate, parse the `## Dependencies` section from the issue body. Extract issue numbers from the `Blocked by:` line.

   Handle formatting variations:
   - `Blocked by: #45, #46` or `Blocked by: #45,#46`
   - `- Blocked by: #45` (with leading dash)
   - `Blocked by:` with nothing after it = no blockers

   For each blocker found, check if it's satisfied:
   ```bash
   gh issue view <dep_number> --json state,labels \
     --jq '{state: .state, labels: [.labels[].name]}'
   ```

   **Blocker satisfaction criteria:**
   - Satisfied if: issue has `status:done` in labels OR state is `CLOSED`
   - Unmet if: issue is `OPEN` without `status:done` label

   If ANY blocker is unmet, this story is NOT eligible. Also fix its label:
   ```bash
   gh issue edit <number> --add-label "status:blocked" --remove-label "status:todo"
   ```

4. **Filter** — keep only stories where ALL blockers are satisfied.

5. **Area filter** — if an area argument was provided, narrow to stories with that `area:*` label.

6. **Rank** the remaining stories by:
   1. Priority: `priority:critical` > `priority:high` > `priority:medium` > `priority:low` > no priority
   2. Creation date: older first (lower issue number = created earlier)

7. **Present recommendation**:
   - Issue number and title
   - Why it's next (priority level, unblocked status)
   - Key acceptance criteria (from issue body)
   - File scope (from issue body)
   - Parent feature and epic
   - Ask: "Start working on this story?"

8. **On confirmation**:
   ```bash
   gh issue edit <number> --add-label "status:in-progress" --remove-label "status:todo"
   ```
   Then read the full issue body and begin the development workflow from `.claude/rules/workflow.md`.
```

- [ ] **Step 2: Rewrite sync-issues**

Replace the entire contents of `.claude/skills/sync-issues/SKILL.md`:

```markdown
---
name: sync-issues
description: Audit the full GitHub issue hierarchy — fix stale labels, validate dependencies, detect orphans and cycles, report project status. Use for a progress check or when issues might be stale.
allowed-tools: Read, Bash, Grep, Glob
argument-hint: "[optional: area filter like 'auth', 'api', 'agents', 'ui', 'infra', 'search']"
---

# Sync Issues

Audit and fix the full issue hierarchy. Validates labels, dependencies, and parent-child relationships.

## Steps

### 1. Fetch All Issues

```bash
# Open issues by type
gh issue list --state open --label "type:epic" --limit 200 --json number,title,body,labels
gh issue list --state open --label "type:feature" --limit 200 --json number,title,body,labels
gh issue list --state open --label "type:story" --limit 200 --json number,title,body,labels

# Closed issues with potentially stale labels
gh issue list --state closed --label "status:in-progress" --limit 200 --json number,title,labels
gh issue list --state closed --label "status:todo" --limit 200 --json number,title,labels
```

If area filter provided, add `--label "area:[area]"` to each query.

### 2. Fix Stale Labels

For each closed issue that still has `status:in-progress` or `status:todo`:
```bash
gh issue edit <number> --add-label "status:done" --remove-label "status:in-progress" --remove-label "status:todo"
```

### 3. Dependency Audit

For each open story, parse `Blocked by:` from the issue body.

For each blocker, check satisfaction:
```bash
gh issue view <dep> --json state,labels \
  --jq '{state: .state, labels: [.labels[].name]}'
```

**Fix mismatched labels:**
- If all blockers are satisfied but story is `status:blocked` → update to `status:todo`
- If any blocker is unmet but story is `status:todo` → update to `status:blocked`

```bash
# Unblock
gh issue edit <number> --add-label "status:todo" --remove-label "status:blocked"
# Block
gh issue edit <number> --add-label "status:blocked" --remove-label "status:todo"
```

### 4. Orphan Detection

For each issue number referenced in a `Blocked by` or `Blocks` line:
```bash
gh issue view <ref_number> --json state 2>&1
```
If the issue doesn't exist, flag it as an orphaned reference.

### 5. Circular Dependency Detection

Build a dependency adjacency list from all open issues:
- Key: issue number
- Value: list of issue numbers from its `Blocked by` line

For each issue, perform a DFS walk through the blocker chain:
- Start from the issue
- Follow each blocker's blockers
- If the starting issue is encountered, report the cycle:
  `Circular dependency: #A → #B → #C → #A`

### 6. Hierarchy Check

For each open story: verify it has a `## Parent` section with both Epic and Feature references.
For each open feature: verify it has a `## Parent` section with an Epic reference.

Flag any issues missing parent links.

### 7. Report

Present a summary:

```
## Sync Report

**Totals:** X epics, Y features, Z stories
**Status:** Done: X | In Progress: X | Todo: X | Blocked: X

**Fixes Applied:**
- Stale labels fixed: N (list issue numbers)
- Unblocked: N (issues moved from blocked → todo)
- Newly blocked: N (issues moved from todo → blocked)

**Issues Found:**
- Orphaned dep references: N (list them)
- Circular dependencies: N (list the cycles)
- Missing parent links: N (list them)

**Next Recommended Stories:**
[Top 3 unblocked stories by priority]
```

## Rules

- Do not manually close issues — issues close when PRs merge
- Fix stale labels automatically (closed + wrong status)
- Fix blocked/todo mismatches automatically
- Report but do NOT auto-fix: orphaned references, cycles, missing parents (these need human judgment)
```

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/pick-task/SKILL.md .claude/skills/sync-issues/SKILL.md
git commit -m "feat(skills): rewrite pick-task and sync-issues with dependency model"
```

---

## Task 11: Update CLAUDE.md skill descriptions

The skill descriptions in CLAUDE.md need to match the new skill names and purposes. This was partially done in Task 4, but the contextual skills section and any remaining references need a final pass.

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Verify all SPEC.md references are gone**

```bash
grep -n "SPEC\|specs/in-progress\|update-decision" CLAUDE.md
```

If any remain, fix them.

- [ ] **Step 2: Verify skill list matches actual skills**

```bash
ls .claude/skills/*/SKILL.md | sed 's|.claude/skills/||;s|/SKILL.md||' | sort
```

Compare with the Skills section in CLAUDE.md. Ensure every skill is listed with correct description.

- [ ] **Step 3: Commit if changes were needed**

```bash
git add CLAUDE.md
git commit -m "docs: final CLAUDE.md cleanup for SDLC skill suite"
```

---

## Task 12: Final verification

- [ ] **Step 1: Verify all skill files exist**

```bash
for skill in create-prd update-prd plan-increment update-pi close-pi create-epic create-feature detail-story update-epic update-feature update-story pick-task sync-issues review-coderabbit update-decision; do
  if [ -f ".claude/skills/$skill/SKILL.md" ]; then
    echo "OK: $skill"
  else
    echo "MISSING: $skill"
  fi
done
```

Expected: all 15 show OK (13 active + review-coderabbit + deprecated update-decision).

- [ ] **Step 2: Verify no SPEC.md references remain in active files**

```bash
grep -r "SPEC\.md\|specs/in-progress" CLAUDE.md .claude/rules/ .claude/agents/ .claude/skills/ 2>/dev/null
```

Expected: only the deprecated `update-decision/SKILL.md` might mention it (acceptable) and the design spec in `docs/` (expected). No hits in CLAUDE.md, rules, or agents.

- [ ] **Step 3: Verify directory structure**

```bash
echo "=== PRD ===" && ls .claude/prd/
echo "=== PI ===" && ls .claude/pi/ && ls .claude/pi/completed/
echo "=== Skills ===" && ls .claude/skills/
```

Expected:
- `.claude/prd/PRD.md` exists
- `.claude/pi/PI.md` exists
- `.claude/pi/completed/` exists (with .gitkeep)
- All skill directories present

- [ ] **Step 4: Run git status and verify clean**

```bash
git status
git log --oneline -10
```

Expected: clean working tree, ~8-10 commits from this plan.
