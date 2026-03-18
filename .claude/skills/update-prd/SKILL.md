---
name: update-prd
description: Record a design change or update a PRD section. Replaces /update-decision. Use when the user makes a decision about how something should be built, or when a PRD section needs updating.
allowed-tools: Read, Edit, Write, Bash, Grep, Glob
argument-hint: "[decision description or section name to update]"
---

# Update PRD

Record a design decision or update a section of the Product Requirements Document.

## Preflight

1. Read the current PRD:
   ```bash
   cat .claude/prd/PRD.md
   ```
   If it doesn't exist, STOP — suggest `/create-prd` first.

2. Read the current PI Plan for context (if it exists):
   ```bash
   cat .claude/pi/PI.md 2>/dev/null
   ```

## Mode Detection

Determine the type of update from the user's argument:

### Mode A: Record a Decision

If the argument describes a decision (architecture choice, tech change, scope change, approach change):

1. Add a new row to the Decision Log table:
   ```
   | [today's date] | [decision] | [reason] | [affected PRD section] |
   ```

2. Do NOT modify the affected body section yet — decisions are baked into body sections only at PI close (`/close-pi`). The Decision Log is the buffer.

3. If the decision changes scope, check which GitHub Issues may be affected:
   ```bash
   gh issue list --state open --label "type:story" --limit 200 --json number,title,body \
     --jq '.[] | select(.body | test("KEYWORD"; "i")) | "#\(.number) \(.title)"'
   ```
   Report affected issues to the user but do NOT auto-update them — suggest `/update-story`, `/update-feature`, or `/update-epic` as appropriate.

4. If the decision supersedes a previous decision in the log, mark the old one:
   ```
   | [old date] | ~~old decision~~ **Superseded [today]** | ~~old reason~~ | [section] |
   ```

### Mode B: Update a PRD Section

If the argument names a section (e.g., "update API contracts", "update data models"):

1. Read the current section content
2. Present the proposed change to the user
3. On approval, edit the section using the Edit tool
4. If this changes scope, flag affected GitHub Issues (same as Mode A step 3)

## Commit

```bash
git add .claude/prd/PRD.md
git commit -m "docs(prd): [concise description of the change]"
```

## Rules

- The PRD is the source of truth — always update it FIRST
- Never delete decision history — mark old decisions as superseded with date and strikethrough
- If a decision affects the PI Plan, remind the user to run `/update-pi`
- If a decision affects GitHub Issues, list which ones and suggest the appropriate update skill
