# PRD Reference Guide

## Scope Assessment Criteria

| Signal | LIGHT | STANDARD | DEEP |
|--------|-------|----------|------|
| What's changing | Minor section update (tweak description, add a bullet) | New section or major revision of existing section | Full PRD from scratch (greenfield or complete rewrite) |
| Sections affected | 1 | 2-3 | All |
| Questions needed | 0-1 | 2-4 | 8-10 (full interview) |

## Greenfield / Brownfield Detection

Run this before scope assessment — the result affects the entire flow.

### Detection Logic

1. Check if `.claude/sdlc/prd/PRD.md` exists.
2. If **no PRD exists**, scan for codebase indicators:
   - `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `pom.xml`
   - `src/`, `app/`, `lib/`, `backend/`, `frontend/` directories
3. Classify:
   - **No PRD + no codebase** = GREENFIELD (building from nothing)
   - **No PRD + codebase exists** = BROWNFIELD (documenting what already exists)
   - **PRD exists** = RESHAPE (modifying an existing PRD)

### Greenfield Handling

Full interview (11 questions). The user is the sole source of information. Scope is always DEEP.

### Brownfield Handling

Before asking questions, dispatch a research subagent to scan the codebase:

```
Use Agent tool to scan the existing codebase.
Prompt: "Analyze this repository and report:
1. Tech stack (languages, frameworks, package managers — read package.json, pyproject.toml, etc.)
2. Directory structure (top-level layout, key directories)
3. Architecture patterns (monolith vs services, API framework, database ORM)
4. Data models (entity names, schemas, relationships)
5. API endpoints (routes, auth patterns)
6. Security patterns (auth mechanism, middleware, environment usage)
Do not modify any files."
```

Then present findings to the user and ask targeted questions about gaps only. This typically reduces the interview to 4-6 questions.

### Reshape Handling

Load the current PRD, identify what's changing, and scope accordingly (usually LIGHT or STANDARD).

## Question Templates

### Greenfield Interview (11 questions, one at a time)

1. **Project name and overview:** "What's the project called, and what does it do in one sentence?"
2. **Tech stack:** "What languages, frameworks, databases, and cloud provider will you use?"
3. **Architecture:** "What's the high-level architecture? (monolith, microservices, serverless, modular monolith, etc.)"
4. **Data models:** "What are the key entities and their relationships? (users, orders, products, etc.)"
5. **API contracts:** "What are the main API endpoints? What auth do they use? What do request/response shapes look like?"
6. **Security constraints:** "What auth mechanism? How sensitive is the data? Any compliance requirements? (GDPR, HIPAA, SOC2, etc.)"
7. **Roadmap:** "What's the build order? List features/capabilities in priority order."
8. **Acceptance criteria:** "What does 'done' look like for v1? What must work for you to consider it shipped?"
9. **Out of scope:** "What will we explicitly NOT build? (important to set boundaries early)"
10. **Decision log seed:** "Any decisions already made that we should capture? (tech choices, architectural bets, rejected alternatives)"
11. **Area labels:** "Based on the architecture, I'd propose these area labels for tracking work: [list derived from architecture answer]. Do these cover the major areas, or should we add/remove any?"

### Brownfield Questions (ask only about gaps after codebase scan)

- "I found [tech stack]. Is this complete, or are there services/tools I missed?"
- "The codebase has [entities]. Are there planned entities not yet implemented?"
- "I see [auth pattern]. Is this the intended long-term approach?"
- "What's the roadmap from here? What's built vs. what's planned?"
- "Any security or compliance requirements beyond what's in the code?"
- "What decisions have been made that aren't obvious from the code?"

### Reshape Questions (targeted to the change)

- "Which section needs updating and why?"
- "Has the tech stack, architecture, or scope changed?"
- "Any new decisions to capture?"

## Draft Body Template

```markdown
---
name: <project name>
version: 1.0
created: <YYYY-MM-DD>
status: draft
---

## Overview
[1-2 paragraphs: what the project is, who it's for, what problem it solves]

## Tech Stack
[bullet list: languages, frameworks, databases, cloud, key libraries]

## Architecture
[description of high-level architecture + key patterns (e.g., "Next.js frontend with FastAPI backend, communicating via REST API. LangGraph agents for AI workflows.")]

## Data Models
[key entities, their fields, and relationships — can be prose, table, or both]

## API Contracts
[endpoints, HTTP methods, auth requirements, request/response shapes — at the level of detail useful for implementation planning]

## Security Constraints
[auth mechanism, data sensitivity level, compliance requirements, encryption needs, access control model]

## Roadmap
[ordered priority list of what gets built and in what sequence]

## Acceptance Criteria
[what "done" means for v1 — concrete, testable checkboxes]

## Out of Scope
[explicit exclusions — things we will NOT build, at least not now]

## Label Taxonomy

### Areas
| Label | Description |
|-------|-------------|
| area:<name> | <one-line description of what this area covers> |

(Derive areas from the project's architecture. For brownfield projects, analyze the codebase directory structure and module boundaries. For greenfield, ask the user about the major areas/modules of the project.)

## Decision Log
| Date | Decision | Reason | Affects |
|------|----------|--------|---------|
| <YYYY-MM-DD> | <what was decided> | <why> | <which sections/areas> |
```
