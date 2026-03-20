# PI Reference Guide

## Scope Assessment Criteria

| Signal | LIGHT | STANDARD | DEEP |
|--------|-------|----------|------|
| Epic count | 1-2 epics | 3-4 epics | 5+ epics |
| Cross-epic dependencies | None | Some (linear chain) | Complex (diamond, circular risk) |
| Worktree parallelism | Single stream | 2 parallel streams | 3+ parallel streams needing coordination |
| Carry-over items | None | A few stories from prior PI | Significant re-planning from failed PI |
| Questions needed | 2-3 | 4-5 | 6+ |

## Context to Read

1. **PRD Roadmap section:** `.claude/sdlc/prd/PRD.md` — focus on the Roadmap. This is where the user picks items for the PI.
2. **Previous PI retro:** Check `.claude/sdlc/retros/` for the most recent retro file. If one exists, read it for:
   - Carry-over items (stories not completed)
   - Velocity observations (did we over-scope?)
   - Process recommendations

## PI Archival Note

If an active PI already exists at `.claude/sdlc/pi/PI.md` when the user defines a new one, inform them:

> "There's an active PI already. When you run `sdlc:create pi`, it will archive the current PI (tag + move to history), bake any new decisions into the PRD, and set up the new PI. You don't need to do that manually."

## Question Templates

### Questions (adapt count to depth)

1. **Roadmap selection:** "Here's the current roadmap from the PRD:\n\n[paste roadmap items]\n\nWhich items go into this PI?"
2. **Theme:** "What's the one-line theme for this PI? (e.g., 'Foundation sprint: auth, infra, and basic chat')"
3. **Target date:** "When should this PI wrap up? (target date)"
4. **Epic breakdown:** "For each epic, what features does it contain? (high-level titles — we'll flesh them out when defining each epic)"
5. **Dependencies:** "Are there dependencies between epics or features? (what blocks what)"
6. **Worktree strategy:** "Which features can be worked on in parallel in separate worktrees? Any that must be sequential?"

### If carry-over items exist from retro

Add this question before the roadmap selection:

- "The last PI retro flagged these carry-over items: [list]. Should they be included in this PI, deferred, or dropped?"

## Draft Body Template

```markdown
---
name: PI-<N>
theme: <one-line theme>
started: <YYYY-MM-DD>
target: <YYYY-MM-DD>
status: active
---

## Goals
[2-3 sentences describing what this PI delivers and why it matters]

## Epics

### Epic: <name> (#TBD)
- Feature: <name> (#TBD)
- Feature: <name> (#TBD)

### Epic: <name> (#TBD)
- Feature: <name> (#TBD)

## Dependency Graph
[plain language description of ordering constraints, e.g.:
- "Epic A must complete before Epic B's feature X can start"
- "Feature Y in Epic B and Feature Z in Epic C can run in parallel"
- "Epic D has no dependencies and can start immediately"]

## Worktree Strategy
[which features can be parallelized in separate worktrees, e.g.:
- Worktree 1: Epic A (sequential — foundational)
- Worktree 2: Epic B Feature X + Epic C Feature Y (parallel — independent areas)]
```
