# Claude Code Plugin Architecture — Research Report

**Date:** 2026-03-19
**Purpose:** Determine whether and how to package the SDLC skill suite as a Claude Code plugin for namespaced invocation (`sdlc:define`, `sdlc:create`, etc.)

---

## Executive Summary

**The plugin system supports everything we need.** A plugin named `sdlc` with skills named `define`, `create`, etc. will automatically produce the `sdlc:define`, `sdlc:create` namespacing we want. The plugin can be loaded locally from the repo using `--plugin-dir` during development and eventually published to a marketplace for distribution.

However, there is a critical design question: **should the SDLC suite be a plugin or stay as local project skills?** The answer depends on whether we want it to be reusable across repos or specific to this one.

---

## 1. How Plugins Work

### Plugin Directory Structure

Every plugin follows this layout:

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json          # Required: manifest with at minimum {"name": "plugin-name"}
├── commands/                 # Slash commands (.md files)
├── agents/                   # Subagent definitions (.md files)
├── skills/                   # Auto-discovered skills
│   └── skill-name/
│       └── SKILL.md
├── hooks/
│   └── hooks.json
├── .mcp.json
└── scripts/
```

**Critical rules:**
- `.claude-plugin/plugin.json` is the only required file
- Component directories (commands/, agents/, skills/, hooks/) MUST be at plugin root, NOT inside `.claude-plugin/`
- Only `name` field is required in plugin.json; everything else is optional
- All component directories are optional — only create what you use

### Plugin Manifest (plugin.json)

Minimal:
```json
{
  "name": "sdlc"
}
```

Recommended for distribution:
```json
{
  "name": "sdlc",
  "version": "1.0.0",
  "description": "Software development lifecycle management skills for Claude Code",
  "author": { "name": "Raul" },
  "license": "MIT",
  "keywords": ["sdlc", "project-management", "github-issues", "planning"]
}
```

---

## 2. Answers to Critical Questions

### a. Can a plugin be local to a repo?

**Yes, via `--plugin-dir`.** The CLI flag `--plugin-dir <path>` loads a plugin from any local directory for the current session:

```bash
claude --plugin-dir /path/to/plugin
# or for multiple plugins:
claude --plugin-dir /path/to/A --plugin-dir /path/to/B
```

**Discovery mechanisms (3 levels):**

1. **Marketplace-installed plugins** — installed via `/plugin install`, cached in `~/.claude/plugins/cache/`, tracked in `~/.claude/plugins/installed_plugins.json`
2. **`--plugin-dir` flag** — per-session, loads from any local directory. This is the development/testing mechanism.
3. **No auto-discovery from repo** — there is NO mechanism to auto-discover a plugin from within a repo (e.g., no `.claude-plugin/plugin.json` at repo root that auto-loads). The plugin must be either globally installed or explicitly loaded via `--plugin-dir`.

**For our use case:** During development, we would use `--plugin-dir .claude/sdlc-plugin` (or wherever we put it). For production use, we would either:
- Always launch Claude with `--plugin-dir`, or
- Publish to a marketplace and install globally, or
- Add it to a launch script/alias

### b. What's the file structure of a plugin?

See Section 1 above. For our SDLC suite specifically:

```
sdlc/                                   # Plugin root
├── .claude-plugin/
│   └── plugin.json                     # {"name": "sdlc", ...}
├── skills/
│   ├── define/
│   │   ├── SKILL.md                    # Core 5-phase flow
│   │   └── reference/
│   │       ├── prd-guide.md
│   │       ├── pi-guide.md
│   │       ├── epic-guide.md
│   │       ├── feature-guide.md
│   │       └── story-guide.md
│   ├── create/
│   │   ├── SKILL.md
│   │   └── reference/
│   │       ├── prd-execution.md
│   │       ├── pi-execution.md
│   │       ├── epic-execution.md
│   │       ├── feature-execution.md
│   │       └── story-execution.md
│   ├── update/
│   │   ├── SKILL.md
│   │   └── reference/
│   │       ├── prd-update.md
│   │       ├── pi-update.md
│   │       ├── epic-update.md
│   │       ├── feature-update.md
│   │       └── story-update.md
│   ├── status/
│   │   └── SKILL.md
│   ├── reconcile/
│   │   └── SKILL.md
│   ├── retro/
│   │   └── SKILL.md
│   └── capture/
│       └── SKILL.md
└── agents/                             # Optional: if skills dispatch subagents
    └── codebase-explorer.md
```

### c. How does skill namespacing work?

**Yes, it works exactly as we want.** The convention observed across installed plugins:

- Plugin `superpowers` has skill `test-driven-development` → referenced as `superpowers:test-driven-development`
- Plugin `plugin-dev` has skill `skill-development` → displayed as `(plugin:plugin-dev)` in `/help`

**For our case:** Plugin name `sdlc` + skill directory `define/` = invocable as `/sdlc:define` and referenceable as `sdlc:define`.

The namespacing comes from the plugin name in `plugin.json` combined with the skill directory name. Commands in plugins appear in `/help` as `(plugin:plugin-name)` or `(plugin:plugin-name:namespace)` for subdirectory-organized commands.

### d. What's the difference between a skill and a command in a plugin?

**Skills** (in `skills/` directory):
- Auto-activated by Claude based on context matching the description
- User-invocable as `/skill-name` (becomes `/plugin:skill-name` in plugins)
- Support `SKILL.md` with YAML frontmatter (name, description, allowed-tools, model, etc.)
- Support reference files, scripts, examples subdirectories
- Can be model-only invocable (`user-invocable: false`) or user-only (`disable-model-invocation: true`)
- Progressive disclosure: metadata always in context, SKILL.md body loaded on trigger, reference files loaded as needed

**Commands** (in `commands/` directory):
- User-invoked only via `/command-name`
- Simpler format: just a `.md` file with optional frontmatter
- Support `$ARGUMENTS`, `$1`, `$2` for positional args
- Support `@file` references and `` !`bash` `` execution
- The `commands/` directory is described as "legacy format" — new development should use `skills/<name>/SKILL.md` layout instead

**Key insight from the command-development SKILL.md:**
> "The `.claude/commands/` directory is a legacy format. For new skills, use the `.claude/skills/<name>/SKILL.md` directory format. Both are loaded identically — the only difference is file layout."

**For our use case:** Skills are the right choice. Our SDLC suite needs:
- Rich reference files (progressive disclosure)
- `allowed-tools` control
- User invocation (explicit `/sdlc:define`)
- Potentially auto-invocation when context matches

### e. Can a plugin have both skills AND commands?

**Yes, absolutely.** The `plugin-dev` plugin has all of:
- 7 skills (plugin-structure, skill-development, agent-development, etc.)
- 1 command (`create-plugin.md`)
- 3 agents (agent-creator, skill-reviewer, plugin-validator)

The `example-plugin` demonstrates both skills and commands coexisting. But per the guidance above, there is no need to use both — `skills/<name>/SKILL.md` format supports everything commands do, including `$ARGUMENTS`, `allowed-tools`, and `argument-hint`.

**For our use case:** Use only skills. No need for separate commands.

### f. How is a plugin distributed?

**Three distribution mechanisms:**

1. **Marketplace** — plugins in `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/` are published via a git repository. Install via `/plugin install plugin-name`. Cached to `~/.claude/plugins/cache/`. Tracked in `installed_plugins.json` with `scope`, `installPath`, `version`, `gitCommitSha`.

2. **Local directory** — `--plugin-dir /path/to/plugin` loads from any local path. No installation required. Per-session only.

3. **In-repo** — there is no auto-discovery mechanism for repo-local plugins. A plugin inside the repo (e.g., `.claude/sdlc-plugin/`) would need `--plugin-dir` to load.

**For our use case (repo-local):** The plugin can live at any path in the repo. Options:
- `.claude/sdlc-plugin/` — keeps it in the `.claude/` namespace
- `tools/sdlc-plugin/` — separate from Claude config
- A standalone repo — for cross-project reuse

To make it convenient, add an alias or wrapper:
```bash
# In .zshrc or a project script:
alias claude-sdlc="claude --plugin-dir .claude/sdlc-plugin"
```

Or in `.claude/settings.json` if plugin-dir can be configured there (needs verification).

### g. What's `${CLAUDE_PLUGIN_ROOT}`?

**An environment variable that resolves to the plugin's absolute install path at runtime.** Available in:
- Hook commands: `bash ${CLAUDE_PLUGIN_ROOT}/scripts/validate.sh`
- MCP server configurations
- Command/skill file references: `@${CLAUDE_PLUGIN_ROOT}/templates/report.md`
- Bash execution within commands: `` !`bash ${CLAUDE_PLUGIN_ROOT}/scripts/run.sh` ``

**Why it matters:** Plugins install to different locations depending on installation method (marketplace cache, local directory, npm). Using `${CLAUDE_PLUGIN_ROOT}` ensures portable paths.

**For our use case:** All reference file paths in SKILL.md should use `${CLAUDE_PLUGIN_ROOT}`:
```markdown
For level-specific guidance, read `${CLAUDE_PLUGIN_ROOT}/skills/define/reference/epic-guide.md`
```

**Important nuance:** Within SKILL.md, relative paths like `reference/epic-guide.md` may also work for skills (since Claude can resolve them relative to the SKILL.md file), but `${CLAUDE_PLUGIN_ROOT}` is the official portable pattern and should be preferred for hook scripts and bash commands.

### h. Can plugins have agents (subagents)?

**Yes.** Agents go in the `agents/` directory. They are `.md` files with YAML frontmatter defining:
- `name` (required): lowercase-hyphens identifier
- `description` (required): triggering conditions with `<example>` blocks
- `model` (required): `inherit`, `sonnet`, `opus`, `haiku`
- `color` (required): visual identifier (`blue`, `cyan`, `green`, `yellow`, `magenta`, `red`)
- `tools` (optional): array of tool names to restrict access

**Agent discovery:** All `.md` files in `agents/` are auto-discovered. Agents are namespaced automatically — `plugin:agent-name` or `plugin:subdir:agent-name`.

**Agent invocation:** Claude selects agents automatically based on task context, or users can reference them. Commands/skills can trigger agents via the Task tool.

**For our use case:** If `sdlc:define` or `sdlc:retro` need to dispatch research subagents, those agents can be defined in `sdlc/agents/`. The skill SKILL.md would reference them:
```markdown
Dispatch the codebase-explorer agent to analyze the current architecture.
```

### i. What are hooks?

**Event-driven automation scripts** that execute in response to Claude Code events. Two types:

1. **Command hooks** — execute bash scripts for deterministic checks
2. **Prompt hooks** — use LLM-driven evaluation for context-aware decisions

**Available events:**
| Event | When | Use For |
|-------|------|---------|
| PreToolUse | Before tool runs | Validation, deny/allow |
| PostToolUse | After tool completes | Feedback, logging |
| UserPromptSubmit | User submits prompt | Context injection |
| Stop | Agent stopping | Completeness check |
| SubagentStop | Subagent done | Task validation |
| SessionStart | Session begins | Context loading |
| SessionEnd | Session ends | Cleanup |
| PreCompact | Before compaction | Preserve context |

**For our use case:** Hooks could be useful for:
- **SessionStart** — auto-load project context (which PI is active, current status summary)
- **Stop** — verify that a story implementation actually committed conventional commits referencing the issue number
- **PostToolUse on Bash** — after `gh issue create`, auto-update PI.md with new issue numbers

However, hooks add complexity and have limitations:
- Changes require Claude Code restart
- Hooks run in parallel (no guaranteed ordering)
- Plugin hooks merge with user hooks

**Recommendation:** Start without hooks. Add them in a future iteration if automation gaps emerge.

### j. What's the auto-discovery mechanism?

When Claude Code starts a session:

1. Read `.claude-plugin/plugin.json` for each enabled plugin
2. Scan default directories (`commands/`, `agents/`, `skills/`, `hooks/hooks.json`, `.mcp.json`)
3. Scan custom paths from plugin.json (supplements defaults)
4. Parse YAML frontmatter from all discovered files
5. Register components (skills metadata always in context, bodies loaded on trigger)
6. Start MCP servers, register hooks

**Discovery timing:** At session initialization, not continuously. Changes require new session.

**Skills specifically:** Claude always has skill metadata (name + description) in context. When a task matches a skill's description triggers, the SKILL.md body is loaded. Reference files are loaded as needed by Claude.

---

## 3. Migration Path: Local Skills to Plugin

### Current State (v1 skills)

24 skills in `.claude/skills/`, flat namespace:
- 14 SDLC skills (create-prd, update-prd, plan-increment, etc.)
- 5 frontend design skills (shadcn, vercel-*, ckm-*, etc.)
- 3 operational skills (pick-task, sync-issues, update-decision, review-coderabbit)
- 2 UI/UX skills

### Target State (plugin)

```
.claude/sdlc-plugin/                    # OR a separate repo
├── .claude-plugin/
│   └── plugin.json                     # {"name": "sdlc", "version": "1.0.0", ...}
├── skills/
│   ├── define/
│   │   ├── SKILL.md
│   │   └── reference/
│   │       ├── prd-guide.md
│   │       ├── pi-guide.md
│   │       ├── epic-guide.md
│   │       ├── feature-guide.md
│   │       └── story-guide.md
│   ├── create/
│   │   ├── SKILL.md
│   │   └── reference/
│   │       ├── prd-execution.md
│   │       ├── pi-execution.md
│   │       ├── epic-execution.md
│   │       ├── feature-execution.md
│   │       └── story-execution.md
│   ├── update/
│   │   ├── SKILL.md
│   │   └── reference/
│   │       ├── prd-update.md
│   │       ├── pi-update.md
│   │       ├── epic-update.md
│   │       ├── feature-update.md
│   │       └── story-update.md
│   ├── status/
│   │   └── SKILL.md
│   ├── reconcile/
│   │   └── SKILL.md
│   ├── retro/
│   │   └── SKILL.md
│   └── capture/
│       └── SKILL.md
└── agents/                             # If needed for subagent dispatch
    └── codebase-explorer.md
```

### Mapping: v1 Skills to v2 Plugin Skills

| v1 Skill | v2 Plugin Skill | Notes |
|----------|----------------|-------|
| `create-prd` | `sdlc:define prd` + `sdlc:create prd` | Split into brainstorm + execute |
| `update-prd` | `sdlc:update prd` | Small changes direct, large escalate to define |
| `plan-increment` | `sdlc:define pi` + `sdlc:create pi` | Split |
| `update-pi` | `sdlc:update pi` | |
| `close-pi` | `sdlc:retro pi` + `sdlc:create pi` | Retro + archive during next PI creation |
| `create-epic` | `sdlc:define epic` + `sdlc:create epic` | Split |
| `create-feature` | `sdlc:define feature` + `sdlc:create feature` | Split |
| `detail-story` | `sdlc:define story` + `sdlc:create story` | Split |
| `update-epic` | `sdlc:update epic` | |
| `update-feature` | `sdlc:update feature` | |
| `update-story` | `sdlc:update story` | |
| `pick-task` | `sdlc:status` | Richer analysis, parallelization |
| `sync-issues` | `sdlc:reconcile` | Focused on label hygiene |
| `update-decision` | `sdlc:update prd` | Decision log in PRD |
| (new) | `sdlc:capture` | Quick-capture with triage label |

### What Stays as Local Skills

These are NOT part of the SDLC suite and should remain as local project skills:
- `shadcn/` — project-specific frontend skill
- `vercel-composition-patterns/` — project-specific frontend skill
- `vercel-react-best-practices/` — project-specific frontend skill
- `web-design-guidelines/` — project-specific frontend skill
- `review-coderabbit/` — project-specific operational skill
- `ckm-*` skills — project-specific design system skills
- `ui-ux-pro-max/` — project-specific design skill

---

## 4. What Changes When Making It a Plugin

### Capabilities

| Feature | Local Skill | Plugin Skill |
|---------|------------|--------------|
| User invocable | `/skill-name` | `/skill-name` (with `(plugin:sdlc)` label in /help) |
| Auto-invocable | Yes | Yes |
| `allowed-tools` | Yes | Yes |
| `$ARGUMENTS` | Yes | Yes |
| Reference files | Relative paths | `${CLAUDE_PLUGIN_ROOT}` for portability |
| Agents | Shared global agents dir | Plugin-scoped `agents/` directory |
| Hooks | Shared `.claude/settings.json` | Plugin-scoped `hooks/hooks.json` |
| MCP servers | Not available | Plugin-scoped `.mcp.json` |
| Progressive disclosure | Same | Same |

**Key differences:**
1. **Path references** — must use `${CLAUDE_PLUGIN_ROOT}` for portability instead of relative paths from `.claude/skills/`
2. **Namespacing** — skills automatically get `plugin-name:skill-name` format
3. **Loading** — requires `--plugin-dir` flag or marketplace installation (not auto-discovered from repo)
4. **Isolation** — plugin components are scoped to the plugin, not mixed with project skills

### SKILL.md Format

**No change in format.** Plugin skills use the exact same YAML frontmatter and markdown body as local skills:

```yaml
---
name: define
description: This skill should be used when the user asks to "define a feature", "plan an epic", "create a PRD", "brainstorm a story"...
allowed-tools: [Read, Edit, Write, Bash, Grep, Glob, Agent]
---
```

The `allowed-tools` field works identically in both local skills and plugin skills.

### Invocation

- Local: `/define`, `/create`, `/status`
- Plugin: `/define` still works, but displayed as `(plugin:sdlc)` in `/help`. Can also be referenced as `sdlc:define` in cross-skill references.

---

## 5. Risks and Mitigations

### Risk 1: No Auto-Discovery from Repo

**Problem:** Unlike local skills in `.claude/skills/`, a plugin requires `--plugin-dir` or marketplace installation. There is no mechanism to auto-load a plugin from the repo.

**Impact:** Every Claude Code session must include `--plugin-dir .claude/sdlc-plugin` to use the SDLC skills.

**Mitigations:**
- Create a launch alias: `alias cc="claude --plugin-dir .claude/sdlc-plugin"`
- Document in CLAUDE.md how to start sessions
- Eventually publish to marketplace for global installation
- Investigate if `.claude/settings.json` supports `plugin-dir` configuration (would make it persistent)

### Risk 2: Conflict with Existing Local Skills

**Problem:** If v1 skills (e.g., `create-prd`, `pick-task`) remain in `.claude/skills/` alongside the plugin, both will be discovered. A user saying "create a PRD" could trigger both the local `create-prd` skill and the plugin's `sdlc:define` skill.

**Mitigation:** Remove v1 SDLC skills from `.claude/skills/` when deploying the plugin. Keep only non-SDLC skills (frontend, design, review-coderabbit) as local project skills.

**Migration sequence:**
1. Build the plugin
2. Test with `--plugin-dir`
3. Remove v1 skills from `.claude/skills/`
4. Commit cleanup

### Risk 3: `${CLAUDE_PLUGIN_ROOT}` in Skill Bodies

**Problem:** Reference files inside skills need portable paths. In local skills, we use relative paths like `reference/epic-guide.md`. In plugins, we should use `${CLAUDE_PLUGIN_ROOT}/skills/define/reference/epic-guide.md`.

**Mitigation:** All reference file paths in SKILL.md should use the pattern:
```markdown
For level-specific guidance, read `${CLAUDE_PLUGIN_ROOT}/skills/define/reference/epic-guide.md`
```

However, testing is needed to confirm whether relative references from within SKILL.md (like `reference/epic-guide.md`) work in plugin context. The superpowers plugin and plugin-dev plugin both use relative-looking references in their SKILL.md files, suggesting this may work.

### Risk 4: Session Restart Required for Changes

**Problem:** Plugin components are loaded at session start. Any change to SKILL.md, reference files, or hooks requires restarting Claude Code.

**Impact:** During development, each skill edit requires a new session to test.

**Mitigation:** This is the same behavior as local skills and hooks. Use `cc --plugin-dir .claude/sdlc-plugin` to start fresh sessions for testing.

### Risk 5: Plugin Not Portable Across Projects

**Problem:** If the plugin lives inside the repo at `.claude/sdlc-plugin/`, it is tied to this specific repo. Other repos cannot use it without copying.

**Mitigation:** Two paths:
- **For now:** Keep it in-repo. It references project-specific artifacts (`.claude/prd/PRD.md`, `.claude/pi/PI.md`) so some coupling to the project conventions is expected.
- **Later:** Extract to a standalone repo and publish to marketplace. The skill SKILL.md files would reference conventions (artifact paths) that are documented but configurable via plugin settings (`.claude/sdlc.local.md`).

### Risk 6: No Plugin Settings for Project-Specific Config

**Problem:** The SDLC suite assumes specific artifact paths (`.claude/prd/PRD.md`, `.claude/pi/PI.md`). If used across projects, these may differ.

**Mitigation:** The plugin settings pattern supports per-project configuration via `.claude/sdlc.local.md` with YAML frontmatter. This can store:
```yaml
---
prd_path: .claude/prd/PRD.md
pi_path: .claude/pi/PI.md
drafts_path: .claude/drafts/
retros_path: .claude/retros/
---
```

Skills read this at runtime. Not needed for v1 (single project), but architecturally clean for future portability.

---

## 6. Recommended Approach

### Phase 1: Build as In-Repo Plugin (Now)

1. Create `.claude/sdlc-plugin/` with full plugin structure
2. Write all 7 skills with reference files following the v2 design spec
3. Test with `--plugin-dir .claude/sdlc-plugin`
4. Remove v1 SDLC skills from `.claude/skills/`
5. Update CLAUDE.md with launch instructions
6. Add launch alias to make `--plugin-dir` convenient

### Phase 2: Cross-Project Portability (Later)

1. Extract to standalone repo (e.g., `github.com/raul/claude-sdlc`)
2. Add plugin settings pattern for configurable paths
3. Publish to Claude Code marketplace
4. Install globally via `/plugin install sdlc`
5. Remove `--plugin-dir` dependency

### Implementation Priority

The plugin structure is a container, not a blocker. The hard work is writing the 7 SKILL.md files and their reference documents. The plugin manifest (`plugin.json`) is trivial to add. Therefore:

1. Write SKILL.md files and reference docs (the bulk of the work)
2. Wrap in plugin structure (add `.claude-plugin/plugin.json`)
3. Test and iterate

---

## 7. Quick Reference: Plugin Anatomy

```
sdlc/                                    # Plugin root
├── .claude-plugin/
│   └── plugin.json                      # {"name": "sdlc"}
├── skills/                              # Auto-discovered
│   ├── define/                          # → sdlc:define
│   │   ├── SKILL.md                     # Core instructions
│   │   └── reference/                   # Loaded on demand
│   │       ├── prd-guide.md
│   │       ├── pi-guide.md
│   │       ├── epic-guide.md
│   │       ├── feature-guide.md
│   │       └── story-guide.md
│   ├── create/                          # → sdlc:create
│   │   ├── SKILL.md
│   │   └── reference/
│   ├── update/                          # → sdlc:update
│   │   ├── SKILL.md
│   │   └── reference/
│   ├── status/                          # → sdlc:status
│   │   └── SKILL.md
│   ├── reconcile/                       # → sdlc:reconcile
│   │   └── SKILL.md
│   ├── retro/                           # → sdlc:retro
│   │   └── SKILL.md
│   └── capture/                         # → sdlc:capture
│       └── SKILL.md
├── agents/                              # Optional subagents
│   └── codebase-explorer.md
└── README.md                            # Usage documentation
```

**To use:** `claude --plugin-dir .claude/sdlc-plugin`

**Skills appear as:** `/define (plugin:sdlc)`, `/create (plugin:sdlc)`, etc. in `/help`

**Cross-skill references:** `sdlc:define`, `sdlc:create`, etc.

---

## Sources

All findings based on reading the following installed plugin skills and reference files:

- `plugin-dev` plugin — 7 skills: plugin-structure, skill-development, command-development, agent-development, hook-development, mcp-integration, plugin-settings
- `plugin-dev` reference files — manifest-reference.md, component-patterns.md, plugin-features-reference.md
- `superpowers` plugin — writing-skills skill, plugin.json (namespacing example)
- `example-plugin` — plugin.json, example-skill, example-command (format examples)
- `feature-dev` plugin — plugin.json, agents/, commands/ (real-world structure)
- `claude-code-setup` plugin — plugins-reference.md, skills-reference.md
- `installed_plugins.json` — installation and caching mechanism
- `claude --help` output — `--plugin-dir` flag documentation
- `stripe` external plugin — real-world plugin with skills and commands
