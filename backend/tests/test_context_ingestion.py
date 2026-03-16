"""Tests for the context ingestion orchestrator."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest


def _make_event(
    *,
    event_id: str = "evt-1",
    summary: str = "Test Event",
) -> dict[str, Any]:
    return {
        "id": event_id,
        "summary": summary,
        "start": {"dateTime": "2026-03-16T09:00:00-04:00"},
        "end": {"dateTime": "2026-03-16T09:30:00-04:00"},
    }


class TestIngestEvents:
    @patch("app.context_ingestion.service.delete_events", new_callable=AsyncMock)
    @patch("app.context_ingestion.service.process_events", new_callable=AsyncMock)
    async def test_should_process_created_events(
        self, mock_process: AsyncMock, mock_delete: AsyncMock
    ) -> None:
        from app.context_ingestion.service import ingest_events

        events = [_make_event(event_id="evt-1")]
        mock_process.return_value = ["evt-1"]

        await ingest_events(user_id="user-123", created=events)

        mock_process.assert_awaited_once()
        call_args = mock_process.call_args
        assert call_args.kwargs["user_id"] == "user-123"
        assert len(call_args.kwargs["events"]) == 1

    @patch("app.context_ingestion.service.delete_events", new_callable=AsyncMock)
    @patch("app.context_ingestion.service.process_events", new_callable=AsyncMock)
    async def test_should_process_updated_events(
        self, mock_process: AsyncMock, mock_delete: AsyncMock
    ) -> None:
        from app.context_ingestion.service import ingest_events

        events = [_make_event(event_id="evt-2")]
        mock_process.return_value = ["evt-2"]

        await ingest_events(user_id="user-123", updated=events)

        mock_process.assert_awaited_once()
        call_args = mock_process.call_args
        assert len(call_args.kwargs["events"]) == 1

    @patch("app.context_ingestion.service.delete_events", new_callable=AsyncMock)
    @patch("app.context_ingestion.service.process_events", new_callable=AsyncMock)
    async def test_should_combine_created_and_updated_for_processing(
        self, mock_process: AsyncMock, mock_delete: AsyncMock
    ) -> None:
        from app.context_ingestion.service import ingest_events

        created = [_make_event(event_id="evt-1")]
        updated = [_make_event(event_id="evt-2")]
        mock_process.return_value = ["evt-1", "evt-2"]

        await ingest_events(user_id="user-123", created=created, updated=updated)

        mock_process.assert_awaited_once()
        call_args = mock_process.call_args
        assert len(call_args.kwargs["events"]) == 2

    @patch("app.context_ingestion.service.delete_events", new_callable=AsyncMock)
    @patch("app.context_ingestion.service.process_events", new_callable=AsyncMock)
    async def test_should_delete_events_by_source_ids(
        self, mock_process: AsyncMock, mock_delete: AsyncMock
    ) -> None:
        from app.context_ingestion.service import ingest_events

        mock_delete.return_value = ["evt-3"]

        await ingest_events(user_id="user-123", deleted_ids=["evt-3"])

        mock_delete.assert_awaited_once_with(user_id="user-123", source_ids=["evt-3"])
        mock_process.assert_not_awaited()

    @patch("app.context_ingestion.service.delete_events", new_callable=AsyncMock)
    @patch("app.context_ingestion.service.process_events", new_callable=AsyncMock)
    async def test_should_handle_mixed_creates_updates_deletes(
        self, mock_process: AsyncMock, mock_delete: AsyncMock
    ) -> None:
        from app.context_ingestion.service import ingest_events

        created = [_make_event(event_id="evt-1")]
        updated = [_make_event(event_id="evt-2")]
        deleted_ids = ["evt-3"]
        mock_process.return_value = ["evt-1", "evt-2"]
        mock_delete.return_value = ["evt-3"]

        await ingest_events(
            user_id="user-123",
            created=created,
            updated=updated,
            deleted_ids=deleted_ids,
        )

        mock_process.assert_awaited_once()
        mock_delete.assert_awaited_once()

    async def test_should_reject_empty_user_id(self) -> None:
        from app.context_ingestion.service import ingest_events

        with pytest.raises(ValueError, match="user_id"):
            await ingest_events(user_id="", created=[_make_event()])

    @patch("app.context_ingestion.service.delete_events", new_callable=AsyncMock)
    @patch("app.context_ingestion.service.process_events", new_callable=AsyncMock)
    async def test_should_handle_all_none_inputs(
        self, mock_process: AsyncMock, mock_delete: AsyncMock
    ) -> None:
        from app.context_ingestion.service import ingest_events

        await ingest_events(user_id="user-123")

        mock_process.assert_not_awaited()
        mock_delete.assert_not_awaited()
