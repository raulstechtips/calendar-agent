---
name: update-feature
description: Modify a feature — add/remove stories, change description, update dependencies. Use when a feature's scope changes mid-sprint.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
argument-hint: "#[feature issue number]"
---

# Update Feature

Modify a feature's scope, stories, or dependencies.

## Preflight

1. Read the feature issue:
   ```bash
   gh issue view [number] --json number,title,body,labels
   ```
2. List its child stories (parse the `## Stories` checklist):
   ```bash
   # For each story number found:
   gh issue view [story_number] --json number,title,body,labels
   ```
3. Read PI Plan and PRD for context.

## Steps

1. Identify what's changing:
   - **Adding stories**: new work discovered (bug, new requirement)
   - **Removing stories**: scope cut
   - **Dependency change**: feature now blocks/is blocked by something new
   - **Description/non-goals update**

2. Make the changes:

   **Adding a story:**
   - Create a stub story issue (same as `/create-feature` step 3)
   - Update the feature issue's Stories checklist
   - Check: does this new story block anything already in progress? Flag it.
   - Check: should any existing `status:todo` stories now depend on this new story?

   **Removing a story:**
   - Close the story issue with a comment
   - Update the feature issue's Stories checklist
   - Check: did any other story depend on the removed one? Update their deps.

   **Dependency change:**
   - Update the feature issue's Dependencies section
   - Re-evaluate: should any child stories have their status labels updated?
   - Apply `status:blocked` or `status:todo` as appropriate using shared blocker satisfaction criteria:
     - Satisfied if: issue has `status:done` label OR issue state is `CLOSED`
     - Unmet if: issue is `OPEN` without `status:done`

3. Update PI.md if the feature-level plan changed:
   ```bash
   git add .claude/pi/PI.md
   git commit -m "docs(pi): update feature #[number]"
   ```
