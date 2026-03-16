"""Context ingestion orchestrator.

Routes create/update/delete signals to the embedding pipeline.
"""

from __future__ import annotations

import logging
from typing import Any

from app.search.embeddings import delete_events, process_events

logger = logging.getLogger(__name__)


async def ingest_events(
    user_id: str,
    *,
    created: list[dict[str, Any]] | None = None,
    updated: list[dict[str, Any]] | None = None,
    deleted_ids: list[str] | None = None,
) -> None:
    """Route create/update/delete signals from delta sync to the embedding pipeline.

    Args:
        user_id: Google user ID — required for all operations.
        created: New calendar events to embed and index.
        updated: Modified events to re-embed and upsert (overwrites existing).
        deleted_ids: Source IDs of events removed from Google Calendar.
    """
    if not user_id:
        raise ValueError("user_id must not be empty")

    events_to_process = (created or []) + (updated or [])
    ids_to_delete = deleted_ids or []

    if events_to_process:
        upserted = await process_events(user_id=user_id, events=events_to_process)
        logger.info(
            "Embedded and upserted %d documents for user %s",
            len(upserted),
            user_id,
        )

    if ids_to_delete:
        deleted = await delete_events(user_id=user_id, source_ids=ids_to_delete)
        logger.info(
            "Deleted %d documents for user %s",
            len(deleted),
            user_id,
        )
