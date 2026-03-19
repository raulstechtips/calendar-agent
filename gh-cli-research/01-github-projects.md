# GitHub Projects CLI Reference for SDLC Skills

> Comprehensive reference for `gh project` commands and GraphQL fallbacks.
> Target repo: `raulstechtips/calendar-agent` | Owner: `raulstechtips`
> Research date: 2026-03-19

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Project CRUD](#2-project-crud)
3. [Linking Projects to Repositories](#3-linking-projects-to-repositories)
4. [Adding Issues and PRs to Projects](#4-adding-issues-and-prs-to-projects)
5. [Draft Issues (Project-Only Items)](#5-draft-issues-project-only-items)
6. [Listing and Querying Items](#6-listing-and-querying-items)
7. [Custom Fields: Create, List, Delete](#7-custom-fields-create-list-delete)
8. [Setting Field Values on Items](#8-setting-field-values-on-items)
9. [Iterations (Sprints)](#9-iterations-sprints)
10. [Single-Select Fields (Status, Priority, etc.)](#10-single-select-fields-status-priority-etc)
11. [Archiving and Deleting Items](#11-archiving-and-deleting-items)
12. [Views (Board, Table, Roadmap)](#12-views-board-table-roadmap)
13. [Built-in Automations and Workflows](#13-built-in-automations-and-workflows)
14. [GraphQL Fallbacks](#14-graphql-fallbacks)
15. [Bulk Operations](#15-bulk-operations)
16. [Integration: Projects vs Issue Labels](#16-integration-projects-vs-issue-labels)
17. [Default Project Configuration](#17-default-project-configuration)
18. [Organization vs User Projects](#18-organization-vs-user-projects)
19. [Limits and Rate Limits](#19-limits-and-rate-limits)
20. [SDLC Skill Mapping](#20-sdlc-skill-mapping)

---

## 1. Prerequisites

### Authentication Scope

The `gh project` commands require the `project` OAuth scope, which is **not** included in the default `gh auth login` scopes.

```bash
# Check current scopes
gh auth status

# Add the project scope (opens browser for re-auth)
gh auth refresh -s project
```

**Caveat:** Without this scope, `gh project` commands fail with confusing/misleading error messages rather than a clear "missing scope" error.

**SDLC skill mapping:** The `setup` or `init` skill should verify this scope before any project operations.

### Owner Flag

Most commands accept `--owner <login>`. For our repo:
- User projects: `--owner raulstechtips`
- You can use `--owner "@me"` for the currently authenticated user
- If you omit `--owner`, some commands infer from the current repo context, but this is inconsistent -- always pass `--owner` explicitly for reliability

---

## 2. Project CRUD

### Create a Project

```bash
gh project create --owner raulstechtips --title "Calendar Agent Sprint Board"
```

**Flags:**
| Flag | Description |
|------|-------------|
| `--owner <string>` | Login of the owner (`@me` for current user) |
| `--title <string>` | Project title |
| `--format json` | Output as JSON (returns project number, URL, etc.) |
| `-q, --jq <expr>` | Filter JSON output with jq expression |
| `-t, --template <string>` | Format output using Go template |

**Example JSON output:**
```json
{
  "number": 1,
  "url": "https://github.com/users/raulstechtips/projects/1",
  "shortDescription": "",
  "public": false,
  "closed": false,
  "title": "Calendar Agent Sprint Board",
  "id": "PVT_kwHOAxxxxx",
  "readme": "",
  "items": { "totalCount": 0 },
  "fields": { "totalCount": 0 },
  "owner": { "login": "raulstechtips" }
}
```

**SDLC skill:** `init-project` -- called once during project bootstrap.

### List Projects

```bash
# List open projects
gh project list --owner raulstechtips

# Include closed projects
gh project list --owner raulstechtips --closed

# JSON output
gh project list --owner raulstechtips --format json

# Get just the project number
gh project list --owner raulstechtips --format json --jq '.projects[] | select(.title == "Calendar Agent Sprint Board") | .number'
```

**Flags:**
| Flag | Description |
|------|-------------|
| `--owner <string>` | Login of the owner |
| `--closed` | Include closed projects |
| `-L, --limit <int>` | Max projects to fetch (default 30) |
| `--format json` | JSON output |
| `-q, --jq <expr>` | jq filter |

**Default table output:**
```
NUMBER  TITLE                          STATE  ID
1       Calendar Agent Sprint Board    open   PVT_kwHOAxxxxx
```

**SDLC skill:** `pick-task`, `sync-issues` -- need to discover the project number.

### View a Project

```bash
# View in terminal
gh project view 1 --owner raulstechtips

# View in browser
gh project view 1 --owner raulstechtips --web

# JSON output with full details
gh project view 1 --owner raulstechtips --format json
```

**Flags:**
| Flag | Description |
|------|-------------|
| `--owner <string>` | Login of the owner |
| `-w, --web` | Open in browser |
| `--format json` | JSON output |
| `-q, --jq <expr>` | jq filter |

**SDLC skill:** `view-board` -- show project status overview.

### Edit a Project

```bash
# Update title
gh project edit 1 --owner raulstechtips --title "Calendar Agent PI-1"

# Update description
gh project edit 1 --owner raulstechtips -d "PI-1: Auth + Calendar Agent MVP"

# Update readme
gh project edit 1 --owner raulstechtips --readme "## Sprint Board\nThis project tracks..."
```

**Flags:**
| Flag | Description |
|------|-------------|
| `--owner <string>` | Login of the owner |
| `--title <string>` | New title |
| `-d, --description <string>` | New description |
| `--readme <string>` | New readme content |
| `--format json` | JSON output |

**Caveat:** There is no `--visibility` flag on `gh project edit`. Visibility is controlled through the web UI only.

**SDLC skill:** `update-project` -- update project metadata between PIs.

### Close a Project

```bash
# Close
gh project close 1 --owner raulstechtips

# Reopen (there is no separate "reopen" command -- use --undo)
gh project close 1 --owner raulstechtips --undo
```

**SDLC skill:** `close-pi` -- close a project at end of PI.

### Delete a Project

```bash
gh project delete 1 --owner raulstechtips
```

**Warning:** This is destructive and irreversible. All project-specific data (field values, views, draft issues) is deleted. The underlying GitHub Issues are NOT deleted.

**SDLC skill:** Generally not needed. Prefer closing over deleting.

### Copy a Project (Templates)

```bash
# Copy a project (useful for sprint templates)
gh project copy 1 --source-owner raulstechtips --target-owner raulstechtips --title "PI-2 Sprint Board"

# Include draft issues in the copy
gh project copy 1 --source-owner raulstechtips --target-owner raulstechtips --title "PI-2 Sprint Board" --drafts
```

**Flags:**
| Flag | Description |
|------|-------------|
| `--source-owner <string>` | Owner of the source project |
| `--target-owner <string>` | Owner of the new copy |
| `--title <string>` | Title for the copied project |
| `--drafts` | Include draft issues in the copy |
| `--format json` | JSON output |

### Mark as Template

```bash
# Mark a project as a template
gh project mark-template 1 --owner raulstechtips

# Unmark
gh project mark-template 1 --owner raulstechtips --undo
```

**SDLC skill:** `init-pi` -- copy a template project to start a new PI.

---

## 3. Linking Projects to Repositories

Linking a project to a repo makes the project appear in the repo's "Projects" tab and enables built-in automations.

```bash
# Link to current repo (when CWD is inside the repo)
gh project link 1 --owner raulstechtips

# Link to a specific repo
gh project link 1 --owner raulstechtips --repo calendar-agent

# Link to a team (org projects only)
gh project link 1 --owner my-org --team my-team

# Unlink
gh project unlink 1 --owner raulstechtips --repo calendar-agent
```

**SDLC skill:** `init-project` -- link immediately after creating.

---

## 4. Adding Issues and PRs to Projects

### Add an Existing Issue/PR

```bash
# Add by issue URL
gh project item-add 1 --owner raulstechtips --url "https://github.com/raulstechtips/calendar-agent/issues/42"

# Add by PR URL
gh project item-add 1 --owner raulstechtips --url "https://github.com/raulstechtips/calendar-agent/pull/43"

# Get the project item ID (needed for field edits)
gh project item-add 1 --owner raulstechtips \
  --url "https://github.com/raulstechtips/calendar-agent/issues/42" \
  --format json --jq '.id'
```

**Flags:**
| Flag | Description |
|------|-------------|
| `--owner <string>` | Login of the owner |
| `--url <string>` | URL of the issue or PR to add |
| `--format json` | JSON output (returns item ID) |
| `-q, --jq <expr>` | jq filter |

**Example JSON output:**
```json
{
  "id": "PVTI_lAHOAxxxxx",
  "title": "Add Google OAuth with refresh token support",
  "body": "...",
  "type": "Issue",
  "url": "https://github.com/raulstechtips/calendar-agent/issues/42"
}
```

**Caveat:** If the item is already in the project, the existing item ID is returned (no error, no duplicate).

**SDLC skill:** `create-story`, `plan-sprint` -- add issues to the project after creating them.

---

## 5. Draft Issues (Project-Only Items)

Draft issues live only in the project (not in any repo's issue tracker) until converted.

```bash
# Create a draft issue in the project
gh project item-create 1 --owner raulstechtips \
  --title "Spike: Evaluate Azure AI Search pricing" \
  --body "Research task for PI planning"

# Get the ID
gh project item-create 1 --owner raulstechtips \
  --title "Spike: Evaluate pricing" \
  --format json --jq '.id'
```

**Flags:**
| Flag | Description |
|------|-------------|
| `--owner <string>` | Login of the owner |
| `--title <string>` | Title for the draft issue |
| `--body <string>` | Body for the draft issue |
| `--format json` | JSON output |

**Caveat:** Draft issues cannot be assigned, labeled, or milestoned until converted to real issues. They are project-only artifacts.

**SDLC skill:** `plan-sprint` -- create placeholder items during sprint planning.

---

## 6. Listing and Querying Items

### List All Items

```bash
# Default table output (first 30 items)
gh project item-list 1 --owner raulstechtips

# All items (up to limit)
gh project item-list 1 --owner raulstechtips -L 200

# JSON output
gh project item-list 1 --owner raulstechtips --format json
```

**Default table output:**
```
TYPE    TITLE                                    NUMBER  REPOSITORY                          ID
Issue   Add Google OAuth with refresh token      9       raulstechtips/calendar-agent         PVTI_lAHOAxxxxx
Issue   Create LangGraph ReAct agent             15      raulstechtips/calendar-agent         PVTI_lAHOAyyyyy
PR      fix: handle expired token                43      raulstechtips/calendar-agent         PVTI_lAHOAzzzzz
Draft   Spike: Evaluate pricing                          raulstechtips/calendar-agent         PVTI_lAHOAwwwww
```

**Flags:**
| Flag | Description |
|------|-------------|
| `--owner <string>` | Login of the owner |
| `-L, --limit <int>` | Max items to fetch (default 30) |
| `--format json` | JSON output |
| `-q, --jq <expr>` | jq filter |

### Filtering with --query

The `--query` flag (available on github.com and GHES 3.20+) uses the Projects filter syntax:

```bash
# Filter by status
gh project item-list 1 --owner raulstechtips --query 'status:"In Progress"'

# Filter by label
gh project item-list 1 --owner raulstechtips --query 'label:bug'

# Filter by assignee
gh project item-list 1 --owner raulstechtips --query 'assignee:raulstechtips'

# Filter by custom single-select field
gh project item-list 1 --owner raulstechtips --query 'priority:P0'

# Filter by iteration/sprint
gh project item-list 1 --owner raulstechtips --query 'iteration:"Sprint 1"'

# Combine filters (logical AND)
gh project item-list 1 --owner raulstechtips --query 'status:"Todo" label:"type:story"'

# Negate with hyphen
gh project item-list 1 --owner raulstechtips --query '-status:Done'

# Items with a field value set
gh project item-list 1 --owner raulstechtips --query 'has:priority'

# Items missing a field value
gh project item-list 1 --owner raulstechtips --query 'no:sprint'

# Filter by type
gh project item-list 1 --owner raulstechtips --query 'is:issue'
gh project item-list 1 --owner raulstechtips --query 'is:pr'
gh project item-list 1 --owner raulstechtips --query 'is:draft'

# Date/number ranges
gh project item-list 1 --owner raulstechtips --query 'date:>2026-03-01'
gh project item-list 1 --owner raulstechtips --query 'estimate:>=5'
```

**Filter syntax summary:**
| Operator | Meaning | Example |
|----------|---------|---------|
| `:` | Equals | `status:"In Progress"` |
| `-` prefix | Negate | `-status:Done` |
| `has:` | Field has a value | `has:priority` |
| `no:` | Field has no value | `no:sprint` |
| `is:` | Type filter | `is:issue`, `is:pr`, `is:draft`, `is:open`, `is:closed` |
| `>`, `>=`, `<`, `<=` | Range | `estimate:>=5` |
| `..` | Inclusive range | `estimate:3..8` |
| `,` | OR within field | `status:"Todo","In Progress"` |

**Caveat:** The `--query` flag may not be available on older GHES versions. It is available on github.com.

**SDLC skill:** `pick-task` (find todo items), `sync-issues` (audit status), `sprint-report` (items by sprint).

### Extracting Specific Data with jq

```bash
# Get all item IDs and titles
gh project item-list 1 --owner raulstechtips --format json \
  --jq '.items[] | {id: .id, title: .title, type: .type}'

# Get just open issues
gh project item-list 1 --owner raulstechtips --format json \
  --jq '.items[] | select(.type == "Issue")'
```

---

## 7. Custom Fields: Create, List, Delete

### List Fields

```bash
# Table output
gh project field-list 1 --owner raulstechtips

# JSON output (essential for getting field IDs and option IDs)
gh project field-list 1 --owner raulstechtips --format json

# Get Status field options with IDs
gh project field-list 1 --owner raulstechtips --format json \
  --jq '.fields[] | select(.name == "Status") | .options[] | {name, id}'

# Get all field names and IDs
gh project field-list 1 --owner raulstechtips --format json \
  --jq '.fields[] | {name: .name, id: .id, type: .type}'
```

**Flags:**
| Flag | Description |
|------|-------------|
| `--owner <string>` | Login of the owner |
| `-L, --limit <int>` | Max fields to fetch (default 30) |
| `--format json` | JSON output |
| `-q, --jq <expr>` | jq filter |

**Example JSON output:**
```json
{
  "fields": [
    {
      "id": "PVTF_lAHOAxxxxx",
      "name": "Status",
      "type": "ProjectV2SingleSelectField",
      "options": [
        { "id": "f75ad846", "name": "Todo" },
        { "id": "47fc9ee4", "name": "In Progress" },
        { "id": "98236657", "name": "Done" }
      ]
    },
    {
      "id": "PVTF_lAHOAyyyyy",
      "name": "Priority",
      "type": "ProjectV2SingleSelectField",
      "options": [
        { "id": "abc12345", "name": "P0" },
        { "id": "def67890", "name": "P1" },
        { "id": "ghi11111", "name": "P2" }
      ]
    },
    {
      "id": "PVTF_lAHOAzzzzz",
      "name": "Estimate",
      "type": "ProjectV2Field",
      "options": null
    },
    {
      "id": "PVTIF_lAHOAwwwww",
      "name": "Sprint",
      "type": "ProjectV2IterationField"
    }
  ]
}
```

**SDLC skill:** Every skill that reads or writes field values needs to call this first to resolve field IDs and option IDs.

### Create a Field

```bash
# Text field
gh project field-create 1 --owner raulstechtips \
  --name "Epic" --data-type TEXT

# Number field
gh project field-create 1 --owner raulstechtips \
  --name "Estimate" --data-type NUMBER

# Date field
gh project field-create 1 --owner raulstechtips \
  --name "Target Date" --data-type DATE

# Single-select field with options
gh project field-create 1 --owner raulstechtips \
  --name "Priority" --data-type SINGLE_SELECT \
  --single-select-options "P0,P1,P2,P3"

# Single-select for Area
gh project field-create 1 --owner raulstechtips \
  --name "Area" --data-type SINGLE_SELECT \
  --single-select-options "auth,api,agent,calendar,search,chat,ui,infra"
```

**Flags:**
| Flag | Description |
|------|-------------|
| `--owner <string>` | Login of the owner |
| `--name <string>` | Name of the field |
| `--data-type <string>` | One of: `TEXT`, `SINGLE_SELECT`, `DATE`, `NUMBER` |
| `--single-select-options <string>` | Comma-separated options (only for SINGLE_SELECT) |
| `--format json` | JSON output |

**Supported data types via CLI:**
| Type | CLI `--data-type` | Notes |
|------|-------------------|-------|
| Text | `TEXT` | Free-form text |
| Number | `NUMBER` | Numeric values (estimates, story points) |
| Date | `DATE` | YYYY-MM-DD format |
| Single Select | `SINGLE_SELECT` | Enum-like, requires `--single-select-options` |
| Iteration | N/A | **Cannot be created via `gh project field-create`** -- use GraphQL or web UI |

**IMPORTANT LIMITATION:** The `--data-type` flag does NOT support `ITERATION`. You cannot create iteration/sprint fields via the CLI. You must use the web UI or GraphQL (see [Section 9](#9-iterations-sprints)).

**SDLC skill:** `init-project` -- create all custom fields during project bootstrap.

### Delete a Field

```bash
# First, get the field ID
FIELD_ID=$(gh project field-list 1 --owner raulstechtips --format json \
  --jq '.fields[] | select(.name == "Obsolete Field") | .id')

# Delete it
gh project field-delete --id "$FIELD_ID"
```

**Flags:**
| Flag | Description |
|------|-------------|
| `--id <string>` | ID of the field to delete (required) |
| `--format json` | JSON output |

**Caveat:** You cannot delete built-in fields (Title, Assignees, Status, Labels, Milestone, etc.).

---

## 8. Setting Field Values on Items

### The Two-Step Dance

Every field update requires two IDs you must look up first:
1. **Item ID** (`PVTI_...`) -- from `item-add`, `item-list`, or `item-create`
2. **Field ID** (`PVTF_...`) -- from `field-list`

For single-select fields, you also need:
3. **Option ID** -- from `field-list` JSON output

For iteration fields:
4. **Iteration ID** -- from `field-list` JSON output or GraphQL

### Command Syntax

```bash
gh project item-edit \
  --id <ITEM_ID> \
  --project-id <PROJECT_ID> \
  --field-id <FIELD_ID> \
  --<value-flag> <value>
```

**Flags:**
| Flag | Description | Mutually Exclusive |
|------|-------------|-------------------|
| `--id <string>` | Item ID (PVTI_...) | Required |
| `--project-id <string>` | Project node ID (PVT_...) | Required |
| `--field-id <string>` | Field ID (PVTF_...) | Required |
| `--text <string>` | Set a text value | Yes -- pick one |
| `--number <float>` | Set a number value | Yes -- pick one |
| `--date <string>` | Set a date (YYYY-MM-DD) | Yes -- pick one |
| `--single-select-option-id <string>` | Set a single-select option | Yes -- pick one |
| `--iteration-id <string>` | Set an iteration | Yes -- pick one |
| `--clear` | Remove the field value | Cannot combine with value flags |
| `--format json` | JSON output | |

**Key constraint:** Only ONE of `--text`, `--number`, `--date`, `--single-select-option-id`, or `--iteration-id` can be used per call. `--clear` cannot be combined with any value flag.

### Practical Examples

```bash
# --- Setup: Get IDs first ---

# Get the project node ID (PVT_...)
PROJECT_ID=$(gh project view 1 --owner raulstechtips --format json --jq '.id')

# Get item ID for issue #42
ITEM_ID=$(gh project item-list 1 --owner raulstechtips --format json \
  --jq '.items[] | select(.content.number == 42) | .id')

# Get field IDs and option IDs
gh project field-list 1 --owner raulstechtips --format json

# --- Set values ---

# Set Status to "In Progress"
gh project item-edit \
  --id "$ITEM_ID" \
  --project-id "$PROJECT_ID" \
  --field-id "PVTF_status_id" \
  --single-select-option-id "47fc9ee4"

# Set Priority to "P0"
gh project item-edit \
  --id "$ITEM_ID" \
  --project-id "$PROJECT_ID" \
  --field-id "PVTF_priority_id" \
  --single-select-option-id "abc12345"

# Set Estimate (number)
gh project item-edit \
  --id "$ITEM_ID" \
  --project-id "$PROJECT_ID" \
  --field-id "PVTF_estimate_id" \
  --number 5

# Set Target Date
gh project item-edit \
  --id "$ITEM_ID" \
  --project-id "$PROJECT_ID" \
  --field-id "PVTF_target_date_id" \
  --date "2026-03-25"

# Set Epic (text field linking to epic issue)
gh project item-edit \
  --id "$ITEM_ID" \
  --project-id "$PROJECT_ID" \
  --field-id "PVTF_epic_id" \
  --text "#5"

# Set Sprint/Iteration
gh project item-edit \
  --id "$ITEM_ID" \
  --project-id "$PROJECT_ID" \
  --field-id "PVTIF_sprint_id" \
  --iteration-id "iteration_id_here"

# Clear a field value
gh project item-edit \
  --id "$ITEM_ID" \
  --project-id "$PROJECT_ID" \
  --field-id "PVTF_priority_id" \
  --clear
```

**Caveat on --number:** Setting `--number 0` was broken in older CLI versions (treated as "not provided"). Verify with `gh --version >= 2.40+`.

**Caveat on field types you CANNOT set via item-edit:** Assignees, Labels, Milestone, and Repository are properties of the underlying issue/PR, not project fields. Use `gh issue edit` to change those:

```bash
# These are issue properties, not project fields
gh issue edit 42 --add-label "status:in-progress" -R raulstechtips/calendar-agent
gh issue edit 42 --add-assignee raulstechtips -R raulstechtips/calendar-agent
```

**SDLC skill:** `pick-task` (set status to In Progress), `complete-task` (set status to Done), `plan-sprint` (set sprint, priority, estimate).

---

## 9. Iterations (Sprints)

### The Iteration Problem

Iterations are the GitHub Projects equivalent of sprints. They support:
- Configurable duration (e.g., 2 weeks)
- Breaks between iterations
- Past, current, and future iterations

**MAJOR LIMITATION:** The `gh project field-create` CLI command does NOT support creating iteration fields. The `--data-type` flag only accepts `TEXT`, `SINGLE_SELECT`, `DATE`, and `NUMBER`.

### Creating an Iteration Field

**Option A: Web UI (recommended for initial setup)**
1. Open the project in browser: `gh project view 1 --owner raulstechtips --web`
2. Click "+" to add a field
3. Select "Iteration" type
4. Configure duration (e.g., 14 days) and start date

**Option B: GraphQL via `gh api graphql`**

There is no direct `createProjectV2Field` mutation for iteration type in the public API as of this writing. The iteration field must be created through the web UI. Once created, you can query and update it via GraphQL and CLI.

### Querying Iteration Field Configuration

Once an iteration field exists, get its details:

```bash
# Via CLI field-list (limited info)
gh project field-list 1 --owner raulstechtips --format json \
  --jq '.fields[] | select(.type == "ProjectV2IterationField")'

# Via GraphQL (full iteration details with IDs)
gh api graphql -f query='
  query {
    user(login: "raulstechtips") {
      projectV2(number: 1) {
        fields(first: 50) {
          nodes {
            ... on ProjectV2IterationField {
              id
              name
              configuration {
                duration
                startDay
                iterations {
                  id
                  title
                  startDate
                  duration
                }
                completedIterations {
                  id
                  title
                  startDate
                  duration
                }
              }
            }
          }
        }
      }
    }
  }
'
```

**Example output:**
```json
{
  "id": "PVTIF_lAHOAxxxxx",
  "name": "Sprint",
  "configuration": {
    "duration": 14,
    "startDay": 1,
    "iterations": [
      { "id": "iter_001", "title": "Sprint 1", "startDate": "2026-03-10", "duration": 14 },
      { "id": "iter_002", "title": "Sprint 2", "startDate": "2026-03-24", "duration": 14 }
    ],
    "completedIterations": []
  }
}
```

### Setting an Iteration Value on an Item

```bash
# Get the iteration ID from the query above, then:
gh project item-edit \
  --id "$ITEM_ID" \
  --project-id "$PROJECT_ID" \
  --field-id "PVTIF_lAHOAxxxxx" \
  --iteration-id "iter_001"
```

**Known issue:** Finding the iteration ID requires GraphQL or parsing `field-list` JSON carefully. The CLI does not provide a convenient `--iteration-name` flag. See [GitHub CLI issue #11068](https://github.com/cli/cli/issues/11068).

### Updating Iteration Configuration via GraphQL

**WARNING:** The `updateProjectV2Field` mutation for iterations does a FULL REPLACE of all iterations. This means if you add a new iteration, you must include all existing ones in the mutation, or they will be deleted and all items assigned to them will lose their iteration association.

```bash
gh api graphql -f query='
  mutation {
    updateProjectV2Field(input: {
      fieldId: "PVTIF_lAHOAxxxxx"
      projectId: "PVT_kwHOAxxxxx"
      iterationConfiguration: {
        duration: 14
        startDay: MONDAY
        iterations: [
          { startDate: "2026-03-10", duration: 14, title: "Sprint 1" },
          { startDate: "2026-03-24", duration: 14, title: "Sprint 2" },
          { startDate: "2026-04-07", duration: 14, title: "Sprint 3" }
        ]
      }
    }) {
      field { ... on ProjectV2IterationField { id name } }
    }
  }
'
```

### Mapping to Our PI Concept

| Our Concept | GitHub Projects Equivalent |
|-------------|---------------------------|
| PI (Program Increment) | A Project (one project per PI) |
| Sprint | An Iteration within the project |
| Sprint backlog | Items filtered by iteration |
| PI backlog | All items in the project |

**SDLC skill:** `init-pi` (create project + iteration field), `plan-sprint` (assign items to iterations), `sprint-report` (query by iteration).

---

## 10. Single-Select Fields (Status, Priority, etc.)

### Default Status Field

Every new project comes with a built-in **Status** field with these default options:
- `Todo`
- `In Progress`
- `Done`

You can customize the Status options in the web UI (add "Blocked", "In Review", rename, reorder). The Status field cannot be deleted.

### Creating Custom Single-Select Fields

```bash
# Status alternatives (if you need more granularity than built-in)
# Note: You CANNOT modify the built-in Status options via CLI.
# Instead, create a custom field:
gh project field-create 1 --owner raulstechtips \
  --name "Workflow" --data-type SINGLE_SELECT \
  --single-select-options "Backlog,Todo,In Progress,In Review,Done,Blocked"

# Priority field
gh project field-create 1 --owner raulstechtips \
  --name "Priority" --data-type SINGLE_SELECT \
  --single-select-options "P0-Critical,P1-High,P2-Medium,P3-Low"

# Type field (to replace type: labels)
gh project field-create 1 --owner raulstechtips \
  --name "Type" --data-type SINGLE_SELECT \
  --single-select-options "Epic,Feature,Story,Bug,Spike,Chore"

# Area field (to replace area: labels)
gh project field-create 1 --owner raulstechtips \
  --name "Area" --data-type SINGLE_SELECT \
  --single-select-options "auth,api,agent,calendar,search,chat,ui,infra"
```

### Modifying Single-Select Options

**LIMITATION:** There is no CLI command to add/remove/rename options on an existing single-select field. You must use:

**Option A: Web UI** -- edit field settings in the project.

**Option B: GraphQL mutation:**

```bash
# Add an option to an existing single-select field
gh api graphql -f query='
  mutation {
    updateProjectV2Field(input: {
      fieldId: "PVTF_lAHOAxxxxx"
      projectId: "PVT_kwHOAxxxxx"
      singleSelectOptions: [
        { name: "Todo", color: BLUE, description: "" },
        { name: "In Progress", color: YELLOW, description: "" },
        { name: "In Review", color: PURPLE, description: "" },
        { name: "Done", color: GREEN, description: "" },
        { name: "Blocked", color: RED, description: "" }
      ]
    }) {
      field { ... on ProjectV2SingleSelectField { id name options { id name } } }
    }
  }
'
```

**WARNING:** Like iterations, updating single-select options does a FULL REPLACE. Include all existing options or they will be deleted.

### Setting a Single-Select Value

```bash
# 1. Get the option ID
OPTION_ID=$(gh project field-list 1 --owner raulstechtips --format json \
  --jq '.fields[] | select(.name == "Status") | .options[] | select(.name == "In Progress") | .id')

# 2. Set it
gh project item-edit \
  --id "$ITEM_ID" \
  --project-id "$PROJECT_ID" \
  --field-id "$STATUS_FIELD_ID" \
  --single-select-option-id "$OPTION_ID"
```

**SDLC skill:** `pick-task`, `complete-task`, `block-task`, `triage-issue`.

---

## 11. Archiving and Deleting Items

### Archive an Item

Archived items are hidden from views but still count toward limits. Good for completed sprint items.

```bash
# Archive
gh project item-archive 1 --owner raulstechtips --id "PVTI_lAHOAxxxxx"

# Unarchive
gh project item-archive 1 --owner raulstechtips --id "PVTI_lAHOAxxxxx" --undo
```

**Flags:**
| Flag | Description |
|------|-------------|
| `--id <string>` | Item ID to archive |
| `--owner <string>` | Login of the owner |
| `--undo` | Unarchive the item |
| `--format json` | JSON output |

### Delete an Item from Project

Removes the item from the project entirely. Does NOT delete the underlying issue/PR.

```bash
gh project item-delete 1 --owner raulstechtips --id "PVTI_lAHOAxxxxx"
```

**Flags:**
| Flag | Description |
|------|-------------|
| `--id <string>` | Item ID to delete |
| `--owner <string>` | Login of the owner |
| `--format json` | JSON output |

**SDLC skill:** `close-sprint` (archive done items), `cleanup-board` (remove stale items).

---

## 12. Views (Board, Table, Roadmap)

### View Types

GitHub Projects v2 supports three view layouts:
- **Table** -- spreadsheet-like, shows all fields as columns
- **Board** -- kanban board, columns driven by a single-select or iteration field (typically Status)
- **Roadmap** -- timeline view, requires date fields

### CLI Support for Views

**LIMITATION:** There is NO `gh project view-create` or `gh project view-edit` CLI command. Views can only be managed through:

1. **Web UI** -- create/edit views interactively
2. **GraphQL mutation** -- `createProjectV2View`

### Creating Views via GraphQL

```bash
# Create a Board view grouped by Status
gh api graphql -f query='
  mutation {
    createProjectV2View(input: {
      projectId: "PVT_kwHOAxxxxx"
      name: "Sprint Board"
      layout: BOARD_LAYOUT
    }) {
      projectV2View {
        id
        name
        layout
      }
    }
  }
'

# Create a Table view
gh api graphql -f query='
  mutation {
    createProjectV2View(input: {
      projectId: "PVT_kwHOAxxxxx"
      name: "Backlog Table"
      layout: TABLE_LAYOUT
    }) {
      projectV2View { id name layout }
    }
  }
'

# Create a Roadmap view
gh api graphql -f query='
  mutation {
    createProjectV2View(input: {
      projectId: "PVT_kwHOAxxxxx"
      name: "PI Roadmap"
      layout: ROADMAP_LAYOUT
    }) {
      projectV2View { id name layout }
    }
  }
'
```

**Caveat:** View configuration (column field, filters, sort, visible fields) may require additional GraphQL mutations or web UI configuration after creation.

### Opening a View in Browser

```bash
# Opens the project's default view in browser
gh project view 1 --owner raulstechtips --web
```

**SDLC skill:** `init-project` (create standard views), `view-board` (open in browser).

---

## 13. Built-in Automations and Workflows

### Default Workflows (Enabled Automatically)

When a project is created, two workflows are enabled:

1. **Item closed** -- When an issue or PR is closed, its Status is set to **Done**
2. **PR merged** -- When a PR is merged, its Status is set to **Done**

### Additional Built-in Workflows (Configurable via Web UI)

- **Auto-add from repository** -- Automatically add new issues/PRs matching a filter from linked repos
- **Auto-archive** -- Automatically archive items matching criteria (e.g., `is:closed updated:<30d`)
- **Item added to project** -- Set Status to a value when items are added (e.g., auto-set to "Todo")
- **Item reopened** -- Set Status when a closed item is reopened

### CLI Support for Automations

**LIMITATION:** There are NO CLI commands to configure project automations/workflows. All workflow configuration must be done through the web UI or GitHub Actions.

### GitHub Actions Integration

You can use GitHub Actions to automate project operations:

```yaml
# .github/workflows/auto-add-to-project.yml
name: Auto-add to project
on:
  issues:
    types: [opened]
  pull_request:
    types: [opened]

jobs:
  add-to-project:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/add-to-project@v1
        with:
          project-url: https://github.com/users/raulstechtips/projects/1
          github-token: ${{ secrets.PROJECT_TOKEN }}
```

For more complex automation (setting status on PR events, etc.), use `gh api graphql` within Actions:

```yaml
# Set Status to "In Review" when PR is opened
- name: Set status
  env:
    GH_TOKEN: ${{ secrets.PROJECT_TOKEN }}
  run: |
    # Add to project and get item ID
    ITEM_ID=$(gh project item-add 1 --owner raulstechtips \
      --url "${{ github.event.pull_request.html_url }}" \
      --format json --jq '.id')

    # Set status
    gh project item-edit \
      --id "$ITEM_ID" \
      --project-id "$PROJECT_ID" \
      --field-id "$STATUS_FIELD_ID" \
      --single-select-option-id "$IN_REVIEW_OPTION_ID"
```

**SDLC skill:** `init-project` (set up Actions workflows), but our primary use case is CLI-driven by agent skills, not event-driven automation.

---

## 14. GraphQL Fallbacks

For operations the CLI cannot handle, use `gh api graphql`. Here are the essential queries and mutations.

### Get Project ID and All Field Details (Master Query)

This is the single most important query. Run it once and cache the IDs.

```bash
gh api graphql -f query='
  query {
    user(login: "raulstechtips") {
      projectV2(number: 1) {
        id
        title
        url
        fields(first: 50) {
          nodes {
            ... on ProjectV2Field {
              id
              name
              dataType
            }
            ... on ProjectV2SingleSelectField {
              id
              name
              options {
                id
                name
                color
              }
            }
            ... on ProjectV2IterationField {
              id
              name
              configuration {
                duration
                startDay
                iterations {
                  id
                  title
                  startDate
                  duration
                }
                completedIterations {
                  id
                  title
                  startDate
                  duration
                }
              }
            }
          }
        }
      }
    }
  }
'
```

**For organization-owned projects**, replace `user(login:)` with `organization(login:)`.

### Add Item to Project

```bash
gh api graphql -f query='
  mutation($projectId: ID!, $contentId: ID!) {
    addProjectV2ItemById(input: {
      projectId: $projectId
      contentId: $contentId
    }) {
      item { id }
    }
  }
' -f projectId="PVT_kwHOAxxxxx" -f contentId="I_kwDOAxxxxx"
```

**Note:** `contentId` is the node ID of the issue or PR, obtainable via:
```bash
gh issue view 42 -R raulstechtips/calendar-agent --json id --jq '.id'
```

### Update Field Value

```bash
# Single-select (Status, Priority, etc.)
gh api graphql -f query='
  mutation {
    updateProjectV2ItemFieldValue(input: {
      projectId: "PVT_kwHOAxxxxx"
      itemId: "PVTI_lAHOAxxxxx"
      fieldId: "PVTF_lAHOAxxxxx"
      value: { singleSelectOptionId: "option_id_here" }
    }) {
      projectV2Item { id }
    }
  }
'

# Text field
gh api graphql -f query='
  mutation {
    updateProjectV2ItemFieldValue(input: {
      projectId: "PVT_kwHOAxxxxx"
      itemId: "PVTI_lAHOAxxxxx"
      fieldId: "PVTF_lAHOAxxxxx"
      value: { text: "some value" }
    }) {
      projectV2Item { id }
    }
  }
'

# Number field
gh api graphql -f query='
  mutation {
    updateProjectV2ItemFieldValue(input: {
      projectId: "PVT_kwHOAxxxxx"
      itemId: "PVTI_lAHOAxxxxx"
      fieldId: "PVTF_lAHOAxxxxx"
      value: { number: 5.0 }
    }) {
      projectV2Item { id }
    }
  }
'

# Date field
gh api graphql -f query='
  mutation {
    updateProjectV2ItemFieldValue(input: {
      projectId: "PVT_kwHOAxxxxx"
      itemId: "PVTI_lAHOAxxxxx"
      fieldId: "PVTF_lAHOAxxxxx"
      value: { date: "2026-03-25" }
    }) {
      projectV2Item { id }
    }
  }
'

# Iteration field
gh api graphql -f query='
  mutation {
    updateProjectV2ItemFieldValue(input: {
      projectId: "PVT_kwHOAxxxxx"
      itemId: "PVTI_lAHOAxxxxx"
      fieldId: "PVTIF_lAHOAxxxxx"
      value: { iterationId: "iteration_id_here" }
    }) {
      projectV2Item { id }
    }
  }
'
```

### Clear a Field Value

```bash
gh api graphql -f query='
  mutation {
    clearProjectV2ItemFieldValue(input: {
      projectId: "PVT_kwHOAxxxxx"
      itemId: "PVTI_lAHOAxxxxx"
      fieldId: "PVTF_lAHOAxxxxx"
    }) {
      projectV2Item { id }
    }
  }
'
```

### Query Items with Field Values

The CLI `item-list` shows items but not their custom field values in an easily parseable way. Use GraphQL for that:

```bash
gh api graphql -f query='
  query {
    user(login: "raulstechtips") {
      projectV2(number: 1) {
        items(first: 100) {
          nodes {
            id
            content {
              ... on Issue {
                title
                number
                url
                state
                labels(first: 10) { nodes { name } }
              }
              ... on PullRequest {
                title
                number
                url
                state
              }
              ... on DraftIssue {
                title
                body
              }
            }
            fieldValues(first: 20) {
              nodes {
                ... on ProjectV2ItemFieldTextValue {
                  field { ... on ProjectV2Field { name } }
                  text
                }
                ... on ProjectV2ItemFieldNumberValue {
                  field { ... on ProjectV2Field { name } }
                  number
                }
                ... on ProjectV2ItemFieldDateValue {
                  field { ... on ProjectV2Field { name } }
                  date
                }
                ... on ProjectV2ItemFieldSingleSelectValue {
                  field { ... on ProjectV2SingleSelectField { name } }
                  name
                }
                ... on ProjectV2ItemFieldIterationValue {
                  field { ... on ProjectV2IterationField { name } }
                  title
                  startDate
                  duration
                }
              }
            }
          }
        }
      }
    }
  }
'
```

### Create a Draft Issue via GraphQL

```bash
gh api graphql -f query='
  mutation {
    addProjectV2DraftIssue(input: {
      projectId: "PVT_kwHOAxxxxx"
      title: "Spike: Research vector search pricing"
      body: "Compare Azure AI Search tiers"
    }) {
      projectV2Item { id }
    }
  }
'
```

### Fields You CANNOT Update via Project API

These are properties of the issue/PR itself, not project fields:
- **Assignees** -- use `gh issue edit --add-assignee`
- **Labels** -- use `gh issue edit --add-label`
- **Milestone** -- use `gh issue edit --milestone`
- **Repository** -- inherent to the issue, cannot be changed

**SDLC skill:** Every skill that needs rich field data should prefer GraphQL over CLI for reads. CLI is fine for simple writes.

---

## 15. Bulk Operations

### Adding Multiple Issues at Once

There is no native bulk-add command. You must loop:

```bash
# Bash loop to add multiple issues
for ISSUE_NUM in 1 2 3 4 5; do
  gh project item-add 1 --owner raulstechtips \
    --url "https://github.com/raulstechtips/calendar-agent/issues/$ISSUE_NUM" \
    --format json
done
```

### Bulk Update Field Values

No native bulk-update. Loop over items:

```bash
# Set all items in "Todo" to Sprint 1
ITEMS=$(gh project item-list 1 --owner raulstechtips --format json \
  --jq '.items[] | select(.status == "Todo") | .id')

for ITEM_ID in $ITEMS; do
  gh project item-edit \
    --id "$ITEM_ID" \
    --project-id "$PROJECT_ID" \
    --field-id "$SPRINT_FIELD_ID" \
    --iteration-id "$SPRINT_1_ID"
done
```

### Bulk via GraphQL (More Efficient)

GraphQL does not support batch mutations natively, but you can alias multiple mutations in one request:

```bash
gh api graphql -f query='
  mutation {
    a: updateProjectV2ItemFieldValue(input: {
      projectId: "PVT_xxx" itemId: "PVTI_aaa" fieldId: "PVTF_yyy"
      value: { singleSelectOptionId: "opt_zzz" }
    }) { projectV2Item { id } }

    b: updateProjectV2ItemFieldValue(input: {
      projectId: "PVT_xxx" itemId: "PVTI_bbb" fieldId: "PVTF_yyy"
      value: { singleSelectOptionId: "opt_zzz" }
    }) { projectV2Item { id } }

    c: updateProjectV2ItemFieldValue(input: {
      projectId: "PVT_xxx" itemId: "PVTI_ccc" fieldId: "PVTF_yyy"
      value: { singleSelectOptionId: "opt_zzz" }
    }) { projectV2Item { id } }
  }
'
```

**Caveat:** GitHub's secondary rate limits may throttle rapid successive mutations. Space them out if doing 50+ operations.

**SDLC skill:** `plan-sprint` (bulk assign items to sprint), `close-sprint` (bulk archive done items).

---

## 16. Integration: Projects vs Issue Labels

### Key Principle: They Are Independent

Project field values and issue labels are **completely independent systems**. Changing a project Status field does NOT add/remove labels on the issue, and adding a label to an issue does NOT change any project field.

### Implications for Our SDLC Skills

| Current approach (labels) | Projects approach (fields) | Independence |
|---------------------------|---------------------------|--------------|
| `status:todo` label | Status field = "Todo" | Separate -- must sync manually |
| `type:story` label | Type field = "Story" | Separate -- must sync manually |
| `area:auth` label | Area field = "auth" | Separate -- must sync manually |
| `priority:p0` label | Priority field = "P0" | Separate -- must sync manually |

### Migration Strategy Options

**Option A: Projects only (drop labels for status/type)**
- Use project fields for Status, Priority, Area, Type
- Keep labels only for cross-cutting concerns (e.g., `good-first-issue`, `help-wanted`)
- Pro: Single source of truth, richer querying
- Con: Fields only visible within the project context; `gh issue list --label` stops working for status queries

**Option B: Dual-write (sync labels + fields)**
- When a skill sets a project field, also add/remove the corresponding label
- Pro: Both systems stay in sync; issue list filtering still works
- Con: More API calls, more complexity, drift risk

**Option C: Labels for cross-repo, fields for project-scoped**
- Use project fields for sprint-scoped data (Status, Sprint, Priority)
- Keep labels for data that outlives the project (Type, Area)
- Pro: Pragmatic middle ground
- Con: Split mental model

**Recommendation for SDLC skills:** Start with **Option A** (projects only) for new projects. The `--query` flag on `item-list` provides equivalent filtering. Only dual-write if external tools depend on labels.

**SDLC skill:** `migrate-to-projects` (one-time migration of label data to project fields).

---

## 17. Default Project Configuration

### What a New Project Comes With

When you run `gh project create`, the project starts with:

**Built-in fields (always present, cannot be deleted):**
| Field | Type | Notes |
|-------|------|-------|
| Title | Text | The issue/PR title (read from the issue) |
| Assignees | People | Read from the issue (cannot set via item-edit) |
| Status | Single Select | Default options: `Todo`, `In Progress`, `Done` |
| Labels | Labels | Read from the issue (cannot set via item-edit) |
| Milestone | Milestone | Read from the issue (cannot set via item-edit) |
| Repository | Repository | Read from the issue (cannot set via item-edit) |
| Reviewers | People | For PRs only |
| Linked PRs | Link | Auto-populated from issue references |
| Tracks | Tracking | Shows sub-issue progress |
| Tracked by | Tracking | Shows parent issue |

**Built-in views:**
- One default **Table** view

**Built-in workflows (enabled by default):**
1. Item closed -> Status = Done
2. PR merged -> Status = Done

**Custom field limit:** Up to 50 fields per project (including built-in).

### Recommended Initial Setup for Our SDLC

```bash
# 1. Create project
gh project create --owner raulstechtips --title "Calendar Agent PI-1" --format json

# 2. Link to repo
gh project link 1 --owner raulstechtips --repo calendar-agent

# 3. Create custom fields
gh project field-create 1 --owner raulstechtips \
  --name "Priority" --data-type SINGLE_SELECT \
  --single-select-options "P0-Critical,P1-High,P2-Medium,P3-Low"

gh project field-create 1 --owner raulstechtips \
  --name "Type" --data-type SINGLE_SELECT \
  --single-select-options "Epic,Feature,Story,Bug,Spike,Chore"

gh project field-create 1 --owner raulstechtips \
  --name "Area" --data-type SINGLE_SELECT \
  --single-select-options "auth,api,agent,calendar,search,chat,ui,infra"

gh project field-create 1 --owner raulstechtips \
  --name "Estimate" --data-type NUMBER

gh project field-create 1 --owner raulstechtips \
  --name "Target Date" --data-type DATE

# 4. Create iteration field (must use web UI -- see Section 9)
# gh project view 1 --owner raulstechtips --web

# 5. Customize Status options (must use web UI or GraphQL)
# Add "Blocked" and "In Review" to the Status field

# 6. Add existing issues
gh issue list -R raulstechtips/calendar-agent --state open --json url --jq '.[].url' | \
  while read URL; do
    gh project item-add 1 --owner raulstechtips --url "$URL"
  done
```

---

## 18. Organization vs User Projects

### User Projects (Our Case)

- Owned by a GitHub user account
- Created with `--owner <username>` or `--owner "@me"`
- Can include issues from any repo the user has access to
- Visibility: private by default, can be made public via web UI
- Limit: effectively unlimited projects per user

### Organization Projects

- Owned by a GitHub organization
- Created with `--owner <org-login>`
- All org members can see the project (visibility configurable)
- Can include issues from any repo in the organization
- Team linking: `gh project link 1 --owner my-org --team my-team`
- Better for multi-repo, multi-team coordination

### Key Differences

| Feature | User Project | Org Project |
|---------|-------------|-------------|
| Owner flag | `--owner raulstechtips` | `--owner my-org` |
| Visibility | Private/Public (web UI) | Private/Org-visible/Public |
| Team linking | N/A | `--team` flag supported |
| GraphQL query | `user(login:)` | `organization(login:)` |
| Cross-repo items | Any accessible repo | Any repo in the org |
| Role-based access | Just the owner | Org roles apply |

**For our repo (`raulstechtips/calendar-agent`):** Use user projects with `--owner raulstechtips`.

---

## 19. Limits and Rate Limits

### Project Limits

| Limit | Value | Notes |
|-------|-------|-------|
| Items per project | **50,000** | Increased from 1,200 in Feb 2025 public preview |
| Archived items | 10,000 | Within the 50k total |
| Custom fields per project | 50 | Including built-in fields |
| Single-select options per field | ~50 | Practical limit |
| Views per project | ~50 | Practical limit |
| Projects per user/org | Effectively unlimited | No documented hard limit |

### API Rate Limits

| Limit Type | Value | Notes |
|------------|-------|-------|
| Authenticated REST | 5,000 requests/hour | Standard GitHub rate limit |
| Authenticated GraphQL | 5,000 points/hour | GraphQL uses point-based costing |
| Secondary rate limits | Variable | Protects against burst abuse |
| gh CLI calls | Same as REST/GraphQL | Each `gh project` command = 1+ API calls |

### Performance Considerations for SDLC Skills

- **Cache field IDs:** The master GraphQL query (Section 14) should be run once per session and cached. Field IDs are stable.
- **Batch GraphQL mutations:** Use aliased mutations (Section 15) instead of sequential CLI calls for bulk operations.
- **Pagination:** `item-list` defaults to 30 items. Always set `-L` to a reasonable limit. For projects with >100 items, use GraphQL with cursor-based pagination.
- **Avoid polling:** Don't poll `item-list` in a loop. Use GitHub webhooks or Actions for event-driven updates.

---

## 20. SDLC Skill Mapping

### How Each Skill Maps to Project Commands

| Skill | Primary Commands | GraphQL Needed? |
|-------|-----------------|-----------------|
| **init-project** | `project create`, `project link`, `field-create` | Yes (iteration field, views) |
| **init-pi** | `project copy` or `project create` | Yes (iteration config) |
| **pick-task** | `item-list --query`, `item-edit` (set status) | No (CLI sufficient) |
| **create-story** | `gh issue create`, `item-add`, `item-edit` (set fields) | No |
| **plan-sprint** | `item-list`, `item-edit` (set iteration, priority) | Maybe (iteration IDs) |
| **sync-issues** | `item-list --query`, `field-list` | Yes (rich field value reads) |
| **complete-task** | `item-edit` (set status to Done) | No |
| **block-task** | `item-edit` (set status to Blocked) | No |
| **sprint-report** | `item-list --query`, GraphQL for field aggregation | Yes |
| **close-sprint** | `item-archive` (loop), iteration query | Maybe |
| **view-board** | `project view --web` | No |
| **triage-issue** | `item-add`, `item-edit` (set priority, type, area) | No |
| **update-decision** | N/A (local file operation) | No |
| **migrate-to-projects** | `item-add` (bulk), `item-edit` (bulk set fields) | Yes (batch mutations) |

### Recommended Helper: ID Resolution Cache

Every skill that writes field values needs the "Two-Step Dance" (Section 8). Build a shared helper:

```bash
# Cache this output at session start
gh project field-list 1 --owner raulstechtips --format json > /tmp/project-fields.json

# Helper function to resolve field + option IDs
get_field_id() { jq -r ".fields[] | select(.name == \"$1\") | .id" /tmp/project-fields.json; }
get_option_id() { jq -r ".fields[] | select(.name == \"$1\") | .options[] | select(.name == \"$2\") | .id" /tmp/project-fields.json; }
get_project_id() { gh project view 1 --owner raulstechtips --format json --jq '.id'; }
```

---

## Appendix: Quick Command Reference

### Project Lifecycle
```bash
gh project create --owner OWNER --title TITLE
gh project list --owner OWNER [--closed]
gh project view NUM --owner OWNER [--web] [--format json]
gh project edit NUM --owner OWNER [--title T] [-d DESC] [--readme R]
gh project close NUM --owner OWNER [--undo]
gh project delete NUM --owner OWNER
gh project copy NUM --source-owner SRC --target-owner DST --title T [--drafts]
gh project mark-template NUM --owner OWNER [--undo]
gh project link NUM --owner OWNER [--repo R | --team T]
gh project unlink NUM --owner OWNER [--repo R | --team T]
```

### Fields
```bash
gh project field-list NUM --owner OWNER [--format json] [-L LIMIT]
gh project field-create NUM --owner OWNER --name N --data-type {TEXT|NUMBER|DATE|SINGLE_SELECT} [--single-select-options "a,b,c"]
gh project field-delete --id FIELD_ID
```

### Items
```bash
gh project item-add NUM --owner OWNER --url ISSUE_URL [--format json]
gh project item-create NUM --owner OWNER --title T [--body B] [--format json]
gh project item-list NUM --owner OWNER [-L LIMIT] [--query FILTER] [--format json]
gh project item-edit --id ITEM_ID --project-id PROJ_ID --field-id FIELD_ID {--text V|--number V|--date V|--single-select-option-id V|--iteration-id V|--clear}
gh project item-archive NUM --owner OWNER --id ITEM_ID [--undo]
gh project item-delete NUM --owner OWNER --id ITEM_ID
```

### Auth
```bash
gh auth status                    # Check scopes
gh auth refresh -s project        # Add project scope
```

---

## Sources

- [gh project CLI manual](https://cli.github.com/manual/gh_project)
- [gh project create](https://cli.github.com/manual/gh_project_create)
- [gh project item-edit](https://cli.github.com/manual/gh_project_item-edit)
- [gh project field-create](https://cli.github.com/manual/gh_project_field-create)
- [gh project field-list](https://cli.github.com/manual/gh_project_field-list)
- [gh project item-add](https://cli.github.com/manual/gh_project_item-add)
- [gh project item-list](https://cli.github.com/manual/gh_project_item-list)
- [gh project item-archive](https://cli.github.com/manual/gh_project_item-archive)
- [gh project item-create](https://cli.github.com/manual/gh_project_item-create)
- [gh project item-delete](https://cli.github.com/manual/gh_project_item-delete)
- [gh project copy](https://cli.github.com/manual/gh_project_copy)
- [gh project close](https://cli.github.com/manual/gh_project_close)
- [gh project edit](https://cli.github.com/manual/gh_project_edit)
- [gh project link](https://cli.github.com/manual/gh_project_link)
- [gh project unlink](https://cli.github.com/manual/gh_project_unlink)
- [gh project mark-template](https://cli.github.com/manual/gh_project_mark-template)
- [gh project delete](https://cli.github.com/manual/gh_project_delete)
- [gh project field-delete](https://cli.github.com/manual/gh_project_field-delete)
- [Using the API to manage Projects (GitHub Docs)](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects)
- [About iteration fields (GitHub Docs)](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-iteration-fields)
- [Filtering projects (GitHub Docs)](https://docs.github.com/en/issues/planning-and-tracking-with-projects/customizing-views-in-your-project/filtering-projects)
- [Using built-in automations (GitHub Docs)](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-built-in-automations)
- [Automating Projects using Actions (GitHub Docs)](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions)
- [GitHub CLI project command GA announcement](https://github.blog/developer-skills/github/github-cli-project-command-is-now-generally-available/)
- [Increased Project Item Limits (GitHub Changelog)](https://github.blog/changelog/2025-02-26-increased-items-in-github-projects-now-in-public-preview/)
- [About Tracks and Tracked by fields](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-tracks-and-tracked-by-fields)
- [gh-iteration CLI extension](https://github.com/tasshi-me/gh-iteration)
- [GitHub Actions add-to-project](https://github.com/actions/add-to-project)
- [GraphQL examples for ProjectsV2](https://devopsjournal.io/blog/2022/11/28/github-graphql-queries)
- [GitHub Project automation blog post](https://thomasthornton.cloud/2024/11/14/using-github-cli-with-github-actions-for-github-project-automation/)
