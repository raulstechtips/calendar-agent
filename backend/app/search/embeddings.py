"""Embedding pipeline for calendar context ingestion."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from langchain_openai import AzureOpenAIEmbeddings

from app.core.config import settings
from app.search.service import delete_documents, upsert_documents

logger = logging.getLogger(__name__)

_embeddings_client: AzureOpenAIEmbeddings | None = None
_credential: DefaultAzureCredential | None = None


def get_embeddings_client() -> AzureOpenAIEmbeddings:
    """Return the singleton AzureOpenAIEmbeddings, creating on first call."""
    global _embeddings_client, _credential
    if _embeddings_client is None:
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

    return "\n".join(lines)


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


async def process_events(user_id: str, events: list[dict[str, Any]]) -> list[str]:
    """Embed calendar events and upsert to the search index.

    Handles both creates and updates — upsert semantics overwrite
    existing documents with the same source_id.

    Returns list of document IDs that were successfully upserted.
    """
    _validate_user_id(user_id)
    if not events:
        return []

    texts = [format_event_text(event) for event in events]
    client = get_embeddings_client()
    embeddings = await client.aembed_documents(texts)

    documents = [
        build_search_document(event, text, embedding)
        for event, text, embedding in zip(events, texts, embeddings, strict=True)
    ]

    return await upsert_documents(user_id, documents)


async def delete_events(user_id: str, source_ids: list[str]) -> list[str]:
    """Remove events from the search index by source ID.

    Returns list of document IDs that were successfully deleted.
    """
    _validate_user_id(user_id)
    if not source_ids:
        return []

    return await delete_documents(user_id, source_ids)
