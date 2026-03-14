---
name: sync-issues
description: Review GitHub issues status against actual code state and update labels/descriptions accordingly. Use when you want a progress check or when issues might be stale.
allowed-tools: Read, Bash, Grep, Glob
argument-hint: "[optional: area filter like 'auth' or 'api']"
---

# Sync Issues Workflow

Review the current state of GitHub issues and sync them with reality.

## Steps

1. **Get current issue state**:
   ```bash
   gh issue list --state open --label "status:in-progress" --json number,title,labels
   gh issue list --state open --label "status:todo" --json number,title,labels
   ```

   Also check for **stale labels on closed issues** (closed but not labeled `status:done`):
   ```bash
   gh issue list --state closed --label "status:in-progress" --json number,title,labels
   gh issue list --state closed --label "status:todo" --json number,title,labels
   ```

2. **Check code state** — for each open in-progress issue, verify if the work described in its acceptance criteria is actually done by checking the file scope listed in the issue.

3. **Update statuses** (labels must be mutually exclusive — always remove old status):
   - If acceptance criteria are met → `gh issue edit <number> --add-label "status:done" --remove-label "status:in-progress" --remove-label "status:todo"`
   - If work hasn't started → keep at `status:todo` (no action needed)
   - If dependencies aren't met → `gh issue edit <number> --add-label "status:blocked" --remove-label "status:todo" --remove-label "status:in-progress"`
   - If issue is **closed but has stale label** (`status:in-progress` or `status:todo`) → fix the label: `gh issue edit <number> --add-label "status:done" --remove-label "status:in-progress" --remove-label "status:todo"`

4. **Report summary**:
   - Total: X stories
   - Done: X | In Progress: X | Todo: X | Blocked: X
   - Stale labels fixed: X (closed issues whose labels were updated to `status:done`)
   - Next recommended stories to pick up (unblocked, highest priority)

## Rules

- If an area filter is provided (e.g., "auth"), only check issues with that area label
- Do not manually close issues — issues close automatically when their PR is merged
- Fix stale labels: if a closed issue still has `status:in-progress` or `status:todo`, update its label to `status:done`
- Flag any issues where the described file scope doesn't match what actually exists
