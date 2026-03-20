# Story Execution Reference

## Required Fields

### Frontmatter
- `name` — story name
- `priority` — one of: `critical`, `high`, `medium`, `low`
- `areas` — array of area labels
- `parent-epic` — issue number of the parent epic
- `parent-feature` — issue number of the parent feature (or `none` for flat epics)

### Body Sections
- `## Description` — non-empty
- `## Acceptance Criteria` — at least one checkbox item

Additional sections (File Scope, Technical Notes, Dependencies, Parent) are expected but not blocking.

## Execution Steps

### 1. Check Blocker Satisfaction

Before creating the story, determine its initial status label by checking whether its blockers are satisfied.

Parse the `## Dependencies` section for `Blocked by:` references.

**If no blockers** (or `Blocked by: none`): status will be `status:todo`.

**If blockers exist**, check each one:

```bash
# For each blocker issue number, check if it's done
gh issue view <N> --json labels,state \
  --jq '{done: ([.labels[].name] | contains(["status:done"])), closed: (.state == "CLOSED")}'
```

- If **all** blockers are satisfied (`done: true` or `closed: true`): status = `status:todo`
- If **any** blocker is unmet: status = `status:blocked`

Store the determined status for use in step 2.

### 2. Create the Story Issue

Write the draft body (without YAML frontmatter) to a temp file and create the issue with the full set of labels:

```bash
cat <<'BODY' > /tmp/sdlc-story-body.md
<draft body content without frontmatter>
BODY

STORY_URL=$(gh issue create \
  --title "<name>" \
  --body-file /tmp/sdlc-story-body.md \
  --label "type:story" \
  --label "priority:<priority>" \
  --label "area:<area1>" \
  --label "area:<area2>" \
  --label "<status:todo or status:blocked>")
STORY_NUM=$(echo "$STORY_URL" | grep -o '[0-9]*$')
```

**Label rules:**
- `type:story` — always
- `priority:<priority>` — from frontmatter
- `area:<area>` — one `--label` per area from frontmatter
- `status:todo` or `status:blocked` — exactly ONE status label, determined in step 1
- Multiple area labels are fine: `--label "area:auth" --label "area:api"`

### 3. Update Parent Feature's Stories Checklist

Read the parent feature's body and replace the `#TBD` placeholder next to this story's name with the real issue number.

```bash
# Read the parent feature's body
FEAT_BODY=$(gh issue view <parent-feature> --json body --jq '.body')

# Find the line with this story's name and (#TBD), replace #TBD with #<STORY_NUM>

# Write back
echo "$UPDATED_FEAT_BODY" | gh issue edit <parent-feature> --body-file -
```

**For flat epics** (`parent-feature: none`): update the parent epic's `## Stories` checklist instead:

```bash
EPIC_BODY=$(gh issue view <parent-epic> --json body --jq '.body')

# Find the line with this story's name and (#TBD), replace #TBD with #<STORY_NUM>

echo "$UPDATED_EPIC_BODY" | gh issue edit <parent-epic> --body-file -
```

### 4. Bidirectional Dependency Linking

If the story draft has `Blocked by: #N, #M` in its Dependencies section:

For each referenced blocker issue number:

```bash
# Read the blocker's body
BLOCKER_BODY=$(gh issue view <N> --json body --jq '.body')

# Update the "Blocks:" line in the blocker's Dependencies section:
# - If "Blocks: none" -> replace with "Blocks: #<STORY_NUM>"
# - If "Blocks: #X" -> change to "Blocks: #X, #<STORY_NUM>"
# - If "Blocks: #X, #Y" -> change to "Blocks: #X, #Y, #<STORY_NUM>"
# - If no Dependencies section exists -> append:
#     ## Dependencies
#     - Blocked by: (unchanged)
#     - Blocks: #<STORY_NUM>

# Write back
echo "$UPDATED_BLOCKER_BODY" | gh issue edit <N> --body-file -
```

### 5. Clean Up Temp Files

```bash
rm -f /tmp/sdlc-story-body.md
```

## Report Format

> **Created:**
> - Story: #`<STORY_NUM>` — "`<name>`"
>   - Labels: `type:story`, `priority:<priority>`, `area:<areas>`, `<status>`
>   - Status rationale: `<"all blockers satisfied" or "blocked by #N (status:in-progress)">`
>
> **Updated:**
> - Parent feature #`<parent-feature>` body: replaced `#TBD` with #`<STORY_NUM>`
> - Blocker #`<N>` body: added `Blocks: #<STORY_NUM>` to Dependencies
