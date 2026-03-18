---
name: update-epic
description: Modify an epic's scope — add/remove features, change description, update dependencies. Use when an epic needs restructuring mid-sprint.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
argument-hint: "#[epic issue number]"
---

# Update Epic

Modify an epic's scope, features, or dependencies.

## Preflight

1. Read the epic issue:
   ```bash
   gh issue view [number] --json number,title,body,labels
   ```
2. List its child features (parse the `## Features` checklist from the body for issue numbers):
   ```bash
   # For each feature number found in the epic body:
   gh issue view [feature_number] --json number,title,body,labels
   ```
3. Read PI Plan:
   ```bash
   cat .claude/pi/PI.md
   ```

## Steps

1. Identify what's changing based on the user's request:
   - **Adding features**: new capability needed under this epic
   - **Removing features**: scope cut or moved to another epic
   - **Splitting epic**: this epic is too large, should become two
   - **Dependency change**: blocking relationships shifted
   - **Description update**: success criteria or overview changed

2. Make the changes:

   **Adding a feature:**
   - Create a stub feature issue (same as `/create-epic` step 3)
   - Update the epic issue's Features checklist to include it
   - Update PI.md to add the feature under this epic

   **Removing a feature:**
   - Close the feature issue with a comment explaining why
   - Close any child story issues
   - Update the epic issue's Features checklist
   - Update PI.md

   **Splitting an epic:**
   - Create a new epic issue for the split portion
   - Move relevant features to the new epic (update their Parent section)
   - Update PI.md with the new epic and redistributed features
   - Update the dependency graph

   **Dependency change:**
   - Update the epic issue's Dependencies section
   - Check downstream: do any features/stories need their deps updated?
   - Update PI.md dependency graph

3. Flag downstream impacts:
   - List features/stories that may need updating
   - Suggest running `/update-feature` or `/update-story` for affected issues

4. Commit:
   ```bash
   git add .claude/pi/PI.md
   git commit -m "docs(pi): update epic #[number] scope"
   ```
