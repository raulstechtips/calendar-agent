# gh CLI Issue Management Reference

> Comprehensive reference for every `gh issue` (and related) command needed by the SDLC skill suite.
> Verified against repo `raulstechtips/calendar-agent` on 2026-03-19.

---

## Table of Contents

1. [Creating Issues](#1-creating-issues)
2. [Reading Issues](#2-reading-issues)
3. [Listing and Querying Issues](#3-listing-and-querying-issues)
4. [Editing Issues](#4-editing-issues)
5. [Closing and Reopening Issues](#5-closing-and-reopening-issues)
6. [Label Management](#6-label-management)
7. [Searching Issues](#7-searching-issues)
8. [Sub-Issues and Parent-Child Relationships](#8-sub-issues-and-parent-child-relationships)
9. [Cross-Referencing and Auto-Close](#9-cross-referencing-and-auto-close)
10. [Batch Operations](#10-batch-operations)
11. [Appendix: JSON Fields Reference](#appendix-json-fields-reference)
12. [Appendix: jq Cookbook](#appendix-jq-cookbook)

---

## 1. Creating Issues

**Used by:** `sdlc:create`

### Basic creation with inline body

```bash
gh issue create \
  --title "feat(auth): add Google OAuth with refresh token support" \
  --body "## Description\nImplement OAuth flow.\n\n## Acceptance Criteria\n- [ ] Login works" \
  --label "type:story" \
  --label "area:auth" \
  --label "status:todo" \
  --label "priority:high" \
  --assignee "@me"
```

**Output:**
```
https://github.com/raulstechtips/calendar-agent/issues/119
```

Returns the issue URL on stdout. The issue number can be extracted from this URL.

### Flags reference

| Flag | Short | Description |
|------|-------|-------------|
| `--title` | `-t` | Issue title (required unless interactive) |
| `--body` | `-b` | Inline body string |
| `--body-file` | `-F` | Read body from file (`-` for stdin) |
| `--label` | `-l` | Add label (repeatable for multiple labels) |
| `--assignee` | `-a` | Assign user (repeatable; `@me` for self) |
| `--milestone` | `-m` | Add to milestone by name |
| `--project` | `-p` | Add to project by title (requires `project` scope) |
| `--template` | `-T` | Use issue template as starting body |
| `--editor` | `-e` | Open text editor for title+body |
| `--web` | `-w` | Open browser to create issue |

### Creating with a markdown body file (recommended for complex bodies)

```bash
# Write the body to a temp file, then create
cat <<'BODY' > /tmp/issue-body.md
## Description
Implement the calendar event creation tool with recurrence support.

## Parent
Epic: #1

## Acceptance Criteria
- [ ] User can create single events
- [ ] User can create recurring events with RRULE
- [ ] Confirmation card shows recurrence pattern

## Dependencies
Blocked by: #9, #12
Blocks: #25

## Technical Notes
Uses Google Calendar API v3 `events.insert` endpoint.
BODY

gh issue create \
  --title "feat(agent): calendar event creation tool" \
  --body-file /tmp/issue-body.md \
  --label "type:story" \
  --label "area:agents" \
  --label "status:todo" \
  --label "priority:high"
```

### Creating with heredoc (no temp file)

```bash
gh issue create \
  --title "feat(agent): calendar event creation tool" \
  --body "$(cat <<'EOF'
## Description
Implement the calendar event creation tool with recurrence support.

## Parent
Epic: #1

## Acceptance Criteria
- [ ] User can create single events
- [ ] User can create recurring events with RRULE

## Dependencies
Blocked by: #9, #12
EOF
)" \
  --label "type:story" \
  --label "area:agents" \
  --label "status:todo"
```

### Creating with stdin pipe

```bash
echo "## Description\nAuto-generated issue body" | gh issue create \
  --title "chore: cleanup" \
  --body-file - \
  --label "type:chore"
```

### Extracting the issue number from creation output

```bash
# gh issue create outputs a URL like: https://github.com/owner/repo/issues/119
URL=$(gh issue create --title "test" --body "test" --label "type:story")
NUMBER=$(echo "$URL" | grep -o '[0-9]*$')
echo "Created issue #$NUMBER"
```

### Creating multiple issues in sequence

There is no bulk-create command. Issues must be created sequentially:

```bash
# Create epic, capture its number, then create children referencing it
EPIC_URL=$(gh issue create \
  --title "EPIC: User Authentication" \
  --body "## Overview\nAuthentication system.\n\n## Features\n- [ ] Google OAuth\n- [ ] Token refresh" \
  --label "type:epic" --label "status:todo" --label "area:auth")
EPIC_NUM=$(echo "$EPIC_URL" | grep -o '[0-9]*$')

STORY_URL=$(gh issue create \
  --title "feat(auth): Google OAuth flow" \
  --body "## Parent\nEpic: #${EPIC_NUM}\n\n## Acceptance Criteria\n- [ ] Login works" \
  --label "type:story" --label "status:todo" --label "area:auth")
```

### Caveats

- No `--json` output flag on `create` -- returns only the URL as plain text
- Multiple `--label` flags required (comma-separated `"a,b"` works for a single `--label` flag too)
- `--project` requires the `project` OAuth scope: `gh auth refresh -s project`
- No way to set issue type (the GitHub UI "issue type" feature) via `gh issue create` -- must use GraphQL or the issue type is inferred from templates
- Max body size: 65536 characters (GitHub API limit)

---

## 2. Reading Issues

**Used by:** `sdlc:create` (verify after creation), `sdlc:update` (read-before-edit), `sdlc:status`, `sdlc:reconcile`, `sdlc:retro`

### Basic view (human-readable)

```bash
gh issue view 118
```

Output: renders the issue title, state, labels, body as a formatted terminal view.

### JSON output with specific fields

```bash
gh issue view 118 --json number,title,body,labels,state,assignees,createdAt,updatedAt
```

**Example output (truncated):**
```json
{
  "assignees": [],
  "body": "## Description\nThe agent cannot create recurring events...",
  "createdAt": "2026-03-18T01:58:14Z",
  "labels": [
    {"name": "type:bug", "description": "Bug report", "color": "DC143C"},
    {"name": "status:todo", "description": "Ready to be picked up", "color": "EEEEEE"}
  ],
  "number": 118,
  "state": "OPEN",
  "title": "Cannot create or update recurring events",
  "updatedAt": "2026-03-18T02:51:32Z"
}
```

### All available JSON fields

```
assignees, author, body, closed, closedAt, closedByPullRequestsReferences,
comments, createdAt, id, isPinned, labels, milestone, number, projectCards,
projectItems, reactionGroups, state, stateReason, title, updatedAt, url
```

**Field details:**

| Field | Type | Notes |
|-------|------|-------|
| `assignees` | `[{login, id, name, ...}]` | List of assigned users |
| `author` | `{login, id, name, is_bot}` | Issue creator |
| `body` | `string` | Full markdown body |
| `closed` | `bool` | Whether issue is closed |
| `closedAt` | `string\|null` | ISO 8601 timestamp |
| `closedByPullRequestsReferences` | `[{number, url, repository}]` | PRs that closed this issue |
| `comments` | `[{author, body, createdAt, url, ...}]` | All comments |
| `createdAt` | `string` | ISO 8601 timestamp |
| `id` | `string` | Node ID (e.g., `I_kwDORnARWM7z6jxr`) -- needed for GraphQL mutations |
| `isPinned` | `bool` | Whether issue is pinned |
| `labels` | `[{name, color, description, id}]` | All labels |
| `milestone` | `{title, number, ...}\|null` | Associated milestone |
| `number` | `int` | Issue number |
| `projectCards` | `[...]` | Classic project cards (requires `read:project` scope) |
| `projectItems` | `[...]` | ProjectV2 items (requires `read:project` scope) |
| `reactionGroups` | `[{content, users}]` | Emoji reactions |
| `state` | `string` | `"OPEN"` or `"CLOSED"` |
| `stateReason` | `string` | `""`, `"COMPLETED"`, `"NOT_PLANNED"`, or `"DUPLICATE"` |
| `title` | `string` | Issue title |
| `updatedAt` | `string` | ISO 8601 timestamp |
| `url` | `string` | Full GitHub URL |

### Using --jq to extract specific data

```bash
# Extract just the body
gh issue view 118 --json body --jq '.body'

# Extract label names as a flat list
gh issue view 118 --json labels --jq '[.labels[].name]'
# Output: ["type:bug","status:todo","priority:critical","area:agents"]

# Get the node ID (needed for GraphQL mutations like addSubIssue)
gh issue view 118 --json id --jq '.id'
# Output: I_kwDORnARWM7z6jxr

# Check which PR closed an issue
gh issue view 111 --json closedByPullRequestsReferences --jq '.closedByPullRequestsReferences[].number'
# Output: 112

# Count comments
gh issue view 118 --json comments --jq '.comments | length'
# Output: 1
```

### Parsing body sections with jq

```bash
# Extract a specific markdown section (e.g., "## Features" from an epic body)
gh issue view 1 --json body \
  --jq '.body | capture("## Features\n(?<features>[\\s\\S]*?)(\n## |$)") | .features'
```

**Output:**
```
- [x] Auth & OAuth (Google OAuth with incremental consent)
- [x] FastAPI Backend Core (middleware, endpoints, Redis)
- [x] LangGraph Agent Pipeline (ReAct agent, calendar tools, guardrails)
- [ ] Infrastructure & Deploy (Docker, Terraform, CI/CD)
```

```bash
# Parse checklist items into structured data
gh issue view 1 --json body \
  --jq '.body | [scan("- \\[( |x)\\] (.+)") | {done: (.[0] == "x"), text: .[1]}]'
```

**Output:**
```json
[
  {"done": true, "text": "Auth & OAuth (Google OAuth with incremental consent)"},
  {"done": true, "text": "FastAPI Backend Core (middleware, endpoints, Redis)"},
  {"done": false, "text": "Infrastructure & Deploy (Docker, Terraform, CI/CD)"}
]
```

```bash
# Extract the first 3 lines of the body
gh issue view 118 --json body --jq '.body | split("\n") | .[:3] | .[]'

# Extract "Blocked by" references from body
gh issue view 42 --json body \
  --jq '.body | capture("Blocked by: (?<refs>#[\\d, #]+)") | .refs | split(", ") | map(ltrimstr("#") | tonumber)'
# Output: [45, 46]
```

### Viewing comments

```bash
# Human-readable comments
gh issue view 118 --comments

# JSON comments with author and timestamp
gh issue view 118 --json comments --jq '.comments[] | {author: .author.login, date: .createdAt, body: (.body | .[:100])}'
```

### Using the REST API for additional fields

The `gh issue view --json` fields are a subset of what the REST API provides. For fields like `parent` or `sub_issues_summary`, use `gh api`:

```bash
# Get parent and sub-issues summary (not available via gh issue view)
gh api repos/{owner}/{repo}/issues/118 --jq '{number, parent, sub_issues_summary}'
```

**Output:**
```json
{
  "number": 118,
  "parent": null,
  "sub_issues_summary": {"completed": 0, "percent_completed": 0, "total": 0}
}
```

### Caveats

- `projectCards` and `projectItems` fields require the `read:project` OAuth scope -- requesting them without it causes a GraphQL error that fails the entire command
- The `body` field returns raw markdown, not rendered HTML (use `bodyHTML` via GraphQL if needed)
- `stateReason` is empty string `""` for open issues, not `null`
- `closedByPullRequestsReferences` is empty `[]` for open issues and for issues closed manually (without a PR)

---

## 3. Listing and Querying Issues

**Used by:** `sdlc:status`, `sdlc:reconcile`, `sdlc:retro`, `sdlc:create` (duplicate detection)

### Basic listing

```bash
# Default: open issues, most recently created first, limit 30
gh issue list

# All states
gh issue list --state all

# Only closed
gh issue list --state closed

# Custom limit
gh issue list --limit 100

# JSON output
gh issue list --json number,title,labels,state,assignees
```

### Filtering by labels (AND logic)

Multiple `--label` flags use AND logic -- an issue must have ALL specified labels:

```bash
# Issues that are stories AND todo AND in the auth area
gh issue list --label "type:story" --label "status:todo" --label "area:auth"

# Issues that are blocked AND in agents area
gh issue list --label "status:blocked" --label "area:agents"

# All epics
gh issue list --label "type:epic" --state all
```

**Verified:** `--label "status:todo" --label "area:agents"` returns only issues with BOTH labels.

### Filtering by other fields

```bash
# By assignee
gh issue list --assignee "chakraborty29"
gh issue list --assignee "@me"

# By author
gh issue list --author "chakraborty29"

# By milestone
gh issue list --milestone "Sprint 1"

# By mention
gh issue list --mention "@me"
```

### Using --search for complex queries

The `--search` flag accepts GitHub search syntax:

```bash
# Text search in title and body
gh issue list --search "recurrence in:body"

# Search with label qualifiers
gh issue list --search "is:open label:type:story label:status:blocked label:area:auth"

# Search by date
gh issue list --search "created:>2026-03-15"
gh issue list --search "updated:2026-03-14..2026-03-18"

# Sort by various fields
gh issue list --search "sort:updated-desc"
gh issue list --search "sort:created-asc"
gh issue list --search "sort:comments-desc"

# Issues with no assignee
gh issue list --search "no:assignee label:status:todo"

# Issues mentioning a specific issue number in body
gh issue list --search "#42 in:body"

# Issues without a specific label
gh issue list --search "-label:status:done"
```

### Combining --label and --search

```bash
# --label for AND filtering, --search for text/sort
gh issue list --label "type:story" --label "area:auth" --search "sort:created-asc"
```

### JSON output with jq filtering

```bash
# Clean tabular output
gh issue list --json number,title,labels \
  --jq '.[] | "\(.number)\t\(.title)\t\(.labels | map(.name) | join(","))"'
```

**Output:**
```
118	Cannot create or update recurring events	type:bug,status:todo,priority:critical,area:agents
117	Deleting a recurring event removes entire series	type:bug,status:todo,priority:critical,area:agents
116	Multi-action requests only execute first action	type:bug,status:todo,priority:critical,area:agents
```

```bash
# Filter in jq for complex conditions (e.g., issues with BOTH status:todo AND area:agents)
gh issue list --json number,title,labels --limit 50 \
  --jq '.[] | select(.labels | map(.name) | contains(["status:todo","area:agents"])) | {number, title}'
```

```bash
# Group issues by status for a dashboard
gh issue list --state all --limit 200 --json number,labels \
  --jq 'group_by(
    .labels | map(.name) |
    if contains(["status:done"]) then "done"
    elif contains(["status:in-progress"]) then "in-progress"
    elif contains(["status:blocked"]) then "blocked"
    elif contains(["status:todo"]) then "todo"
    else "unlabeled" end
  ) | map({
    status: .[0].labels | map(.name) |
      if contains(["status:done"]) then "done"
      elif contains(["status:in-progress"]) then "in-progress"
      elif contains(["status:blocked"]) then "blocked"
      elif contains(["status:todo"]) then "todo"
      else "unlabeled" end,
    count: length
  })'
```

**Output (from real repo):**
```json
[
  {"count": 53, "status": "done"},
  {"count": 4, "status": "todo"},
  {"count": 1, "status": "unlabeled"}
]
```

### Pagination

```bash
# gh issue list has a --limit flag (default 30, max ~1000 per call)
gh issue list --limit 200 --state all --json number,title

# For repos with >1000 issues, use gh api with --paginate
gh api repos/{owner}/{repo}/issues --paginate --jq '.[].number'
```

**Note:** `gh issue list --limit 200` returned 58 issues (all issues in the repo) when there are fewer than the limit. The CLI handles the GraphQL cursor pagination internally up to the limit.

### All available JSON fields for list

Same as `gh issue view`:
```
assignees, author, body, closed, closedAt, closedByPullRequestsReferences,
comments, createdAt, id, isPinned, labels, milestone, number, projectCards,
projectItems, reactionGroups, state, stateReason, title, updatedAt, url
```

**Performance warning:** Requesting `body` or `comments` on a list of many issues is slow because each requires a separate API call. For bulk operations, request only the fields you need:
```bash
# Fast (metadata only)
gh issue list --limit 200 --json number,title,labels,state

# Slow (fetches full body for each issue)
gh issue list --limit 200 --json number,title,body
```

### Caveats

- `--label` flags are AND not OR -- to get OR behavior, use `--search "label:type:story label:type:bug"` (search qualifiers in the same query are OR within the same qualifier type) -- **actually, this is also AND in GitHub search**. True OR requires separate queries.
- `--limit 0` does not mean unlimited -- it means "use default (30)"
- Default sort is by creation date descending; use `--search "sort:..."` to change
- `--search` query syntax follows [GitHub Search syntax](https://docs.github.com/en/search-github/searching-on-github/searching-issues-and-pull-requests)
- When `--search` is used with `--label`, both conditions are ANDed together
- `projectCards` and `projectItems` require `read:project` scope -- will error if included without it

---

## 4. Editing Issues

**Used by:** `sdlc:update`, `sdlc:reconcile`

### Changing title

```bash
gh issue edit 118 --title "fix(agent): add recurrence and colorId to calendar tools"
```

### Replacing the entire body

```bash
# Inline
gh issue edit 118 --body "## Description\nNew body content here."

# From file
gh issue edit 118 --body-file /tmp/updated-body.md

# From stdin
echo "New body" | gh issue edit 118 --body-file -

# From heredoc
gh issue edit 118 --body "$(cat <<'EOF'
## Description
Updated description.

## Acceptance Criteria
- [ ] Recurrence parameter added
- [ ] Color ID parameter added
EOF
)"
```

### Adding and removing labels

```bash
# Add labels
gh issue edit 118 --add-label "status:in-progress"

# Remove labels
gh issue edit 118 --remove-label "status:todo"

# Swap status labels (add + remove in one command)
gh issue edit 118 --add-label "status:in-progress" --remove-label "status:todo"

# Add multiple labels
gh issue edit 118 --add-label "status:blocked" --add-label "priority:critical"

# Comma-separated also works
gh issue edit 118 --add-label "status:blocked,priority:critical"
```

### Assignee management

```bash
gh issue edit 118 --add-assignee "@me"
gh issue edit 118 --add-assignee "username1,username2"
gh issue edit 118 --remove-assignee "username1"
```

### Milestone management

```bash
gh issue edit 118 --milestone "Sprint 2"
gh issue edit 118 --remove-milestone
```

### Surgical body edits (partial update)

**The `gh issue edit --body` flag replaces the ENTIRE body.** There is no built-in partial edit. To surgically update one section, use a read-modify-write pattern:

```bash
# Step 1: Read current body
BODY=$(gh issue view 118 --json body --jq '.body')

# Step 2: Modify in-place (e.g., update the Dependencies section)
# Using sed to replace a section:
NEW_BODY=$(echo "$BODY" | sed '/^## Dependencies$/,/^## /{
  /^## Dependencies$/!{/^## /!d}
  /^## Dependencies$/a\
Blocked by: #45, #46, #50\
Blocks: #52
}')

# Step 3: Write back
echo "$NEW_BODY" | gh issue edit 118 --body-file -
```

**More robust approach using a script:**

```bash
# Read body, replace a section, write back
gh issue view 42 --json body --jq '.body' > /tmp/body.md

# Edit the file with any tool (sed, python, manual)
# For example, update the status section:
python3 -c "
import re, sys
body = open('/tmp/body.md').read()
body = re.sub(
    r'(## Dependencies\n).*?(\n## |\Z)',
    r'\1Blocked by: #45, #46\nBlocks: #52\n\2',
    body,
    flags=re.DOTALL
)
sys.stdout.write(body)
" > /tmp/body-updated.md

gh issue edit 42 --body-file /tmp/body-updated.md
```

**Recommended pattern for `sdlc:update`:** Read the body as a string, parse it into sections (split on `## ` headers), modify the target section, rejoin, and write back. This avoids fragile regex.

### Editing multiple issues at once (label operations only)

```bash
# Add a label to multiple issues in one command
gh issue edit 116 117 118 --add-label "sprint:day2"

# Remove a label from multiple issues
gh issue edit 116 117 118 --remove-label "sprint:day1"
```

**Note:** Multi-issue edit only works for label, assignee, milestone, and project changes. You CANNOT set `--title` or `--body` when editing multiple issues.

### Flags reference

| Flag | Description |
|------|-------------|
| `--title` / `-t` | Set new title (single issue only) |
| `--body` / `-b` | Set new body (single issue only) |
| `--body-file` / `-F` | Read body from file (single issue only) |
| `--add-label` | Add labels (repeatable, comma-separated) |
| `--remove-label` | Remove labels (repeatable, comma-separated) |
| `--add-assignee` | Add assignees (`@me` supported) |
| `--remove-assignee` | Remove assignees |
| `--milestone` / `-m` | Set milestone |
| `--remove-milestone` | Remove milestone |
| `--add-project` | Add to project (requires `project` scope) |
| `--remove-project` | Remove from project |

### Caveats

- No `--json` output flag -- edit commands produce no parseable output on success
- No partial body edit -- must read-modify-write the full body
- Multi-issue edit (`gh issue edit 1 2 3`) does NOT support `--title` or `--body`
- No way to edit comments via `gh issue edit` -- use `gh api` for that
- Label names with colons (e.g., `status:todo`) work fine -- no escaping needed

---

## 5. Closing and Reopening Issues

**Used by:** `sdlc:reconcile` (auto-close completed parents), `sdlc:update`

### Closing an issue

```bash
# Basic close (reason defaults to "completed")
gh issue close 118

# Close with a specific reason
gh issue close 118 --reason "completed"
gh issue close 118 --reason "not planned"

# Close as duplicate
gh issue close 118 --duplicate-of 42

# Close with a comment
gh issue close 118 --comment "All child stories are done. Auto-closing parent."

# Close with both reason and comment
gh issue close 118 --reason "completed" --comment "Resolved by #112"
```

### Close reasons

| Reason | Description |
|--------|-------------|
| `completed` | Default. Issue was resolved. |
| `not planned` | Issue won't be addressed. |
| `duplicate` | Requires `--duplicate-of <number\|url>` |

### Reopening an issue

```bash
# Basic reopen
gh issue reopen 118

# Reopen with a comment
gh issue reopen 118 --comment "Reopening -- the fix in #112 introduced a regression."
```

### Caveats

- `--reason` flag values are: `completed`, `not planned`, `duplicate` (not custom strings)
- `--duplicate-of` implies `--reason duplicate` -- you don't need both
- No `--json` output on close/reopen -- returns human-readable confirmation only
- Closing does NOT remove labels -- the `status:done` label must be added separately via `gh issue edit`
- There is no `gh issue close 1 2 3` for bulk close -- must close one at a time

---

## 6. Label Management

**Used by:** `sdlc:create` (bootstrap label taxonomy), `sdlc:reconcile` (label hygiene)

### Creating a label

```bash
gh label create "type:story" \
  --color "6495ED" \
  --description "Implementable unit of work"
```

**Output:**
```
✓ Label "type:story" created in raulstechtips/calendar-agent
```

### Creating with --force (idempotent upsert)

```bash
# Creates if missing, updates color/description if exists
gh label create "type:story" \
  --color "6495ED" \
  --description "Implementable unit of work" \
  --force
```

This is essential for `sdlc:create` -- run the full taxonomy with `--force` to ensure all labels exist without erroring on duplicates.

### Editing a label

```bash
# Change color
gh label edit "type:story" --color "4169E1"

# Change description
gh label edit "type:story" --description "Updated description"

# Rename a label
gh label edit "type:story" --name "type:task"
```

### Deleting a label

```bash
# Interactive (prompts for confirmation)
gh label delete "type:spike"

# Non-interactive
gh label delete "type:spike" --yes
```

### Listing labels

```bash
# Default list (limit 30)
gh label list

# All labels (increase limit)
gh label list --limit 100

# JSON output
gh label list --json name,color,description

# Search labels by name
gh label list --search "status"

# Sort by name
gh label list --sort name

# Sort by creation date descending
gh label list --sort created --order desc
```

**JSON fields for labels:**
```
color, createdAt, description, id, isDefault, name, updatedAt, url
```

### Clean tabular output

```bash
gh label list --json name,color,description \
  --jq '.[] | "\(.name)\t#\(.color)\t\(.description)"'
```

**Output (from real repo):**
```
type:epic       #7B68EE   Top-level initiative
type:feature    #4169E1   Feature under an epic
type:story      #6495ED   Implementable unit of work
type:bug        #DC143C   Bug report
status:todo     #EEEEEE   Ready to be picked up
status:in-progress  #FFFF00   Currently being worked on
status:done     #2E8B57   Completed
status:blocked  #FF4500   Blocked by dependency
priority:critical   #8B0000   Must ship
priority:high   #FF6347   Important for MVP
priority:medium #FFA07A   Nice to have
priority:low    #FFD700   Post-MVP improvement
area:api        #20B2AA   FastAPI backend
area:auth       #9370DB   Authentication & OAuth
area:ui         #FF69B4   Frontend UI
area:agents     #32CD32   LangGraph agent pipeline
area:infra      #708090   Infrastructure & deployment
area:search     #DAA520   Azure AI Search & vectors
```

### Bootstrapping the full label taxonomy

Script for `sdlc:create` to ensure all labels exist:

```bash
# Type labels
gh label create "type:epic"    -c "7B68EE" -d "Top-level initiative" --force
gh label create "type:feature" -c "4169E1" -d "Feature under an epic" --force
gh label create "type:story"   -c "6495ED" -d "Implementable unit of work" --force
gh label create "type:bug"     -c "DC143C" -d "Bug report" --force
gh label create "type:spike"   -c "FF8C00" -d "Research/investigation task" --force
gh label create "type:chore"   -c "C0C0C0" -d "Maintenance and cleanup task" --force

# Status labels
gh label create "status:todo"        -c "EEEEEE" -d "Ready to be picked up" --force
gh label create "status:in-progress" -c "FFFF00" -d "Currently being worked on" --force
gh label create "status:done"        -c "2E8B57" -d "Completed" --force
gh label create "status:blocked"     -c "FF4500" -d "Blocked by dependency" --force

# Priority labels
gh label create "priority:critical" -c "8B0000" -d "Must ship" --force
gh label create "priority:high"     -c "FF6347" -d "Important for MVP" --force
gh label create "priority:medium"   -c "FFA07A" -d "Nice to have" --force
gh label create "priority:low"      -c "FFD700" -d "Post-MVP improvement" --force

# Area labels
gh label create "area:api"     -c "20B2AA" -d "FastAPI backend" --force
gh label create "area:auth"    -c "9370DB" -d "Authentication & OAuth" --force
gh label create "area:ui"      -c "FF69B4" -d "Frontend UI" --force
gh label create "area:agents"  -c "32CD32" -d "LangGraph agent pipeline" --force
gh label create "area:infra"   -c "708090" -d "Infrastructure & deployment" --force
gh label create "area:search"  -c "DAA520" -d "Azure AI Search & vectors" --force
```

### Caveats

- Color must be 6-character hex WITHOUT the `#` prefix
- `--force` on `gh label create` makes it idempotent (upsert behavior)
- `gh label delete` has no `--json` output
- No bulk label create command -- must be sequential
- GitHub default labels (bug, enhancement, etc.) coexist with custom labels -- delete them explicitly if unwanted
- `isDefault` field in JSON indicates GitHub's auto-created labels

---

## 7. Searching Issues

**Used by:** `sdlc:status`, `sdlc:reconcile`, `sdlc:retro`

### gh issue list --search vs gh search issues

There are two search mechanisms:

| Feature | `gh issue list --search` | `gh search issues` |
|---------|--------------------------|---------------------|
| **Scope** | Single repo (current or `--repo`) | Cross-repo, global search |
| **Backend** | GitHub Issues API with filter params | GitHub Search API |
| **Speed** | Faster for single-repo queries | Slower, rate-limited separately |
| **Result limit** | Up to ~1000 with `--limit` | Up to 1000 |
| **Combinable with** | `--label`, `--assignee`, `--state` flags | Only its own flags |
| **JSON fields** | Full issue fields (body, comments, etc.) | Subset of fields |
| **Rate limiting** | Standard API rate limit | Search API: 30 req/min (authenticated) |
| **Best for** | Single-repo queries by SDLC skills | Cross-repo or full-text search |

**Recommendation for SDLC skills:** Always use `gh issue list` with `--label` and `--search` for single-repo operations. Reserve `gh search issues` for cross-repo scenarios only.

### gh issue list --search query syntax

The `--search` flag accepts GitHub's [issue search syntax](https://docs.github.com/en/search-github/searching-on-github/searching-issues-and-pull-requests):

```bash
# Text in title or body
gh issue list --search "calendar tool"

# Text in specific location
gh issue list --search "recurrence in:body"
gh issue list --search "EPIC in:title"

# By label (within --search)
gh issue list --search "label:type:story"
gh issue list --search "label:type:story label:area:auth"   # AND

# Negation
gh issue list --search "-label:status:done"
gh issue list --search "-is:closed"

# By date
gh issue list --search "created:>2026-03-01"
gh issue list --search "updated:>=2026-03-15"
gh issue list --search "closed:2026-03-14..2026-03-18"

# By assignee
gh issue list --search "assignee:chakraborty29"
gh issue list --search "no:assignee"

# Sorting
gh issue list --search "sort:updated-desc"
gh issue list --search "sort:created-asc"
gh issue list --search "sort:reactions-+1-desc"      # Most thumbs-up
gh issue list --search "sort:comments-desc"

# Combined complex query: "all blocked auth stories"
gh issue list --label "type:story" --label "status:blocked" --label "area:auth" \
  --json number,title,labels

# "All open stories not yet assigned, sorted by priority"
gh issue list --label "type:story" --search "no:assignee sort:created-asc" \
  --json number,title,labels
```

### gh search issues syntax

```bash
# Basic repo-scoped search
gh search issues --repo raulstechtips/calendar-agent "recurrence" \
  --json number,title,url

# With filters
gh search issues --repo raulstechtips/calendar-agent \
  --label "type:bug" \
  --state open \
  --limit 10

# Full-text across all repos you have access to
gh search issues "calendar agent RRULE"
```

**Available flags for `gh search issues`:**
- `--repo` -- scope to a repo
- `--label` -- filter by label
- `--state` -- open/closed
- `--assignee` -- filter by assignee
- `--author` -- filter by author
- `--match` -- search in title, body, or comments
- `--language` -- filter by repo language
- `--limit` -- max results
- `--sort` -- sort by: best-match, created, updated, comments, reactions, etc.
- `--order` -- asc/desc
- `--json` -- JSON output with fields
- `--jq` -- jq filter

### Example: complex query for sdlc:status

```bash
# Dashboard: count issues by status across all types
gh issue list --state all --limit 500 --json labels \
  --jq '
    def status: .labels | map(.name) |
      if contains(["status:done"]) then "done"
      elif contains(["status:in-progress"]) then "in-progress"
      elif contains(["status:blocked"]) then "blocked"
      elif contains(["status:todo"]) then "todo"
      else "no-status" end;
    group_by(status) | map({status: .[0] | status, count: length}) | sort_by(.status)
  '
```

### Caveats

- GitHub search is eventually consistent -- newly created issues may not appear in search for a few seconds
- `gh search issues` has a stricter rate limit (30 searches/minute authenticated)
- `--search` label syntax uses `label:name` (no quotes needed even with colons)
- Combining `--label` flags (AND) with `--search` label qualifiers is additive (more AND)
- There is no OR operator in GitHub issue search for labels -- for OR, make separate queries and merge results
- Search results max at 1000 items regardless of `--limit` setting

---

## 8. Sub-Issues and Parent-Child Relationships

**Used by:** `sdlc:create`, `sdlc:reconcile`, `sdlc:status`

### Native sub-issues support

GitHub has **native sub-issue support** available through:
1. **GraphQL API** -- `subIssues`, `parent`, `addSubIssue`, `removeSubIssue`
2. **REST API** -- `sub_issues_summary`, `parent` fields
3. **CLI** -- No dedicated `gh` subcommand yet; must use `gh api graphql`

### Reading sub-issues (GraphQL)

```bash
# List sub-issues of an epic
gh api graphql -f query='
  query($owner: String!, $repo: String!, $number: Int!) {
    repository(owner: $owner, name: $repo) {
      issue(number: $number) {
        title
        subIssues(first: 50) {
          nodes {
            number
            title
            state
            labels(first: 10) { nodes { name } }
          }
        }
      }
    }
  }
' -f owner=raulstechtips -f repo=calendar-agent -F number=1
```

### Reading parent of an issue (GraphQL)

```bash
gh api graphql -f query='
  query($owner: String!, $repo: String!, $number: Int!) {
    repository(owner: $owner, name: $repo) {
      issue(number: $number) {
        title
        parent {
          number
          title
        }
      }
    }
  }
' -f owner=raulstechtips -f repo=calendar-agent -F number=118
```

**Output:**
```json
{
  "data": {
    "repository": {
      "issue": {
        "title": "Cannot create or update recurring events",
        "parent": null
      }
    }
  }
}
```

### Reading sub-issues summary (REST API)

```bash
gh api repos/{owner}/{repo}/issues/1 --jq '.sub_issues_summary'
```

**Output:**
```json
{"completed": 0, "percent_completed": 0, "total": 0}
```

### Adding a sub-issue (GraphQL mutation)

```bash
# First, get the node IDs for both issues
PARENT_ID=$(gh issue view 1 --json id --jq '.id')
CHILD_ID=$(gh issue view 118 --json id --jq '.id')

# Add the sub-issue relationship
gh api graphql -f query='
  mutation($parentId: ID!, $childId: ID!) {
    addSubIssue(input: {
      issueId: $parentId
      subIssueId: $childId
    }) {
      issue { number title }
      subIssue { number title }
    }
  }
' -f parentId="$PARENT_ID" -f childId="$CHILD_ID"
```

**AddSubIssueInput fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `issueId` | `ID!` | Yes | Node ID of the parent issue |
| `subIssueId` | `ID` | No* | Node ID of the child issue |
| `subIssueUrl` | `String` | No* | URL of the child issue (alternative to subIssueId) |
| `replaceParent` | `Boolean` | No | If true, moves the child from its current parent |
| `clientMutationId` | `String` | No | Opaque mutation ID |

*One of `subIssueId` or `subIssueUrl` must be provided.

### Removing a sub-issue (GraphQL mutation)

```bash
PARENT_ID=$(gh issue view 1 --json id --jq '.id')
CHILD_ID=$(gh issue view 118 --json id --jq '.id')

gh api graphql -f query='
  mutation($parentId: ID!, $childId: ID!) {
    removeSubIssue(input: {
      issueId: $parentId
      subIssueId: $childId
    }) {
      issue { number title }
      subIssue { number title }
    }
  }
' -f parentId="$PARENT_ID" -f childId="$CHILD_ID"
```

### gh issue develop (branch linking, not parent-child)

`gh issue develop` manages **linked branches**, not parent-child relationships:

```bash
# Create and link a branch to an issue
gh issue develop 118 --name "fix/118-recurrence" --checkout

# List branches linked to an issue
gh issue develop 118 --list

# Create branch from a specific base
gh issue develop 118 --base main --name "fix/118-recurrence"
```

This is useful for `sdlc:update` when transitioning an issue to `status:in-progress`.

### Convention-based hierarchy (body links)

For our SDLC system, we use BOTH native sub-issues AND body conventions:

**Epic body:**
```markdown
## Features
- [ ] #10 Google OAuth
- [ ] #11 Token refresh
- [x] #12 Session management
```

**Feature/Story body:**
```markdown
## Parent
Epic: #1

## Dependencies
Blocked by: #9, #12
Blocks: #25, #30
```

**Parsing conventions with jq:**

```bash
# Extract parent reference from body
gh issue view 42 --json body \
  --jq '.body | capture("## Parent\n(?:Epic|Feature): #(?<parent>\\d+)") | .parent | tonumber'

# Extract "Blocked by" references
gh issue view 42 --json body \
  --jq '.body | capture("Blocked by: (?<refs>[#\\d, ]+)") | .refs | split(", ") | map(ltrimstr("#") | tonumber)'

# Extract checklist items with issue references from epic body
gh issue view 1 --json body \
  --jq '.body | [scan("- \\[( |x)\\] #?(\\d+)?\\s*(.+)") | {done: (.[0] == "x"), issue: (.[1] | if . != "" then tonumber else null end), text: .[2]}]'
```

### GraphQL fields on Issue relevant to hierarchy

| Field | Description |
|-------|-------------|
| `subIssues(first: N)` | Direct child issues |
| `subIssuesSummary` | `{completed, percentCompleted, total}` |
| `parent` | Parent issue (if this is a sub-issue) |
| `trackedIssues(first: N)` | Issues tracked by this issue (task list items) |
| `trackedInIssues(first: N)` | Issues that track this issue |
| `trackedIssuesCount` | Count of tracked issues |
| `blockedBy(first: N)` | Issues blocking this one (native blocking) |
| `blocking(first: N)` | Issues this one blocks |

### Caveats

- Native sub-issues are **not exposed in `gh issue view --json`** -- must use `gh api graphql`
- The REST API only provides `sub_issues_summary` and `parent`, not the full list of sub-issues
- `addSubIssue` will error if the child already has a parent (use `replaceParent: true` to move it)
- Sub-issues hierarchy is limited to one level in the GitHub UI, but the API allows nesting
- `trackedIssues` is the older "task list" feature (autolinked from `- [ ] #N` in body) -- separate from `subIssues`
- Native sub-issues are a newer GitHub feature (2024+) -- not all orgs may have it enabled

---

## 9. Cross-Referencing and Auto-Close

**Used by:** `sdlc:create` (PR body generation), `sdlc:reconcile` (verify closed state), `sdlc:retro` (PR-to-issue mapping)

### Auto-close keywords in PR body

When a PR body contains these keywords followed by an issue reference, merging the PR automatically closes the referenced issue:

| Keyword | Example |
|---------|---------|
| `close` / `closes` / `closed` | `Closes #42` |
| `fix` / `fixes` / `fixed` | `Fixes #42` |
| `resolve` / `resolves` / `resolved` | `Resolves #42` |

**Multiple issues:**
```
Closes #42, closes #43, closes #44
```

**Cross-repo:**
```
Fixes raulstechtips/other-repo#42
```

### Creating a PR with auto-close via gh

```bash
gh pr create \
  --title "feat(agent): add recurrence support to calendar tools" \
  --body "$(cat <<'EOF'
## Summary
- Add `recurrence` parameter to `create_event` and `update_event`
- Add `color_id` parameter to both tools
- Update confirmation card to display recurrence pattern

Closes #118

## Test Plan
- [ ] Create recurring event via chat
- [ ] Update existing event to add recurrence
- [ ] Verify confirmation card shows RRULE
EOF
)"
```

### Checking which PR closed an issue

```bash
# Via gh issue view
gh issue view 111 --json closedByPullRequestsReferences \
  --jq '.closedByPullRequestsReferences[] | {pr: .number, url: .url}'
```

**Output:**
```json
{"pr": 112, "url": "https://github.com/raulstechtips/calendar-agent/pull/112"}
```

### Checking issue state reason

```bash
gh issue view 111 --json stateReason --jq '.stateReason'
# Output: COMPLETED

# Possible values: "" (open), "COMPLETED", "NOT_PLANNED", "DUPLICATE"
```

### Adding cross-references via comments

```bash
# Reference another issue (creates a cross-reference backlink)
gh issue comment 118 --body "Related to #117 -- both need recurrence support"

# Reference a PR
gh issue comment 118 --body "Fix is in progress: #120"
```

### Checking cross-references via timeline API

```bash
gh api repos/{owner}/{repo}/issues/118/timeline \
  --jq '[.[] | select(.event == "cross-referenced") | {source: .source.issue.number, event: .event}]'
```

### Caveats

- Auto-close only works when the PR is merged into the **default branch** (usually `main`)
- Auto-close keywords are case-insensitive (`Closes`, `closes`, `CLOSES` all work)
- The keyword must be in the PR **body**, not the title or commit messages (commit message keywords work for commits pushed directly to default branch, not via PR merge)
- `closedByPullRequestsReferences` only appears after the PR has been merged and the issue is closed
- Cross-references (mentioning `#N`) create backlinks in the issue timeline but do NOT auto-close
- An issue can be closed by multiple PRs

---

## 10. Batch Operations

**Used by:** `sdlc:create` (bulk issue creation), `sdlc:reconcile` (bulk label updates)

### What supports batch natively

| Operation | Batch? | How |
|-----------|--------|-----|
| `gh issue edit` labels/assignees | Yes | `gh issue edit 1 2 3 --add-label "x"` |
| `gh issue edit` title/body | No | One issue at a time |
| `gh issue create` | No | Sequential calls |
| `gh issue close` | No | One issue at a time |
| `gh issue reopen` | No | One issue at a time |
| `gh label create` | No | Sequential calls (use `--force` for idempotence) |

### Batch label operations (natively supported)

```bash
# Add a label to many issues at once
gh issue edit 116 117 118 --add-label "sprint:day2"

# Remove a label from many issues at once
gh issue edit 116 117 118 --remove-label "sprint:day1"

# Swap labels on many issues
gh issue edit 116 117 118 --add-label "status:in-progress" --remove-label "status:todo"
```

### Sequential creation pattern

```bash
# Create a hierarchy: epic -> features -> stories
# Capture numbers as we go for parent references

EPIC_URL=$(gh issue create \
  --title "EPIC: Authentication System" \
  --body-file /tmp/epic-body.md \
  --label "type:epic" --label "status:todo" --label "area:auth")
EPIC=$(echo "$EPIC_URL" | grep -o '[0-9]*$')

FEAT1_URL=$(gh issue create \
  --title "feat(auth): Google OAuth flow" \
  --body "## Parent\nEpic: #${EPIC}" \
  --label "type:feature" --label "status:todo" --label "area:auth")
FEAT1=$(echo "$FEAT1_URL" | grep -o '[0-9]*$')

STORY1_URL=$(gh issue create \
  --title "feat(auth): implement OAuth redirect handler" \
  --body "## Parent\nFeature: #${FEAT1}\n\nEpic: #${EPIC}" \
  --label "type:story" --label "status:todo" --label "area:auth")
```

### Sequential close with status update

```bash
# Close all done issues that still have status:todo label (reconciliation)
ISSUES=$(gh issue list --label "status:done" --state open --json number --jq '.[].number')
for NUM in $ISSUES; do
  gh issue close "$NUM" --reason completed --comment "Auto-closed by sdlc:reconcile"
done
```

### Parallel batch via background processes

For speed, run multiple independent operations in parallel:

```bash
# Close multiple issues in parallel
gh issue close 10 --reason completed &
gh issue close 11 --reason completed &
gh issue close 12 --reason completed &
wait
```

### Batch via gh api (GraphQL mutations)

For maximum efficiency, use GraphQL aliases to batch multiple mutations in a single API call:

```bash
gh api graphql -f query='
  mutation {
    a: addLabelsToLabelable(input: {labelableId: "I_abc123", labelIds: ["LA_xyz"]}) {
      clientMutationId
    }
    b: addLabelsToLabelable(input: {labelableId: "I_def456", labelIds: ["LA_xyz"]}) {
      clientMutationId
    }
    c: addLabelsToLabelable(input: {labelableId: "I_ghi789", labelIds: ["LA_xyz"]}) {
      clientMutationId
    }
  }
'
```

**Note:** This requires knowing the node IDs ahead of time. Practical for `sdlc:reconcile` which has already fetched issues.

### Caveats

- No true batch create -- must call `gh issue create` sequentially
- Multi-issue `gh issue edit` only for labels, assignees, milestones, projects -- not body/title
- GraphQL batching via aliases has a limit of ~100 mutations per request (varies)
- Parallel shell processes (`&` and `wait`) work but can hit rate limits with many concurrent calls
- Rate limit: 5000 requests/hour for REST, 5000 points/hour for GraphQL

---

## Appendix: JSON Fields Reference

### gh issue view / gh issue list --json

```
assignees          [{login, id, name, ...}]         Assigned users
author             {login, id, name, is_bot}         Issue creator
body               string                            Full markdown body
closed             bool                              Is closed?
closedAt           string|null                       ISO 8601 close timestamp
closedByPullRequestsReferences  [{number, url, repository}]  PRs that closed this
comments           [{author, body, createdAt, url}]  All comments
createdAt          string                            ISO 8601 create timestamp
id                 string                            Node ID (for GraphQL)
isPinned           bool                              Is pinned?
labels             [{name, color, description, id}]  All labels
milestone          {title, number}|null              Milestone
number             int                               Issue number
projectCards       [...]                             Classic projects (needs scope)
projectItems       [...]                             ProjectV2 items (needs scope)
reactionGroups     [{content, users}]                Reactions
state              string                            "OPEN" or "CLOSED"
stateReason        string                            "", "COMPLETED", "NOT_PLANNED", "DUPLICATE"
title              string                            Issue title
updatedAt          string                            ISO 8601 update timestamp
url                string                            Full GitHub URL
```

### gh label list --json

```
color              string     6-char hex (no #)
createdAt          string     ISO 8601
description        string     Label description
id                 string     Node ID
isDefault          bool       GitHub default label?
name               string     Label name
updatedAt          string     ISO 8601
url                string     Full URL
```

### REST API additional fields (via gh api)

```
parent             {number, title, ...}|null    Parent issue (sub-issues feature)
sub_issues_summary {completed, percent_completed, total}   Sub-issue rollup
```

### GraphQL-only fields on Issue

```
subIssues(first: N)          Connection of child issues
subIssuesSummary             {completed, percentCompleted, total}
parent                       Parent issue object
trackedIssues(first: N)      Task-list tracked issues
trackedInIssues(first: N)    Issues tracking this one
trackedIssuesCount           Int
blockedBy(first: N)          Native blocking relationships
blocking(first: N)           Native blocking relationships
linkedBranches(first: N)     Branches linked via gh issue develop
issueType                    Issue type (if configured)
```

---

## Appendix: jq Cookbook

Common jq patterns for SDLC skills, all verified against the real repo.

### Extract label names as flat array

```bash
gh issue view 118 --json labels --jq '[.labels[].name]'
# ["type:bug","status:todo","priority:critical","area:agents"]
```

### Check if issue has a specific label

```bash
gh issue view 118 --json labels --jq '.labels | map(.name) | index("status:todo") != null'
# true
```

### Get status label from an issue

```bash
gh issue view 118 --json labels \
  --jq '.labels | map(.name) | map(select(startswith("status:"))) | .[0]'
# "status:todo"
```

### Get all area labels

```bash
gh issue view 118 --json labels \
  --jq '[.labels[].name | select(startswith("area:"))]'
# ["area:agents"]
```

### Format issues as table rows

```bash
gh issue list --limit 20 --json number,title,labels \
  --jq '.[] | "\(.number)\t\(.labels | map(.name) | join(","))\t\(.title)"'
```

### Count issues by label category

```bash
gh issue list --state all --limit 500 --json labels \
  --jq '[.[].labels[].name | select(startswith("type:"))] | group_by(.) | map({type: .[0], count: length})'
```

### Extract section from markdown body

```bash
# Generic section extractor (returns content between ## headers)
gh issue view 1 --json body \
  --jq '.body | capture("## (?<header>Features)\n(?<content>[\\s\\S]*?)(\n## |$)") | .content'
```

### Parse dependency references from body

```bash
# Extract "Blocked by: #45, #46" into array of ints
gh issue view 42 --json body \
  --jq '.body | capture("Blocked by: (?<refs>[#\\d, ]+)") | .refs | split(", ") | map(ltrimstr("#") | tonumber)'
```

### Parse checklist progress

```bash
gh issue view 1 --json body \
  --jq '.body | {
    total: [scan("- \\[[ x]\\]")] | length,
    done:  [scan("- \\[x\\]")] | length
  } | . + {percent: (if .total > 0 then (.done * 100 / .total | floor) else 0 end)}'
# {"total": 6, "done": 5, "percent": 83}
```

### Filter list results by computed criteria

```bash
# Issues that have status:todo but NO area label (label hygiene check)
gh issue list --label "status:todo" --limit 100 --json number,title,labels \
  --jq '[.[] | select(.labels | map(.name) | map(select(startswith("area:"))) | length == 0) | {number, title}]'
```

### Build a sprint dashboard

```bash
gh issue list --state all --limit 500 --json number,title,labels,state,closedAt,createdAt \
  --jq '
    def status_of: .labels | map(.name) |
      if contains(["status:done"]) then "done"
      elif contains(["status:in-progress"]) then "in-progress"
      elif contains(["status:blocked"]) then "blocked"
      elif contains(["status:todo"]) then "todo"
      else "unlabeled" end;
    def type_of: .labels | map(.name) |
      (map(select(startswith("type:")))[0] // "untyped");
    {
      by_status: group_by(status_of) | map({status: .[0] | status_of, count: length}),
      by_type: group_by(type_of) | map({type: .[0] | type_of, count: length}),
      total: length
    }
  '
```

---

## Appendix: SDLC Skill Command Map

Quick reference showing which `gh` commands each skill needs.

### sdlc:define
No `gh` commands -- produces local draft files only.

### sdlc:create
| Operation | Command |
|-----------|---------|
| Bootstrap labels | `gh label create --force` (sequential) |
| Create epic | `gh issue create --label "type:epic"` |
| Create feature | `gh issue create --label "type:feature"` |
| Create story | `gh issue create --label "type:story"` |
| Link sub-issues | `gh api graphql` with `addSubIssue` mutation |
| Verify creation | `gh issue view <n> --json number,title,labels,body` |
| Check for duplicates | `gh issue list --search "title in:title" --json number,title` |

### sdlc:update
| Operation | Command |
|-----------|---------|
| Read issue | `gh issue view <n> --json body,labels,title,assignees` |
| Update body | `gh issue edit <n> --body-file -` (read-modify-write) |
| Swap status label | `gh issue edit <n> --add-label "status:X" --remove-label "status:Y"` |
| Add/remove labels | `gh issue edit <n> --add-label / --remove-label` |
| Change title | `gh issue edit <n> --title "new title"` |
| Assign | `gh issue edit <n> --add-assignee "@me"` |
| Close | `gh issue close <n> --reason completed` |
| Reopen | `gh issue reopen <n>` |
| Link branch | `gh issue develop <n> --name "type/n-desc" --checkout` |

### sdlc:status
| Operation | Command |
|-----------|---------|
| List by status | `gh issue list --label "status:X" --json number,title,labels` |
| List by area | `gh issue list --label "area:X" --json number,title,labels` |
| Count by status | `gh issue list --state all --limit 500 --json labels` + jq grouping |
| Read epic progress | `gh issue view <n> --json body` + parse checklists |
| Check sub-issues | `gh api graphql` with `subIssuesSummary` query |
| Find blocked | `gh issue list --label "status:blocked" --json number,title,body` |
| Find unassigned | `gh issue list --search "no:assignee label:status:todo"` |

### sdlc:reconcile
| Operation | Command |
|-----------|---------|
| List all open | `gh issue list --state all --limit 500 --json number,labels,state` |
| Batch relabel | `gh issue edit 1 2 3 --add-label "X" --remove-label "Y"` |
| Close completed | `gh issue close <n> --reason completed --comment "..."` |
| Verify labels exist | `gh label list --json name --jq '[.[].name]'` |
| Create missing labels | `gh label create "name" --force` |
| Check parent completion | `gh api graphql` with `subIssues` + state check |
| Find orphaned issues | List + jq to find issues without type/status labels |
| Fix state drift | `gh issue edit` + `gh issue close/reopen` |

### sdlc:retro
| Operation | Command |
|-----------|---------|
| List done issues | `gh issue list --label "status:done" --state closed --json number,title,createdAt,closedAt` |
| Calculate cycle time | `--json createdAt,closedAt` + jq date math |
| Map PRs to issues | `--json closedByPullRequestsReferences` |
| Count by area | `--json labels` + jq group by area |
| Count by type | `--json labels` + jq group by type |
| List blocked items | `--json labels,body` + parse "Blocked by" from body |
