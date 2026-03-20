# PI Update Reference

## Direct Update Criteria

**DIRECT** if all true:
- 1-2 fields changing (date change, theme tweak, status update, single epic/feature rename)
- No epics added or removed
- No dependency graph restructure
- No feature redistribution between epics

**ESCALATE** if any true:
- Epic added or removed from the plan
- Dependency graph restructure (reordering epic dependencies, changing critical path)
- Feature redistribution (moving features between epics)
- 3+ fields changing
- Goal rewrite

## Edit Pattern

### Read current PI

```
Read .claude/sdlc/pi/PI.md
```

### Make targeted edits

Use the Edit tool to modify specific sections. Do NOT rewrite the entire file — change only the targeted content.

### Common direct updates

**Date change:**
Edit the `started` or `target` field in the YAML frontmatter.

**Theme tweak:**
Edit the `theme` field in the YAML frontmatter.

**Status update for an epic entry:**
Find the epic line in the `## Epics` section and update its status annotation.

**Single epic/feature rename:**
Find the line referencing the old name and replace it with the new name. Ensure the issue number reference stays intact.

### Commit

```bash
git add .claude/sdlc/pi/PI.md
git commit -m "docs(pi): <description of change>"
```

Use a descriptive message: `docs(pi): extend target date to 2026-04-15` or `docs(pi): rename epic Auth Setup to Authentication`.

## Cascade Rules

After updating the PI, check for downstream impacts:

- **If an epic was renamed**: the corresponding GitHub issue title may need updating.

```bash
gh issue view <epic-number> --json title --jq '.title'
```

Flag if the title doesn't match the new name in PI.md.

- **If dates changed**: flag stories with time-sensitive dependencies.
- **If structure changed** (escalated via define, then applied): flag all affected epics and features for review.

Do not update downstream artifacts without user confirmation.
