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
