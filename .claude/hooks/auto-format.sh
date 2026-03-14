#!/bin/bash
# Auto-format files after Write/Edit operations
# Reads tool input from stdin (JSON with file_path)
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)

[ -z "$FILE_PATH" ] && exit 0
[ ! -f "$FILE_PATH" ] && exit 0

case "$FILE_PATH" in
  *.py)
    ruff format "$FILE_PATH" 2>/dev/null || true
    ;;
  *.ts|*.tsx|*.js|*.jsx|*.json|*.css)
    npx prettier --write "$FILE_PATH" 2>/dev/null || true
    ;;
esac

exit 0
