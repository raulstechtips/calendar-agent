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
   gh issue list --label "status:in-progress" --json number,title,labels
   gh issue list --label "status:todo" --json number,title,labels
   ```

2. **Check code state** — for each in-progress issue, verify if the work described in its acceptance criteria is actually done by checking the file scope listed in the issue.

3. **Update statuses** (labels must be mutually exclusive — always remove old status):
   - If acceptance criteria are met → `gh issue edit <number> --add-label "status:done" --remove-label "status:in-progress" --remove-label "status:todo"`
   - If work hasn't started → keep at `status:todo` (no action needed)
   - If dependencies aren't met → `gh issue edit <number> --add-label "status:blocked" --remove-label "status:todo" --remove-label "status:in-progress"`

4. **Report summary**:
   - Total: X stories
   - Done: X | In Progress: X | Todo: X | Blocked: X
   - Next recommended stories to pick up (unblocked, highest priority)

## Rules

- If an area filter is provided (e.g., "auth"), only check issues with that area label
- Never close issues — only update status labels
- Flag any issues where the described file scope doesn't match what actually exists
