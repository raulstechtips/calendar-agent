---
description: Next.js 16 · React 19 · Tailwind v4 · shadcn/ui (Base UI) conventions
paths:
  - "frontend/**"
---

# Frontend Rules

## Architecture

- Default to Server Components — add `"use client"` only for state, event handlers, effects, or browser APIs
- Push `"use client"` DOWN to the smallest interactive leaf; use the `children` prop pattern to nest Server Components inside Client wrappers
- Import `server-only` in modules that must never run on the client (`lib/api.ts`, auth utilities)
- `proxy.ts` is the traffic cop — redirects, rewrites, auth checks, header modification only. Never fetch data, manage sessions, or aggregate in proxy
- `error.tsx` (must be `"use client"`) for route-level error boundaries; `not-found.tsx` with `notFound()` for 404 states
- Handle event handler errors with try/catch + useState, not error boundaries
- Use `use cache` for explicit caching (replaces implicit ISR) — pair with `cacheLife()` and `cacheTag()` for granular control
- Every parallel route slot requires an explicit `default.js` — builds fail silently without it

## Data Fetching & Mutations

- Fetch in Server Components with async/await — the primary read pattern
- Server Actions for MUTATIONS only — never for data fetching
- Validate all Server Action inputs with Zod; return errors as data (`{ success, error? }`), never throw
- Route Handlers for webhooks, external APIs, or when you need full HTTP control (e.g., SSE proxy at `/api/chat`)
- `useActionState` for form state management — this replaced the deprecated `useFormState` in React 19
- `useOptimistic` for instant UI feedback before server confirmation (likes, adds, toggles)
- `<form action={serverAction}>` for progressive enhancement — use `redirect()` inside the action for no-JS fallback

## React 19 Patterns

- `ref` is a regular prop — never use `forwardRef` (deprecated in React 19). Write `function MyButton({ ref, ...props })` directly
- `use()` hook reads promises passed from Server to Client Components — do NOT create promises client-side and pass them to `use()`. In Server Components, prefer plain `async/await`
- React Compiler is stable — never manually add `useMemo`, `useCallback`, or `React.memo`. The compiler handles memoization automatically. Remove manual memoization when touching existing code
- Use discriminated unions for mutually exclusive state (`type State = { status: 'loading' } | { status: 'error'; error: string } | { status: 'success'; data: T }`), not boolean flags

## Tailwind v4 + shadcn/ui

- CSS-first configuration — all theme tokens live in `globals.css` via `@theme inline`. Never create a `tailwind.config.js`
- OKLCH color space for all colors — follow `frontend/DESIGN.md` tokens. Never use hex or rgb values
- Always use `cn()` for conditional classNames — never concatenate strings
- Mobile-first: unprefixed utilities are the mobile base, `md:`/`lg:` for larger screens
- No arbitrary values (`mt-[13px]`) — use theme tokens. If a token doesn't exist, add it to `@theme`
- Extract repeated class patterns into React components, not `@apply`
- Use `shadcn` skill when adding UI primitives — never manually create files in `components/ui/`
- This project uses `@base-ui/react` (not Radix) — use render props for composition, not `asChild`
- Container queries (`@container`) are built-in — no plugin needed
- Tailwind v4 changed defaults: border/ring color = `currentColor`, ring width = `1px`. Test visuals after any component migration

## Component Patterns

- One responsibility per component — extract sub-components at ~50-80 lines
- Never declare components inside other components — extract to separate functions or files
- Semantic HTML (`<main>`, `<section>`, `<nav>`, `<header>`) over div soup
- `next/image` with `width`/`height` or `fill` — never use bare `<img>` tags
- Every interactive element: keyboard-accessible with proper ARIA attributes

## Skills

Invoke BEFORE the first edit, not after. If code was already written without a skill: stop, invoke, revise.

1. `impeccable:frontend-design` — before ANY visual work (components, pages, layouts). Provides opinionated design direction. Style guide: `frontend/DESIGN.md`
2. `shadcn` — before adding or editing `components/ui/` files. Checks if the component exists and provides composition patterns
3. `vercel-react-best-practices` — before touching data fetching, bundle-affecting imports, or rendering strategy
4. `vercel-composition-patterns` — when a component exceeds ~80 lines or needs compound component patterns

## Visual Self-Review Loop

jsdom tests verify behavior, not appearance. Screenshots are the only source of truth.

After every batch of visual changes:
1. Run `pnpm e2e:screenshots`
2. Read every affected screenshot — write specific findings ("looks good" is not acceptable)
3. Check: overflow/clipping, data visibility, interaction cues, type hierarchy, consistent spacing
4. Fix issues → re-screenshot → re-inspect. Do not move on while screenshot issues remain
