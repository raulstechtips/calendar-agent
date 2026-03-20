# PI Execution Reference

## Required Fields

### Frontmatter
- `name` — PI identifier (e.g., `PI-1`, `PI-2`)
- `theme` — one-line theme description
- `started` — date in YYYY-MM-DD format
- `target` — date in YYYY-MM-DD format

### Body Sections
- `## Goals` — non-empty
- `## Epics` — at least one epic listed

Additional sections (Dependency Graph, Worktree Strategy) are expected but not blocking.

## Execution Steps

### Check for Active PI

Before creating a new PI, check if one already exists:

```bash
test -f .claude/sdlc/pi/PI.md && echo "ACTIVE_PI_EXISTS" || echo "NO_ACTIVE_PI"
```

If an active PI exists, run the **PI Archival Flow** first. If not, skip to **New PI Creation**.

---

### PI Archival Flow

When an active PI exists at `.claude/sdlc/pi/PI.md`:

**1. Read current PI:**

```
Read .claude/sdlc/pi/PI.md
```

Extract the PI number from the frontmatter `name` field (e.g., `PI-1` -> `1`).

**2. Read the PRD decision log:**

```
Read .claude/sdlc/prd/PRD.md
```

Look for the `## Decision Log` section. Parse the table rows.

**3. Bake decision log entries into the PRD body:**

For each row in the Decision Log table:
- Read the `Affects` column to identify which PRD section is affected.
- Integrate the decision into the relevant section's content (e.g., if Affects says "Architecture", update the Architecture section prose to reflect the decision).
- This makes decisions permanent — they graduate from the log into the body.

**4. Wipe the decision log table:**

Keep the table header row and separator, but remove all data rows:

```markdown
## Decision Log
| Date | Decision | Reason | Affects |
|------|----------|--------|---------|
```

**5. Bump PRD version:**

Increment the minor version in PRD frontmatter (e.g., `1.2` -> `1.3`).

**6. Commit PRD changes:**

```bash
git add .claude/sdlc/prd/PRD.md
git commit -m "chore(prd): bump to v<X.Y> after PI-<N>"
```

**7. Archive the PI file:**

```bash
mkdir -p .claude/sdlc/pi/completed
```

Copy PI.md to the archive, updating the frontmatter `status` from `active` to `completed`:

Write the archived content to `.claude/sdlc/pi/completed/PI-<N>.md` with `status: completed` in the frontmatter.

**8. Commit PI archive:**

```bash
git add .claude/sdlc/pi/
git commit -m "chore(pi): close PI-<N>"
```

**9. Tag the completion:**

```bash
git tag pi-<N>-complete
```

Where `<N>` is the PI number (lowercase, e.g., `pi-1-complete`).

---

### New PI Creation

**1. Ensure directory exists:**

```bash
mkdir -p .claude/sdlc/pi
```

**2. Write draft content to final location:**

Write the validated draft content to `.claude/sdlc/pi/PI.md`. Update the frontmatter: change `status: draft` to `status: active`.

**3. Commit:**

```bash
git add .claude/sdlc/pi/PI.md
git commit -m "docs(pi): create PI-<N> plan"
```

Where `<N>` is the PI number from the frontmatter name field.

## Report Format

**New PI (no archival):**

> Created: `.claude/sdlc/pi/PI.md` — PI-`<N>`: "`<theme>`"
> Committed: `docs(pi): create PI-<N> plan`

**New PI (with archival):**

> **Archived PI-`<old-N>`:**
> - PRD updated: baked `<count>` decisions, bumped to v`<X.Y>`
> - Archived to: `.claude/sdlc/pi/completed/PI-<old-N>.md`
> - Tagged: `pi-<old-N>-complete`
>
> **Created PI-`<new-N>`:**
> - `.claude/sdlc/pi/PI.md` — "`<theme>`"
> - Committed: `docs(pi): create PI-<new-N> plan`
