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
- `noUncheckedIndexedAccess: true` — always check index access results for `undefined`
- Never add `@ts-expect-error` without an explanatory comment describing why

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
- ALWAYS use the `shadcn` skill when adding new UI primitives — never copy-paste or manually create shadcn components

## Skills — MUST invoke before building UI

These skills provide design intelligence that Claude does not have natively. Without them, UI output defaults to safe, generic choices — correct but bland. The skills exist to push past that.

**A plan that prescribes specific UI values (colors, spacing, Tailwind classes) does NOT substitute for skill invocation.** The plan captures *what to change*; the skill provides *design intelligence* about *how to make it look good*. Even if a plan is highly prescriptive, invoke the relevant skill before the first edit to validate and improve the plan's visual choices.

### Skills and why they matter

| Skill | Invoke BEFORE... | Why — what goes wrong without it |
|-------|------------------|----------------------------------|
| **`frontend-design`** | Writing or modifying ANY visual component, page, or layout. Before choosing colors, spacing, typography, or visual hierarchy. | Without it: you pick safe defaults (gray tokens, uniform spacing, no visual rhythm). The skill provides opinionated, anti-generic-AI design direction — distinctive layouts, spatial hierarchy, and polish that make interfaces feel designed rather than assembled. |
| **`shadcn`** | Adding, composing, or debugging ANY shadcn/ui component. Before manually creating files in `components/ui/`. | Without it: you might manually create a component that shadcn already provides, or miss composition patterns (compound components, slot APIs) that the library supports. |
| **`vercel-react-best-practices`** | Touching data fetching, bundle-affecting imports, image loading, or rendering strategy. When adding `"use client"`. | Without it: you may create unnecessary client boundaries, miss streaming opportunities, or introduce bundle bloat that degrades performance. |
| **`vercel-composition-patterns`** | Building compound components, extracting shared APIs, or when a component exceeds ~80 lines. | Without it: components grow monolithic with boolean prop proliferation instead of clean composition patterns. |

### Enforcement: before first edit, not before PR

Skill invocation is a **pre-implementation** step, not a post-implementation gate. The workflow is:

1. **Before the first edit** to any visual file: invoke `frontend-design` to get opinionated design direction and specific aesthetic recommendations
2. **Before creating/editing** any `components/ui/` file: invoke `shadcn` to check if the component exists or has a preferred composition pattern
3. **After edits**: run the Visual Self-Review Loop (see below)

If you already wrote the code without invoking a skill: stop, invoke the skill, and be willing to revise. Sunk cost is not a reason to skip design review.

### Visual Self-Review Loop (MANDATORY after every visual change)

jsdom tests verify behavior but not appearance. **Screenshots are the only source of truth.**

After every batch of visual changes, run `pnpm e2e:screenshots`, then Read and inspect every affected screenshot. For each one, **write out specific findings** — "looks good" is not acceptable. Check for:

- **Overflow & clipping**: text cut off, content bleeding, scroll bars where they shouldn't be, sidebar bottom truncated
- **Data visibility**: overlapping calendar events (need collision layout), obscured labels, missing profile images/avatars
- **Interaction cues**: buttons need clear affordance, async actions need loading/spinner states, inputs need visible focus rings
- **Polish**: clear type hierarchy, consistent spacing, UI should look like a finished product (think Google Calendar / Linear) not a template

If anything fails: fix it, re-screenshot, re-inspect. **Do not move on while screenshot issues remain.** This fix-and-reshoot cycle is how UI quality actually improves.

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
