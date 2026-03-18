---
name: create-feature
description: Detail a stub feature issue and create stub story issues under it. Takes a feature issue number, fleshes out the description, then creates stub stories with parent links.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
argument-hint: "#[feature issue number]"
---

# Create Feature

Take a stub feature issue, flesh it out with full detail, and create stub story issues.

## Preflight

1. Read the feature issue:
   ```bash
   gh issue view [number] --json number,title,body,labels
   ```
2. Extract the parent epic number from the `## Parent` section of the issue body.
3. Read the parent epic:
   ```bash
   gh issue view [epic_number] --json number,title,body
   ```
4. Read the PRD for relevant context:
   ```bash
   cat .claude/prd/PRD.md
   ```
5. Read the PI Plan:
   ```bash
   cat .claude/pi/PI.md
   ```

## Steps

### 1. Collaborate on Feature Detail

Using the epic context and PRD, work with the user to define:
- **Description**: What this feature delivers (2-3 paragraphs)
- **Story breakdown**: List of stories needed to deliver this feature
- **Non-goals**: Explicit boundaries for this feature
- **Dependencies**: Does this feature depend on or block other features?

### 2. Update Feature Issue on GitHub

```bash
gh issue edit [number] --body "$(cat <<'BODY'
## Description
[from discussion]

## Stories
- [ ] #[TBD] — [Story title 1]
- [ ] #[TBD] — [Story title 2]

## Non-goals
[from discussion]

## Dependencies
- Blocked by: [verified blockers]
- Blocks: [what this feature unblocks]

## Parent
- Epic: #[epic_number]
BODY
)"
```

### 3. Create Stub Story Issues

For each story identified:

```bash
gh issue create \
  --title "[Story title]" \
  --body "$(cat <<'BODY'
## Description
[1-line summary]

## Acceptance Criteria
[to be added by /detail-story]

## File Scope
[to be added by /detail-story]

## Technical Notes
[to be added by /detail-story]

## Dependencies
- Blocked by:
- Blocks:

## Parent
- Epic: #[epic_number]
- Feature: #[feature_number]
BODY
)" \
  --label "type:story" --label "area:[area]" --label "status:todo"
```

For each story:
- Set intra-feature dependency ordering where applicable (e.g., story 2 depends on story 1 if they must be done in order)
- Set cross-feature dependencies if any
- If a blocker exists and isn't met, apply `status:blocked` label instead of `status:todo`

### 4. Update Feature Issue with Story Numbers

After all stories are created, update the feature issue's Stories section with actual issue numbers.

### 5. Verify Dependencies

For each story with blockers, verify using the shared blocker satisfaction criteria:
- Satisfied if: issue has `status:done` label OR issue state is `CLOSED`
- Unmet if: issue is `OPEN` without `status:done`

Apply `status:blocked` to any story with unmet blockers.

## Partial Failure

Same as `/create-epic`: report what was created, don't roll back, don't commit until all GitHub operations succeed.
