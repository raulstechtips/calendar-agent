#!/bin/bash
# Prevents modification of test files during implementation.
# Blocks Edit/Write operations on test files unless the commit message
# or current task explicitly involves writing tests.
# Exit code 2 = block with feedback to Claude.

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)

[ -z "$FILE_PATH" ] && exit 0

# Check if the file is a test file
case "$FILE_PATH" in
  test_*|*/test_*|*/*.test.*|*/*.spec.*|*/__tests__/*)
    # Allow if this is explicitly a test-writing task
    # (Claude will be told to set this env var when writing tests)
    if [ "${WRITING_TESTS:-0}" = "1" ]; then
      exit 0
    fi
    echo "BLOCKED: Cannot modify test file '$FILE_PATH' during implementation." >&2
    echo "If you need to write NEW tests, set WRITING_TESTS=1 first." >&2
    echo "If an existing test is wrong, ask the human before modifying it." >&2
    exit 2
    ;;
esac

exit 0
