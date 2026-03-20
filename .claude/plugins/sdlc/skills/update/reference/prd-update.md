# PRD Update Reference

## Direct Update Criteria

**DIRECT** if all true:
- 1-2 sections changing (edit description paragraph, update a decision log entry, tweak a bullet point, fix a typo)
- No new top-level sections added or removed
- No structural rewrite of existing sections
- No version bump needed (cosmetic/clarification changes only)

**ESCALATE** if any true:
- New top-level section added (e.g., adding `## Deployment Strategy`)
- Structural rewrite of an existing section (e.g., rewriting Architecture from scratch)
- 3+ sections changing
- Version bump needed (substantive content change)
- Tech stack change

## Edit Pattern

### Read current PRD

```
Read .claude/sdlc/prd/PRD.md
```

### Make targeted edits

Use the Edit tool to modify specific sections. Do NOT rewrite the entire file — change only the targeted content.

### Decision Log Updates

If adding a row to the Decision Log table, append it at the end of the table:

```markdown
| <YYYY-MM-DD> | <decision> | <reason> | <affected section> |
```

The date should be today's date. The "Affects" column names the PRD section that this decision impacts (e.g., "Architecture", "Security Constraints", "Tech Stack").

### Commit

```bash
git add .claude/sdlc/prd/PRD.md
git commit -m "docs(prd): <description of change>"
```

Use a descriptive message: `docs(prd): update Architecture section with new caching strategy` or `docs(prd): add decision log entry for Redis session store`.

## Cascade Rules

After updating the PRD, check for downstream impacts:

- **If a decision affects the PI plan**: flag the PI for review. Example: "This decision changes the Architecture section. The current PI may need adjustments — want me to check `.claude/sdlc/pi/PI.md`?"
- **If a decision affects open issues**: search for issues in the affected area. Example: if updating Security Constraints, check for open stories in `area:auth`.

```bash
gh issue list --label "area:<affected-area>" --state open --json number,title --jq '.[] | "#\(.number) \(.title)"'
```

Flag any issues that might be affected. Do not update them without user confirmation.
