# Design Playbook — Calendar Assistant

## Brand Color

**Teal** (OKLCH hue ~175) — fresh, calm, productive.
Chosen over indigo-blue (hue ~264) because teal conveys focus and clarity without the generic "default shadcn" feel. It pairs naturally with warm neutral backgrounds and an orange accent for high-visibility CTAs.

References: Evernote, Todoist, Cron — productivity tools that use teal/green tones.

## Color System

### Primary Tokens

| Semantic token | Purpose | Light value | Dark value |
|----------------|---------|-------------|------------|
| `--primary` | Buttons, active indicators, today marker | `oklch(0.600 0.118 175)` | `oklch(0.720 0.12 175)` |
| `--primary-foreground` | Text on primary | `oklch(0.985 0 0)` (white) | `oklch(0.145 0.02 180)` (dark) |
| `--ring` | Focus rings | Same as primary | `oklch(0.637 0.104 175)` |
| `--destructive` | Delete actions, errors | `oklch(0.577 0.245 27)` (red) | `oklch(0.704 0.191 22)` |

### Surface Tokens (Warm Neutrals)

| Token | Light | Dark | Notes |
|-------|-------|------|-------|
| `--background` | `oklch(0.988 0.003 210)` | `oklch(0.145 0.01 240)` | Warm off-white / warm dark |
| `--card` | `oklch(0.995 0.002 210)` | `oklch(0.195 0.012 240)` | Slightly elevated |
| `--muted` | `oklch(0.955 0.01 220)` | `oklch(0.250 0.012 240)` | Soft blue-gray |
| `--border` | `oklch(0.912 0.012 230)` | `oklch(0.30 0.01 240)` | Cool gray |
| `--accent` | `oklch(0.945 0.02 175)` | `oklch(0.250 0.015 200)` | Teal hover tint |

### Chart Colors (Teal Family + Orange Accent)

| Token | Value | Usage |
|-------|-------|-------|
| `--chart-1` | `oklch(0.80 0.10 175)` | Light teal |
| `--chart-2` | `oklch(0.600 0.118 175)` | Primary teal |
| `--chart-3` | `oklch(0.55 0.10 175)` | Deep teal |
| `--chart-4` | `oklch(0.646 0.175 41)` | Warm orange (accent) |
| `--chart-5` | `oklch(0.45 0.08 175)` | Darkest teal |

### Rules

- **Teal hue ~175 for primary.** Orange hue ~41 for accent only (chart-4).
- **Warm neutrals.** All backgrounds/surfaces have slight chroma (0.003–0.015) on hue 210–250. Never pure gray (chroma 0).
- **Opacity variants** (`bg-primary/15`, `bg-primary/20`) for tinted backgrounds — teal at low opacity reads as a calm wash, not cold like indigo.
- **Foreground on primary**: white in light mode, dark in dark mode (teal is lighter than indigo, so dark-on-teal works in dark mode).

## Event Color Mapping

| Type | Background | Border | Text |
|------|-----------|--------|------|
| AI-created | `bg-primary/20` | `border-l-2 border-l-primary` | `text-foreground` |
| Regular (Google) | `bg-card ring-1 ring-border` | — | `text-foreground` |
| All-day | `bg-primary text-primary-foreground` | — | White / Dark |

## Working Hours

- Default band: **9:00 AM – 5:00 PM** (hours 9–16 in the time grid)
- Visual treatment: `bg-muted/40` tint on the working-hours rows
- Configurable per user in Settings (stored in preferences)

## Typography

- Font: Geist Sans (already configured via `next/font`)
- Headings: `font-semibold` (not bold — keeps the UI calm)
- Body: default weight
- Monospace (code, times): Geist Mono
- Minimum body text: `text-sm` (14px). Avoid `text-[10px]` — use `text-xs` (12px) minimum.

## Spacing & Radius

- Card radius: `rounded-xl` (shadcn default)
- Chat bubbles: `rounded-2xl` with tail (`rounded-br-sm` for user, `rounded-bl-sm` for assistant)
- Input fields: `rounded-2xl` for chat, `rounded-lg` for forms
- Comfortable density: `gap-4` between major sections, `gap-2` within groups
- Section spacing: `space-y-8` for page sections, `space-y-4` within cards

## Personality

**Precise, helpful, quietly confident.**

- Transitions serve function: 150ms `transition-colors` on interactive elements
- Clean whitespace over visual clutter — comfortable density, not compact
- Information density is a feature (calendar views), not a bug — but always with clear hierarchy
- Empty states should invite action, not apologize

## Shadows & Elevation

- Cards: use ring (`ring-1 ring-foreground/10`) instead of box-shadow (sharper on retina)
- Chat bubbles: `shadow-xs` for slight depth
- Elevated elements (dialogs, popovers): shadcn defaults
- Hover states: `shadow-sm` for lift
- Current time indicator: `shadow-sm shadow-destructive/50` for gentle glow

## Dark Mode

- All tokens have dark variants — test both modes
- Warm dark backgrounds (chroma > 0) — never pure black
- Primary lightens in dark mode (0.720 vs 0.600) for adequate contrast
- Primary-foreground inverts: dark text on bright teal in dark mode
