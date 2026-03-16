"""Tests for Azure AI Search retrieval tool."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from pydantic import BaseModel

from app.agents.tools.search_tools import (
    _compute_recency_factor,  # pyright: ignore[reportPrivateUsage]
    _format_results,  # pyright: ignore[reportPrivateUsage]
    _rerank_by_recency,  # pyright: ignore[reportPrivateUsage]
    search_context,
    search_tools,
)


class TestComputeRecencyFactor:
    def test_should_return_high_factor_for_recent_timestamp(self) -> None:
        now = datetime.now(UTC).isoformat()
        factor = _compute_recency_factor(now, None)
        assert factor > 0.9

    def test_should_return_low_factor_for_old_timestamp(self) -> None:
        old = (datetime.now(UTC) - timedelta(days=180)).isoformat()
        factor = _compute_recency_factor(old, None)
        assert factor < 0.15

    def test_should_use_last_modified_when_more_recent(self) -> None:
        old_timestamp = (datetime.now(UTC) - timedelta(days=180)).isoformat()
        recent_modified = datetime.now(UTC).isoformat()
        factor = _compute_recency_factor(old_timestamp, recent_modified)
        assert factor > 0.9

    def test_should_return_low_factor_for_missing_values(self) -> None:
        factor = _compute_recency_factor(None, None)
        assert factor < 0.15


class TestRerankByRecency:
    def test_should_boost_recent_results_higher(self) -> None:
        now = datetime.now(UTC)
        results = [
            {
                "@search.score": 1.0,
                "content": "old event",
                "timestamp": (now - timedelta(days=90)).isoformat(),
                "last_modified": None,
            },
            {
                "@search.score": 1.0,
                "content": "recent event",
                "timestamp": now.isoformat(),
                "last_modified": None,
            },
        ]
        reranked = _rerank_by_recency(results)
        assert reranked[0]["content"] == "recent event"
        assert reranked[1]["content"] == "old event"

    def test_should_not_eliminate_relevant_old_results(self) -> None:
        now = datetime.now(UTC)
        results = [
            {
                "@search.score": 5.0,
                "content": "very relevant old",
                "timestamp": (now - timedelta(days=60)).isoformat(),
                "last_modified": None,
            },
            {
                "@search.score": 1.0,
                "content": "less relevant new",
                "timestamp": now.isoformat(),
                "last_modified": None,
            },
        ]
        reranked = _rerank_by_recency(results)
        # Old result with 5x relevance should still rank above new result
        assert reranked[0]["content"] == "very relevant old"

    def test_should_default_search_score_when_missing(self) -> None:
        now = datetime.now(UTC)
        results = [
            {
                "content": "no score",
                "timestamp": now.isoformat(),
                "last_modified": None,
            },
        ]
        reranked = _rerank_by_recency(results)
        assert len(reranked) == 1
        assert reranked[0]["content"] == "no score"


class TestFormatResults:
    def test_should_format_single_result(self) -> None:
        results = [
            {
                "content": "Team standup with Engineering",
                "timestamp": "2026-03-15T09:00:00Z",
            }
        ]
        formatted = _format_results(results)
        assert "Team standup with Engineering" in formatted
        assert "2026-03-15" in formatted

    def test_should_separate_multiple_results(self) -> None:
        results = [
            {
                "content": "Event A",
                "timestamp": "2026-03-15T09:00:00Z",
            },
            {
                "content": "Event B",
                "timestamp": "2026-03-14T10:00:00Z",
            },
        ]
        formatted = _format_results(results)
        assert "Event A" in formatted
        assert "Event B" in formatted
        assert "--- Result 1 ---" in formatted
        assert "--- Result 2 ---" in formatted

    def test_should_handle_results_with_missing_fields(self) -> None:
        results: list[dict[str, Any]] = [{"content": "Minimal event"}]
        formatted = _format_results(results)
        assert "Minimal event" in formatted


class TestSearchContext:
    @patch("app.agents.tools.search_tools.search")
    @patch("app.agents.tools.search_tools.get_embeddings_client")
    async def test_should_embed_query_and_call_search(
        self,
        mock_get_embed: MagicMock,
        mock_search: AsyncMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.aembed_query = AsyncMock(return_value=[0.1] * 1536)
        mock_get_embed.return_value = mock_client

        mock_search.return_value = [
            {
                "@search.score": 1.0,
                "content": "Meeting with Alice",
                "timestamp": "2026-03-15T09:00:00Z",
                "source_type": "event",
                "last_modified": None,
            }
        ]

        result = await search_context.ainvoke(
            {"query": "meeting with Alice", "user_id": "user-123"}
        )

        mock_client.aembed_query.assert_awaited_once_with("meeting with Alice")
        mock_search.assert_awaited_once()
        call_kwargs = mock_search.call_args.kwargs
        assert call_kwargs["user_id"] == "user-123"
        assert call_kwargs["query_vector"] == [0.1] * 1536
        assert call_kwargs["source_type"] == "event"
        assert isinstance(result, str)
        assert "Meeting with Alice" in result

    @patch("app.agents.tools.search_tools.search")
    @patch("app.agents.tools.search_tools.get_embeddings_client")
    async def test_should_return_no_context_message_when_empty(
        self,
        mock_get_embed: MagicMock,
        mock_search: AsyncMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.aembed_query = AsyncMock(return_value=[0.1] * 1536)
        mock_get_embed.return_value = mock_client
        mock_search.return_value = []

        result = await search_context.ainvoke(
            {"query": "nonexistent", "user_id": "user-123"}
        )

        assert "no relevant context" in result.lower()

    @patch("app.agents.tools.search_tools.search")
    @patch("app.agents.tools.search_tools.get_embeddings_client")
    async def test_should_handle_embedding_error_gracefully(
        self,
        mock_get_embed: MagicMock,
        mock_search: AsyncMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.aembed_query = AsyncMock(side_effect=RuntimeError("API down"))
        mock_get_embed.return_value = mock_client

        result = await search_context.ainvoke({"query": "test", "user_id": "user-123"})

        assert isinstance(result, str)
        assert "search failed" in result.lower()
        # Should NOT leak raw exception details
        assert "API down" not in result

    @patch("app.agents.tools.search_tools.search")
    @patch("app.agents.tools.search_tools.get_embeddings_client")
    async def test_should_handle_search_error_gracefully(
        self,
        mock_get_embed: MagicMock,
        mock_search: AsyncMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.aembed_query = AsyncMock(return_value=[0.1] * 1536)
        mock_get_embed.return_value = mock_client
        mock_search.side_effect = RuntimeError("Search service down")

        result = await search_context.ainvoke({"query": "test", "user_id": "user-123"})

        assert isinstance(result, str)
        assert "search failed" in result.lower()
        # Should NOT leak raw exception details
        assert "Search service down" not in result

    @patch("app.agents.tools.search_tools.search")
    @patch("app.agents.tools.search_tools.get_embeddings_client")
    async def test_should_respect_top_parameter(
        self,
        mock_get_embed: MagicMock,
        mock_search: AsyncMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.aembed_query = AsyncMock(return_value=[0.1] * 1536)
        mock_get_embed.return_value = mock_client
        mock_search.return_value = []

        await search_context.ainvoke(
            {"query": "test", "top": 10, "user_id": "user-123"}
        )

        call_kwargs = mock_search.call_args.kwargs
        assert call_kwargs["top"] == 10

    @patch("app.agents.tools.search_tools.search")
    @patch("app.agents.tools.search_tools.get_embeddings_client")
    async def test_should_clamp_top_to_minimum_of_1(
        self,
        mock_get_embed: MagicMock,
        mock_search: AsyncMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.aembed_query = AsyncMock(return_value=[0.1] * 1536)
        mock_get_embed.return_value = mock_client
        mock_search.return_value = []

        await search_context.ainvoke({"query": "test", "top": 0, "user_id": "user-123"})

        assert mock_search.call_args.kwargs["top"] == 1

    @patch("app.agents.tools.search_tools.search")
    @patch("app.agents.tools.search_tools.get_embeddings_client")
    async def test_should_clamp_top_to_maximum_of_20(
        self,
        mock_get_embed: MagicMock,
        mock_search: AsyncMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.aembed_query = AsyncMock(return_value=[0.1] * 1536)
        mock_get_embed.return_value = mock_client
        mock_search.return_value = []

        await search_context.ainvoke(
            {"query": "test", "top": 100, "user_id": "user-123"}
        )

        assert mock_search.call_args.kwargs["top"] == 20


class TestSearchToolsExport:
    def test_search_tools_list_contains_search_context(self) -> None:
        assert len(search_tools) == 1
        assert search_tools[0] is search_context

    def test_search_context_has_injected_user_id(self) -> None:
        # tool_call_schema is the LLM-facing schema (InjectedState excluded)
        tool_schema = search_context.tool_call_schema
        assert isinstance(tool_schema, type) and issubclass(tool_schema, BaseModel)
        schema = tool_schema.model_json_schema()
        assert "user_id" not in schema.get("properties", {})
        assert "query" in schema.get("properties", {})
        assert "top" in schema.get("properties", {})
