# 03 - GitHub Timeline & Events API for Process Metrics

> Reference document for the `sdlc:retro` skill. Every API call needed to measure
> sprint process metrics: time-in-status, blocked duration, PR lead time, review
> turnaround, code review compliance, and dependency accuracy.
>
> **Repo used for examples:** `raulstechtips/calendar-agent`

---

## Table of Contents

1. [Issue Timeline API](#1-issue-timeline-api)
2. [Issue Events API](#2-issue-events-api)
3. [Timeline vs Events: Which Endpoint for What](#3-timeline-vs-events-which-endpoint-for-what)
4. [Label Change Tracking (Time-in-Status)](#4-label-change-tracking-time-in-status)
5. [PR Metrics](#5-pr-metrics)
6. [PR-to-Issue Mapping](#6-pr-to-issue-mapping)
7. [Listing Merged PRs in a Date Range](#7-listing-merged-prs-in-a-date-range)
8. [Issue Body Edit History (GraphQL)](#8-issue-body-edit-history-graphql)
9. [Comment History](#9-comment-history)
10. [Assignment History](#10-assignment-history)
11. [Retro Metrics Cookbook](#11-retro-metrics-cookbook)
12. [What We CANNOT Measure](#12-what-we-cannot-measure)

---

## 1. Issue Timeline API

**Endpoint:** `GET /repos/{owner}/{repo}/issues/{issue_number}/timeline`

**gh command:**

```bash
gh api repos/raulstechtips/calendar-agent/issues/9/timeline \
  --paginate \
  -H "Accept: application/vnd.github.mockingbird-preview+json"
```

> **Note:** The timeline API requires the `mockingbird-preview` Accept header on
> older API versions. With `apiVersion=2022-11-28` it is generally stable, but
> including the header ensures full event coverage.

### All Timeline Event Types

The timeline endpoint is the **superset** -- it returns everything the events
endpoint returns, plus additional event types only available here.

| Event Type | Description | Key Fields | Timeline-Only? |
|---|---|---|---|
| `labeled` | Label added to issue/PR | `label.name`, `label.color`, `created_at`, `actor` | No |
| `unlabeled` | Label removed from issue/PR | `label.name`, `label.color`, `created_at`, `actor` | No |
| `closed` | Issue/PR closed | `created_at`, `actor`, `commit_id` (if closed via commit), `state_reason` | No |
| `reopened` | Issue/PR reopened | `created_at`, `actor` | No |
| `assigned` | User assigned | `assignee`, `assigner`, `created_at` | No |
| `unassigned` | User unassigned | `assignee`, `assigner`, `created_at` | No |
| `milestoned` | Added to milestone | `milestone.title`, `created_at`, `actor` | No |
| `demilestoned` | Removed from milestone | `milestone.title`, `created_at`, `actor` | No |
| `renamed` | Title changed | `rename.from`, `rename.to`, `created_at`, `actor` | No |
| `locked` | Conversation locked | `lock_reason`, `created_at`, `actor` | No |
| `unlocked` | Conversation unlocked | `created_at`, `actor` | No |
| `referenced` | Issue referenced from a commit | `commit_id`, `commit_url`, `created_at`, `actor` | No |
| `cross-referenced` | Referenced from another issue/PR | `source.issue.number`, `source.issue.pull_request`, `created_at`, `actor` | **Yes** |
| `commented` | Comment added | `body`, `user`, `created_at`, `updated_at`, `html_url` | **Yes** |
| `committed` | Commit added to PR branch | `sha`, `message`, `author`, `committer` | **Yes** |
| `reviewed` | PR review submitted | `state` (APPROVED/CHANGES_REQUESTED/COMMENTED/DISMISSED), `body`, `user`, `submitted_at`, `html_url` | **Yes** |
| `review_requested` | Review requested from user/team | `requested_reviewer` or `requested_team`, `review_requester`, `created_at` | **Yes** |
| `review_request_removed` | Review request removed | `requested_reviewer` or `requested_team`, `review_requester`, `created_at` | **Yes** |
| `connected` | Issue linked to PR (via "Closes #N") | `source`, `created_at`, `actor` | **Yes** |
| `disconnected` | Issue unlinked from PR | `source`, `created_at`, `actor` | **Yes** |
| `head_ref_force_pushed` | PR branch force-pushed | `created_at`, `actor` | **Yes** |
| `head_ref_deleted` | PR branch deleted | `created_at`, `actor` | **Yes** |
| `head_ref_restored` | PR branch restored | `created_at`, `actor` | **Yes** |
| `merged` | PR merged | `commit_id`, `commit_url`, `created_at`, `actor` | **Yes** |
| `deployed` | Deployment created | `created_at` (limited useful data) | **Yes** |
| `deployment_environment_changed` | Deployment env changed | `created_at` | **Yes** |
| `convert_to_draft` | PR converted to draft | `created_at`, `actor` | **Yes** |
| `ready_for_review` | PR marked ready for review | `created_at`, `actor` | **Yes** |
| `moved_columns_in_project` | Moved in classic project board | `project_card`, `created_at` | No |
| `added_to_project` | Added to classic project board | `project_card`, `created_at` | No |
| `removed_from_project` | Removed from classic project board | `project_card`, `created_at` | No |
| `converted_note_to_issue` | Project note converted to issue | `project_card`, `created_at` | No |
| `comment_deleted` | Comment was deleted | `created_at`, `actor` | **Yes** |
| `state_change` | State changed (draft/ready) | `state_reason`, `created_at` | **Yes** |
| `automatic_base_change_succeeded` | Base branch auto-updated | `created_at` | **Yes** |
| `automatic_base_change_failed` | Base branch auto-update failed | `created_at` | **Yes** |
| `auto_merge_enabled` | Auto-merge enabled | `created_at`, `actor` | **Yes** |
| `auto_merge_disabled` | Auto-merge disabled | `created_at`, `actor` | **Yes** |
| `auto_squash_enabled` | Auto-squash enabled | `created_at`, `actor` | **Yes** |
| `auto_rebase_enabled` | Auto-rebase enabled | `created_at`, `actor` | **Yes** |

### jq: Extract label events with timestamps

```bash
gh api repos/raulstechtips/calendar-agent/issues/9/timeline --paginate \
  --jq '[.[] | select(.event == "labeled" or .event == "unlabeled") |
  {event: .event, label: .label.name, at: .created_at, actor: .actor.login}]'
```

### Example output (illustrative)

```json
[
  {
    "event": "labeled",
    "label": "status:in-progress",
    "at": "2025-06-15T10:30:00Z",
    "actor": "raulstechtips"
  },
  {
    "event": "unlabeled",
    "label": "status:in-progress",
    "at": "2025-06-16T14:22:00Z",
    "actor": "raulstechtips"
  },
  {
    "event": "labeled",
    "label": "status:done",
    "at": "2025-06-16T14:22:05Z",
    "actor": "raulstechtips"
  }
]
```

### Pagination

- Default: 30 items per page, max: 100 (`per_page=100`)
- Use `--paginate` with `gh api` to auto-follow `Link` headers
- Issues with heavy activity (100+ events) will require multiple pages

### Rate limit cost

- 1 REST API request per page
- Authenticated: 5,000 requests/hour
- For a sprint with 20 issues averaging 30 events each: ~20 requests (comfortably within limits)

### Reliability: HIGH

The timeline is an immutable audit log. Events cannot be deleted or modified after
creation. Timestamps are server-side and accurate.

---

## 2. Issue Events API

**Endpoint:** `GET /repos/{owner}/{repo}/issues/{issue_number}/events`

**gh command:**

```bash
gh api repos/raulstechtips/calendar-agent/issues/9/events --paginate \
  --jq '[.[] | {event: .event, at: .created_at, actor: .actor.login}]'
```

### Events available in this endpoint

| Event Type | Description |
|---|---|
| `labeled` | Label added |
| `unlabeled` | Label removed |
| `closed` | Issue/PR closed |
| `reopened` | Issue/PR reopened |
| `assigned` | User assigned |
| `unassigned` | User unassigned |
| `milestoned` | Added to milestone |
| `demilestoned` | Removed from milestone |
| `renamed` | Title changed |
| `locked` | Conversation locked |
| `unlocked` | Conversation unlocked |
| `referenced` | Referenced from commit |
| `moved_columns_in_project` | Moved in project board |
| `added_to_project` | Added to project board |
| `removed_from_project` | Removed from project board |
| `converted_note_to_issue` | Note converted to issue |
| `head_ref_force_pushed` | Branch force-pushed |
| `head_ref_deleted` | Branch deleted |
| `head_ref_restored` | Branch restored |
| `review_dismissed` | Review dismissed |
| `review_requested` | Review requested |
| `review_request_removed` | Review request removed |
| `marked_as_duplicate` | Marked as duplicate |
| `unmarked_as_duplicate` | Unmarked as duplicate |
| `pinned` | Issue pinned |
| `unpinned` | Issue unpinned |
| `transferred` | Issue transferred to another repo |

### What is MISSING from this endpoint (use timeline instead)

- `commented` -- no comments
- `committed` -- no commits
- `reviewed` -- no reviews
- `cross-referenced` -- no cross-references
- `connected` / `disconnected` -- no link events
- `merged` -- no merge event
- `convert_to_draft` / `ready_for_review` -- no draft state changes

### Reliability: HIGH

Same immutable audit log as timeline. Timestamps are server-side.

---

## 3. Timeline vs Events: Which Endpoint for What

| Metric | Use Timeline? | Use Events? | Reason |
|---|---|---|---|
| Time-in-status (label changes) | YES | YES | Both have `labeled`/`unlabeled` with `created_at` |
| Blocked duration | YES | YES | Both have `labeled`/`unlabeled` |
| PR review turnaround | **YES** | NO | Only timeline has `reviewed` events with `submitted_at` |
| PR lead time (commits) | **YES** | NO | Only timeline has `committed` events |
| Code review comments | **YES** | NO | Only timeline has `commented` |
| PR-to-issue links | **YES** | NO | Only timeline has `connected`/`disconnected` |
| Assignment history | YES | YES | Both have `assigned`/`unassigned` |
| Draft-to-ready time | **YES** | NO | Only timeline has `ready_for_review` |

**Recommendation:** Always use the **timeline** endpoint. It is a strict superset
of the events endpoint for our purposes. The only reason to use the events
endpoint is if you need the repo-wide events list
(`GET /repos/{owner}/{repo}/issues/events`) which returns events across all
issues -- useful for bulk queries but limited to the events-only subset.

### Repo-wide events endpoint

```bash
# Get ALL label events across ALL issues (repo-wide)
gh api repos/raulstechtips/calendar-agent/issues/events --paginate \
  --jq '[.[] | select(.event == "labeled" or .event == "unlabeled") |
  {issue: .issue.number, event: .event, label: .label.name,
   at: .created_at, actor: .actor.login}]'
```

This is useful for bulk time-in-status calculations across a sprint without
querying each issue individually. However, it only includes the events-endpoint
subset (no comments, reviews, commits, or cross-references).

---

## 4. Label Change Tracking (Time-in-Status)

### The core technique

Our workflow uses `status:todo`, `status:in-progress`, `status:done`, and
`status:blocked` labels. Time-in-status is computed by pairing `labeled` and
`unlabeled` events.

### Step 1: Get all label events for an issue

```bash
gh api repos/raulstechtips/calendar-agent/issues/9/timeline --paginate \
  --jq '[.[] | select(.event == "labeled" or .event == "unlabeled") |
  select(.label.name | startswith("status:")) |
  {event: .event, label: .label.name, at: .created_at}]'
```

### Step 2: Reconstruct time-in-status (algorithm)

Given a sorted list of label events:

```
labeled   status:todo          2025-06-14T09:00:00Z
unlabeled status:todo          2025-06-15T10:30:00Z
labeled   status:in-progress   2025-06-15T10:30:00Z
unlabeled status:in-progress   2025-06-16T14:22:00Z
labeled   status:done          2025-06-16T14:22:00Z
```

The algorithm:
1. For each `labeled` event, record `{label, start: created_at}`
2. For each `unlabeled` event, find the matching open interval and set `end: created_at`
3. If a label is still applied (no matching `unlabeled`), use `now()` as end
4. Duration = `end - start`

Result:
```
status:todo          2025-06-14T09:00:00Z -> 2025-06-15T10:30:00Z  = 25.5 hours
status:in-progress   2025-06-15T10:30:00Z -> 2025-06-16T14:22:00Z  = 27.9 hours
status:done          2025-06-16T14:22:00Z -> (still applied)        = ongoing
```

### Step 3: Blocked duration

Same technique but filtering for `status:blocked`:

```bash
gh api repos/raulstechtips/calendar-agent/issues/9/timeline --paginate \
  --jq '[.[] | select(
    (.event == "labeled" or .event == "unlabeled") and
    .label.name == "status:blocked"
  ) | {event: .event, at: .created_at}]'
```

### Bulk approach: All issues in a sprint (via repo-wide events)

```bash
gh api repos/raulstechtips/calendar-agent/issues/events?per_page=100 \
  --paginate \
  --jq '[.[] | select(
    (.event == "labeled" or .event == "unlabeled") and
    (.label.name | startswith("status:"))
  ) | {issue: .issue.number, event: .event, label: .label.name,
       at: .created_at, actor: .actor.login}]'
```

### Reliability: MEDIUM-HIGH

- The data is 100% accurate IF labels are used consistently
- Failure mode: someone changes status without using labels (e.g., just closes the issue)
- Mitigation: also track `closed`/`reopened` events to catch status changes not reflected in labels
- Edge case: if someone removes and re-adds the same label quickly, you get two intervals

---

## 5. PR Metrics

### 5.1 PR Lead Time (First Commit to Merge)

**Definition:** Time from the first commit on the PR branch to merge.

```bash
gh pr view 112 --repo raulstechtips/calendar-agent \
  --json number,title,commits,mergedAt,createdAt
```

**jq to extract lead time inputs:**

```bash
gh pr view 112 --repo raulstechtips/calendar-agent \
  --json commits,mergedAt \
  --jq '{
    first_commit: .commits[0].committedDate,
    last_commit: .commits[-1].committedDate,
    merged_at: .mergedAt,
    total_commits: (.commits | length)
  }'
```

**Example output:**

```json
{
  "first_commit": "2025-06-15T10:30:00Z",
  "last_commit": "2025-06-16T11:00:00Z",
  "merged_at": "2025-06-16T14:22:00Z",
  "total_commits": 3
}
```

**Lead time** = `merged_at - first_commit`

**Note on `commits` field:** The `gh pr view --json commits` returns commit objects
with fields: `oid` (SHA), `messageHeadline`, `messageBody`, `committedDate`,
`authoredDate`, `authors`. The `committedDate` is what we want for lead time.

**Reliability: HIGH** -- commit dates and merge timestamps are immutable.

### 5.2 Review Turnaround

**Definition:** Time from PR creation (or first review request) to first review submission.

```bash
gh pr view 112 --repo raulstechtips/calendar-agent \
  --json createdAt,reviews \
  --jq '{
    pr_created: .createdAt,
    first_review: (
      [.reviews[] | select(.state != "PENDING")] |
      sort_by(.submittedAt) | first |
      {at: .submittedAt, state: .state, by: .author.login}
    ),
    all_reviews: [.reviews[] | select(.state != "PENDING") |
      {at: .submittedAt, state: .state, by: .author.login}]
  }'
```

**Example output:**

```json
{
  "pr_created": "2025-06-15T14:00:00Z",
  "first_review": {
    "at": "2025-06-15T16:30:00Z",
    "state": "APPROVED",
    "by": "reviewer-username"
  },
  "all_reviews": [
    {"at": "2025-06-15T16:30:00Z", "state": "APPROVED", "by": "reviewer-username"}
  ]
}
```

**Review turnaround** = `first_review.at - pr_created`

**Alternative: Time from review request to review:**

```bash
gh api repos/raulstechtips/calendar-agent/issues/112/timeline --paginate \
  --jq '[.[] | select(.event == "review_requested" or .event == "reviewed") |
  {event: .event,
   at: (if .event == "reviewed" then .submitted_at else .created_at end),
   actor: (if .event == "reviewed" then .user.login else
     (.requested_reviewer.login // .requested_team.slug) end),
   state: .state}]'
```

**Reliability: HIGH** -- review timestamps are server-side and immutable.

### 5.3 Code Churn

```bash
gh pr view 112 --repo raulstechtips/calendar-agent \
  --json additions,deletions,changedFiles,files \
  --jq '{
    additions: .additions,
    deletions: .deletions,
    changed_files: .changedFiles,
    files: [.files[] | {path: .path, additions: .additions,
            deletions: .deletions}]
  }'
```

**Example output:**

```json
{
  "additions": 142,
  "deletions": 38,
  "changed_files": 7,
  "files": [
    {"path": "backend/app/main.py", "additions": 45, "deletions": 12},
    {"path": "backend/tests/test_main.py", "additions": 97, "deletions": 26}
  ]
}
```

**Derived metrics:**
- **Net change** = additions - deletions
- **Churn ratio** = (additions + deletions) / total lines (requires separate file size query)
- **Test-to-prod ratio** = test file changes / production file changes

**Reliability: HIGH** -- diff stats are computed from immutable commit data.

### 5.4 Review Decision

```bash
gh pr view 112 --repo raulstechtips/calendar-agent \
  --json reviewDecision,latestReviews \
  --jq '{
    decision: .reviewDecision,
    latest_reviews: [.latestReviews[] |
      {by: .author.login, state: .state, at: .submittedAt}]
  }'
```

**`reviewDecision` values:**
- `APPROVED` -- all required reviewers approved
- `CHANGES_REQUESTED` -- at least one reviewer requested changes
- `REVIEW_REQUIRED` -- required reviews not yet submitted
- `""` (empty) -- no review protection rules configured

**`latestReviews`** contains only the most recent review from each reviewer (not
the full history). Use `reviews` for the complete history.

**Reliability: HIGH**

### 5.5 All PR fields available via `gh pr view --json`

For reference, the complete list of JSON fields:

```
additions, assignees, author, autoMergeRequest, baseRefName, baseRefOid,
body, changedFiles, closed, closedAt, closingIssuesReferences, comments,
commits, createdAt, deletions, files, fullDatabaseId, headRefName,
headRefOid, headRepository, headRepositoryOwner, id, isCrossRepository,
isDraft, labels, latestReviews, maintainerCanModify, mergeCommit,
mergeStateStatus, mergeable, mergedAt, mergedBy, milestone, number,
potentialMergeCommit, projectCards, projectItems, reactionGroups,
reviewDecision, reviewRequests, reviews, state, statusCheckRollup,
title, updatedAt, url
```

### 5.6 Composite PR metrics query (one call per PR)

```bash
gh pr view 112 --repo raulstechtips/calendar-agent \
  --json number,title,createdAt,mergedAt,mergedBy,commits,reviews,latestReviews,reviewDecision,additions,deletions,changedFiles,files,closingIssuesReferences,labels,author \
  --jq '{
    number: .number,
    title: .title,
    author: .author.login,
    created: .createdAt,
    merged: .mergedAt,
    merged_by: .mergedBy.login,
    decision: .reviewDecision,
    commits: (.commits | length),
    first_commit: .commits[0].committedDate,
    additions: .additions,
    deletions: .deletions,
    changed_files: .changedFiles,
    reviews_count: (.reviews | length),
    first_review_at: ([.reviews[] | select(.state != "PENDING")] | sort_by(.submittedAt) | first | .submittedAt),
    closing_issues: [.closingIssuesReferences[].number],
    labels: [.labels[].name]
  }'
```

This single call gives us everything needed for PR-level metrics.

---

## 6. PR-to-Issue Mapping

### 6.1 From PR to Issues (closingIssuesReferences)

**gh CLI (built-in since gh 2.44+):**

```bash
gh pr view 112 --repo raulstechtips/calendar-agent \
  --json closingIssuesReferences \
  --jq '[.closingIssuesReferences[] | {number: .number, title: .title}]'
```

**Example output:**

```json
[
  {"number": 100, "title": "User-based rate limiter and bounded refresh locks"}
]
```

**GraphQL alternative (for older gh versions or more control):**

```bash
gh api graphql -F owner='raulstechtips' -F repo='calendar-agent' -F pr=112 \
  -f query='
    query($owner: String!, $repo: String!, $pr: Int!) {
      repository(owner: $owner, name: $repo) {
        pullRequest(number: $pr) {
          closingIssuesReferences(first: 50) {
            nodes {
              number
              title
              state
              labels(first: 10) {
                nodes { name }
              }
            }
          }
        }
      }
    }
  ' --jq '.data.repository.pullRequest.closingIssuesReferences.nodes'
```

### 6.2 From Issue to PRs (closedByPullRequestsReferences -- GraphQL only)

There is **no REST API equivalent**. You must use GraphQL:

```bash
gh api graphql -F owner='raulstechtips' -F repo='calendar-agent' -F issue=100 \
  -f query='
    query($owner: String!, $repo: String!, $issue: Int!) {
      repository(owner: $owner, name: $repo) {
        issue(number: $issue) {
          timelineItems(first: 100, itemTypes: [CONNECTED_EVENT, DISCONNECTED_EVENT, CLOSED_EVENT, CROSS_REFERENCED_EVENT]) {
            nodes {
              __typename
              ... on ConnectedEvent {
                createdAt
                subject { ... on PullRequest { number title mergedAt } }
              }
              ... on CrossReferencedEvent {
                createdAt
                source { ... on PullRequest { number title mergedAt state } }
              }
              ... on ClosedEvent {
                createdAt
                closer { ... on PullRequest { number title mergedAt } }
              }
            }
          }
        }
      }
    }
  ' --jq '.data.repository.issue.timelineItems.nodes'
```

**Note:** `closedByPullRequestsReferences` was proposed but never shipped as a
first-class field on the Issue type in GitHub's GraphQL schema. The workaround
above uses `timelineItems` with `CONNECTED_EVENT` and `CLOSED_EVENT` filters.

### 6.3 Bulk: Map all merged PRs to their issues

```bash
gh pr list --repo raulstechtips/calendar-agent \
  --state merged --limit 100 \
  --json number,title,mergedAt,closingIssuesReferences \
  --jq '[.[] | {
    pr: .number,
    title: .title,
    merged: .mergedAt,
    closes: [.closingIssuesReferences[].number]
  } | select(.closes | length > 0)]'
```

**Reliability: MEDIUM**

- Only captures issues linked via "Closes #N", "Fixes #N", "Resolves #N" syntax
  in PR body or commit messages, OR via the GitHub UI sidebar "Linked Issues"
- If someone forgets to link, the mapping is missing
- Cross-repo references work but require the full `owner/repo#N` syntax

---

## 7. Listing Merged PRs in a Date Range

### Method 1: `gh search prs` (uses GitHub Search API)

```bash
gh search prs \
  --repo raulstechtips/calendar-agent \
  --merged-at "2025-06-01..2025-06-30" \
  --json number,title,createdAt,closedAt,url,repository \
  --limit 100
```

**Available `--json` fields for `gh search prs`:**
```
assignees, author, authorAssociation, body, closedAt, commentsCount,
createdAt, id, isDraft, isLocked, isPullRequest, labels, number,
repository, state, title, updatedAt, url
```

**Limitation:** `gh search prs --json` does NOT include `mergedAt`, `commits`,
`reviews`, `additions`, `deletions`, or `closingIssuesReferences`. It only
returns search-result-level fields. You must follow up with `gh pr view` for
each PR to get detailed metrics.

### Method 2: `gh pr list` with `--search` (uses Issues & PRs search)

```bash
gh pr list --repo raulstechtips/calendar-agent \
  --state merged \
  --search "merged:2025-06-01..2025-06-30" \
  --json number,title,mergedAt,createdAt,additions,deletions,changedFiles,reviewDecision,author,closingIssuesReferences,commits,reviews \
  --limit 100
```

This is **much better** because `gh pr list --json` has access to the full PR
field set including `mergedAt`, `reviews`, `commits`, etc. The `--search` flag
passes GitHub search syntax.

### Method 3: REST API search endpoint

```bash
gh api "search/issues?q=repo:raulstechtips/calendar-agent+is:pr+is:merged+merged:2025-06-01..2025-06-30&per_page=100" \
  --jq '[.items[] | {number: .number, title: .title, closed_at: .closed_at}]'
```

**Note:** The search API returns issue-level data. For PR-specific fields, you
still need `gh pr view` per item.

### Recommended approach for retro

Use Method 2 (`gh pr list --state merged --search`) to get the full PR data in
one call. Paginate if more than 100 PRs (unlikely for a 2-week sprint).

### Date range syntax

- `merged:2025-06-01..2025-06-30` -- between two dates
- `merged:>=2025-06-01` -- on or after a date
- `merged:<2025-07-01` -- before a date
- `merged:2025-06-15` -- on an exact date
- Dates are ISO8601: `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SS+00:00`

### Rate limits

- Search API: 30 requests/minute for authenticated users (stricter than REST)
- `gh pr list` uses GraphQL under the hood: 5,000 points/hour
- Each `gh pr list` call with `--json` that includes `commits` and `reviews`
  can cost significant GraphQL "node" budget depending on PR size

### Reliability: HIGH

Merge timestamps are immutable. Search indexing delay is typically < 1 minute.

---

## 8. Issue Body Edit History (GraphQL userContentEdits)

### Query

```bash
gh api graphql -F owner='raulstechtips' -F repo='calendar-agent' -F issue=9 \
  -f query='
    query($owner: String!, $repo: String!, $issue: Int!) {
      repository(owner: $owner, name: $repo) {
        issue(number: $issue) {
          createdAt
          lastEditedAt
          userContentEdits(first: 100) {
            totalCount
            nodes {
              createdAt
              editedAt
              editor { login }
              diff
            }
          }
        }
      }
    }
  ' --jq '{
    created: .data.repository.issue.createdAt,
    last_edited: .data.repository.issue.lastEditedAt,
    edit_count: .data.repository.issue.userContentEdits.totalCount,
    edits: .data.repository.issue.userContentEdits.nodes
  }'
```

### Fields returned per edit

| Field | Description |
|---|---|
| `createdAt` | When the edit was made |
| `editedAt` | Same as createdAt for edits (distinct for restorations) |
| `editor.login` | Who made the edit |
| `diff` | The actual content diff (unified diff format) |
| `deletedAt` | Non-null if the edit was deleted |
| `deletedBy` | Who deleted the edit |

### Example output

```json
{
  "created": "2025-06-14T09:00:00Z",
  "last_edited": "2025-06-15T11:00:00Z",
  "edit_count": 2,
  "edits": [
    {
      "createdAt": "2025-06-14T09:00:00Z",
      "editedAt": "2025-06-14T09:00:00Z",
      "editor": {"login": "raulstechtips"},
      "diff": null
    },
    {
      "createdAt": "2025-06-15T11:00:00Z",
      "editedAt": "2025-06-15T11:00:00Z",
      "editor": {"login": "raulstechtips"},
      "diff": "--- \n+++ \n@@ -1,5 +1,8 @@\n+Added acceptance criteria\n"
    }
  ]
}
```

### Limitations

1. **First edit has `diff: null`** -- the first node represents the original creation,
   not an edit. The diff is only available from the second node onward.
2. **No retention policy enforced** -- edits are retained indefinitely on GitHub.com
   (GitHub considered adding a 90-day retention but never shipped it).
3. **Pagination** -- max 100 per page, use `after` cursor for more.
4. **Rate limits** -- counts against GraphQL point budget (5,000 points/hour).
   Each `userContentEdits` connection costs ~1 point per node.
5. **Not available on GHES < 3.0** -- only GitHub.com and recent GHES versions.

### Use case for retro

Track how acceptance criteria evolved during a sprint. If ACs were edited
significantly after work started, that indicates scope creep.

### Reliability: LOW-MEDIUM

- The data exists and is accurate when present
- BUT: many teams edit issue bodies without realizing it creates an edit trail
- Some teams use comments instead of editing the body, so edits may be empty
- The `diff` format is not standardized -- it varies by edit type
- **Not useful as a primary metric; treat as supplementary signal only**

---

## 9. Comment History

### 9.1 Issue/PR comments (regular comments)

**REST API:**

```bash
gh api repos/raulstechtips/calendar-agent/issues/9/comments?per_page=100 \
  --paginate \
  --jq '[.[] | {
    id: .id,
    author: .user.login,
    created_at: .created_at,
    updated_at: .updated_at,
    body: .body,
    html_url: .html_url
  }]'
```

**gh CLI shorthand:**

```bash
gh issue view 9 --repo raulstechtips/calendar-agent --json comments \
  --jq '[.comments[] | {
    author: .author.login,
    created: .createdAt,
    body: (.body | split("\n")[0])
  }]'
```

### 9.2 PR review comments (inline code comments)

```bash
gh api repos/raulstechtips/calendar-agent/pulls/112/comments?per_page=100 \
  --paginate \
  --jq '[.[] | {
    id: .id,
    author: .user.login,
    created_at: .created_at,
    path: .path,
    line: .line,
    body: .body,
    in_reply_to_id: .in_reply_to_id
  }]'
```

### 9.3 All comments via timeline (includes both regular and review comments)

```bash
gh api repos/raulstechtips/calendar-agent/issues/112/timeline --paginate \
  --jq '[.[] | select(.event == "commented" or .event == "reviewed") |
  {event: .event,
   author: (.user.login // .actor.login),
   at: (.created_at // .submitted_at),
   body_preview: ((.body // "") | split("\n")[0] | .[:80])}]'
```

### Parameters

| Parameter | Description |
|---|---|
| `since` | ISO8601 timestamp -- only return comments updated after this time |
| `per_page` | Items per page (max 100) |
| `sort` | `created` (default) or `updated` |
| `direction` | `asc` (default) or `desc` |

### Reliability: HIGH

Comment timestamps are server-side and immutable. `updated_at` changes if a
comment is edited, but `created_at` is always the original post time.

---

## 10. Assignment History

### Via timeline API

```bash
gh api repos/raulstechtips/calendar-agent/issues/9/timeline --paginate \
  --jq '[.[] | select(.event == "assigned" or .event == "unassigned") |
  {event: .event,
   assignee: .assignee.login,
   assigner: .assigner.login,
   at: .created_at}]'
```

### Example output

```json
[
  {
    "event": "assigned",
    "assignee": "raulstechtips",
    "assigner": "raulstechtips",
    "at": "2025-06-14T09:00:00Z"
  },
  {
    "event": "unassigned",
    "assignee": "raulstechtips",
    "assigner": "raulstechtips",
    "at": "2025-06-16T14:00:00Z"
  }
]
```

### Derived metric: Assignment duration

Same interval algorithm as time-in-status:
- Pair `assigned`/`unassigned` events per assignee
- If still assigned, use `now()` as end

### Via events API (also works, same data)

```bash
gh api repos/raulstechtips/calendar-agent/issues/9/events --paginate \
  --jq '[.[] | select(.event == "assigned" or .event == "unassigned") |
  {event: .event, assignee: .assignee.login, at: .created_at}]'
```

### Reliability: HIGH

Assignment events are always recorded. The only gap is if someone uses the API
to set the assignee directly at creation time -- then there is no `assigned`
event, just the initial `assignees` field on the issue. Check `issue.assignees`
at creation time as a baseline.

---

## 11. Retro Metrics Cookbook

### Recipe 1: Average Time-in-Progress for Sprint Stories

**Goal:** Calculate how long stories spend in `status:in-progress` on average.

```bash
# Step 1: Get all issues for the sprint (by milestone or label)
ISSUES=$(gh issue list --repo raulstechtips/calendar-agent \
  --label "status:done" --state closed \
  --search "closed:2025-06-01..2025-06-30" \
  --json number --jq '.[].number')

# Step 2: For each issue, get label timeline events
for ISSUE in $ISSUES; do
  echo "=== Issue #$ISSUE ==="
  gh api "repos/raulstechtips/calendar-agent/issues/$ISSUE/timeline" \
    --paginate \
    --jq '[.[] | select(
      (.event == "labeled" or .event == "unlabeled") and
      .label.name == "status:in-progress"
    ) | {event: .event, at: .created_at}]'
done

# Step 3: Process in the retro skill (Python/jq):
# - Pair labeled/unlabeled events into intervals
# - Sum durations per issue
# - Calculate mean, median, p90
```

**API cost:** 1 call for issue list + 1 call per issue = ~21 calls for 20 stories.

### Recipe 2: PR Review Turnaround per Sprint

**Goal:** Median time from PR creation to first substantive review.

```bash
# Step 1: Get all merged PRs in the sprint window
gh pr list --repo raulstechtips/calendar-agent \
  --state merged \
  --search "merged:2025-06-01..2025-06-30" \
  --json number,createdAt,mergedAt,reviews,author \
  --jq '[.[] | {
    pr: .number,
    author: .author.login,
    created: .createdAt,
    merged: .mergedAt,
    first_review: (
      [.reviews[] | select(.state != "PENDING" and .state != "COMMENTED")] |
      sort_by(.submittedAt) | first |
      {at: .submittedAt, state: .state, by: .author.login}
    )
  }]'

# Step 2: Calculate turnaround for each PR:
# turnaround = first_review.at - created
# Then compute median across all PRs
```

**API cost:** 1 GraphQL call (via `gh pr list`). Very efficient.

### Recipe 3: Code Review Compliance

**Goal:** What percentage of merged PRs had at least one approval before merge?

```bash
gh pr list --repo raulstechtips/calendar-agent \
  --state merged \
  --search "merged:2025-06-01..2025-06-30" \
  --json number,reviewDecision,latestReviews,mergedBy,author \
  --jq '{
    total: length,
    approved: [.[] | select(.reviewDecision == "APPROVED")] | length,
    no_review: [.[] | select(.reviewDecision == "" or .reviewDecision == null)] | length,
    changes_requested_at_merge: [.[] | select(.reviewDecision == "CHANGES_REQUESTED")] | length,
    self_merged: [.[] | select(.mergedBy.login == .author.login)] | length
  }'
```

**Example output:**

```json
{
  "total": 15,
  "approved": 12,
  "no_review": 2,
  "changes_requested_at_merge": 1,
  "self_merged": 3
}
```

**Compliance rate** = `approved / total * 100`

**API cost:** 1 call.

### Recipe 4: Sprint Velocity and Lead Time Distribution

**Goal:** For each story, compute end-to-end lead time (created to PR merged).

```bash
# Step 1: Get all merged PRs with their linked issues
SPRINT_PRS=$(gh pr list --repo raulstechtips/calendar-agent \
  --state merged \
  --search "merged:2025-06-01..2025-06-30" \
  --json number,mergedAt,closingIssuesReferences,commits,createdAt \
  --jq '[.[] | {
    pr: .number,
    merged: .mergedAt,
    first_commit: .commits[0].committedDate,
    issues: [.closingIssuesReferences[].number]
  }]')

# Step 2: For each linked issue, get creation timestamp
echo "$SPRINT_PRS" | jq -r '.[].issues[]' | sort -u | while read ISSUE; do
  gh issue view "$ISSUE" --repo raulstechtips/calendar-agent \
    --json number,createdAt,closedAt \
    --jq '{number: .number, created: .createdAt, closed: .closedAt}'
done

# Step 3: Join and compute:
# story_lead_time = pr.merged - issue.created
# coding_time = pr.merged - pr.first_commit
# queue_time = story_lead_time - coding_time
```

**API cost:** 1 call for PRs + 1 call per unique linked issue.

### Recipe 5: Blocked Duration Impact

**Goal:** Total hours lost to blocked status across all sprint stories.

```bash
# Get all status:blocked label events across the repo
gh api repos/raulstechtips/calendar-agent/issues/events?per_page=100 \
  --paginate \
  --jq '[.[] | select(
    (.event == "labeled" or .event == "unlabeled") and
    .label.name == "status:blocked"
  ) | {
    issue: .issue.number,
    issue_title: .issue.title,
    event: .event,
    at: .created_at,
    actor: .actor.login
  }]'

# Then pair labeled/unlabeled per issue, sum intervals,
# and total across all issues
```

**API cost:** Paginated, ~1-3 calls depending on event volume.

### Recipe 6: Dependency Accuracy (Predicted vs Actual Blockers)

**Goal:** Were issues labeled `blocked-by:X` actually blocked by issue X?

```bash
# Step 1: Find all issues that were ever labeled "status:blocked"
# and get their timeline to see blocker labels
for ISSUE in $(gh issue list --repo raulstechtips/calendar-agent \
  --state all --label "status:blocked" --json number --jq '.[].number'); do

  echo "=== Issue #$ISSUE ==="
  gh api "repos/raulstechtips/calendar-agent/issues/$ISSUE/timeline" \
    --paginate \
    --jq '[.[] | select(
      .event == "labeled" and (.label.name | startswith("blocked-by:"))
    ) | {blocker_label: .label.name, at: .created_at}]'
done

# Step 2: For each blocker reference, check if that issue was actually
# closed before the blocked issue was unblocked
# This requires cross-referencing issue close dates
```

**Note:** This recipe depends on a `blocked-by:N` labeling convention. If your
workflow does not use structured blocker labels, this metric cannot be computed
from GitHub data alone.

**API cost:** Variable, depends on number of blocked issues.

---

## 12. What We CANNOT Measure

### Completely impossible

| Metric | Why |
|---|---|
| **Time spent actually coding** | GitHub has no work-tracking timer. Label timestamps measure process state, not developer effort. |
| **Context switch frequency** | No API tracks when a developer stops working on one issue and starts another. |
| **Meeting overhead** | GitHub has zero visibility into calendar/meeting data. |
| **Local branch age before PR** | Commits have author dates, but local branches are invisible to GitHub until pushed. |
| **Verbal decisions** | Decisions made in Slack, standup, or hallway conversations leave no GitHub trace. |

### Technically possible but unreliable

| Metric | Why Unreliable | Workaround |
|---|---|---|
| **Accurate time-in-status** | Only works if team consistently uses status labels. Manual close without label change creates gaps. | Also track `closed`/`reopened` events as fallback status signals. |
| **PR review quality** | We can count reviews and their state, but not whether the reviewer actually read the code. | Look at review comment count + code churn as proxy. |
| **Scope creep** | `userContentEdits` shows body changes, but not all scope changes happen in the issue body. | Supplement with comment analysis and label tracking. |
| **Issue size estimation accuracy** | No built-in estimation field. Would need a labeling convention (e.g., `size:S/M/L`). | Add size labels to workflow, then compare label vs actual `additions+deletions`. |
| **Draft-to-ready time** | `convert_to_draft` and `ready_for_review` events exist, but only if the PR was actually created as draft first. | Only measure when both events are present. |
| **PR-to-issue mapping completeness** | `closingIssuesReferences` only captures explicit "Closes #N" links. | Supplement with `cross-referenced` timeline events and commit message parsing. |

### Requires non-GitHub data

| Metric | External Source Needed |
|---|---|
| **CI/CD pipeline duration** | GitHub Actions API (`gh run list`, `gh run view`) -- separate from issues/PRs API |
| **Deployment frequency** | Deployment API or Actions workflow run data |
| **Incident response time** | Requires incident management system integration |
| **Customer-reported vs internal bugs** | Requires issue triage metadata or external bug tracker |

### GitHub Projects (v2) limitations

Our label-based workflow sidesteps GitHub Projects, but if we ever adopt Projects
v2, note that:
- Project field changes (status column moves) are **NOT** available via the REST
  timeline API
- They require the GraphQL `ProjectV2ItemFieldValueEvent` which is in preview
  and poorly documented
- The `moved_columns_in_project` event only works with **classic** (v1) projects

---

## Appendix: Rate Limit Budget for a Full Retro

Assuming a 2-week sprint with 20 stories and 15 merged PRs:

| Operation | Calls | Notes |
|---|---|---|
| List merged PRs with full data | 1 | `gh pr list --state merged --search --json` |
| List sprint issues | 1 | `gh issue list` with date/label filters |
| Timeline per issue (20 issues) | 20 | 1 call each (most fit in 1 page) |
| Issue comments (if needed) | 20 | Usually already in timeline |
| Issue body edits (if needed) | 20 | GraphQL, 1 per issue |
| **Total REST calls** | **~42** | Well under 5,000/hour |
| **Total GraphQL calls** | **~22** | Well under 5,000 points/hour |

The full retro data collection fits comfortably in a single burst with no
rate limit concerns.

---

## Appendix: Quick Reference -- gh Commands Cheat Sheet

```bash
# --- Issue timeline (all events) ---
gh api repos/OWNER/REPO/issues/N/timeline --paginate

# --- Issue events (subset, but supports repo-wide query) ---
gh api repos/OWNER/REPO/issues/N/events --paginate
gh api repos/OWNER/REPO/issues/events --paginate  # all issues

# --- Label events for time-in-status ---
gh api repos/OWNER/REPO/issues/N/timeline --paginate \
  --jq '[.[] | select(.event=="labeled" or .event=="unlabeled")]'

# --- PR metrics (one call) ---
gh pr view N --repo OWNER/REPO \
  --json createdAt,mergedAt,commits,reviews,reviewDecision,additions,deletions,changedFiles,closingIssuesReferences

# --- Merged PRs in date range ---
gh pr list --repo OWNER/REPO --state merged \
  --search "merged:YYYY-MM-DD..YYYY-MM-DD" \
  --json number,mergedAt,createdAt,reviews,reviewDecision,additions,deletions

# --- PR-to-issue mapping ---
gh pr view N --repo OWNER/REPO --json closingIssuesReferences

# --- Issue body edit history ---
gh api graphql -F owner=OWNER -F repo=REPO -F issue=N \
  -f query='{ repository(owner:$owner,name:$repo) { issue(number:$issue) {
    userContentEdits(first:100) { nodes { createdAt diff editor { login } } }
  }}}'

# --- Comments ---
gh api repos/OWNER/REPO/issues/N/comments --paginate
gh api repos/OWNER/REPO/pulls/N/comments --paginate  # review comments

# --- Assignment history ---
gh api repos/OWNER/REPO/issues/N/timeline --paginate \
  --jq '[.[] | select(.event=="assigned" or .event=="unassigned")]'
```
