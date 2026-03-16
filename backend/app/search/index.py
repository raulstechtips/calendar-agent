"""Azure AI Search index schema definition and creation."""

from azure.identity.aio import DefaultAzureCredential
from azure.search.documents.indexes.aio import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)

from app.core.config import settings


def build_index_schema() -> SearchIndex:
    """Build the calendar-context SearchIndex schema matching the SPEC."""
    fields = [
        SimpleField(
            name="id",
            type=SearchFieldDataType.String,
            key=True,
            filterable=True,
        ),
        SimpleField(
            name="user_id",
            type=SearchFieldDataType.String,
            filterable=True,
        ),
        SearchableField(
            name="content",
            type=SearchFieldDataType.String,
        ),
        SearchField(
            name="embedding",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=1536,
            vector_search_profile_name="default-vector-profile",
        ),
        SimpleField(
            name="source_type",
            type=SearchFieldDataType.String,
            filterable=True,
        ),
        SimpleField(
            name="source_id",
            type=SearchFieldDataType.String,
            filterable=True,
        ),
        SimpleField(
            name="timestamp",
            type=SearchFieldDataType.DateTimeOffset,
            filterable=True,
            sortable=True,
        ),
        SimpleField(
            name="last_modified",
            type=SearchFieldDataType.DateTimeOffset,
            filterable=True,
        ),
    ]

    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="default-hnsw")],
        profiles=[
            VectorSearchProfile(
                name="default-vector-profile",
                algorithm_configuration_name="default-hnsw",
            )
        ],
    )

    return SearchIndex(
        name=settings.azure_search_index,
        fields=fields,
        vector_search=vector_search,
    )


async def create_index() -> SearchIndex:
    """Create or update the calendar-context index using DefaultAzureCredential.

    Uses SearchIndexClient transiently — not a singleton. Safe to call
    multiple times (idempotent via create_or_update_index).
    """
    credential = DefaultAzureCredential(
        managed_identity_client_id=settings.azure_managed_identity_client_id or None,
    )
    async with SearchIndexClient(
        endpoint=settings.azure_search_endpoint,
        credential=credential,
    ) as client:
        index = build_index_schema()
        return await client.create_or_update_index(index)
