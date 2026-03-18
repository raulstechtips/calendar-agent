---
name: detail-story
description: Add full detail to a stub story issue — acceptance criteria, file scope, technical notes, and verified dependencies. Takes a story issue number and enriches it with implementation-ready detail.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
argument-hint: "#[story issue number]"
---

# Detail Story

Take a stub story issue and add full implementation detail.

## Preflight

1. Read the story issue:
   ```bash
   gh issue view [number] --json number,title,body,labels
   ```
2. Extract parent epic and feature numbers from the `## Parent` section.
3. Read the parent feature and epic for context:
   ```bash
   gh issue view [feature_number] --json number,title,body
   gh issue view [epic_number] --json number,title,body
   ```
4. Read the PRD — focus on sections relevant to this story:
   ```bash
   cat .claude/prd/PRD.md
   ```
   Pay special attention to:
   - **Security Constraints** — which apply to this story?
   - **Data Models** — which models does this story touch?
   - **API Contracts** — which endpoints does this story implement or consume?

## Steps

### 1. Collaborate on Story Detail

Work with the user to define:

- **Description**: What needs to be built and why (2-3 sentences)
- **Acceptance Criteria**: Testable checkboxes — each criterion should be verifiable by a test or manual check. Aim for 3-7 criteria.
- **File Scope**:
  - New files to create (exact paths)
  - Existing files to modify (exact paths)
- **Technical Notes**: Implementation guidance — patterns to follow, edge cases, relevant existing code to reference
- **Dependencies**: Verify and finalize `Blocked by` and `Blocks` lists

### 2. Verify Dependency Integrity

**Blocker satisfaction check** — for each issue in `Blocked by`:
```bash
gh issue view [dep_number] --json state,labels \
  --jq '{state: .state, done: ([.labels[].name] | contains(["status:done"]))}'
```
Satisfied if: `status:done` label OR state is `CLOSED`.

**Circular dependency check** — if this story has new blockers:
1. Fetch all open issues this story is connected to (its blockers, and issues that list this story as a blocker)
2. Walk the blocker chain: if following `Blocked by` links leads back to this story, there's a cycle
3. If cycle detected: report it and do NOT save the dependency. Ask the user to resolve.

**Cross-issue updates** — if this story now blocks an issue that doesn't list it in `Blocked by`:
```bash
gh issue view [blocked_number] --json body
gh issue edit [blocked_number] --body "[updated body]"
```

### 3. Update Story Issue on GitHub

```bash
gh issue edit [number] --body "$(cat <<'BODY'
## Description
[from discussion]

## Acceptance Criteria
- [ ] [criterion 1]
- [ ] [criterion 2]
- [ ] [criterion 3]

## File Scope
**New files:**
- [path/to/new/file]

**Modified files:**
- [path/to/existing/file]

## Technical Notes
[from discussion]

## Dependencies
- Blocked by: #X, #Y
- Blocks: #Z

## Parent
- Epic: #[epic_number]
- Feature: #[feature_number]
BODY
)"
```

### 4. Apply Correct Status Label

If any blocker is unmet:
```bash
gh issue edit [number] --add-label "status:blocked" --remove-label "status:todo"
```

If all blockers are met (or no blockers):
```bash
gh issue edit [number] --add-label "status:todo" --remove-label "status:blocked"
```

### 5. Update PI.md if Needed

If the dependency graph in PI.md needs updating (e.g., a new cross-epic dependency was discovered):
```bash
git add .claude/pi/PI.md
git commit -m "docs(pi): update deps for story #[number]"
```
