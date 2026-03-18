---
name: pick-task
description: Find the next unblocked story to work on from GitHub issues based on priority and dependency analysis. Use at the start of a coding session or after completing a story.
allowed-tools: Read, Bash, Grep, Glob
argument-hint: "[optional: area like 'auth', 'api', 'agents', 'ui', 'infra', 'search']"
---

# Pick Next Task

Find the highest-priority unblocked story to work on next.

## Steps

1. **Read context** — read the PI Plan for current sprint awareness:
   ```bash
   cat .claude/pi/PI.md
   ```

2. **Get candidate stories** — fetch all open stories labeled `status:todo`:
   ```bash
   gh issue list --state open --label "type:story" --label "status:todo" --limit 200 \
     --json number,title,body,labels,createdAt \
     --jq '.[] | {number, title, labels: [.labels[].name], createdAt, body}'
   ```

3. **Check dependencies** — for each candidate, parse the `## Dependencies` section from the issue body. Extract issue numbers from the `Blocked by:` line.

   Handle formatting variations:
   - `Blocked by: #45, #46` or `Blocked by: #45,#46`
   - `- Blocked by: #45` (with leading dash)
   - `Blocked by:` with nothing after it = no blockers

   For each blocker found, check if it's satisfied:
   ```bash
   gh issue view <dep_number> --json state,labels \
     --jq '{state: .state, labels: [.labels[].name]}'
   ```

   **Blocker satisfaction criteria:**
   - Satisfied if: issue has `status:done` in labels OR state is `CLOSED`
   - Unmet if: issue is `OPEN` without `status:done` label

   If ANY blocker is unmet, this story is NOT eligible. Also fix its label:
   ```bash
   gh issue edit <number> --add-label "status:blocked" --remove-label "status:todo"
   ```

4. **Filter** — keep only stories where ALL blockers are satisfied.

5. **Area filter** — if an area argument was provided, narrow to stories with that `area:*` label.

6. **Rank** the remaining stories by:
   1. Priority: `priority:critical` > `priority:high` > `priority:medium` > `priority:low` > no priority
   2. Creation date: older first (lower issue number = created earlier)

7. **Present recommendation**:
   - Issue number and title
   - Why it's next (priority level, unblocked status)
   - Key acceptance criteria (from issue body)
   - File scope (from issue body)
   - Parent feature and epic
   - Ask: "Start working on this story?"

8. **On confirmation**:
   ```bash
   gh issue edit <number> --add-label "status:in-progress" --remove-label "status:todo"
   ```
   Then read the full issue body and begin the development workflow from `.claude/rules/workflow.md`.
