---
description: Test-driven development rules
---

# Test-Driven Development

## Red-Green-Refactor cycle

1. **Red**: Write tests that define expected behavior. Tests MUST fail initially.
2. **Green**: Write the minimum implementation to make tests pass.
3. **Refactor**: Improve code while keeping tests green.

## Test protection rules

IMPORTANT: These rules are non-negotiable.

- NEVER modify test files during implementation to make them pass
- NEVER delete or skip failing tests
- NEVER weaken assertions (e.g., changing `assertEqual` to `assertIn`)
- NEVER add `pytest.mark.skip`, `@pytest.mark.xfail`, or `xit`/`xdescribe` to make a suite pass
- If a test is genuinely wrong, explain WHY and ask the human before changing it

## What to test

### Backend (pytest + pytest-asyncio)
- Every API endpoint: success case + at least one failure case
- Business logic in service layers: edge cases, boundary values
- Auth/token handling: valid tokens, expired tokens, missing tokens
- Agent tools: correct parameters, error handling, return format
- Guardrails: injection attempts blocked, clean input passes

### Frontend (Vitest + Testing Library)
- User interactions: clicks, form submissions, keyboard navigation
- Loading and error states
- API integration: successful responses, error responses
- Conditional rendering based on auth state

## Test file organization

- Backend: `backend/tests/test_<module>.py` mirroring `backend/app/<module>/`
- Frontend: co-located `ComponentName.test.tsx` next to `ComponentName.tsx`

## Test naming

- Use descriptive names: `test_should_reject_expired_token`, `test_should_create_event_with_valid_data`
- Group related tests in classes or describe blocks

## Coverage targets (realistic for 2-day sprint)

- Critical paths (auth, tokens, guardrails): 90%+
- Business logic (endpoints, tools): 80%+
- UI components: 60%+
