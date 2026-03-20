---
name: capture
description: Use when you want to quickly capture an idea or task without going through the full sdlc:define ceremony. Creates a minimal GitHub issue with a triage label.
allowed-tools: Bash
argument-hint: "<one-line description of the idea>"
---

I'm using the sdlc:capture skill to quickly capture this idea.

This is a no-ceremony skill — no context loading, no upstream artifact reading, no brainstorming phases. Just create the issue and report back.

Run the following command:

```bash
gh issue create --title "$ARGUMENTS" --label "triage" --body "## Description\n$ARGUMENTS\n\n## Status\nCaptured via sdlc:capture. Run \`/sdlc:define\` to flesh out when ready."
```

Report the created issue number and URL to the user.

Note: `sdlc:reconcile` flags triage issues older than 14 days so nothing gets lost.
