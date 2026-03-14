---
name: update-decision
description: Record an architecture or product decision into the spec and update affected GitHub issues. Use when the user makes a decision about how something should be built.
allowed-tools: Read, Edit, Write, Bash, Grep, Glob
argument-hint: "[decision description]"
---

# Update Decision Workflow

When the user makes a decision (architecture, scope, tech choice, approach), follow this process:

## Steps

1. **Read** the current spec at `.claude/specs/in-progress/SPEC.md`
2. **Update the spec** — add or modify the relevant section with the decision. Include:
   - What was decided
   - Why (the reasoning, even if brief)
   - What it replaces (if changing a previous decision)
3. **Find affected GitHub issues** — search for issues whose scope, acceptance criteria, or approach is impacted:
   ```bash
   gh issue list --label "status:todo" --json number,title,body --jq '.[] | select(.body | test("KEYWORD")) | "#\(.number) \(.title)"'
   ```
4. **Update affected issues** — edit the issue body to reflect the new decision:
   ```bash
   gh issue edit <number> --body "updated body"
   ```
5. **Summarize** what was changed: which spec section, which issues updated, and any new dependencies or scope changes.

## Rules

- The spec is the source of truth — always update it FIRST
- Never delete decision history from the spec — mark old decisions as superseded with the date
- If a decision changes the sprint plan (day1/day2 assignments), flag it explicitly
- If a decision removes scope, suggest closing or deprioritizing the relevant issues
