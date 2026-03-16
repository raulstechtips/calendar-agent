"""Azure AI Search service wrapper with mandatory user_id filtering."""

from __future__ import annotations

import logging
from typing import Any

from azure.identity.aio import DefaultAzureCredential
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import VectorizedQuery, VectorQuery

from app.core.config import settings

logger = logging.getLogger(__name__)

_search_client: SearchClient | None = None
_credential: DefaultAzureCredential | None = None


def get_search_client() -> SearchClient:
    """Return the singleton async SearchClient, creating on first call."""
    global _search_client, _credential
    if _search_client is None:
        _credential = DefaultAzureCredential(
            managed_identity_client_id=settings.azure_managed_identity_client_id
            or None,
        )
        _search_client = SearchClient(
            endpoint=settings.azure_search_endpoint,
            index_name=settings.azure_search_index,
            credential=_credential,
        )
    return _search_client


async def close_search_client() -> None:
    """Close the singleton SearchClient and credential. Called during app shutdown."""
    global _search_client, _credential
    if _search_client is not None:
        await _search_client.close()
        _search_client = None
    if _credential is not None:
        await _credential.close()
        _credential = None


def reset_search_client() -> None:
    """Clear the singleton without closing. For test isolation only."""
    global _search_client, _credential
    _search_client = None
    _credential = None


def _validate_user_id(user_id: str) -> None:
    """Raise ValueError if user_id is empty."""
    if not user_id:
        raise ValueError("user_id must not be empty")


def _escape_odata_string(value: str) -> str:
    """Escape single quotes for OData filter strings."""
    return value.replace("'", "''")


async def search(
    user_id: str,
    query_text: str,
    query_vector: list[float] | None = None,
    source_type: str | None = None,
    top: int = 5,
) -> list[dict[str, Any]]:
    """Hybrid search (BM25 + vector) with mandatory user_id filtering.

    Args:
        user_id: Required. All queries are scoped to this user.
        query_text: Text query for BM25 matching.
        query_vector: Optional embedding vector for vector search.
        source_type: Optional filter by source type (event, email, contact).
        top: Maximum number of results to return.

    Raises:
        ValueError: If user_id is empty.
        Exception: Propagates Azure SDK errors to the caller.
    """
    _validate_user_id(user_id)

    filter_expression = f"user_id eq '{_escape_odata_string(user_id)}'"
    if source_type:
        filter_expression += (
            f" and source_type eq '{_escape_odata_string(source_type)}'"
        )

    vector_queries: list[VectorQuery] | None = None
    if query_vector is not None:
        vector_queries = [
            VectorizedQuery(
                vector=query_vector,
                k_nearest_neighbors=top,
                fields="embedding",
            )
        ]

    client = get_search_client()
    results = await client.search(
        search_text=query_text,
        filter=filter_expression,
        vector_queries=vector_queries,
        top=top,
    )
    return [dict(result) async for result in results]


async def upsert_documents(user_id: str, documents: list[dict[str, Any]]) -> list[str]:
    """Upsert documents into the search index with user_id enforcement.

    Each document must include 'id', 'content', 'embedding', 'source_type',
    'source_id', 'timestamp', 'last_modified'. The user_id field is set
    automatically from the parameter — never from document data.

    Returns list of document keys that succeeded.
    """
    _validate_user_id(user_id)

    docs_with_user = [{**doc, "user_id": user_id} for doc in documents]

    client = get_search_client()
    results = await client.merge_or_upload_documents(docs_with_user)
    return [r.key for r in results if r.succeeded and r.key is not None]


async def delete_documents(user_id: str, document_ids: list[str]) -> list[str]:
    """Delete documents from the index by ID.

    Returns list of document keys that were deleted.
    """
    _validate_user_id(user_id)

    client = get_search_client()
    docs_to_delete = [{"id": doc_id} for doc_id in document_ids]
    results = await client.delete_documents(docs_to_delete)
    return [r.key for r in results if r.succeeded and r.key is not None]
