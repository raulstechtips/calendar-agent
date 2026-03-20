# Epic Update Reference

## Direct Update Criteria

**DIRECT** if all true:
- 1-2 fields changing (priority change, description tweak, single label change, non-goal addition, title edit)
- No features added or removed from the Features/Stories checklist
- No new dependencies introduced
- No scope expansion (epic doesn't grow to cover new areas)

**ESCALATE** if any true:
- Feature or story added/removed from the checklist
- Scope change (epic now covers additional areas or fundamentally different work)
- Success criteria rewrite (3+ criteria changing)
- Epic split into multiple epics
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

Common sections in an epic body:
- `## Overview` — description
- `## Success Criteria` — checkbox list
- `## Features` or `## Stories` — child checklist
- `## Non-goals` — bullet list
- `## Dependencies` — `Blocked by:` and `Blocks:` lines

### Step 3: Write back the full updated body

```bash
gh issue edit <N> --body-file /tmp/sdlc-update-body.md
```

### Label Changes

```bash
# Change priority
gh issue edit <N> --add-label "priority:high" --remove-label "priority:medium"

# Add area
gh issue edit <N> --add-label "area:search"

# Remove area
gh issue edit <N> --remove-label "area:search"
```

### Title Changes

```bash
gh issue edit <N> --title "New Epic Title"
```

### Clean Up

```bash
rm -f /tmp/sdlc-update-body.md
```

## Dependency Maintenance

When changing `Blocked by` or `Blocks` in the Dependencies section:

### Adding a new blocker (`Blocked by: #X`)

1. Update this epic's body: add `#X` to the `Blocked by:` line.
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

1. Update this epic's body: remove `#X` from the `Blocked by:` line (if it was the only one, set to `none`).
2. Update issue #X's body: remove `#<N>` from its `Blocks:` line (if it was the only one, set to `none`).

### Circular Dependency Check

After any dependency change, verify no circular dependency exists. Walk the blocker chain using DFS:

```bash
# For each blocker of this issue, check what IT is blocked by, recursively
# If we encounter the original issue number, there's a cycle

# Check immediate blockers
gh issue view <blocker> --json body --jq '.body'
# Parse "Blocked by:" line, check each of those, etc.
```

If a circular dependency is detected: STOP, report the cycle to the user, and revert the dependency change.

> "Circular dependency detected: #<N> -> #<X> -> #<Y> -> #<N>. Reverting the dependency change."

## Cascade Rules

After updating an epic:

- **If title changed**: check PI.md for references to the old title. Flag for update.
- **If priority changed**: flag child features/stories that inherit this priority.

```bash
# Find children by searching for "Epic: #<N>" in issue bodies
gh issue list --search "#<N> in:body" --label "type:feature" --json number,title --jq '.[] | "#\(.number) \(.title)"'
gh issue list --search "#<N> in:body" --label "type:story" --json number,title --jq '.[] | "#\(.number) \(.title)"'
```

- **If scope changed** (via escalation + reshape draft): flag all child features and stories.
- **If success criteria changed**: flag features whose scope derives from the changed criteria.
- **If deps changed**: update cross-references (handled in Dependency Maintenance above) and update PI.md if the dependency graph section references this epic.
