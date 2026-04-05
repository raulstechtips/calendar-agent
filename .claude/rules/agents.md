---
description: LangGraph agent conventions — graph design, state, tools, HITL, testing
paths:
  - "backend/app/agents/**"
---

# Agent Rules

## Architecture

- Prefer thin, single-responsibility nodes — smaller nodes checkpoint more often, meaning less re-execution on failure and better observability
- Guard nodes (input/output validation) belong in a wrapper StateGraph around the core agent — separates security from business logic and makes agent implementations swappable
- Use constants or enums for conditional edge route strings — typos in string literals cause silent misroutes
- Subgraphs are for team isolation and reusable components — linear or single-team workflows stay flat
- Treat nodes as pure functions (state in, state out) — avoid mutating shared objects or relying on module-level variables within nodes
- Make tool invocations explicit ToolNode calls, not hidden inside LLM nodes — explicit nodes give better observability and replay semantics

## State Management

- Use TypedDict with Annotated reducers for graph state — Pydantic BaseModel fights LangGraph's incremental update model and only validates on first node input
- Apply reducers sparingly — only on concurrent-write fields (messages, accumulated lists). Single-writer fields don't need one
- Keep state workflow-critical: user_id, messages, pending confirmations. Transient computation values belong in node-local scope — state pollution bloats checkpoints
- When adding state fields, prefer optional fields with defaults — maintains backwards compatibility with existing checkpoints
- MemorySaver is for development only — production requires a persistent checkpointer (PostgresSaver, Redis) that survives restarts
- Call checkpointer.setup() at application startup — PostgresSaver and Redis require table/index creation before first use

## Tool Patterns

- Tool docstrings are LLM-facing contracts — the model reads them to decide when and how to call. Write from its perspective: purpose, usage criteria, parameter semantics
- Use InjectedState for internal fields (user_id, credentials) the LLM should never see — eliminates hallucinated-parameter errors
- Each tool should have one clear purpose — ambiguous multi-purpose tools cause wrong selection. Prefer specific tools (`search_events`, `create_event`) over generic ones
- Return structured error messages from tools instead of raising raw exceptions — the LLM can reason about a clear message but not a traceback
- Use enum types or Literal for constrained tool parameters — free-form strings invite hallucinated values
- When a tool wraps a sync SDK via run_in_executor, guard it with asyncio.wait_for() — unguarded executor calls block the graph indefinitely

## Error Recovery

- ToolNode's handle_tool_errors converts exceptions to ToolMessage replies — the graph continues. RetryPolicy triggers only on graph-level errors (serialization, network), not caught tool errors
- Distinguish temporary failures from permanent ones: timeouts and rate-limits deserve retries, but invalid input or missing permissions never recovers — fail fast
- Never swallow errors in tools (bare except/pass) — return structured messages so the LLM can adapt or inform the user
- If an external service fails persistently, break the retry loop — return "service unavailable" rather than burning retries and API costs
- Attach RetryPolicy for transient infrastructure errors only (connection resets, DNS) — never retry business logic failures or LLM refusals

## Human-in-the-Loop

- Command(resume=value) restarts the entire node — code before interrupt() re-executes. Put side effects AFTER resume, not before
- Never wrap interrupt() in try/except — it raises an internal exception to halt execution. Catching it breaks HITL silently
- Keep approval-required tools in dedicated nodes — never mix auto-execute and approval tools in one node. Auto-execute tools fire again on resume (double-execution bug)
- When parallel tool calls each interrupt, assign unique IDs — default IDs from parallel calls collide, mixing up resume values
- HITL should be reactive, not ubiquitous — interrupt only for write operations and high-stakes decisions. Over-interrupting defeats the agent's purpose

## Testing

- Test at three tiers: (1) unit-test node functions directly, (2) flow-path tests with MemorySaver for routing and transitions, (3) end-to-end with the compiled graph
- Mock LLM responses for deterministic tests — test routing decisions, state updates, and tool calls, not the model's text
- Test interrupt/resume explicitly: update_state(as_node=...) to position, invoke with interrupt_after, resume with Command(resume=...), assert final state
- Fresh graph instance and fresh checkpointer per test — shared state causes flaky failures from checkpoint pollution
- Test guard nodes for both blocked and pass-through paths — a guard that always blocks or always passes is equivalent to no guard
