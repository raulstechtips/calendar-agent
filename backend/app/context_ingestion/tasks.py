"""Background task wrappers for context ingestion.

Entry point for FastAPI BackgroundTasks — decides between full ingest
and delta sync, respects cooldown, and suppresses all errors so the
login flow is never blocked.
"""

from __future__ import annotations

import logging
import time

from app.context_ingestion.sync import (
    delta_sync,
    full_ingest,
    get_sync_metadata,
)

logger = logging.getLogger(__name__)

_COOLDOWN_SECONDS = 3600  # 1 hour


async def run_ingestion(user_id: str) -> None:
    """Decide between full ingest and delta sync, respecting cooldown.

    Intended to be called as a FastAPI BackgroundTask. All errors are caught
    and logged — this function never raises.
    """
    try:
        metadata = await get_sync_metadata(user_id)

        if metadata is None or not metadata.sync_token:
            logger.info("Starting full ingest for user %s", user_id)
            await full_ingest(user_id)
            return

        now = int(time.time())
        elapsed = now - metadata.last_ingested_at
        if elapsed < _COOLDOWN_SECONDS:
            logger.info(
                "Skipping sync for user %s — cooldown active (last sync %ds ago)",
                user_id,
                elapsed,
            )
            return

        logger.info("Starting delta sync for user %s", user_id)
        await delta_sync(user_id, metadata)

    except Exception:
        logger.exception("Background ingestion failed for user %s", user_id)
