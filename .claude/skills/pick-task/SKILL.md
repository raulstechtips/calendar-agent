---
name: pick-task
description: Pick the next story to work on from GitHub issues based on priority and dependencies. Use at the start of a coding session or after completing a story.
allowed-tools: Read, Bash, Grep, Glob
argument-hint: "[optional: area like 'auth', 'api', 'agents']"
---

# Pick Next Task

Find the highest-priority unblocked story to work on next.

## Steps

1. **Read the spec** at `.claude/specs/in-progress/SPEC.md` for current context.

2. **Get available stories** (excluding blocked):
   ```bash
   gh issue list --label "type:story" --label "status:todo" --json number,title,body,labels --jq '[.[] | select(.labels | map(.name) | contains(["status:blocked"]) | not)] | .[] | "#\(.number) [\(.labels | map(.name) | join(", "))] \(.title)"'
   ```

3. **Check dependencies** — for each candidate, read the issue body and verify its dependencies are completed (issues referenced in "Dependencies" section should be `status:done`).

4. **Rank by**: priority:critical > priority:high > priority:medium, then sprint:day1 > sprint:day2.

5. **If area filter provided**, only consider issues with that area label.

6. **Present the recommendation**:
   - Issue number and title
   - Why it's next (priority, unblocked)
   - Key acceptance criteria
   - File scope
   - Ask for confirmation before starting

7. **On confirmation**, update the issue:
   ```bash
   gh issue edit <number> --add-label "status:in-progress" --remove-label "status:todo"
   ```
   Then read the full issue body and begin implementation.
