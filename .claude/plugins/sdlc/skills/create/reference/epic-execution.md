# Epic Execution Reference

## Required Fields

### Frontmatter
- `name` — epic name
- `priority` — one of: `critical`, `high`, `medium`, `low`
- `areas` — array of area labels (e.g., `[auth, api]`)

### Body Sections
- `## Overview` — non-empty
- `## Success Criteria` — at least one checkbox item
- `## Features` or `## Stories` — at least one checklist item with `(#TBD)` placeholder (features for grouped epics, stories for flat epics)

Additional sections (Non-goals, Dependencies) are expected but not blocking.

## Execution Steps

### 1. Create the Epic Issue

Write the draft body (without YAML frontmatter) to a temp file and create the issue:

```bash
# Strip frontmatter from draft, write body to temp file
# (everything after the closing --- of the frontmatter)

cat <<'BODY' > /tmp/sdlc-epic-body.md
<draft body content without frontmatter>
BODY

EPIC_URL=$(gh issue create \
  --title "<name>" \
  --body-file /tmp/sdlc-epic-body.md \
  --label "type:epic" \
  --label "priority:<priority>" \
  --label "area:<area1>" \
  --label "area:<area2>")
EPIC_NUM=$(echo "$EPIC_URL" | grep -o '[0-9]*$')
```

**Note:** Do NOT add a `status:` label to epics. Status labels are for stories only.

### 2. Create Stub Child Issues

For each item in the `## Features` checklist (or `## Stories` for flat epics), create a stub child issue.

**Feature stubs** (grouped epic):

```bash
FEAT_URL=$(gh issue create \
  --title "<feature name>" \
  --body "$(cat <<'EOF'
## Description
<one-line description from the draft checklist>

## Stories
- (to be defined via /sdlc:define feature)

## Non-goals
(to be defined)

## Dependencies
- Blocked by: none
- Blocks: none

## Parent
- Epic: #<EPIC_NUM>
EOF
)" \
  --label "type:feature" \
  --label "priority:<inherited from epic>" \
  --label "area:<inherited from epic>")
FEAT_NUM=$(echo "$FEAT_URL" | grep -o '[0-9]*$')
```

**Story stubs** (flat epic):

```bash
STORY_URL=$(gh issue create \
  --title "<story name>" \
  --body "$(cat <<'EOF'
## Description
<one-line description from the draft checklist>

## Acceptance Criteria
- (to be defined via /sdlc:define story)

## File Scope
(to be defined)

## Technical Notes
(to be defined)

## Dependencies
- Blocked by: none
- Blocks: none

## Parent
- Epic: #<EPIC_NUM>
- Feature: none (flat epic)
EOF
)" \
  --label "type:story" \
  --label "priority:<inherited from epic>" \
  --label "area:<inherited from epic>" \
  --label "status:todo")
STORY_NUM=$(echo "$STORY_URL" | grep -o '[0-9]*$')
```

Collect all created child issue numbers as you go.

### 3. Update Epic Issue Body

After creating all children, the epic body contains `(#TBD)` placeholders next to each child name. Replace them with real issue numbers.

```bash
# Read the current epic body
BODY=$(gh issue view $EPIC_NUM --json body --jq '.body')

# Replace each #TBD with the real issue number
# For each child: replace the first occurrence of "(#TBD)" that follows the child's name
# Use a script or sequential sed replacements

# Write back the updated body
echo "$UPDATED_BODY" | gh issue edit $EPIC_NUM --body-file -
```

Pattern for replacement: find the line containing the child's name and `(#TBD)`, replace `#TBD` with `#<real-number>`.

### 4. Bidirectional Dependency Linking

If the epic draft has a `## Dependencies` section with `Blocked by: #N, #M`:

For each referenced issue number:

```bash
# Read the blocker's body
BLOCKER_BODY=$(gh issue view <N> --json body --jq '.body')

# Check if it has a Dependencies section with a "Blocks:" line
# If "Blocks: none" -> replace with "Blocks: #<EPIC_NUM>"
# If "Blocks: #X" -> append ", #<EPIC_NUM>"
# If no Dependencies section -> append one

# Write back
echo "$UPDATED_BLOCKER_BODY" | gh issue edit <N> --body-file -
```

### 5. Update PI.md

Read `.claude/sdlc/pi/PI.md` and replace the `#TBD` placeholder next to this epic's name with the real issue number.

```bash
# The PI.md has lines like:
# ### Epic: Auth Setup (#TBD)
# Replace (#TBD) with (#<EPIC_NUM>) for the matching epic name
```

Write the updated PI.md back.

### 6. Commit PI.md Update

```bash
git add .claude/sdlc/pi/PI.md
git commit -m "docs(pi): add issue numbers for epic <name> (#<EPIC_NUM>)"
```

### 7. Clean Up Temp Files

```bash
rm -f /tmp/sdlc-epic-body.md
```

## Report Format

> **Created:**
> - Epic: #`<EPIC_NUM>` — "`<name>`"
>   - Labels: `type:epic`, `priority:<priority>`, `area:<areas>`
> - Feature stub: #`<FEAT1_NUM>` — "`<feature1 name>`"
> - Feature stub: #`<FEAT2_NUM>` — "`<feature2 name>`"
>
> **Updated:**
> - Epic #`<EPIC_NUM>` body: replaced `#TBD` placeholders with real issue numbers
> - Blocker #`<N>` body: added `Blocks: #<EPIC_NUM>` to Dependencies
> - PI.md: replaced `#TBD` with #`<EPIC_NUM>`
> - Committed: `docs(pi): add issue numbers for epic <name> (#<EPIC_NUM>)`
