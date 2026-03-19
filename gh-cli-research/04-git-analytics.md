# Git Analytics Commands for SDLC Skills

Reference document for all git commands needed by `sdlc:status` and `sdlc:retro` skills.
Tested against the calendar-agent repository (66 commits on main, ~249 across all branches).

---

## Table of Contents

1. [Commits per Issue](#1-commits-per-issue)
2. [Commit Cadence](#2-commit-cadence)
3. [File Change Hotspots](#3-file-change-hotspots)
4. [Recent Activity per Issue](#4-recent-activity-per-issue)
5. [Branch Activity](#5-branch-activity)
6. [Conventional Commit Parsing](#6-conventional-commit-parsing)
7. [PR Merge History](#7-pr-merge-history)
8. [Tag-Based Sprint Boundaries](#8-tag-based-sprint-boundaries)
9. [Author Statistics](#9-author-statistics)
10. [Diff Statistics](#10-diff-statistics)

---

## 1. Commits per Issue

**Used by:** `sdlc:status`, `sdlc:retro`

### The Problem: `#9` vs `#90` vs `#9)` Matching

Matching `#9` must not match `#90`, `#93`, `#98`, etc. This is the hardest edge case.

### Recommended: Perl-regexp with `\b` (word boundary)

```bash
git log --all --perl-regexp --grep='\#100\b' --format='%h %aI %s'
```

**Example output (issue #100):**
```
a0ddc66 2026-03-17T15:47:18-04:00 fix(api): user-based rate limiter and bounded refresh locks (#100) (#108)
```

**Why `\b` works for most cases:** The `\b` word boundary matches between a digit and a non-word character (like `)`, space, or end-of-string). For our conventional commit format `(#100)`, the boundary sits between `0` and `)`.

### Caveat: `\b` false positives with single-digit issues

For `#9`, `\b` will match `#9` inside `(#98)` because the boundary is between `#` and `9` at the start of `98`. Testing confirmed this:

```bash
git log --all --perl-regexp --grep='\#9\b' --format='%h %s'
```

Returns false positives like `feat(infra): add GitHub Actions CI/CD pipeline (#28) (#98)` because `#9` matches at position 0 of `#98` with the word boundary between `#` and `9`.

### Best approach for exact matching: Parenthesized form

Since our convention wraps issue numbers in `(#N)`, the most reliable approach is:

```bash
# Strategy A: Match the full parenthesized pattern (no false positives)
git log --all --extended-regexp --grep='\(#9\)' --format='%h %aI %s'

# Strategy B: Perl lookaround for non-parenthesized contexts
git log --all --perl-regexp --grep='(?<![0-9])#9(?![0-9])' --format='%h %aI %s'
```

**Strategy A** is simpler and matches our convention exactly. It handles `(#9)` without matching `(#90)` or `(#98)`.

**Strategy B** uses negative lookahead/lookbehind to ensure no digit precedes or follows the issue number. Requires git compiled with PCRE (`--perl-regexp`).

### Recommendation for the skill implementation

Use a **two-pass approach**:

```bash
# Pass 1: Fast grep with \b (works perfectly for multi-digit issues)
git log --all --perl-regexp --grep='\#100\b' --format='%h %aI %s'

# Pass 2: For single/double-digit issues, use parenthesized form
git log --all --extended-regexp --grep='\(#9\)' --format='%h %aI %s'
```

Or simply always use the parenthesized form since our convention requires `(#N)`:

```bash
ISSUE_NUM=9
git log --all --fixed-strings --grep="(#${ISSUE_NUM})" --format='%h %aI %s'
```

**`--fixed-strings`** treats the pattern literally, so `(#9)` matches only that exact string. No regex needed, no escaping needed. This is the safest and fastest approach.

### Count commits per issue

```bash
ISSUE_NUM=100
git log --all --fixed-strings --grep="(#${ISSUE_NUM})" --format='%h' | wc -l
```

### Performance considerations

- `--all` searches all branches; omit for main-only queries
- `--fixed-strings` is faster than regex; use it when the pattern has no wildcards
- For repos with 10K+ commits, add `--since` to bound the search window

---

## 2. Commit Cadence

**Used by:** `sdlc:retro`

### Commits per day

```bash
git log --format='%ad' --date=format:'%Y-%m-%d' | sort | uniq -c | sort -rn
```

**Example output:**
```
  19 2026-03-14
  16 2026-03-15
  15 2026-03-16
  14 2026-03-17
   2 2026-03-18
```

**Parsing:** Leading whitespace + count + space + date. Split on first non-space.

### Commits per ISO week

```bash
git log --format='%ad' --date=format:'%Y-W%V' | sort | uniq -c
```

**Example output:**
```
  35 2026-W11
  31 2026-W12
```

### Commits per day within a date range

```bash
git log --since='2026-03-16' --until='2026-03-18' --format='%ad' --date=format:'%Y-%m-%d' | sort | uniq -c
```

### Commits per hour of day (work pattern analysis)

```bash
git log --format='%ad' --date=format:'%H' | sort -n | uniq -c
```

**Example output:**
```
   7 00
   2 01
   1 02
   4 10
   3 11
   6 17
   6 18
   6 21
```

### Total commit count in a date range

```bash
git rev-list --count --since='2026-03-14' HEAD
```

**Example output:** `57`

### Commits per author per day

```bash
git log --format='%ad %aN' --date=format:'%Y-%m-%d' | sort | uniq -c | sort -rn
```

**Example output:**
```
  19 2026-03-14 Raul Chakraborty
  15 2026-03-16 Raul Chakraborty
  14 2026-03-15 Raul Chakraborty
  13 2026-03-17 Raul Chakraborty
   2 2026-03-15 chakraborty29
```

### Parsing strategy

All `uniq -c` output follows the same format: `<spaces><count><space><value>`. Parse with:

```python
# Python
for line in output.strip().split('\n'):
    count, value = line.strip().split(None, 1)
    # count is str, convert to int
```

### Performance considerations

- `--format` with `--date` is O(n) on commit count; fast for repos under 50K commits
- Adding `--since`/`--until` bounds the walk and speeds up large repos significantly
- `sort | uniq -c` is linear on output size, negligible overhead

---

## 3. File Change Hotspots

**Used by:** `sdlc:retro`

### Most frequently changed files (by commit count)

```bash
git log --all --name-only --format='' | sort | uniq -c | sort -rn | head -20
```

**Example output:**
```
  29 backend/app/main.py
  27 backend/app/agents/router.py
  23 backend/tests/test_agent.py
  22 .claude/specs/in-progress/SPEC.md
  21 backend/pyproject.toml
  17 infra/environments/dev/main.tf
  17 CLAUDE.md
  16 backend/app/core/config.py
  15 backend/tests/test_scaffold.py
  15 backend/tests/test_calendar_tools.py
  15 backend/app/agents/tools/calendar_tools.py
  14 frontend/auth.ts
```

**Parsing:** Same `uniq -c` format. Blank lines in output should be filtered (empty format lines between commits).

### Most frequently changed files in a date range

```bash
git log --since='2026-03-17' --name-only --format='' | sort | uniq -c | sort -rn | head -20
```

### Most frequently changed files scoped to a directory

```bash
git log --all --name-only --format='' -- backend/ | sort | uniq -c | sort -rn | head -15
```

### File churn (total lines added + deleted)

```bash
git log --numstat --format='' | awk 'NF==3 {files[$3]+=$1+$2} END {for(f in files) print files[f],f}' | sort -rn | head -20
```

**Note:** Binary files show `-` for add/delete counts; the `NF==3` guard in awk handles this by only processing lines with exactly 3 fields (but `-` will cause awk arithmetic to treat it as 0, which is acceptable).

### Churn for a specific file

```bash
git log --numstat --format='' -- backend/app/main.py
```

**Example output:**
```
3	5	backend/app/main.py
13	10	backend/app/main.py
13	2	backend/app/main.py
5	0	backend/app/main.py
```

Each line is: `<additions>\t<deletions>\t<filename>`.

### New files added in a period

```bash
git log --diff-filter=A --name-only --format='' --since='2026-03-17'
```

**Example output:**
```
docs/ARCHITECTURE.md
frontend/DESIGN.md
frontend/e2e/screenshots.spec.mts
backend/app/core/startup.py
backend/scripts/entrypoint.sh
.github/workflows/cd.yml
.github/workflows/ci.yml
```

### Files deleted in a period

```bash
git log --diff-filter=D --name-only --format='' --since='2026-03-17'
```

### Diff filters

| Filter | Meaning |
|--------|---------|
| `A` | Added |
| `D` | Deleted |
| `M` | Modified |
| `R` | Renamed |
| `C` | Copied |

### Performance considerations

- `--name-only --format=''` is much lighter than `--stat` or `--numstat` for counting
- The `sort | uniq -c | sort -rn` pipeline is efficient; the sort is the bottleneck
- For large repos, always add `--since` to bound the commit walk
- `-- <path>` pathspec filtering happens at the git level, not in shell, so it is fast

---

## 4. Recent Activity per Issue

**Used by:** `sdlc:status` (stale detection)

### Most recent commit for an issue

```bash
git log --all --fixed-strings --grep="(#98)" --format='%h %aI %s' -1
```

**Example output:**
```
9e39188 2026-03-17T18:07:47-04:00 feat(infra): add GitHub Actions CI/CD pipeline (#28) (#98)
```

The `-1` flag returns only the most recent match. The ISO 8601 date (`%aI`) is directly parseable.

### All commits for an issue, newest first

```bash
git log --all --fixed-strings --grep="(#100)" --format='%h %aI %s'
```

**Example output:**
```
a0ddc66 2026-03-17T15:47:18-04:00 fix(api): user-based rate limiter and bounded refresh locks (#100) (#108)
```

### Stale detection logic

```python
from datetime import datetime, timedelta, timezone

# Parse the ISO date from the most recent commit
last_commit_date = datetime.fromisoformat("2026-03-17T18:07:47-04:00")
now = datetime.now(timezone.utc)
days_since = (now - last_commit_date).days

if days_since > 3:
    status = "stale"
elif days_since > 1:
    status = "cooling"
else:
    status = "active"
```

### Finding issues with no recent activity

Combine with the full issue list from `gh issue list` and check which issues have no git log match in the last N days:

```bash
# For each open issue, check last commit date
for ISSUE in 100 98 95; do
    LAST=$(git log --all --fixed-strings --grep="(#${ISSUE})" --format='%aI' -1)
    echo "${ISSUE} ${LAST:-NEVER}"
done
```

### Performance considerations

- `-1` with `--grep` is fast: git stops walking after the first match
- For bulk stale detection, running one git log per issue is acceptable for < 200 issues
- For 200+ issues, consider a single `git log` dump and parsing in Python

---

## 5. Branch Activity

**Used by:** `sdlc:status`

### All branches sorted by last commit date

```bash
git branch -a --sort=-committerdate --format='%(refname:short) %(committerdate:short) %(subject)'
```

**Example output:**
```
chore/add-architechture-docs 2026-03-18 chore(docs): added architecture docs
fix/infra-frontend-env-vars 2026-03-18 fix(infra): add AUTH_URL, use INTERNAL_API_URL
main 2026-03-18 chore(deps): bump backend to 0.1.5 and frontend to 0.1.2 (#120)
chore/sdlc-skill-suite 2026-03-17 docs: add SDLC skill suite usage guide
chore/bump-versions 2026-03-17 chore(deps): bump backend to 0.1.5 and frontend to 0.1.2
chore/104-code-quality-fixes 2026-03-17 chore(deps): pin all dependency versions
```

### Structured branch listing with pipe separator (easier to parse)

```bash
git branch -a --sort=-committerdate --format='%(refname:short)|%(committerdate:iso8601)|%(subject)'
```

**Parsing:** Split on `|` for structured fields.

### Map branches to issues

Branch naming convention is `<type>/<issue-number>-<description>`. Extract with:

```bash
git branch --format='%(refname:short)' | grep -oE '^[a-z]+/[0-9]+'
```

Or parse in Python:

```python
import re
pattern = re.compile(r'^(?:feat|fix|chore|refactor|test|docs|ci|perf)/(\d+)')
for branch in branches:
    m = pattern.match(branch)
    if m:
        issue_number = int(m.group(1))
```

### Local branches only (exclude remote tracking)

```bash
git branch --sort=-committerdate --format='%(refname:short) %(committerdate:short) %(subject)'
```

### Branches not merged to main

```bash
git branch --no-merged main --format='%(refname:short) %(committerdate:short)'
```

### Performance considerations

- Branch listing is O(n) on branch count, always fast (typically < 100 branches)
- `--sort=-committerdate` is efficient; git sorts in memory after collecting
- No commit walk needed; branch tip metadata is sufficient

---

## 6. Conventional Commit Parsing

**Used by:** `sdlc:status`, `sdlc:retro`

### Extract commit type, scope, description, and issue number

The format is: `<type>(<scope>): <description> (#<issue>)`

### Filter by commit type

```bash
# Features only
git log --perl-regexp --grep='^feat\(' --format='%h %ad %s' --date=short

# Fixes only
git log --perl-regexp --grep='^fix\(' --format='%h %ad %s' --date=short

# All conventional commits with scope
git log --perl-regexp --grep='^(feat|fix|refactor|chore|test|docs|ci|perf)\(' --format='%h %ad %s' --date=short
```

**Example output (features):**
```
953c44e 2026-03-17 feat(ui): redesign with deeper colors, shadow depth, loading feedback
9e39188 2026-03-17 feat(infra): add GitHub Actions CI/CD pipeline (#28) (#98)
260b588 2026-03-17 feat(ui): add confirmation card for human-in-the-loop calendar writes (#106)
7a4d678 2026-03-16 feat(infra): add Container Apps module with VNet-integrated environment (#90)
```

### Count commits by type

```bash
git log --format='%s' | grep -oE '^[a-z]+' | sort | uniq -c | sort -rn
```

**Example output:**
```
  34 feat
  13 fix
   8 docs
   7 chore
   2 refactor
   1 test
```

### Count commits by scope

```bash
git log --format='%s' | grep -o '([a-z-]*)' | sort | uniq -c | sort -rn
```

**Example output:**
```
  14 (infra)
  11 (api)
   9 (ui)
   8 (auth)
   5 (spec)
   5 (agent)
   4 (search)
   2 (docs)
   2 (agents)
   1 (rules)
   1 (deps)
```

### Parse conventional commits in Python

```python
import re

CONVENTIONAL_RE = re.compile(
    r'^(?P<type>feat|fix|refactor|chore|test|docs|ci|perf)'
    r'\((?P<scope>[a-z-]+)\): '
    r'(?P<description>.+?)'
    r'(?:\s+\(#(?P<issue>\d+)\))?'
    r'(?:\s+\(#(?P<pr>\d+)\))?$'
)

def parse_commit(subject: str) -> dict | None:
    m = CONVENTIONAL_RE.match(subject)
    if not m:
        return None
    return m.groupdict()

# Example:
parse_commit("feat(auth): add Google OAuth (#9) (#57)")
# {'type': 'feat', 'scope': 'auth', 'description': 'add Google OAuth',
#  'issue': '9', 'pr': '57'}
```

### Extract all issue references from a commit message

Some commits reference multiple issues: `refactor(agents): deprecation fix (#104) (#115)`.

```python
import re

def extract_issues(subject: str) -> list[int]:
    return [int(m) for m in re.findall(r'#(\d+)', subject)]

# Example:
extract_issues("refactor(agents): deprecation fix (#104) (#115)")
# [104, 115]
```

### Structured log output for programmatic parsing

```bash
git log --format='COMMIT:%h|%aI|%aN|%s' --since='2026-03-17'
```

**Example output:**
```
COMMIT:560606b|2026-03-18T05:08:36-04:00|chakraborty29|chore(docs): added architecture docs
COMMIT:cd3879d|2026-03-18T00:03:17-04:00|Raul Chakraborty|chore(deps): bump backend to 0.1.5 (#120)
COMMIT:953c44e|2026-03-17T23:27:20-04:00|Raul Chakraborty|feat(ui): redesign (#119)
```

**Parsing:** Split on `|` after stripping the `COMMIT:` prefix.

### NUL-delimited output (safest for parsing)

```bash
git log --format='%h%x00%aI%x00%aN%x00%s%x00' -z
```

Use `%x00` (NUL byte) as field separator and `-z` for NUL record terminators. This handles author names with `|` in them safely.

### Performance considerations

- `--perl-regexp` requires git compiled with PCRE; check with `git log --perl-regexp --grep='.' -1 2>&1`
- Falls back to `--extended-regexp` if PCRE unavailable; most patterns work with both
- `grep -o` on formatted output is faster than repeated git log calls for aggregate stats

---

## 7. PR Merge History

**Used by:** `sdlc:retro` (sprint velocity)

### Squash-merge commits on main (first-parent)

This repo uses squash merges, so each main commit corresponds to one PR:

```bash
git log --oneline --first-parent main
```

**Example output:**
```
cd3879d chore(deps): bump backend to 0.1.5 and frontend to 0.1.2 (#120)
953c44e feat(ui): redesign with deeper colors, shadow depth, loading feedback (#119)
2f1d279 fix(api): retry create_index on startup for managed identity sidecar (#114)
21c455c refactor(agents): deprecation fix, redundant Redis call (#104) (#115)
517f00c fix(infra): add health probes to prevent SIGTERM restart loop (#112)
```

### Squash merges with dates (for velocity tracking)

```bash
git log --first-parent main --format='%h %ad %s' --date=short
```

**Example output:**
```
cd3879d 2026-03-18 chore(deps): bump backend to 0.1.5 and frontend to 0.1.2 (#120)
953c44e 2026-03-17 feat(ui): redesign with deeper colors (#119)
2f1d279 2026-03-17 fix(api): retry create_index on startup (#114)
```

### PRs merged per day

```bash
git log --first-parent main --format='%ad' --date=format:'%Y-%m-%d' | sort | uniq -c | sort -rn
```

### Count merges in a date range

```bash
git rev-list --count --first-parent --since='2026-03-17' main
```

### True merge commits (if using merge commits instead of squash)

```bash
git log --merges --oneline --format='%h %ad %s' --date=short
```

**Note:** This repo uses squash merges, so `--merges` returns nothing. Use `--first-parent` instead.

### Structured format with file stats

```bash
git log --first-parent main --format='%h %aI %s' --shortstat
```

**Example output:**
```
560606b 2026-03-18T05:08:36-04:00 chore(docs): added architecture docs

 2 files changed, 896 insertions(+), 1 deletion(-)
cd3879d 2026-03-18T00:03:17-04:00 chore(deps): bump backend to 0.1.5 (#120)

 2 files changed, 2 insertions(+), 2 deletions(-)
```

**Parsing note:** `--shortstat` adds a blank line and the stat line after each commit. Handle the multi-line output by reading commit/stat pairs.

### Performance considerations

- `--first-parent` is efficient; it only walks the main branch spine
- For repos with > 10K commits on main, `--since` is essential
- `--shortstat` adds a stat computation per commit; slower than `--oneline` but still fast for < 5K commits

---

## 8. Tag-Based Sprint Boundaries

**Used by:** `sdlc:retro`

### List all tags with dates

```bash
git tag -l --sort=-creatordate --format='%(refname:short) %(creatordate:short) %(subject)'
```

### Commits between two tags

```bash
git log --oneline tag1..tag2
```

### Commit count between tags

```bash
git rev-list --count tag1..tag2
```

### Diff stats between tags

```bash
git diff --stat tag1..tag2
```

### If using sprint tags (e.g., `sprint-1-start`, `sprint-1-end`)

```bash
# All commits in sprint 1
git log --oneline sprint-1-start..sprint-1-end

# Stats for the sprint
git diff --shortstat sprint-1-start..sprint-1-end

# Files changed in the sprint
git diff --name-only sprint-1-start..sprint-1-end
```

### If tagging with milestones (e.g., `pi-1-complete`)

```bash
# Commits since last milestone to HEAD
git log --oneline pi-1-complete..HEAD

# Count
git rev-list --count pi-1-complete..HEAD
```

### Creating sprint tags

```bash
# Tag the current commit as sprint boundary
git tag sprint-1-end
git tag -a sprint-1-end -m "Sprint 1 complete: auth + calendar tools"

# Tag a historical commit
git tag sprint-1-start <commit-hash>
```

### Current state of this repo

```
No tags exist yet. Sprint boundaries would need to be added.
```

### Using date ranges as alternative to tags

When tags are unavailable, use `--since`/`--until` as sprint boundaries:

```bash
# Sprint dates as pseudo-boundaries
git log --oneline --since='2026-03-14' --until='2026-03-17'
```

### Performance considerations

- Tag-based range queries (`tag1..tag2`) are fast; git resolves the range endpoints in O(1) and walks only the included commits
- `git diff --stat tag1..tag2` computes a single diff between two trees, very fast
- Tags are free metadata; recommend tagging sprint boundaries for clean retrospectives

---

## 9. Author Statistics

**Used by:** `sdlc:retro`

### Commit count per author (all time)

```bash
git shortlog -sn HEAD
```

**Example output:**
```
    62	Raul Chakraborty
     4	chakraborty29
```

### Commit count per author (all branches)

```bash
git shortlog -sn --all
```

**Example output:**
```
   174	chakraborty29
    75	Raul Chakraborty
```

**Note:** Branch commits are counted separately, so totals across branches will be higher than main-only.

### Author commits in a date range

```bash
git log --since='2026-03-17' --format='%aN' | sort | uniq -c | sort -rn
```

### Author with email (de-duplication)

```bash
git shortlog -sne HEAD
```

Useful for detecting the same person with different git configs (e.g., `Raul Chakraborty` vs `chakraborty29`).

### Author contribution per day

```bash
git log --format='%ad %aN' --date=format:'%Y-%m-%d' | sort | uniq -c | sort -rn
```

**Example output:**
```
  19 2026-03-14 Raul Chakraborty
  15 2026-03-16 Raul Chakraborty
  14 2026-03-15 Raul Chakraborty
  13 2026-03-17 Raul Chakraborty
   2 2026-03-15 chakraborty29
   1 2026-03-18 Raul Chakraborty
   1 2026-03-18 chakraborty29
   1 2026-03-17 chakraborty29
```

### Author contribution by scope (type of work)

Combine with conventional commit parsing:

```bash
git log --format='%aN|%s' | grep -o '[^|]*|[a-z]*([a-z-]*)' | sort | uniq -c | sort -rn
```

### .mailmap for author normalization

Create a `.mailmap` file to merge author identities:

```
Raul Chakraborty <raul@example.com> chakraborty29 <chakraborty29@users.noreply.github.com>
```

After creating `.mailmap`, all git commands automatically normalize author names.

### Performance considerations

- `git shortlog` is the most efficient way to aggregate by author
- For date-range queries, `git log --format` + sort/uniq is efficient
- `.mailmap` normalization is free and applies automatically

---

## 10. Diff Statistics

**Used by:** `sdlc:retro`

### Lines added/removed per commit (shortstat)

```bash
git log --shortstat --oneline -5
```

**Example output:**
```
560606b chore(docs): added architecture docs
 2 files changed, 896 insertions(+), 1 deletion(-)
cd3879d chore(deps): bump backend to 0.1.5 and frontend to 0.1.2 (#120)
 2 files changed, 2 insertions(+), 2 deletions(-)
953c44e feat(ui): redesign with deeper colors (#119)
 233 files changed, 1341 insertions(+), 29905 deletions(-)
```

**Parsing shortstat:**

```python
import re

SHORTSTAT_RE = re.compile(
    r'(\d+) files? changed'
    r'(?:, (\d+) insertions?\(\+\))?'
    r'(?:, (\d+) deletions?\(-\))?'
)

def parse_shortstat(line: str) -> dict:
    m = SHORTSTAT_RE.search(line)
    if not m:
        return {}
    return {
        'files_changed': int(m.group(1)),
        'insertions': int(m.group(2) or 0),
        'deletions': int(m.group(3) or 0),
    }
```

### Lines added/removed per file per commit (numstat)

```bash
git log --numstat --format='COMMIT:%h|%aI|%s' --since='2026-03-17'
```

**Example output:**
```
COMMIT:560606b|2026-03-18T05:08:36-04:00|chore(docs): added architecture docs

1	1	.claude/settings.json
895	0	docs/ARCHITECTURE.md
COMMIT:cd3879d|2026-03-18T00:03:17-04:00|chore(deps): bump backend to 0.1.5 (#120)

1	1	backend/pyproject.toml
1	1	frontend/package.json
```

**Format:** `<additions>\t<deletions>\t<filename>` per file, with blank line between commits.

**Parsing:**

```python
def parse_numstat_output(output: str) -> list[dict]:
    """Parse git log --numstat output into structured data."""
    commits = []
    current = None
    for line in output.strip().split('\n'):
        if line.startswith('COMMIT:'):
            parts = line[7:].split('|', 2)
            current = {
                'hash': parts[0],
                'date': parts[1],
                'subject': parts[2],
                'files': [],
            }
            commits.append(current)
        elif '\t' in line and current is not None:
            adds, dels, path = line.split('\t', 2)
            # Binary files show '-' for adds/dels
            current['files'].append({
                'path': path,
                'additions': int(adds) if adds != '-' else 0,
                'deletions': int(dels) if dels != '-' else 0,
            })
    return commits
```

### Diff stats between two points

```bash
# Between two commits
git diff --stat HEAD~5..HEAD

# Between two dates (using rev-list to find boundary commits)
git diff --stat $(git rev-list -1 --before='2026-03-17' HEAD)..HEAD
```

### Total lines added/removed in a date range

```bash
git log --since='2026-03-17' --format='' --shortstat
```

Then sum the insertions/deletions across all shortstat lines.

### Per-file stat summary for a commit

```bash
git show --stat --format='' <commit-hash>
```

### Per-file detailed diff for a commit

```bash
git show --numstat --format='' <commit-hash>
```

### Performance considerations

- `--shortstat` is lighter than `--stat` (no per-file breakdown)
- `--numstat` is lighter than `--stat` (no ASCII bar graph, tab-separated)
- For aggregation, prefer `--numstat` for machine parsing or `--shortstat` for per-commit totals
- Binary files in `--numstat` show `-` for add/delete; guard against this in parsing
- For massive commits (e.g., vendor directory adds), consider `--diff-filter=M` to only count modified files

---

## Appendix A: Format Placeholders Quick Reference

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `%h` | Abbreviated commit hash | `560606b` |
| `%H` | Full commit hash | `560606b...` |
| `%s` | Subject line | `feat(ui): redesign...` |
| `%aI` | Author date, ISO 8601 | `2026-03-18T05:08:36-04:00` |
| `%ad` | Author date (respects `--date`) | `2026-03-18` |
| `%aN` | Author name (respects .mailmap) | `Raul Chakraborty` |
| `%aE` | Author email (respects .mailmap) | `raul@example.com` |
| `%x00` | NUL byte (for safe parsing) | (binary) |

### Date format options

| Flag | Format | Example |
|------|--------|---------|
| `--date=short` | YYYY-MM-DD | `2026-03-18` |
| `--date=iso` | ISO-ish | `2026-03-18 05:08:36 -0400` |
| `--date=iso-strict` | ISO 8601 | `2026-03-18T05:08:36-04:00` |
| `--date=format:'%Y-%m-%d'` | Custom strftime | `2026-03-18` |
| `--date=format:'%Y-W%V'` | ISO week | `2026-W12` |
| `--date=format:'%H'` | Hour only | `05` |
| `--date=unix` | Unix timestamp | `1742288916` |

---

## Appendix B: Command-to-Skill Mapping

| Command Pattern | Primary Skill | Secondary |
|----------------|---------------|-----------|
| `git log --grep="(#N)"` | `sdlc:status` | `sdlc:retro` |
| `git log --format='%ad' \| sort \| uniq -c` | `sdlc:retro` | |
| `git log --name-only \| sort \| uniq -c` | `sdlc:retro` | |
| `git log --fixed-strings --grep="(#N)" -1` | `sdlc:status` | |
| `git branch --sort=-committerdate` | `sdlc:status` | |
| `git log --perl-regexp --grep='^feat\('` | `sdlc:retro` | `sdlc:status` |
| `git log --first-parent main` | `sdlc:retro` | |
| `git log tag1..tag2` | `sdlc:retro` | |
| `git shortlog -sn` | `sdlc:retro` | |
| `git log --shortstat` / `--numstat` | `sdlc:retro` | |

---

## Appendix C: Recommended Execution Strategy

### For `sdlc:status` (what's active now)

Run these three commands in parallel:

```bash
# 1. Recent commits on main (last 7 days)
git log --first-parent main --since='7 days ago' --format='%h|%aI|%s'

# 2. Active branches (sorted by date)
git branch --sort=-committerdate --format='%(refname:short)|%(committerdate:iso8601)|%(subject)' | head -10

# 3. Unmerged branches
git branch --no-merged main --format='%(refname:short)|%(committerdate:iso8601)'
```

Parse all three outputs, cross-reference branch names with issue numbers, and correlate with `gh issue list` data.

### For `sdlc:retro` (process metrics for a sprint)

Run these commands sequentially (each depends on knowing the sprint range):

```bash
SINCE='2026-03-14'
UNTIL='2026-03-19'

# 1. Commit cadence
git log --since="$SINCE" --until="$UNTIL" --format='%ad' --date=format:'%Y-%m-%d' | sort | uniq -c

# 2. Type distribution
git log --since="$SINCE" --until="$UNTIL" --format='%s' | grep -oE '^[a-z]+' | sort | uniq -c | sort -rn

# 3. Scope distribution
git log --since="$SINCE" --until="$UNTIL" --format='%s' | grep -o '([a-z-]*)' | sort | uniq -c | sort -rn

# 4. File hotspots
git log --since="$SINCE" --until="$UNTIL" --name-only --format='' | sort | uniq -c | sort -rn | head -15

# 5. PRs merged (velocity)
git log --first-parent main --since="$SINCE" --until="$UNTIL" --format='%h|%aI|%s'

# 6. Total line churn
git log --since="$SINCE" --until="$UNTIL" --format='' --shortstat
```

### Output aggregation in Python

```python
def aggregate_sprint_metrics(since: str, until: str) -> dict:
    """Run all retro commands and return structured metrics."""
    return {
        "period": {"start": since, "end": until},
        "commit_count": run("git rev-list --count --since=... HEAD"),
        "commits_per_day": parse_uniq_c(run("git log ... | sort | uniq -c")),
        "type_distribution": parse_uniq_c(run("git log ... | grep -oE ...")),
        "scope_distribution": parse_uniq_c(run("git log ... | grep -o ...")),
        "file_hotspots": parse_uniq_c(run("git log --name-only ...")),
        "prs_merged": parse_pipe_delimited(run("git log --first-parent ...")),
        "total_insertions": sum_shortstat_insertions(run("git log --shortstat")),
        "total_deletions": sum_shortstat_deletions(run("git log --shortstat")),
    }
```
