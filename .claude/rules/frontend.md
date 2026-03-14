---
description: Next.js 16 + TypeScript + Tailwind + shadcn/ui conventions
paths:
  - "frontend/**"
---

# Frontend Rules (Next.js 16)

## Server vs Client Components

- Default to Server Components — only add `"use client"` when you need state, event handlers, effects, or browser APIs
- Push `"use client"` boundaries DOWN to the smallest interactive leaf component
- Never put `"use client"` on layouts or pages unless absolutely necessary
- Use the `children` prop pattern to nest Server Components inside Client Components
- Import `server-only` in files that must never run on the client

## Data Fetching

- Fetch data in Server Components with async/await — this is the primary pattern
- Server Actions are for MUTATIONS only — never use them for data fetching
- Always validate Server Action inputs with Zod
- Return errors as data from Server Actions, never throw
- Use `useActionState` for form state management
- Use Route Handlers for webhooks, external APIs, or when you need full HTTP control

## Streaming and Suspense

- Wrap slow data-fetching components in `<Suspense>` with skeleton fallbacks
- Never block the shell with top-level awaits in layouts
- Use `loading.tsx` for route-level loading states
- Keep layouts structural — no slow data fetching in layouts

## Error Handling

- Use `error.tsx` (must be `"use client"`) for error boundaries at each route level
- Use `not-found.tsx` with `notFound()` for 404 states
- Handle event handler errors with try/catch + useState, not error boundaries

## proxy.ts (replaces middleware.ts)

- Keep it lean — traffic cop, not database admin
- Use for: redirects, rewrites, auth checks, header modification
- Never use for: heavy data fetching, session management, data aggregation

## TypeScript

- `strict: true` always — never disable
- Never use `any` — use `unknown` and narrow with type guards
- Never use `@ts-ignore` — fix the actual type issue
- Use `interface` for component props (more extensible than `type`)
- Use discriminated unions for mutually exclusive state, not boolean flags
- Use `z.infer<typeof schema>` to derive types from Zod schemas — single source of truth

## Documentation

- Add `/** ... */` JSDoc to exported utility functions in `lib/` and custom hooks in `hooks/`
- Do NOT add JSDoc to React components — the component name + props interface are the documentation
- Do NOT add JSDoc to props interfaces — property names + TypeScript types are self-documenting
- Server Actions and Route Handlers: add a one-line JSDoc describing what the action/handler does (these are effectively API endpoints)
- Inline comments: explain "why" not "what" — non-obvious Tailwind workarounds, browser-specific hacks, Next.js caching behavior

## Tailwind + shadcn/ui

- Never use inline styles — always Tailwind classes
- Always use `cn()` from shadcn for conditional classNames — never concatenate strings
- Mobile-first: unprefixed utilities are the mobile styles, use `md:`, `lg:` for larger screens
- Never use arbitrary values (`mt-[13px]`) — use theme values
- Extract repeated patterns into React components, not `@apply` classes

## Component Patterns

- Components should do ONE thing — extract sub-components at ~50-80 lines
- Never declare components inside other components — extract to separate functions/files
- Use semantic HTML (`<main>`, `<section>`, `<nav>`, `<header>`) not div soup
- Every interactive element must be keyboard-accessible with proper ARIA attributes
- Always use `next/image` (not `<img>`) and `next/font` (not external font links)
- Always set `width`/`height` or `fill` on images to prevent layout shifts

## Forms (React Hook Form + Zod)

- Define validation schema with Zod first
- Use `useForm<z.infer<typeof schema>>({ resolver: zodResolver(schema) })`
- Make error messages actionable: "Username must be at least 3 characters" not "Invalid input"

## Testing

- Use Vitest + Testing Library for component tests
- Prefer `getByRole` over `getByTestId` — matches user experience
- Test user-visible behavior, not implementation details
- Every component with data fetching must test loading AND error states
