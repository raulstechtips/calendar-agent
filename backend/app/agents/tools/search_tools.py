"""Azure AI Search retrieval tool for the LangGraph ReAct agent."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Annotated, Any

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from app.search.embeddings import get_embeddings_client
from app.search.service import search

logger = logging.getLogger(__name__)

_DECAY_RATE = 0.05


def _parse_datetime(value: str | None) -> datetime | None:
    """Parse an ISO 8601 datetime string, returning None on failure."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt
    except (ValueError, TypeError):
        return None


def _compute_recency_factor(
    timestamp: str | None, last_modified: str | None
) -> float:
    """Compute a recency factor between 0 and 1 using hyperbolic decay.

    Uses the more recent of timestamp and last_modified so that
    recently-updated old events still get a boost.
    """
    ts = _parse_datetime(timestamp)
    lm = _parse_datetime(last_modified)

    candidates = [d for d in (ts, lm) if d is not None]
    if not candidates:
        return 1.0 / (1.0 + 365 * _DECAY_RATE)

    most_recent = max(candidates)
    age_days = max((datetime.now(UTC) - most_recent).total_seconds() / 86400, 0.0)
    return 1.0 / (1.0 + age_days * _DECAY_RATE)


def _rerank_by_recency(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Re-rank search results by combining relevance score with recency."""

    def combined_score(result: dict[str, Any]) -> float:
        search_score = float(result.get("@search.score", 1.0))
        recency = _compute_recency_factor(
            result.get("timestamp"), result.get("last_modified")
        )
        return search_score * recency

    return sorted(results, key=combined_score, reverse=True)


def _format_results(results: list[dict[str, Any]]) -> str:
    """Format search results as structured text for LLM consumption."""
    if not results:
        return "No relevant context found."

    blocks: list[str] = []
    for i, result in enumerate(results, start=1):
        lines: list[str] = [f"--- Result {i} ---"]
        content = result.get("content", "")
        if content:
            lines.append(content)
        timestamp = result.get("timestamp")
        if timestamp:
            lines.append(f"When: {timestamp}")
        blocks.append("\n".join(lines))

    return "\n\n".join(blocks)


@tool(parse_docstring=True)
async def search_context(
    query: str,
    user_id: Annotated[str, InjectedState("user_id")],
    top: int = 5,
) -> str:
    """Search the user's calendar history for relevant context.

    Use this tool when the user asks about past events, recurring patterns,
    people they have met with, or any question requiring historical calendar
    data. Do NOT use this for real-time schedule lookups in a specific date
    range — use search_events for that instead.

    Args:
        query: Natural language search query describing what to find.
        top: Maximum number of results to return (default 5).
    """
    top = max(1, min(top, 20))

    try:
        client = get_embeddings_client()
        query_vector = await client.aembed_query(query)
    except Exception as e:
        logger.warning("Failed to embed search query: %s", e)
        return "Search failed — could not process query."

    try:
        results = await search(
            user_id=user_id,
            query_text=query,
            query_vector=query_vector,
            source_type="event",
            top=top,
        )
    except Exception as e:
        logger.warning("Search query failed: %s", e)
        return "Search failed — could not retrieve results."

    if not results:
        return "No relevant context found in calendar history."

    reranked = _rerank_by_recency(results)
    return _format_results(reranked)


search_tools: list[Any] = [search_context]
