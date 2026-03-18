---
name: sync-issues
description: Audit the full GitHub issue hierarchy — fix stale labels, validate dependencies, detect orphans and cycles, report project status. Use for a progress check or when issues might be stale.
allowed-tools: Read, Bash, Grep, Glob
argument-hint: "[optional: area filter like 'auth', 'api', 'agents', 'ui', 'infra', 'search']"
---

# Sync Issues

Audit and fix the full issue hierarchy. Validates labels, dependencies, and parent-child relationships.

## Steps

### 1. Fetch All Issues

```bash
# Open issues by type
gh issue list --state open --label "type:epic" --limit 200 --json number,title,body,labels
gh issue list --state open --label "type:feature" --limit 200 --json number,title,body,labels
gh issue list --state open --label "type:story" --limit 200 --json number,title,body,labels

# Closed issues with potentially stale labels
gh issue list --state closed --label "status:in-progress" --limit 200 --json number,title,labels
gh issue list --state closed --label "status:todo" --limit 200 --json number,title,labels
```

If area filter provided, add `--label "area:[area]"` to each query.

### 2. Fix Stale Labels

For each closed issue that still has `status:in-progress` or `status:todo`:
```bash
gh issue edit <number> --add-label "status:done" --remove-label "status:in-progress" --remove-label "status:todo"
```

### 3. Dependency Audit

For each open story, parse `Blocked by:` from the issue body.

For each blocker, check satisfaction:
```bash
gh issue view <dep> --json state,labels \
  --jq '{state: .state, labels: [.labels[].name]}'
```

**Fix mismatched labels:**
- If all blockers are satisfied but story is `status:blocked` → update to `status:todo`
- If any blocker is unmet but story is `status:todo` → update to `status:blocked`

```bash
# Unblock
gh issue edit <number> --add-label "status:todo" --remove-label "status:blocked"
# Block
gh issue edit <number> --add-label "status:blocked" --remove-label "status:todo"
```

### 4. Orphan Detection

For each issue number referenced in a `Blocked by` or `Blocks` line:
```bash
gh issue view <ref_number> --json state 2>&1
```
If the issue doesn't exist, flag it as an orphaned reference.

### 5. Circular Dependency Detection

Build a dependency adjacency list from all open issues:
- Key: issue number
- Value: list of issue numbers from its `Blocked by` line

For each issue, perform a DFS walk through the blocker chain:
- Start from the issue
- Follow each blocker's blockers
- If the starting issue is encountered, report the cycle:
  `Circular dependency: #A → #B → #C → #A`

### 6. Hierarchy Check

For each open story: verify it has a `## Parent` section with both Epic and Feature references.
For each open feature: verify it has a `## Parent` section with an Epic reference.

Flag any issues missing parent links.

### 7. Report

Present a summary:

```
## Sync Report

**Totals:** X epics, Y features, Z stories
**Status:** Done: X | In Progress: X | Todo: X | Blocked: X

**Fixes Applied:**
- Stale labels fixed: N (list issue numbers)
- Unblocked: N (issues moved from blocked → todo)
- Newly blocked: N (issues moved from todo → blocked)

**Issues Found:**
- Orphaned dep references: N (list them)
- Circular dependencies: N (list the cycles)
- Missing parent links: N (list them)

**Next Recommended Stories:**
[Top 3 unblocked stories by priority]
```

## Rules

- Do not manually close issues — issues close when PRs merge
- Fix stale labels automatically (closed + wrong status)
- Fix blocked/todo mismatches automatically
- Report but do NOT auto-fix: orphaned references, cycles, missing parents (these need human judgment)
