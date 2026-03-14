# Human Workflow: Managing the 2-Day Sprint

Your role is **tech lead**, not individual contributor. You make decisions, review code, unblock agents, and merge work. The AI does the heavy lifting.

---

## Starting a Session

```bash
# 1. Check project state
git log --oneline -10
git worktree list
gh issue list -R raulstechtips/calendar-agent --label "status:in-progress"
gh issue list -R raulstechtips/calendar-agent --label "status:todo" --label "priority:critical"

# 2. Read the spec (always do this first)
cat .claude/specs/in-progress/SPEC.md

# 3. Pick 2-3 independent stories from the current phase
# Stories are independent if they touch DIFFERENT directories/files
```

---

## Launching Parallel Agents

### Option A: Separate terminals (simplest)

Open 3 terminal windows. In each:

```bash
# Terminal 1 — Frontend
claude --worktree frontend-work

# Terminal 2 — Backend
claude --worktree backend-work

# Terminal 3 — Agent/AI
claude --worktree agent-work
```

Then give each agent its task:

```text
Read the spec at .claude/specs/in-progress/SPEC.md, then work on issue #8.
Run `gh issue view 8` to read the full acceptance criteria.
Mark the issue in-progress: `gh issue edit 8 --add-label "status:in-progress" --remove-label "status:todo"`
When done, commit, update the issue label to `status:done`, and create a PR.
```

### Option B: tmux (monitor all at once)

```bash
# Create a 2x2 grid: 1 main pane + 3 agent panes
tmux new-session -d -s sprint
tmux split-window -h
tmux split-window -v -t 0
tmux split-window -v -t 1
tmux select-layout tiled
tmux attach -t sprint

# Navigate: Ctrl-b + arrow keys
# Zoom one pane: Ctrl-b + z
# Scroll history: Ctrl-b + [  (q to exit)
# Detach (agents keep running): Ctrl-b + d
# Re-attach: tmux attach -t sprint
```

### Option C: tmux with persistence

```bash
# Each agent in its own tmux session (survives terminal close)
claude --worktree frontend-work --tmux
claude --worktree backend-work --tmux
claude --worktree agent-work --tmux
```

---

## Your Loop (Every 10-15 Minutes)

```text
┌─────────────────────┐
│ Glance at all panes  │
│ Is anyone stuck?      │──── Yes ──→ Intervene (see below)
│ Anyone asking a Q?    │
└──────────┬───────────┘
           │ No
           ▼
┌─────────────────────┐
│ Anyone finished?      │──── Yes ──→ Review & Merge (see below)
└──────────┬───────────┘
           │ No
           ▼
    Continue waiting.
    Work on something else
    (update spec, plan next phase,
     review docs, test manually).
```

---

## When to Intervene

| Signal | Action |
|--------|--------|
| Agent loops on same error 3+ times | Press `Esc`, diagnose, give specific fix instruction |
| Agent modifies files outside its scope | Press `Esc`, tell it to revert and stay in scope |
| Agent asks a question | Answer it — you're the bottleneck |
| Agent invents new patterns | Redirect to existing patterns in CLAUDE.md |
| Agent installs unexpected deps | Press `Esc`, evaluate if the dep is needed |
| Context at ~60% | Tell agent to `/compact focus on [current task]` |

---

## Code Review (When an Agent Finishes)

### Quick review (in terminal)

```bash
# See what changed on the worktree branch
git diff main..worktree-frontend-work
git diff main..worktree-frontend-work --stat  # summary only
```

### Deep review (use a fresh Claude session — unbiased)

```bash
# In your main pane or a new terminal
claude -p "Review the changes on branch worktree-frontend-work vs main. Check for: security issues, spec compliance, test coverage, file scope violations. Be critical."
```

### What to look for

1. **Does it match the acceptance criteria?** (check the issue)
2. **Tests exist and pass?**
3. **Lint/typecheck pass?**
4. **No files modified outside the story's scope?**
5. **No hardcoded secrets, debug code, or unnecessary deps?**
6. **Interfaces match what other worktrees will expect?** (API contracts, types)

---

## Merging Worktree Work

```bash
# 1. Make sure you're on main
git checkout main

# 2. Merge the worktree branch
git merge worktree-frontend-work

# 3. If conflicts: resolve, git add, git commit
# For complex conflicts, ask Claude:
# claude -p "Resolve merge conflicts in path/to/file.ts"

# 4. Run tests to verify the merge
cd frontend && pnpm test && pnpm typecheck
cd backend && uv run pytest

# 5. Update the GitHub issue
gh issue edit 8 --add-label "status:done" --remove-label "status:in-progress"
# Issue closes automatically when the PR is merged

# 6. Clean up the worktree
git worktree remove .claude/worktrees/frontend-work
git branch -d worktree-frontend-work

# 7. Push to remote
git push origin main
```

**Merge order**: Backend first (provides interfaces), then Agent (depends on backend), then Frontend (depends on both).

**Merge frequency**: After each story, not in batch. Keeps conflicts small.

---

## Decisions You Make vs. Delegate

### You decide

- Architecture changes (new patterns, different libraries)
- Task decomposition (what's parallel, what's sequential)
- Merge order and conflict resolution
- UX/product decisions (what the user sees)
- What to cut when behind schedule
- Whether a story is "done" (acceptance criteria met)

### AI decides

- Implementation details within a scoped story
- Test writing and debugging test failures
- Code style (enforced via CLAUDE.md + linters)
- Commit messages
- Boilerplate patterns

### When to use `/update-decision`

When you make a decision that changes the spec (e.g., "let's use X instead of Y"), tell Claude:

```text
/update-decision We're switching from Auth.js to better-auth because [reason]
```

This updates SPEC.md (source of truth) and affected GitHub issues automatically.

---

## End of Session Checklist

```bash
# 1. Check all worktrees
git worktree list

# 2. Merge any completed work
git checkout main && git merge <branch>

# 3. Commit any uncommitted changes
git status

# 4. Push to remote
git push origin main

# 5. Update issues
gh issue list -R raulstechtips/calendar-agent --label "status:in-progress"
# Verify completed ones have `status:done` label — issues close automatically when PRs merge

# 6. Document progress (optional but recommended between days)
# Have Claude write a progress summary:
# "Write current progress to .claude/specs/in-progress/PROGRESS.md"

# 7. Clean up worktrees
git worktree prune
```

---

## Day 1 → Day 2 Handoff

Before closing Day 1:
1. Merge all completed work to main
2. Push to remote
3. Have Claude write progress to a file: "Summarize what's done, what's in progress, and what's blocked to `.claude/specs/in-progress/PROGRESS.md`"

Starting Day 2:
1. `git pull origin main`
2. Read SPEC.md and PROGRESS.md
3. Check issues: `gh issue list --label "status:todo" --label "sprint:day2"`
4. Launch new worktrees for Day 2 phase

---

## Quick Reference: Key Commands

| Task | Command |
|------|---------|
| Launch agent in worktree | `claude --worktree <name>` |
| Launch with tmux persistence | `claude --worktree <name> --tmux` |
| Check worktrees | `git worktree list` |
| Diff a worktree branch | `git diff main..worktree-<name>` |
| Merge worktree | `git checkout main && git merge worktree-<name>` |
| Clean up worktree | `git worktree remove .claude/worktrees/<name>` |
| Check issue status | `gh issue list --label "status:in-progress"` |
| Update issue (done) | `gh issue edit <n> --add-label "status:done" --remove-label "status:in-progress"` (issue auto-closes on PR merge) |
| Compact context | `/compact focus on [current task]` |
| Clear and restart | `/clear` |
| Resume last session | `claude --continue` |
| Check sprint progress | `/sync-issues` |
| Pick next task | `/pick-task [area]` |
| Record a decision | `/update-decision [description]` |
