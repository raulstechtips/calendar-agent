---
name: update-story
description: Modify a story's acceptance criteria, file scope, dependencies, or technical notes. Use when a story's requirements change.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
argument-hint: "#[story issue number]"
---

# Update Story

Modify a story's detail — acceptance criteria, file scope, deps, or technical notes.

## Preflight

1. Read the story issue:
   ```bash
   gh issue view [number] --json number,title,body,labels
   ```
2. Read parent feature and epic for context.

## Steps

1. Identify what's changing based on user's request.

2. Update the story issue body on GitHub:
   ```bash
   gh issue edit [number] --body "[updated body]"
   ```

3. If dependencies changed:

   **Circular dependency check:**
   - Fetch the blocker chain for this story
   - Walk `Blocked by` links from each blocker
   - If the chain leads back to this story, STOP and report the cycle

   **Downstream updates:**
   - If this story now blocks a new issue, update that issue's `Blocked by` section:
     ```bash
     gh issue view [blocked_number] --json body
     gh issue edit [blocked_number] --body "[add this story to Blocked by]"
     ```
   - If a blocker was removed, check if the previously blocked issue is now unblocked

   **Status label update:**
   - If a new blocker was added and it's unmet → apply `status:blocked`
   - If a blocker was removed and all remaining blockers are met → apply `status:todo`
   - Blocker satisfaction criteria: satisfied if `status:done` label OR state is `CLOSED`

4. If this change was driven by a bug or decision:
   - Remind user to run `/update-prd` if the decision isn't recorded yet
   - Remind user to run `/update-pi` if the PI Plan is affected

5. Commit only if PI.md was changed:
   ```bash
   git add .claude/pi/PI.md
   git commit -m "docs(pi): update deps for story #[number]"
   ```
