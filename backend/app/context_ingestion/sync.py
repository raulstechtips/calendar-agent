"""Google Calendar sync engine with syncToken-based delta sync.

Manages full ingestion (6 months back, 3 months forward) and incremental
delta sync using Google Calendar's syncToken API. Sync metadata (syncToken,
last_ingested_at) is stored in Redis.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import UTC, datetime, timedelta
from typing import Any

from googleapiclient.errors import HttpError
from pydantic import BaseModel

from app.context_ingestion.service import ingest_events
from app.core.redis import get_redis

logger = logging.getLogger(__name__)

_PAST_WINDOW_DAYS = 183  # ~6 months
_FUTURE_WINDOW_DAYS = 91  # ~3 months


class SyncMetadata(BaseModel):
    sync_token: str = ""
    last_ingested_at: int = 0


class SyncTokenInvalidError(Exception):
    """Raised when Google returns 410 Gone for an invalidated syncToken."""


# ---------------------------------------------------------------------------
# Redis metadata helpers
# ---------------------------------------------------------------------------


def _sync_metadata_key(user_id: str) -> str:
    return f"sync_metadata:{user_id}:calendar"


async def get_sync_metadata(user_id: str) -> SyncMetadata | None:
    """Retrieve sync metadata from Redis. Returns None if no metadata exists."""
    redis = get_redis()
    data: dict[str, str] = await redis.hgetall(_sync_metadata_key(user_id))  # type: ignore[misc]
    if not data:
        return None
    return SyncMetadata(
        sync_token=data.get("sync_token", ""),
        last_ingested_at=int(data.get("last_ingested_at", "0")),
    )


async def store_sync_metadata(user_id: str, metadata: SyncMetadata) -> None:
    """Persist sync metadata to Redis (no TTL — lives as long as user has tokens)."""
    redis = get_redis()
    await redis.hset(  # type: ignore[misc]
        name=_sync_metadata_key(user_id),
        mapping={
            "sync_token": metadata.sync_token,
            "last_ingested_at": metadata.last_ingested_at,
        },
    )


# ---------------------------------------------------------------------------
# Google Calendar service builder
# ---------------------------------------------------------------------------


async def _get_calendar_service(user_id: str) -> Any:
    """Build a Google Calendar API service for the given user.

    Reuses credential handling from the shared google_credentials module
    to avoid duplicating token refresh logic. Raises RuntimeError on failure.
    """
    from app.auth.google_credentials import build_calendar_service

    service = await build_calendar_service(user_id)
    if isinstance(service, str):
        raise RuntimeError(service)
    return service


# ---------------------------------------------------------------------------
# Paginated event fetcher
# ---------------------------------------------------------------------------


async def _fetch_all_events(
    service: Any,
    *,
    time_min: str | None = None,
    time_max: str | None = None,
    sync_token: str | None = None,
) -> tuple[list[dict[str, Any]], str]:
    """Fetch all events from Google Calendar, handling pagination.

    Pass time_min/time_max for full ingest, or sync_token for delta sync.
    Returns (events, nextSyncToken).

    Raises:
        SyncTokenInvalidError: If Google returns 410 Gone (stale syncToken).
    """
    loop = asyncio.get_running_loop()
    all_events: list[dict[str, Any]] = []
    page_token: str | None = None
    next_sync_token: str = ""

    while True:
        kwargs: dict[str, Any] = {"calendarId": "primary"}

        if sync_token:
            kwargs["syncToken"] = sync_token
        else:
            if time_min:
                kwargs["timeMin"] = time_min
            if time_max:
                kwargs["timeMax"] = time_max
            kwargs["singleEvents"] = True

        if page_token:
            kwargs["pageToken"] = page_token

        def _execute_list(
            svc: Any = service, kw: dict[str, Any] = kwargs
        ) -> dict[str, Any]:
            return svc.events().list(**kw).execute()  # type: ignore[no-any-return]

        try:
            result: dict[str, Any] = await loop.run_in_executor(None, _execute_list)
        except HttpError as e:
            if e.resp.status == 410:
                raise SyncTokenInvalidError(
                    "syncToken invalidated by Google (410 Gone)"
                ) from e
            raise

        all_events.extend(result.get("items", []))

        page_token = result.get("nextPageToken")
        if not page_token:
            next_sync_token = result.get("nextSyncToken", "")
            break

    return all_events, next_sync_token


# ---------------------------------------------------------------------------
# Core sync functions
# ---------------------------------------------------------------------------


async def full_ingest(user_id: str) -> None:
    """Perform a full calendar event ingest (6 months back, 3 months forward).

    Fetches all events in the time window, embeds them, upserts to the search
    index, and stores the sync metadata in Redis.
    """
    service = await _get_calendar_service(user_id)

    now = datetime.now(UTC)
    time_min = (now - timedelta(days=_PAST_WINDOW_DAYS)).isoformat()
    time_max = (now + timedelta(days=_FUTURE_WINDOW_DAYS)).isoformat()

    events, sync_token = await _fetch_all_events(
        service, time_min=time_min, time_max=time_max
    )

    # Store metadata first so partial failures don't cause full re-ingest loops
    await store_sync_metadata(
        user_id,
        SyncMetadata(sync_token=sync_token, last_ingested_at=int(time.time())),
    )

    await ingest_events(user_id=user_id, created=events)

    logger.info(
        "Full ingest complete for user %s: %d events ingested",
        user_id,
        len(events),
    )


async def delta_sync(user_id: str, metadata: SyncMetadata) -> None:
    """Perform an incremental sync using the stored Google Calendar syncToken.

    Classifies returned events as updated or deleted and routes them
    to the ingestion service. Falls back to full_ingest if the syncToken
    is invalidated by Google (410 Gone).
    """
    service = await _get_calendar_service(user_id)

    try:
        events, new_sync_token = await _fetch_all_events(
            service, sync_token=metadata.sync_token
        )
    except SyncTokenInvalidError:
        logger.warning(
            "syncToken invalidated for user %s — falling back to full ingest",
            user_id,
        )
        await full_ingest(user_id)
        return

    updated: list[dict[str, Any]] = []
    deleted_ids: list[str] = []

    for event in events:
        if event.get("status") == "cancelled":
            deleted_ids.append(event["id"])
        else:
            updated.append(event)

    # Store metadata first so partial failures don't cause full re-ingest loops
    await store_sync_metadata(
        user_id,
        SyncMetadata(sync_token=new_sync_token, last_ingested_at=int(time.time())),
    )

    await ingest_events(user_id=user_id, updated=updated, deleted_ids=deleted_ids)

    logger.info(
        "Delta sync complete for user %s: %d updated, %d deleted",
        user_id,
        len(updated),
        len(deleted_ids),
    )
