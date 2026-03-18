---
name: create-epic
description: Create a detailed epic on GitHub with stub feature issues. Takes an epic from the PI Plan, creates the GitHub Issue with full detail, then creates stub feature issues with parent links and dependency placeholders.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
argument-hint: "[epic name from PI Plan]"
---

# Create Epic

Take a high-level epic from the PI Plan, create a detailed GitHub Issue, and create stub feature issues.

## Preflight

1. Read the PI Plan:
   ```bash
   cat .claude/pi/PI.md
   ```
2. Read the PRD for context:
   ```bash
   cat .claude/prd/PRD.md
   ```
3. Find the epic in PI.md by the argument name. If ambiguous, list available epics and ask user to select.

## Steps

### 1. Collaborate on Epic Detail

Using the PRD and PI Plan context, work with the user to define:
- **Overview**: What this epic delivers and why
- **Success criteria**: Measurable outcomes (checkboxes)
- **Non-goals**: What this epic explicitly does NOT include
- **Priority**: critical, high, medium, or low
- **Area labels**: which area(s) this epic spans

### 2. Create Epic Issue on GitHub

```bash
gh issue create \
  --title "EPIC: [Name]" \
  --body "$(cat <<'BODY'
## Overview
[from discussion]

## Success Criteria
- [ ] [criterion 1]
- [ ] [criterion 2]

## Features
[will be filled as stub features are created]

## Non-goals
[from discussion]

## Dependencies
- Blocked by: [epic-level blockers, if any]
- Blocks: [what depends on this epic]
BODY
)" \
  --label "type:epic" --label "priority:[level]" --label "area:[area]" --label "status:todo"
```

Note the epic issue number from the output.

### 3. Create Stub Feature Issues

For each feature listed under this epic in PI.md:

```bash
gh issue create \
  --title "FEATURE: [Feature Name]" \
  --body "$(cat <<'BODY'
## Description
[1-line from PI Plan]

## Stories
[to be added by /create-feature]

## Non-goals
[to be added by /create-feature]

## Dependencies
- Blocked by:
- Blocks:

## Parent
- Epic: #[epic_number]
BODY
)" \
  --label "type:feature" --label "area:[area]" --label "status:todo"
```

For each stub feature:
- Ask if it has cross-epic dependencies (blocked by features from other epics)
- If yes, add the blocker issue numbers to the `Blocked by` line
- If the blocker isn't met yet, also apply `status:blocked` label

### 4. Update Epic Issue with Feature List

After all features are created, update the epic's body to list them:

```bash
gh issue edit [epic_number] --body "[updated body with feature list]"
```

### 5. Update PI.md

Replace `#TBD` placeholders with actual issue numbers for this epic and its features.

### 6. Commit

```bash
git add .claude/pi/PI.md
git commit -m "docs(pi): add issue numbers for epic [name]"
```

## Partial Failure

If creating a stub feature fails mid-flight:
- Report what was created and what failed
- Do NOT roll back already-created issues
- Do NOT commit PI.md changes until all GitHub operations succeed
- User decides whether to retry or clean up
