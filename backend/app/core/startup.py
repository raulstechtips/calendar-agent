"""Pre-start tasks that run once before uvicorn workers spawn."""

import asyncio
import logging

from app.search.index import create_index

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_INITIAL_DELAY = 30.0


async def ensure_search_index() -> None:
    """Create the search index with retry/backoff for MI sidecar readiness.

    The Azure managed identity sidecar may take several seconds to become
    available on cold start.  Retries up to 3 times (30s, 60s) before
    raising — if it still fails, the process should not start.
    """
    delay = _INITIAL_DELAY
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            await create_index()
            logger.info("Search index ready")
            return
        except Exception:
            if attempt == _MAX_RETRIES:
                logger.exception(
                    "Search index creation failed after %d attempts",
                    _MAX_RETRIES,
                )
                raise
            logger.warning(
                "Search index creation attempt %d/%d failed, "
                "retrying in %ds",
                attempt,
                _MAX_RETRIES,
                int(delay),
                exc_info=True,
            )
            await asyncio.sleep(delay)
            delay *= 2


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(ensure_search_index())
