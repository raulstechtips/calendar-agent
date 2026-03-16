"""Tests for the context ingestion orchestrator and sync pipeline."""

from __future__ import annotations

import asyncio
import time
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.context_ingestion.sync import (
    SyncMetadata,
    SyncTokenInvalidError,
    _fetch_all_events,  # pyright: ignore[reportPrivateUsage]
)


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


# ---------------------------------------------------------------------------
# SyncMetadata Redis helpers
# ---------------------------------------------------------------------------


class TestSyncMetadata:
    async def test_should_return_none_when_no_metadata(self) -> None:
        from app.context_ingestion.sync import get_sync_metadata

        mock_redis = AsyncMock()
        mock_redis.hgetall.return_value = {}

        with patch("app.context_ingestion.sync.get_redis", return_value=mock_redis):
            result = await get_sync_metadata("user-123")

        assert result is None
        mock_redis.hgetall.assert_awaited_once_with("sync_metadata:user-123:calendar")

    async def test_should_return_metadata_when_exists(self) -> None:
        from app.context_ingestion.sync import get_sync_metadata

        mock_redis = AsyncMock()
        mock_redis.hgetall.return_value = {
            "sync_token": "some-sync-token",
            "last_ingested_at": "1710000000",
        }

        with patch("app.context_ingestion.sync.get_redis", return_value=mock_redis):
            result = await get_sync_metadata("user-123")

        assert result is not None
        assert result.sync_token == "some-sync-token"
        assert result.last_ingested_at == 1710000000

    async def test_should_store_metadata_in_redis(self) -> None:
        from app.context_ingestion.sync import store_sync_metadata

        mock_redis = AsyncMock()
        metadata = SyncMetadata(sync_token="tok-abc", last_ingested_at=1710000000)

        with patch("app.context_ingestion.sync.get_redis", return_value=mock_redis):
            await store_sync_metadata("user-123", metadata)

        mock_redis.hset.assert_awaited_once()
        call_args = mock_redis.hset.call_args
        assert call_args.kwargs["name"] == "sync_metadata:user-123:calendar"
        mapping = call_args.kwargs["mapping"]
        assert mapping["sync_token"] == "tok-abc"
        assert mapping["last_ingested_at"] == 1710000000

    async def test_should_treat_empty_sync_token_as_no_metadata(self) -> None:
        from app.context_ingestion.sync import get_sync_metadata

        mock_redis = AsyncMock()
        mock_redis.hgetall.return_value = {
            "sync_token": "",
            "last_ingested_at": "1710000000",
        }

        with patch("app.context_ingestion.sync.get_redis", return_value=mock_redis):
            result = await get_sync_metadata("user-123")

        # Returns metadata but sync_token is empty — caller checks emptiness
        assert result is not None
        assert result.sync_token == ""


# ---------------------------------------------------------------------------
# _fetch_all_events — paginated Google Calendar fetcher
# ---------------------------------------------------------------------------


def _mock_events_list(
    events: list[dict[str, Any]],
    next_page_token: str | None = None,
    next_sync_token: str | None = None,
) -> dict[str, Any]:
    response: dict[str, Any] = {"items": events}
    if next_page_token:
        response["nextPageToken"] = next_page_token
    if next_sync_token:
        response["nextSyncToken"] = next_sync_token
    return response


class TestFetchAllEvents:
    async def test_should_fetch_single_page(self) -> None:

        events = [_make_event(event_id="evt-1")]
        mock_service = MagicMock()
        mock_service.events.return_value.list.return_value.execute.return_value = (
            _mock_events_list(events, next_sync_token="sync-tok-1")
        )

        result_events, sync_token = await _fetch_all_events(
            mock_service,
            time_min="2025-09-01T00:00:00Z",
            time_max="2026-06-01T00:00:00Z",
        )

        assert len(result_events) == 1
        assert result_events[0]["id"] == "evt-1"
        assert sync_token == "sync-tok-1"

    async def test_should_paginate_multiple_pages(self) -> None:

        page1 = _mock_events_list(
            [_make_event(event_id="evt-1")],
            next_page_token="page-2-token",
        )
        page2 = _mock_events_list(
            [_make_event(event_id="evt-2")],
            next_sync_token="sync-tok-final",
        )

        mock_service = MagicMock()
        mock_service.events.return_value.list.return_value.execute.side_effect = [
            page1,
            page2,
        ]

        result_events, sync_token = await _fetch_all_events(
            mock_service,
            time_min="2025-09-01T00:00:00Z",
            time_max="2026-06-01T00:00:00Z",
        )

        assert len(result_events) == 2
        assert result_events[0]["id"] == "evt-1"
        assert result_events[1]["id"] == "evt-2"
        assert sync_token == "sync-tok-final"

    async def test_should_raise_sync_token_invalid_on_410(self) -> None:
        from googleapiclient.errors import HttpError

        mock_resp = MagicMock()
        mock_resp.status = 410
        mock_resp.reason = "Gone"
        http_error = HttpError(mock_resp, b"Resource has been deleted")

        mock_service = MagicMock()
        mock_service.events.return_value.list.return_value.execute.side_effect = (
            http_error
        )

        with pytest.raises(SyncTokenInvalidError):
            await _fetch_all_events(mock_service, sync_token="stale-token")

    async def test_should_pass_sync_token_without_time_filters(self) -> None:

        mock_service = MagicMock()
        mock_service.events.return_value.list.return_value.execute.return_value = (
            _mock_events_list([], next_sync_token="new-token")
        )

        await _fetch_all_events(mock_service, sync_token="old-token")

        list_call = mock_service.events.return_value.list
        call_kwargs = list_call.call_args.kwargs
        assert call_kwargs.get("syncToken") == "old-token"
        assert "timeMin" not in call_kwargs
        assert "timeMax" not in call_kwargs


# ---------------------------------------------------------------------------
# full_ingest
# ---------------------------------------------------------------------------


class TestFullIngest:
    @patch("app.context_ingestion.sync.store_sync_metadata", new_callable=AsyncMock)
    @patch("app.context_ingestion.sync.ingest_events", new_callable=AsyncMock)
    @patch("app.context_ingestion.sync._fetch_all_events", new_callable=AsyncMock)
    @patch("app.context_ingestion.sync._get_calendar_service", new_callable=AsyncMock)
    async def test_should_call_ingest_events_with_fetched_events(
        self,
        mock_service: AsyncMock,
        mock_fetch: AsyncMock,
        mock_ingest: AsyncMock,
        mock_store_meta: AsyncMock,
    ) -> None:
        from app.context_ingestion.sync import full_ingest

        events = [_make_event(event_id="evt-1"), _make_event(event_id="evt-2")]
        mock_fetch.return_value = (events, "sync-tok-1")

        await full_ingest("user-123")

        mock_ingest.assert_awaited_once()
        call_kwargs = mock_ingest.call_args.kwargs
        assert call_kwargs["user_id"] == "user-123"
        assert len(call_kwargs["created"]) == 2

    @patch("app.context_ingestion.sync.store_sync_metadata", new_callable=AsyncMock)
    @patch("app.context_ingestion.sync.ingest_events", new_callable=AsyncMock)
    @patch("app.context_ingestion.sync._fetch_all_events", new_callable=AsyncMock)
    @patch("app.context_ingestion.sync._get_calendar_service", new_callable=AsyncMock)
    async def test_should_store_metadata_before_ingest(
        self,
        mock_service: AsyncMock,
        mock_fetch: AsyncMock,
        mock_ingest: AsyncMock,
        mock_store_meta: AsyncMock,
    ) -> None:
        from app.context_ingestion.sync import full_ingest

        call_order: list[str] = []

        def track_store(*a: Any, **kw: Any) -> None:
            call_order.append("store")

        def track_ingest(*a: Any, **kw: Any) -> None:
            call_order.append("ingest")

        mock_store_meta.side_effect = track_store
        mock_ingest.side_effect = track_ingest
        mock_fetch.return_value = ([], "sync-tok-new")

        await full_ingest("user-123")

        mock_store_meta.assert_awaited_once()
        call_args = mock_store_meta.call_args
        assert call_args[0][0] == "user-123"
        metadata: SyncMetadata = call_args[0][1]
        assert metadata.sync_token == "sync-tok-new"
        assert metadata.last_ingested_at > 0
        assert call_order == ["store", "ingest"]

    @patch("app.context_ingestion.sync.store_sync_metadata", new_callable=AsyncMock)
    @patch("app.context_ingestion.sync.ingest_events", new_callable=AsyncMock)
    @patch("app.context_ingestion.sync._fetch_all_events", new_callable=AsyncMock)
    @patch("app.context_ingestion.sync._get_calendar_service", new_callable=AsyncMock)
    async def test_should_store_metadata_even_when_ingest_fails(
        self,
        mock_service: AsyncMock,
        mock_fetch: AsyncMock,
        mock_ingest: AsyncMock,
        mock_store_meta: AsyncMock,
    ) -> None:
        from app.context_ingestion.sync import full_ingest

        mock_fetch.return_value = ([_make_event()], "sync-tok-new")
        mock_ingest.side_effect = RuntimeError("rate limit exceeded")

        with pytest.raises(RuntimeError, match="rate limit exceeded"):
            await full_ingest("user-123")

        mock_store_meta.assert_awaited_once()
        metadata: SyncMetadata = mock_store_meta.call_args[0][1]
        assert metadata.sync_token == "sync-tok-new"

    @patch("app.context_ingestion.sync.store_sync_metadata", new_callable=AsyncMock)
    @patch("app.context_ingestion.sync.ingest_events", new_callable=AsyncMock)
    @patch("app.context_ingestion.sync._fetch_all_events", new_callable=AsyncMock)
    @patch("app.context_ingestion.sync._get_calendar_service", new_callable=AsyncMock)
    async def test_should_fetch_with_time_window(
        self,
        mock_service: AsyncMock,
        mock_fetch: AsyncMock,
        mock_ingest: AsyncMock,
        mock_store_meta: AsyncMock,
    ) -> None:
        from app.context_ingestion.sync import full_ingest

        mock_fetch.return_value = ([], "tok")

        await full_ingest("user-123")

        mock_fetch.assert_awaited_once()
        call_kwargs = mock_fetch.call_args.kwargs
        assert "time_min" in call_kwargs
        assert "time_max" in call_kwargs
        # time_min should be roughly 6 months ago, time_max ~3 months ahead
        assert call_kwargs["time_min"] < call_kwargs["time_max"]

    @patch("app.context_ingestion.sync.store_sync_metadata", new_callable=AsyncMock)
    @patch("app.context_ingestion.sync.ingest_events", new_callable=AsyncMock)
    @patch("app.context_ingestion.sync._fetch_all_events", new_callable=AsyncMock)
    @patch("app.context_ingestion.sync._get_calendar_service", new_callable=AsyncMock)
    async def test_should_handle_empty_calendar(
        self,
        mock_service: AsyncMock,
        mock_fetch: AsyncMock,
        mock_ingest: AsyncMock,
        mock_store_meta: AsyncMock,
    ) -> None:
        from app.context_ingestion.sync import full_ingest

        mock_fetch.return_value = ([], "sync-tok-empty")

        await full_ingest("user-123")

        mock_ingest.assert_awaited_once()
        assert mock_ingest.call_args.kwargs["created"] == []
        mock_store_meta.assert_awaited_once()


# ---------------------------------------------------------------------------
# delta_sync
# ---------------------------------------------------------------------------


class TestDeltaSync:
    @patch("app.context_ingestion.sync.store_sync_metadata", new_callable=AsyncMock)
    @patch("app.context_ingestion.sync.ingest_events", new_callable=AsyncMock)
    @patch("app.context_ingestion.sync._fetch_all_events", new_callable=AsyncMock)
    @patch("app.context_ingestion.sync._get_calendar_service", new_callable=AsyncMock)
    async def test_should_classify_cancelled_as_deletes(
        self,
        mock_service: AsyncMock,
        mock_fetch: AsyncMock,
        mock_ingest: AsyncMock,
        mock_store_meta: AsyncMock,
    ) -> None:
        from app.context_ingestion.sync import delta_sync

        cancelled = {"id": "evt-del", "status": "cancelled"}
        mock_fetch.return_value = ([cancelled], "new-sync-tok")
        metadata = SyncMetadata(sync_token="old-tok", last_ingested_at=1710000000)

        await delta_sync("user-123", metadata)

        mock_ingest.assert_awaited_once()
        call_kwargs = mock_ingest.call_args.kwargs
        assert call_kwargs["deleted_ids"] == ["evt-del"]
        assert call_kwargs.get("updated") == []

    @patch("app.context_ingestion.sync.store_sync_metadata", new_callable=AsyncMock)
    @patch("app.context_ingestion.sync.ingest_events", new_callable=AsyncMock)
    @patch("app.context_ingestion.sync._fetch_all_events", new_callable=AsyncMock)
    @patch("app.context_ingestion.sync._get_calendar_service", new_callable=AsyncMock)
    async def test_should_classify_active_as_updates(
        self,
        mock_service: AsyncMock,
        mock_fetch: AsyncMock,
        mock_ingest: AsyncMock,
        mock_store_meta: AsyncMock,
    ) -> None:
        from app.context_ingestion.sync import delta_sync

        active = _make_event(event_id="evt-upd")
        mock_fetch.return_value = ([active], "new-sync-tok")
        metadata = SyncMetadata(sync_token="old-tok", last_ingested_at=1710000000)

        await delta_sync("user-123", metadata)

        mock_ingest.assert_awaited_once()
        call_kwargs = mock_ingest.call_args.kwargs
        assert len(call_kwargs["updated"]) == 1
        assert call_kwargs["updated"][0]["id"] == "evt-upd"
        assert call_kwargs["deleted_ids"] == []

    @patch("app.context_ingestion.sync.store_sync_metadata", new_callable=AsyncMock)
    @patch("app.context_ingestion.sync.ingest_events", new_callable=AsyncMock)
    @patch("app.context_ingestion.sync._fetch_all_events", new_callable=AsyncMock)
    @patch("app.context_ingestion.sync._get_calendar_service", new_callable=AsyncMock)
    async def test_should_handle_mixed_updates_and_deletes(
        self,
        mock_service: AsyncMock,
        mock_fetch: AsyncMock,
        mock_ingest: AsyncMock,
        mock_store_meta: AsyncMock,
    ) -> None:
        from app.context_ingestion.sync import delta_sync

        events = [
            _make_event(event_id="evt-1"),
            {"id": "evt-2", "status": "cancelled"},
            _make_event(event_id="evt-3"),
        ]
        mock_fetch.return_value = (events, "new-tok")
        metadata = SyncMetadata(sync_token="old-tok", last_ingested_at=1710000000)

        await delta_sync("user-123", metadata)

        call_kwargs = mock_ingest.call_args.kwargs
        assert len(call_kwargs["updated"]) == 2
        assert call_kwargs["deleted_ids"] == ["evt-2"]

    @patch("app.context_ingestion.sync.full_ingest", new_callable=AsyncMock)
    @patch("app.context_ingestion.sync.store_sync_metadata", new_callable=AsyncMock)
    @patch("app.context_ingestion.sync.ingest_events", new_callable=AsyncMock)
    @patch("app.context_ingestion.sync._fetch_all_events", new_callable=AsyncMock)
    @patch("app.context_ingestion.sync._get_calendar_service", new_callable=AsyncMock)
    async def test_should_fallback_to_full_ingest_on_sync_token_invalid(
        self,
        mock_service: AsyncMock,
        mock_fetch: AsyncMock,
        mock_ingest: AsyncMock,
        mock_store_meta: AsyncMock,
        mock_full_ingest: AsyncMock,
    ) -> None:
        from app.context_ingestion.sync import delta_sync

        mock_fetch.side_effect = SyncTokenInvalidError("token expired")
        metadata = SyncMetadata(sync_token="stale-tok", last_ingested_at=1710000000)

        await delta_sync("user-123", metadata)

        mock_full_ingest.assert_awaited_once_with("user-123")
        mock_ingest.assert_not_awaited()

    @patch("app.context_ingestion.sync.store_sync_metadata", new_callable=AsyncMock)
    @patch("app.context_ingestion.sync.ingest_events", new_callable=AsyncMock)
    @patch("app.context_ingestion.sync._fetch_all_events", new_callable=AsyncMock)
    @patch("app.context_ingestion.sync._get_calendar_service", new_callable=AsyncMock)
    async def test_should_store_new_sync_token_before_ingest(
        self,
        mock_service: AsyncMock,
        mock_fetch: AsyncMock,
        mock_ingest: AsyncMock,
        mock_store_meta: AsyncMock,
    ) -> None:
        from app.context_ingestion.sync import delta_sync

        call_order: list[str] = []

        def track_store(*a: Any, **kw: Any) -> None:
            call_order.append("store")

        def track_ingest(*a: Any, **kw: Any) -> None:
            call_order.append("ingest")

        mock_store_meta.side_effect = track_store
        mock_ingest.side_effect = track_ingest
        mock_fetch.return_value = ([], "brand-new-tok")
        metadata = SyncMetadata(sync_token="old-tok", last_ingested_at=1710000000)

        await delta_sync("user-123", metadata)

        mock_store_meta.assert_awaited_once()
        stored: SyncMetadata = mock_store_meta.call_args[0][1]
        assert stored.sync_token == "brand-new-tok"
        assert stored.last_ingested_at > 0
        assert call_order == ["store", "ingest"]

    @patch("app.context_ingestion.sync.store_sync_metadata", new_callable=AsyncMock)
    @patch("app.context_ingestion.sync.ingest_events", new_callable=AsyncMock)
    @patch("app.context_ingestion.sync._fetch_all_events", new_callable=AsyncMock)
    @patch("app.context_ingestion.sync._get_calendar_service", new_callable=AsyncMock)
    async def test_should_store_metadata_even_when_ingest_fails(
        self,
        mock_service: AsyncMock,
        mock_fetch: AsyncMock,
        mock_ingest: AsyncMock,
        mock_store_meta: AsyncMock,
    ) -> None:
        from app.context_ingestion.sync import delta_sync

        mock_fetch.return_value = ([_make_event()], "new-tok")
        mock_ingest.side_effect = RuntimeError("rate limit exceeded")
        metadata = SyncMetadata(sync_token="old-tok", last_ingested_at=1710000000)

        with pytest.raises(RuntimeError, match="rate limit exceeded"):
            await delta_sync("user-123", metadata)

        mock_store_meta.assert_awaited_once()
        stored: SyncMetadata = mock_store_meta.call_args[0][1]
        assert stored.sync_token == "new-tok"


# ---------------------------------------------------------------------------
# run_ingestion — BackgroundTask wrapper
# ---------------------------------------------------------------------------


class TestRunIngestion:
    @patch("app.context_ingestion.tasks.full_ingest", new_callable=AsyncMock)
    @patch("app.context_ingestion.tasks.get_sync_metadata", new_callable=AsyncMock)
    async def test_should_full_ingest_when_no_metadata(
        self, mock_get_meta: AsyncMock, mock_full: AsyncMock
    ) -> None:
        from app.context_ingestion.tasks import run_ingestion

        mock_get_meta.return_value = None

        await run_ingestion("user-123")

        mock_full.assert_awaited_once_with("user-123")

    @patch("app.context_ingestion.tasks.full_ingest", new_callable=AsyncMock)
    @patch("app.context_ingestion.tasks.get_sync_metadata", new_callable=AsyncMock)
    async def test_should_full_ingest_when_no_sync_token(
        self, mock_get_meta: AsyncMock, mock_full: AsyncMock
    ) -> None:
        from app.context_ingestion.tasks import run_ingestion

        mock_get_meta.return_value = SyncMetadata(sync_token="", last_ingested_at=0)

        await run_ingestion("user-123")

        mock_full.assert_awaited_once_with("user-123")

    @patch("app.context_ingestion.tasks.delta_sync", new_callable=AsyncMock)
    @patch("app.context_ingestion.tasks.full_ingest", new_callable=AsyncMock)
    @patch("app.context_ingestion.tasks.get_sync_metadata", new_callable=AsyncMock)
    async def test_should_skip_when_within_cooldown(
        self,
        mock_get_meta: AsyncMock,
        mock_full: AsyncMock,
        mock_delta: AsyncMock,
    ) -> None:
        from app.context_ingestion.tasks import run_ingestion

        mock_get_meta.return_value = SyncMetadata(
            sync_token="valid-tok", last_ingested_at=int(time.time()) - 600
        )

        await run_ingestion("user-123")

        mock_full.assert_not_awaited()
        mock_delta.assert_not_awaited()

    @patch("app.context_ingestion.tasks.delta_sync", new_callable=AsyncMock)
    @patch("app.context_ingestion.tasks.get_sync_metadata", new_callable=AsyncMock)
    async def test_should_delta_sync_after_cooldown(
        self, mock_get_meta: AsyncMock, mock_delta: AsyncMock
    ) -> None:
        from app.context_ingestion.tasks import run_ingestion

        metadata = SyncMetadata(
            sync_token="valid-tok", last_ingested_at=int(time.time()) - 7200
        )
        mock_get_meta.return_value = metadata

        await run_ingestion("user-123")

        mock_delta.assert_awaited_once_with("user-123", metadata)

    @patch("app.context_ingestion.tasks.full_ingest", new_callable=AsyncMock)
    @patch("app.context_ingestion.tasks.get_sync_metadata", new_callable=AsyncMock)
    async def test_should_not_raise_on_failure(
        self, mock_get_meta: AsyncMock, mock_full: AsyncMock
    ) -> None:
        from app.context_ingestion.tasks import run_ingestion

        mock_get_meta.return_value = None
        mock_full.side_effect = RuntimeError("service unavailable")

        # Should not raise — errors are logged and swallowed
        await run_ingestion("user-123")

    @patch("app.context_ingestion.tasks.full_ingest", new_callable=AsyncMock)
    @patch("app.context_ingestion.tasks.get_sync_metadata", new_callable=AsyncMock)
    async def test_should_propagate_cancelled_error(
        self, mock_get_meta: AsyncMock, mock_full: AsyncMock
    ) -> None:
        from app.context_ingestion.tasks import run_ingestion

        mock_get_meta.return_value = None
        mock_full.side_effect = asyncio.CancelledError()

        with pytest.raises(asyncio.CancelledError):
            await run_ingestion("user-123")
