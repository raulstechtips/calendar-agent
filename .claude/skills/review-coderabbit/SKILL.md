---
name: review-coderabbit
description: Fetch and analyze CodeRabbit review comments on a PR. Triages each comment by severity, evaluates whether it's valid, and presents an action plan.
allowed-tools: Read, Bash, Grep, Glob
argument-hint: "[PR number, or omit to auto-detect from current branch]"
---

# Review CodeRabbit Comments

Fetch all CodeRabbit review comments from a GitHub PR, analyze them, and present a prioritized action plan.

## Steps

1. **Resolve the PR number.** If an argument was provided, use it. Otherwise, detect from the current branch:
   ```bash
   gh pr view --json number --jq '.number'
   ```
   If no PR exists for the current branch, tell the user and stop.

2. **Fetch all review comments** on the PR:
   ```bash
   gh api repos/{owner}/{repo}/pulls/<PR>/comments --paginate --jq '.[] | select(.user.login == "coderabbitai" or .user.login == "coderabbit-ai[bot]" or (.user.login | test("coderabbit"; "i"))) | {id: .id, path: .path, line: .original_line, body: .body, created: .created_at}'
   ```
   Also check top-level PR review bodies (the summary review):
   ```bash
   gh api repos/{owner}/{repo}/pulls/<PR>/reviews --jq '.[] | select(.user.login == "coderabbitai" or .user.login == "coderabbit-ai[bot]" or (.user.login | test("coderabbit"; "i"))) | {id: .id, body: .body, state: .state}'
   ```

3. **If no CodeRabbit comments found**, report that and stop.

4. **For each inline comment**, read the referenced file and surrounding context to understand the code CodeRabbit is commenting on.

5. **Triage each comment** into one of these categories:
   - **VALID — Must Fix**: The comment identifies a real bug, security issue, or spec violation. Action is required.
   - **VALID — Should Fix**: The comment is correct and improves quality, but isn't blocking.
   - **VALID — Consider**: A reasonable suggestion but debatable or low-impact.
   - **NOISE — Dismiss**: The comment is incorrect, outdated, stylistic nitpick already handled by linters, or not applicable to this codebase.

6. **For each VALID comment**, explain:
   - What CodeRabbit flagged and why it matters (or doesn't)
   - The specific file and line
   - Your recommended fix (1-2 sentences)

7. **Present the analysis** in this format:

   ```
   ## CodeRabbit Review Analysis — PR #<number>

   **Summary**: X comments total — Y must-fix, Z should-fix, W consider, N noise

   ### Must Fix
   - **[path:line]** — <description of issue and recommended fix>

   ### Should Fix
   - **[path:line]** — <description and recommendation>

   ### Consider
   - **[path:line]** — <description and trade-off>

   ### Dismissed
   - **[path:line]** — <why this is noise>
   ```

8. **Ask the user** which comments they'd like you to address. Do NOT make changes automatically.

## Rules

- Do NOT auto-fix anything. Present the analysis and wait for the user's decision.
- Be honest — if CodeRabbit caught a real issue, say so. Don't dismiss valid feedback.
- If a comment references a pattern or convention you're unsure about, check the SPEC and existing code before judging.
- Group related comments (e.g., same issue across multiple files) into a single item.
