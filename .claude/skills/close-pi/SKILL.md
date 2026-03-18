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
