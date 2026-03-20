# Feature Reference Guide

## Scope Assessment Criteria

| Signal | LIGHT | STANDARD | DEEP |
|--------|-------|----------|------|
| Story count | 1-2 stories | 3-4 stories | 5+ stories |
| Pattern novelty | Clear pattern to follow | Extends existing patterns | Introduces new patterns |
| Cross-feature dependencies | None | 1 dependency | 2+ dependencies |
| Area span | 1 area | 1-2 areas | 3+ areas |
| Questions needed | 1-2 | 3-4 | 4+ |

**Quick rules:**
- DEEP if ANY: 5+ stories, cross-feature dependencies, introduces new patterns
- STANDARD if ANY: 3-4 stories, extends existing patterns
- LIGHT if ALL: 1-2 stories, clear pattern to follow

## Context to Read

1. **Parent epic:** `gh issue view <epic-number> --json title,body,labels` — understand the epic's scope, success criteria, and where this feature fits.
2. **PI Plan:** `.claude/sdlc/pi/PI.md` — overall PI context and dependency graph.
3. **PRD:** `.claude/sdlc/prd/PRD.md` — architecture, data models, API contracts, security constraints relevant to this feature.

## Question Templates

### Questions (adapt count to depth)

1. **Description:** "What does this feature deliver? (2-3 paragraphs covering what it does, who benefits, and how it connects to the epic)"
2. **Story breakdown:** "What units of work does this split into? (each story should be independently implementable and testable)"
3. **Non-goals:** "What's out of scope for this feature specifically? (things the epic covers but this feature does not)"
4. **Dependencies:** "Does this feature depend on or block other features? (within this epic or across epics)"

### LIGHT: Summarize from parent epic context, ask 1 confirming question.
### STANDARD: Ask questions 1-3, infer dependencies from context.
### DEEP: Ask all 4, plus follow-ups on story breakdown and architecture implications.

## Draft Body Template

```markdown
---
type: feature
name: <feature name>
priority: <inherited from epic or override>
areas: [<area labels>]
status: draft
parent-epic: <epic issue number>
---

## Description
[What this feature delivers — 2-3 paragraphs covering functionality, user/system impact, and how it fits within the parent epic]

## Stories
- [ ] <Story name> (#TBD) — [1-line description]
- [ ] <Story name> (#TBD) — [1-line description]
- [ ] <Story name> (#TBD) — [1-line description]

## Non-goals
- [explicit exclusion 1]

## Dependencies
- Blocked by: [#N or "none"]
- Blocks: [#N or "none"]

## Parent
- Epic: #<epic number>
```
