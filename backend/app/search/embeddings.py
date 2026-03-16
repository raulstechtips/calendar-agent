"""Embedding pipeline for calendar context ingestion."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

import httpx
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from langchain_openai import AzureOpenAIEmbeddings
from openai import (
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
    RateLimitError,
)

from app.core.config import settings
from app.search.service import delete_documents, upsert_documents

logger = logging.getLogger(__name__)

_embeddings_client: AzureOpenAIEmbeddings | None = None
_credential: DefaultAzureCredential | None = None


def get_embeddings_client() -> AzureOpenAIEmbeddings:
    """Return the singleton AzureOpenAIEmbeddings, creating on first call."""
    global _embeddings_client, _credential
    if _embeddings_client is None:
        if not settings.azure_openai_endpoint:
            raise RuntimeError(
                "AZURE_OPENAI_ENDPOINT is not configured — "
                "cannot create embeddings client"
            )
        _credential = DefaultAzureCredential(
            managed_identity_client_id=settings.azure_managed_identity_client_id
            or None,
        )
        token_provider = get_bearer_token_provider(
            _credential, "https://cognitiveservices.azure.com/.default"
        )
        _embeddings_client = AzureOpenAIEmbeddings(
            azure_endpoint=settings.azure_openai_endpoint,
            azure_ad_token_provider=token_provider,
            deployment=settings.azure_openai_embed_deployment,  # pyright: ignore[reportCallIssue]
            openai_api_version=settings.azure_openai_api_version,  # pyright: ignore[reportCallIssue]
        )
    return _embeddings_client


def close_embeddings_client() -> None:
    """Close the singleton embeddings client and credential."""
    global _embeddings_client, _credential
    if _credential is not None:
        _credential.close()
        _credential = None
    _embeddings_client = None


def reset_embeddings_client() -> None:
    """Clear the singleton without closing. For test isolation only."""
    global _embeddings_client, _credential
    _embeddings_client = None
    _credential = None


def _validate_user_id(user_id: str) -> None:
    """Raise ValueError if user_id is empty."""
    if not user_id:
        raise ValueError("user_id must not be empty")


def _utc_now() -> datetime:
    """Return the current UTC datetime. Extracted for test mocking."""
    return datetime.now(UTC)


def format_event_text(event: dict[str, Any]) -> str:
    """Convert a Google Calendar event dict into embeddable text.

    Produces a structured text with title, time, location, attendees,
    and description. Omits lines for absent/empty fields.
    """
    lines: list[str] = []

    title = event.get("summary", "(untitled)")
    lines.append(f"Title: {title}")

    start = event.get("start", {})
    end = event.get("end", {})
    start_time = start.get("dateTime") or start.get("date", "")
    end_time = end.get("dateTime") or end.get("date", "")
    if start_time:
        lines.append(f"When: {start_time} to {end_time}")

    location = event.get("location")
    if location:
        lines.append(f"Location: {location}")

    attendees = event.get("attendees")
    if attendees:
        emails = ", ".join(a.get("email", "") for a in attendees if a.get("email"))
        if emails:
            lines.append(f"Attendees: {emails}")

    description = event.get("description")
    if description:
        lines.append(f"Description: {description}")

    text = "\n".join(lines)
    max_len = settings.embedding_max_text_length
    if len(text) > max_len:
        text = text[:max_len]
    return text


def build_search_document(
    event: dict[str, Any], content: str, embedding: list[float]
) -> dict[str, Any]:
    """Build a search index document from a calendar event and its embedding."""
    event_id: str = event["id"]
    start = event.get("start", {})
    timestamp = start.get("dateTime") or start.get("date", "")

    return {
        "id": event_id,
        "content": content,
        "embedding": embedding,
        "source_type": "event",
        "source_id": event_id,
        "timestamp": timestamp,
        "last_modified": _utc_now().isoformat(),
    }


_RETRYABLE_ERRORS = (
    RateLimitError,
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
)


def _parse_retry_after(exc: BaseException, *, fallback: float) -> float:
    """Extract Retry-After header from an API error, or return fallback."""
    import contextlib

    response = getattr(exc, "response", None)
    if response is not None:
        header = getattr(response, "headers", {}).get("retry-after")
        if header is not None:
            with contextlib.suppress(ValueError, TypeError):
                return float(header)
    return fallback


async def _embed_with_retry(
    client: AzureOpenAIEmbeddings,
    texts: list[str],
    user_id: str,
    batch_num: int,
    total_batches: int,
) -> list[list[float]]:
    """Embed texts with exponential backoff retry on transient errors."""
    delay = settings.embedding_retry_initial_delay
    for attempt in range(1, settings.embedding_max_retries + 1):
        try:
            return await client.aembed_documents(texts)
        except _RETRYABLE_ERRORS as exc:
            # Don't retry permanent config errors (e.g., missing endpoint URL)
            if isinstance(exc.__cause__, httpx.UnsupportedProtocol):
                raise
            if attempt == settings.embedding_max_retries:
                logger.error(
                    "Batch %d/%d: max retries exhausted for user %s",
                    batch_num,
                    total_batches,
                    user_id,
                )
                raise
            # Respect Retry-After header when present
            wait = _parse_retry_after(exc, fallback=delay)
            logger.warning(
                "Batch %d/%d: %s (attempt %d/%d), retrying in %.1fs for user %s",
                batch_num,
                total_batches,
                type(exc).__name__,
                attempt,
                settings.embedding_max_retries,
                wait,
                user_id,
            )
            await asyncio.sleep(wait)
            delay *= 2
    raise RuntimeError("unreachable")


async def process_events(user_id: str, events: list[dict[str, Any]]) -> list[str]:
    """Embed calendar events in batches and upsert to the search index.

    Handles both creates and updates — upsert semantics overwrite
    existing documents with the same source_id.

    Returns list of document IDs that were successfully upserted.
    """
    _validate_user_id(user_id)
    if not events:
        return []

    batch_size = settings.embedding_batch_size
    client = get_embeddings_client()
    all_ids: list[str] = []
    total_batches = -(-len(events) // batch_size)

    for i in range(0, len(events), batch_size):
        batch_events = events[i : i + batch_size]
        batch_num = i // batch_size + 1

        texts = [format_event_text(event) for event in batch_events]
        embeddings = await _embed_with_retry(
            client, texts, user_id, batch_num, total_batches
        )

        documents = [
            build_search_document(event, text, embedding)
            for event, text, embedding in zip(
                batch_events, texts, embeddings, strict=True
            )
        ]

        ids = await upsert_documents(user_id, documents)
        all_ids.extend(ids)

        if len(ids) < len(batch_events):
            logger.warning(
                "Batch %d/%d: %d/%d upserts failed for user %s",
                batch_num,
                total_batches,
                len(batch_events) - len(ids),
                len(batch_events),
                user_id,
            )

        logger.info(
            "Batch %d/%d: embedded %d events for user %s",
            batch_num,
            total_batches,
            len(batch_events),
            user_id,
        )

        if batch_num < total_batches:
            await asyncio.sleep(settings.embedding_batch_delay)

    return all_ids


async def delete_events(user_id: str, source_ids: list[str]) -> list[str]:
    """Remove events from the search index by source ID.

    Returns list of document IDs that were successfully deleted.
    """
    _validate_user_id(user_id)
    if not source_ids:
        return []

    return await delete_documents(user_id, source_ids)
