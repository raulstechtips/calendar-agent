# Feature Execution Reference

## Required Fields

### Frontmatter
- `name` — feature name
- `priority` — one of: `critical`, `high`, `medium`, `low`
- `areas` — array of area labels
- `parent-epic` — issue number of the parent epic

### Body Sections
- `## Description` — non-empty
- `## Stories` — at least one checklist item with `(#TBD)` placeholder

Additional sections (Non-goals, Dependencies, Parent) are expected but not blocking.

## Execution Steps

### 1. Create the Feature Issue

Write the draft body (without YAML frontmatter) to a temp file and create the issue:

```bash
cat <<'BODY' > /tmp/sdlc-feature-body.md
<draft body content without frontmatter>
BODY

FEAT_URL=$(gh issue create \
  --title "<name>" \
  --body-file /tmp/sdlc-feature-body.md \
  --label "type:feature" \
  --label "priority:<priority>" \
  --label "area:<area1>" \
  --label "area:<area2>")
FEAT_NUM=$(echo "$FEAT_URL" | grep -o '[0-9]*$')
```

**Note:** Do NOT add a `status:` label to features. Status labels are for stories only.

### 2. Create Stub Story Issues

For each item in the `## Stories` checklist, create a stub story issue:

```bash
STORY_URL=$(gh issue create \
  --title "<story name>" \
  --body "$(cat <<'EOF'
## Description
<one-line description from the draft checklist>

## Acceptance Criteria
- (to be defined via /sdlc:define story)

## Dependencies
- Blocked by: none
- Blocks: none

## Parent
- Epic: #<parent-epic from frontmatter>
- Feature: #<FEAT_NUM>
EOF
)" \
  --label "type:story" \
  --label "priority:<inherited from feature>" \
  --label "area:<inherited from feature>" \
  --label "status:todo")
STORY_NUM=$(echo "$STORY_URL" | grep -o '[0-9]*$')
```

Collect all created story issue numbers as you go.

### 3. Update Feature Issue Body

After creating all story stubs, the feature body contains `(#TBD)` placeholders next to each story name. Replace them with real issue numbers.

```bash
# Read the current feature body
BODY=$(gh issue view $FEAT_NUM --json body --jq '.body')

# Replace each #TBD with the real story issue number
# Pattern: find the line containing the story's name and (#TBD), replace #TBD with #<real-number>

# Write back the updated body
echo "$UPDATED_BODY" | gh issue edit $FEAT_NUM --body-file -
```

### 4. Update Parent Epic Body

Read the parent epic's body and replace the `#TBD` placeholder next to this feature's name with the real feature issue number.

```bash
# Read the parent epic's body
EPIC_BODY=$(gh issue view <parent-epic> --json body --jq '.body')

# Find the line with this feature's name and (#TBD), replace #TBD with #<FEAT_NUM>

# Write back
echo "$UPDATED_EPIC_BODY" | gh issue edit <parent-epic> --body-file -
```

### 5. Bidirectional Dependency Linking

If the feature draft has a `## Dependencies` section with `Blocked by: #N, #M`:

For each referenced issue number:

```bash
# Read the blocker's body
BLOCKER_BODY=$(gh issue view <N> --json body --jq '.body')

# Check if it has a Dependencies section with a "Blocks:" line
# If "Blocks: none" -> replace with "Blocks: #<FEAT_NUM>"
# If "Blocks: #X" -> append ", #<FEAT_NUM>"
# If no Dependencies section -> append one

# Write back
echo "$UPDATED_BLOCKER_BODY" | gh issue edit <N> --body-file -
```

### 6. Update PI.md (if feature is listed there)

Some PI plans list features explicitly under their epics. If `.claude/sdlc/pi/PI.md` has a `#TBD` next to this feature's name, replace it:

```bash
# Read PI.md, check if this feature's name appears with (#TBD)
# If so, replace (#TBD) with (#<FEAT_NUM>)
# Write back and commit
```

If PI.md was updated:

```bash
git add .claude/sdlc/pi/PI.md
git commit -m "docs(pi): add issue number for feature <name> (#<FEAT_NUM>)"
```

### 7. Clean Up Temp Files

```bash
rm -f /tmp/sdlc-feature-body.md
```

## Report Format

> **Created:**
> - Feature: #`<FEAT_NUM>` — "`<name>`"
>   - Labels: `type:feature`, `priority:<priority>`, `area:<areas>`
> - Story stub: #`<STORY1_NUM>` — "`<story1 name>`"
> - Story stub: #`<STORY2_NUM>` — "`<story2 name>`"
>
> **Updated:**
> - Feature #`<FEAT_NUM>` body: replaced `#TBD` placeholders with real issue numbers
> - Parent epic #`<parent-epic>` body: replaced `#TBD` with #`<FEAT_NUM>`
> - Blocker #`<N>` body: added `Blocks: #<FEAT_NUM>` to Dependencies
> - PI.md: replaced `#TBD` with #`<FEAT_NUM>` *(if applicable)*
> - Committed: `docs(pi): add issue number for feature <name> (#<FEAT_NUM>)` *(if applicable)*
