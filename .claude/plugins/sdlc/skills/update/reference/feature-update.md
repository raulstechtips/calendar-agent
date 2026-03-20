# Feature Update Reference

## Direct Update Criteria

**DIRECT** if all true:
- 1-2 fields changing (description edit, priority change, title edit, non-goal addition, single label change)
- No stories added or removed from the Stories checklist
- No new dependencies introduced
- No scope expansion

**ESCALATE** if any true:
- Story added or removed from the Stories checklist
- Scope expansion (feature now covers new areas or fundamentally different work)
- Dependency restructure (new blockers, removing critical blockers)
- 3+ fields changing

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

Common sections in a feature body:
- `## Description` — feature description
- `## Stories` — child story checklist
- `## Non-goals` — bullet list
- `## Dependencies` — `Blocked by:` and `Blocks:` lines
- `## Parent` — epic reference

### Step 3: Write back the full updated body

```bash
gh issue edit <N> --body-file /tmp/sdlc-update-body.md
```

### Label Changes

```bash
# Change priority
gh issue edit <N> --add-label "priority:high" --remove-label "priority:medium"

# Add/remove area
gh issue edit <N> --add-label "area:search"
gh issue edit <N> --remove-label "area:search"
```

### Title Changes

```bash
gh issue edit <N> --title "New Feature Title"
```

### Clean Up

```bash
rm -f /tmp/sdlc-update-body.md
```

## Dependency Maintenance

When changing `Blocked by` or `Blocks` in the Dependencies section:

### Adding a new blocker (`Blocked by: #X`)

1. Update this feature's body: add `#X` to the `Blocked by:` line.
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

1. Update this feature's body: remove `#X` from the `Blocked by:` line (if it was the only one, set to `none`).
2. Update issue #X's body: remove `#<N>` from its `Blocks:` line (if it was the only one, set to `none`).

### Circular Dependency Check

After any dependency change, verify no circular dependency exists. Walk the blocker chain using DFS:

```bash
# For each blocker of this issue, check what IT is blocked by, recursively
# If we encounter the original issue number, there's a cycle
gh issue view <blocker> --json body --jq '.body'
# Parse "Blocked by:" line, check each of those, etc.
```

If a circular dependency is detected: STOP, report the cycle to the user, and revert the dependency change.

> "Circular dependency detected: #<N> -> #<X> -> #<Y> -> #<N>. Reverting the dependency change."

## Cascade Rules

After updating a feature:

- **If title changed**: update the parent epic's Features/Stories checklist to reflect the new title.

```bash
# Read parent epic body
gh issue view <parent-epic> --json body --jq '.body' > /tmp/sdlc-parent-body.md
```

Find the line referencing this feature's old title and replace it with the new title. Keep the issue number reference intact.

```bash
gh issue edit <parent-epic> --body-file /tmp/sdlc-parent-body.md
rm -f /tmp/sdlc-parent-body.md
```

Also check PI.md for references to the old title:

```
Read .claude/sdlc/pi/PI.md
```

If PI.md references the old feature title, update it and commit:

```bash
git add .claude/sdlc/pi/PI.md
git commit -m "docs(pi): rename feature to <new title>"
```

- **If priority changed**: flag child stories that inherit this priority.

```bash
gh issue list --search "#<N> in:body" --label "type:story" --json number,title --jq '.[] | "#\(.number) \(.title)"'
```

- **If scope changed** (via escalation + reshape draft): flag all child stories for review.
- **If deps changed**: bidirectional updates handled in Dependency Maintenance above.
