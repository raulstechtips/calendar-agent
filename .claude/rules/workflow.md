---
description: Development workflow for every story/task
---

# Agent Development Workflow

Follow this exact process for every story/task:

## Step-by-step

1. **Read the issue**: `gh issue view <number>` — understand acceptance criteria before writing code
2. **Read the spec**: `.claude/specs/in-progress/SPEC.md` — understand architecture context
3. **Explore existing code**: search for existing patterns to follow before writing anything new
4. **Plan thoroughly**: list files to create/modify, patterns to follow, and review the SPEC's Security Constraints section — for each constraint that applies to this story, note how the implementation will satisfy it
5. **Write failing tests first** (Red phase) — see tdd.md
6. **Implement minimum code to pass tests** (Green phase)
7. **Refactor** while tests stay green
8. **Verify**: run the full verification suite for your area
9. **Internal code review**: launch the `code-reviewer` agent as a subagent to review all changes on the current branch. Address any CRITICAL findings before proceeding — WARNING and SUGGESTION items are at your discretion but should be considered.
10. **Commit**: conventional commit referencing the issue number
11. **Update issue and open PR**:
    ```bash
    gh issue edit <n> --add-label "status:done" --remove-label "status:in-progress"
    ```
    Then create a PR referencing the issue (`Closes #<n>` in the PR body). The issue closes automatically when the PR is merged.

## When to ask the human

- Task description is ambiguous about BEHAVIOR (not just implementation details)
- Multiple architecturally different approaches exist
- Change would affect files OUTSIDE the story's file scope
- An existing test needs modification
- A dependency not in the spec needs to be added
- Credentials or environment config is needed

## When to decide autonomously

- Implementation approach is clear from spec + existing patterns
- Choosing between equivalent minor details
- Fixing lint/type errors from the current change
- Adding error handling at boundaries
- Writing test assertions for documented behavior

## Error handling during development

- Maximum 3 attempts to fix a failing test, then ask the human
- NEVER modify or delete a failing test — fix the implementation
- NEVER suppress errors (`try/except pass`, `@ts-ignore`, `# noqa`) to make tests pass
- If a test fails for reasons outside the story's scope, report it and move on
