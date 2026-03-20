# Story Update Reference

## Direct Update Criteria

**DIRECT** if all true:
- 1-2 fields changing (AC edit, priority change, technical notes update, file scope change within same area, title edit, description tweak)
- No scope expansion (story doesn't grow to cover new files/areas beyond its current scope)
- No fundamental rework of the story's purpose
- Acceptance criteria changes limited to 1-2 items (add, remove, or reword)

**ESCALATE** if any true:
- Scope expansion (new files or areas not originally in scope)
- Fundamental rework (story purpose or approach changes)
- AC overhaul (3+ acceptance criteria changing)
- 3+ fields changing
- Story needs to be split

## Read-Modify-Write Pattern

**The `gh issue edit --body` flag replaces the ENTIRE body.** There is no partial edit. Always use the read-modify-write pattern.

### Step 1: Read current body

```bash
gh issue view <N> --json body --jq '.body' > /tmp/sdlc-update-body.md
```

Also read the full issue metadata for context:

```bash
gh issue view <N> --json number,title,body,labels,state
```

### Step 2: Modify the specific section

Read `/tmp/sdlc-update-body.md`, identify the section to change, and modify ONLY that section.

Common sections in a story body:
- `## Description` — story description
- `## Acceptance Criteria` — checkbox list
- `## File Scope` — files/directories involved
- `## Technical Notes` — implementation guidance
- `## Dependencies` — `Blocked by:` and `Blocks:` lines
- `## Parent` — epic and feature references

### Step 3: Write back the full updated body

```bash
gh issue edit <N> --body-file /tmp/sdlc-update-body.md
```

### Label Changes

```bash
# Change priority
gh issue edit <N> --add-label "priority:high" --remove-label "priority:medium"

# Change status
gh issue edit <N> --add-label "status:in-progress" --remove-label "status:todo"

# Add/remove area
gh issue edit <N> --add-label "area:api"
gh issue edit <N> --remove-label "area:api"
```

### Title Changes

```bash
gh issue edit <N> --title "feat(auth): new story title"
```

### Clean Up

```bash
rm -f /tmp/sdlc-update-body.md
```

## Dependency Maintenance

When changing `Blocked by` or `Blocks` in the Dependencies section:

### Adding a new blocker (`Blocked by: #X`)

1. Update this story's body: add `#X` to the `Blocked by:` line.
2. Update issue #X's body: add `#<N>` to its `Blocks:` line.

```bash
# Read the blocker's body
gh issue view <X> --json body --jq '.body' > /tmp/sdlc-blocker-body.md
```

Modify `/tmp/sdlc-blocker-body.md`:
- If `Blocks: none` -> replace with `Blocks: #<N>`
- If `Blocks: #A` -> change to `Blocks: #A, #<N>`
- If `Blocks: #A, #B` -> change to `Blocks: #A, #B, #<N>`
- If no Dependencies section exists -> append:
  ```
  ## Dependencies
  - Blocked by: none
  - Blocks: #<N>
  ```

```bash
gh issue edit <X> --body-file /tmp/sdlc-blocker-body.md
rm -f /tmp/sdlc-blocker-body.md
```

### Removing a blocker (`Blocked by: #X`)

1. Update this story's body: remove `#X` from the `Blocked by:` line (if it was the only one, set to `none`).
2. Update issue #X's body: remove `#<N>` from its `Blocks:` line (if it was the only one, set to `none`).

### Circular Dependency Check

After any dependency change, verify no circular dependency exists. Walk the blocker chain using DFS:

```bash
# Start from this story's blockers
# For each blocker, read its body and parse "Blocked by:" line
# For each of those, do the same
# If we encounter the original story number, there's a cycle

gh issue view <blocker> --json body --jq '.body'
# Parse "Blocked by:" line, recurse
```

If a circular dependency is detected: STOP, report the cycle to the user, and revert the dependency change.

> "Circular dependency detected: #<N> -> #<X> -> #<Y> -> #<N>. Reverting the dependency change."

### Status Label Recalculation After Dependency Change

After adding or removing a blocker, recalculate whether this story should be `status:blocked` or `status:todo`.

**Check each remaining blocker:**

```bash
gh issue view <blocker-number> --json labels,state \
  --jq '{done: ([.labels[].name] | contains(["status:done"])), closed: (.state == "CLOSED")}'
```

**Blocker satisfaction rule:**
- **Satisfied:** issue has `status:done` label OR issue state is `CLOSED`
- **Unmet:** issue is `OPEN` without `status:done`

**Update status label:**
- If ALL blockers are satisfied (or no blockers remain): set `status:todo`
- If ANY blocker is unmet: set `status:blocked`

```bash
# Example: unblock a story
gh issue edit <N> --add-label "status:todo" --remove-label "status:blocked"

# Example: block a story
gh issue edit <N> --add-label "status:blocked" --remove-label "status:todo"
```

Only change the status label if the current label doesn't match the calculated state. Do NOT change status for stories that are `status:in-progress` or `status:done` — those states are managed by the developer workflow, not by dependency recalculation.

## Cascade Rules

After updating a story:

- **If title changed**: update the parent feature's Stories checklist (or parent epic's Stories checklist for flat epics) to reflect the new title.

```bash
# Read parent feature body (or parent epic for flat epics)
gh issue view <parent-feature> --json body --jq '.body' > /tmp/sdlc-parent-body.md
```

Find the line referencing this story's old title and replace it with the new title. Keep the issue number reference intact.

```bash
gh issue edit <parent-feature> --body-file /tmp/sdlc-parent-body.md
rm -f /tmp/sdlc-parent-body.md
```

- **If deps changed**: bidirectional updates and status recalculation handled in Dependency Maintenance above.
- **If scope changed** (via escalation + reshape draft): no automatic cascade — the reshape draft should have accounted for any parent-level impacts.
