---
name: update-pi
description: Update the PI Plan when reality diverges mid-sprint — epic splits, feature moves, dependency changes, scope adjustments. Use when the plan needs to change.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
argument-hint: "[description of what changed]"
---

# Update PI

Update the PI Plan when scope, dependencies, or structure changes mid-sprint.

## Preflight

1. Read current PI Plan:
   ```bash
   cat .claude/pi/PI.md
   ```
   If no active PI exists, STOP — suggest `/plan-increment` first.

2. Read PRD for context:
   ```bash
   cat .claude/prd/PRD.md
   ```

## Steps

1. Based on the user's description, identify what changed:
   - **Epic split**: one epic becoming two or more
   - **Feature moved**: feature moving between epics
   - **Story added/removed**: new work discovered or scope cut
   - **Dependency change**: blocking relationships shifted
   - **Worktree reassignment**: parallel strategy needs adjusting

2. Update the relevant section of PI.md:
   - If epic split: create new epic section, redistribute features, update issue numbers
   - If feature moved: move the feature line, update parent epic references
   - If dependency graph changed: update the `## Dependency Graph` section
   - If worktree strategy affected: update `## Worktree Strategy`

3. If dependency graph changed, re-evaluate worktree strategy:
   - Can the same worktrees still run in parallel?
   - Does a new sequential dependency exist?

4. Check PRD decision log consistency:
   - If this PI change was driven by a decision, verify it's logged in the PRD
   - If not, remind user to run `/update-prd` to record the decision

5. If GitHub Issues need updating (e.g., parent links changed, new stubs needed):
   - Suggest the appropriate skill: `/update-epic`, `/update-feature`, `/create-epic`, etc.
   - Do NOT auto-update GitHub Issues from this skill — that's the work skills' job

## Commit

```bash
git add .claude/pi/PI.md
git commit -m "docs(pi): [concise description of the change]"
```
