# Agent Rules Design Spec

## Context

Story #134 creates `.claude/rules/agents.md` — a best-practice-oriented rules file scoped to `backend/app/agents/**`. The AI agent (Claude Code) needs LangGraph-specific production guidance that it cannot infer from reading the codebase alone. Without this file, the agent will default to generic Python patterns and miss LangGraph-specific gotchas around state management, interrupt semantics, tool design, and error recovery.

This is part of Feature #130 (Rules & Workflow Overhaul) under Epic #126. The backend.md rewrite (#133) is already merged, so deduplication is finalized.

## Approach

**Best-Practice Backbone**: Include production best practices that represent the contract the codebase should maintain. Rules are forward-looking ("do this") not backward-looking ("we currently do this"). Every rule passes the RULES-GUIDE litmus test with the bar: "would the AI likely get this wrong on new code?"

## Deliverable

Single file: `.claude/rules/agents.md`
- 60-80 lines, 3-5 KB (~800-1200 tokens)
- Prose rules, no tables or code blocks
- 6 sections matching the story acceptance criteria

## Frontmatter

```yaml
description: LangGraph agent conventions — graph design, state, tools, HITL, testing
paths:
  - "backend/app/agents/**"
```

## Section Design

### Architecture (~4 rules)

Focus: graph structure decisions the AI could get wrong on new code.

1. **Thin nodes over monolithic** — each node gets its own checkpoint; smaller nodes = less re-execution on failure + better trace observability
2. **Guard-node wrapper pattern** — input/output validation in a wrapper StateGraph around the core agent; separates security from business logic
3. **Route constants** — use constants/enums for conditional edge strings; typos cause silent misroutes
4. **Subgraph discipline** — subgraphs for team isolation and reusable components only; linear/single-team workflows stay flat

### State Management (~4 rules)

Focus: LangGraph-specific state pitfalls the AI would hit using general Python intuition.

1. **TypedDict + Annotated reducers** (not Pydantic BaseModel) — Pydantic expects complete instances, fights incremental updates, validation only runs on first node
2. **Sparse reducers** — only on fields needing merge from concurrent nodes (messages, accumulated lists); single-writer fields don't need them
3. **Workflow-critical state only** — transient computation values stay in node-local scope; state pollution bloats checkpoints and creates stale-data bugs
4. **Persistent checkpointer for production** — MemorySaver is dev-only; production requires PostgresSaver or Redis

### Tool Patterns (~5 rules)

Focus: the LLM-facing contract model that distinguishes agent tools from regular functions.

1. **Docstrings as LLM contracts** — written from the model's perspective: purpose, when to use vs alternatives, parameter semantics
2. **InjectedState for internal fields** — user_id, credentials hidden from LLM; eliminates hallucinated-parameter errors
3. **Single-purpose tools** — ambiguous multi-purpose tools cause wrong tool selection
4. **Structured error returns** — clear error messages the LLM can reason about, never raw exceptions/tracebacks
5. **wait_for around run_in_executor** — agent-specific application of the general timeout rule; unguarded executor calls block the graph indefinitely

### Error Recovery (~4 rules)

Focus: LangGraph's two-layer error model (ToolNode vs RetryPolicy) and failure classification.

1. **ToolNode vs RetryPolicy distinction** — handle_tool_errors converts tool exceptions to ToolMessages (graph continues); RetryPolicy fires on graph-level errors only
2. **Temporary vs permanent failure classification** — timeouts/rate-limits retry; invalid input/missing permissions fail fast
3. **No swallowed errors** — structured error messages so the LLM can adapt; bare except/pass is forbidden
4. **Break persistent retry loops** — return "service unavailable" rather than burning retries and API costs

### Human-in-the-Loop (~4 rules)

Focus: interrupt() semantics and non-obvious production bugs. Highest-value section.

1. **Node restart on resume** — interrupt() persists state; Command(resume=value) restarts the entire node; side effects before interrupt re-execute
2. **Never try/except around interrupt** — interrupt raises an internal exception; catching it silently breaks HITL
3. **Dedicated approval nodes** — never mix auto-execute and approval-required tools; auto-execute tools fire again on resume (double-execution bug)
4. **Reactive, not ubiquitous** — interrupt only for write operations and high-stakes decisions; over-interrupting defeats the agent's purpose

### Testing (~4 rules)

Focus: agent-specific test patterns that complement tdd.md's general framework.

1. **Three-tier model** — (1) unit-test node functions directly, (2) flow-path tests with MemorySaver for routing/transitions, (3) end-to-end with full compiled graph
2. **Mock LLM responses** — test routing decisions, state updates, tool calls; never assert on raw LLM text
3. **Interrupt/resume test pattern** — update_state(as_node=...) to position, invoke with interrupt_after, resume with Command(resume=...), assert final state
4. **Fresh graph + checkpointer per test** — prevents checkpoint pollution and flaky cross-test failures

## Deduplication Verification

Rules explicitly excluded because they're covered elsewhere:

| Rule topic | Covered by |
|---|---|
| Explicit timeouts on external calls | backend.md (Async Patterns) |
| run_in_executor for sync SDKs | backend.md (Async Patterns) |
| AppError hierarchy, global exception handler | backend.md (Error Handling) |
| SSE terminal events, generator error handling | backend.md (SSE Streaming) |
| asyncio_mode="auto", httpx.AsyncClient, singleton reset | backend.md (Testing) |
| No abstraction layers with one implementation | code-quality.md (Over-engineering) |
| Every external call must have error handling | code-quality.md (Under-engineering) |
| Docstrings on framework-read code | code-quality.md (Documentation) |
| Never log secrets | code-quality.md (Security) |
| Red-Green-Refactor, test protection | tdd.md |
| Prompt engineering | PRD security constraints |
| Guardrails architecture | PRD 3-layer defense |

## Research Sources

Research was conducted via web search before writing, covering:
- LangChain official docs (Thinking in LangGraph, Graph API, Subgraphs, Persistence, Interrupts, Streaming, Test)
- LangChain blog (Building LangGraph from First Principles, LangGraph v0.2, Is LangGraph Used in Production?)
- Production case studies and community posts on error handling, HITL double-execution, parallel interrupt bugs
- Tool design patterns from Anthropic's SWE-bench agent development

## Verification

1. Line count: `wc -l .claude/rules/agents.md` — expect 60-80
2. File size: `wc -c .claude/rules/agents.md` — expect 3000-5000 bytes
3. No duplication: manually cross-check each rule against backend.md, code-quality.md, tdd.md
4. Litmus test: for each rule, confirm the AI would plausibly get it wrong without the rule
5. No Azure references: `grep -i azure .claude/rules/agents.md` — expect no matches
6. No code blocks: `grep '```' .claude/rules/agents.md` — expect no matches
7. Frontmatter paths: confirm `paths: backend/app/agents/**`
