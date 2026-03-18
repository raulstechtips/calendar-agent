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
