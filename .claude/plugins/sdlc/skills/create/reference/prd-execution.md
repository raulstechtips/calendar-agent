# PRD Execution Reference

## Required Fields

### Frontmatter
- `name` — project name
- `version` — semantic version (e.g., `1.0`)
- `created` — date in YYYY-MM-DD format

### Body Sections
- `## Overview` — non-empty
- `## Tech Stack` — non-empty
- `## Architecture` — non-empty

These are the minimum required sections. Additional sections (Data Models, API Contracts, Security Constraints, Roadmap, Acceptance Criteria, Out of Scope, Decision Log) are expected but not blocking — warn if missing but proceed.

## Execution Steps

### New PRD

1. **Ensure directory exists:**

```bash
mkdir -p .claude/sdlc/prd
```

2. **Write draft content to final location:**

```bash
# Copy the validated draft to the PRD location
cp .claude/sdlc/drafts/<draft-filename> .claude/sdlc/prd/PRD.md
```

Or use the Write tool to write the draft content directly to `.claude/sdlc/prd/PRD.md`.

3. **Update frontmatter status:** Change `status: draft` to remove the status field (PRD doesn't carry a status — it's always the current truth).

4. **Commit:**

```bash
git add .claude/sdlc/prd/PRD.md
git commit -m "docs(prd): create PRD v<version>"
```

Where `<version>` comes from the frontmatter (e.g., `1.0`).

### PRD Update (via reshape flow)

When the draft has a `## Changes` section (produced by `sdlc:define` reshape), this is an update to an existing PRD.

1. **Read current PRD:**

```
Read .claude/sdlc/prd/PRD.md
```

2. **Apply changes from the draft.** The draft contains the complete updated content — write it to `.claude/sdlc/prd/PRD.md`.

3. **Bump version in frontmatter:** Increment the minor version (e.g., `1.0` -> `1.1`).

4. **Commit:**

```bash
git add .claude/sdlc/prd/PRD.md
git commit -m "docs(prd): update PRD to v<new-version>"
```

## Report Format

> Created: `.claude/sdlc/prd/PRD.md` v`<version>`
> Committed: `docs(prd): create PRD v<version>`

Or for updates:

> Updated: `.claude/sdlc/prd/PRD.md` v`<old-version>` -> v`<new-version>`
> Committed: `docs(prd): update PRD to v<new-version>`
