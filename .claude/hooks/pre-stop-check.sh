#!/bin/bash
# Reminder before Claude stops working — outputs to stderr as feedback
echo "Before stopping, verify:" >&2
echo "  1. Tests pass (pytest / pnpm test)" >&2
echo "  2. Linting clean (ruff check / pnpm lint)" >&2
echo "  3. Related GitHub issue updated (gh issue edit)" >&2
exit 0
