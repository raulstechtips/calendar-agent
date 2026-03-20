---
name: init
description: Bootstrap SDLC infrastructure — creates GitHub labels, artifact directories, and checks project setup. Run after creating a PRD.
allowed-tools: Read, Bash, Grep, Glob
argument-hint: "(no arguments)"
---

I'm using the sdlc:init skill to bootstrap SDLC infrastructure for this project.

**BOOTSTRAP, DON'T BUILD**

<HARD-GATE>
Do NOT define artifacts, brainstorm, or create issues. Only set up infrastructure. If the PRD doesn't exist, tell the user to run sdlc:define prd first.
</HARD-GATE>

## Process Flow

```dot
digraph init {
    rankdir=TB;
    "Check PRD exists" [shape=box];
    "PRD found?" [shape=diamond];
    "Stop — tell user to create PRD" [shape=box];
    "Read Label Taxonomy" [shape=box];
    "Create GitHub labels" [shape=box];
    "Ensure artifact directories" [shape=box];
    "Check CLAUDE.md" [shape=box];
    "Check plugins" [shape=box];
    "Report summary" [shape=box];

    "Check PRD exists" -> "PRD found?";
    "PRD found?" -> "Stop — tell user to create PRD" [label="no"];
    "PRD found?" -> "Read Label Taxonomy" [label="yes"];
    "Read Label Taxonomy" -> "Create GitHub labels";
    "Create GitHub labels" -> "Ensure artifact directories";
    "Ensure artifact directories" -> "Check CLAUDE.md";
    "Check CLAUDE.md" -> "Check plugins";
    "Check plugins" -> "Report summary";
}
```

---

## Step 1: Validate PRD Exists

```
Read .claude/sdlc/prd/PRD.md
```

If the file does not exist, report:

> "No PRD found at `.claude/sdlc/prd/PRD.md`. Run `sdlc:define prd` followed by `sdlc:create prd` first."

STOP. Do not proceed further.

---

## Step 2: Read Label Taxonomy

Parse the PRD for a `## Label Taxonomy` section. If found, extract the area label names from the table rows (each row has `| area:<name> | <description> |`).

If no Label Taxonomy section exists, announce:

> "PRD does not have a Label Taxonomy section. I'll create universal labels only. Consider running `sdlc:update prd` to add a Label Taxonomy section, then re-run `sdlc:init`."

Record: `AREA_LABELS` (list of area names, possibly empty).

---

## Step 3: Create GitHub Labels

Create all labels using `--force` for idempotency (creates if missing, updates color if exists).

```bash
# Type labels (blue)
gh label create "type:epic" --color "0075ca" --force
gh label create "type:feature" --color "0075ca" --force
gh label create "type:story" --color "0075ca" --force

# Status labels (green)
gh label create "status:todo" --color "0e8a16" --force
gh label create "status:in-progress" --color "0e8a16" --force
gh label create "status:done" --color "0e8a16" --force
gh label create "status:blocked" --color "0e8a16" --force

# Priority labels (red)
gh label create "priority:critical" --color "d93f0b" --force
gh label create "priority:high" --color "d93f0b" --force
gh label create "priority:medium" --color "d93f0b" --force
gh label create "priority:low" --color "d93f0b" --force

# Triage (yellow)
gh label create "triage" --color "fbca04" --force
```

Then for each area label from the PRD:

```bash
gh label create "area:<name>" --color "7057ff" --force
```

Track counts: how many labels were newly created vs already existed. The `--force` flag means existing labels are silently updated (color only), so count the total attempted.

---

## Step 4: Ensure Artifact Directories

```bash
mkdir -p .claude/sdlc/prd
mkdir -p .claude/sdlc/pi/completed
mkdir -p .claude/sdlc/drafts
mkdir -p .claude/sdlc/retros
```

Add `.gitkeep` files to any empty directories:

```bash
for dir in .claude/sdlc/prd .claude/sdlc/pi .claude/sdlc/pi/completed .claude/sdlc/drafts .claude/sdlc/retros; do
  if [ -z "$(ls -A $dir 2>/dev/null)" ]; then
    touch "$dir/.gitkeep"
  fi
done
```

---

## Step 5: Check CLAUDE.md

```bash
grep -l "sdlc:" CLAUDE.md 2>/dev/null || grep -l ".claude/sdlc/" CLAUDE.md 2>/dev/null
```

If neither pattern is found in CLAUDE.md, suggest:

> "Your CLAUDE.md doesn't reference the SDLC workflow yet. Consider running the `claude-md-management:claude-md-improver` skill to add SDLC conventions based on your PRD."

If found, report: "CLAUDE.md already references SDLC workflow."

---

## Step 6: Check Recommended Plugins

Check for key plugins. This is informational only — do not install anything.

Report which of the following are available:
- `superpowers` — workflow discipline (brainstorming, TDD, verification)
- `commit-commands` — conventional commit helpers

If any are missing, suggest: "Consider enabling [plugin] for [benefit]."

---

## Step 7: Report Summary

Present a summary:

```
## SDLC Init Complete

**Labels:**
- Universal: 12 labels (type, status, priority, triage)
- Project areas: N labels from PRD Label Taxonomy
- Total: N+12 labels ensured

**Directories:**
- .claude/sdlc/prd/ ✓
- .claude/sdlc/pi/ ✓
- .claude/sdlc/pi/completed/ ✓
- .claude/sdlc/drafts/ ✓
- .claude/sdlc/retros/ ✓

**CLAUDE.md:** [references SDLC | needs SDLC sections — see suggestion above]

**Plugins:** [all recommended present | missing: X — see suggestions above]

**Next step:** Run `sdlc:define pi` to plan your first increment.
```

---

## Execution Checklist

- [ ] Step 1: PRD existence verified
- [ ] Step 2: Label Taxonomy read (or noted as missing)
- [ ] Step 3: All GitHub labels created
- [ ] Step 4: Artifact directories confirmed
- [ ] Step 5: CLAUDE.md checked
- [ ] Step 6: Plugins checked
- [ ] Step 7: Summary reported
