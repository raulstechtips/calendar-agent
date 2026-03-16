"""Tests for Azure AI Search index schema, service, and config."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from azure.core.exceptions import HttpResponseError, ServiceRequestError

from app.search.index import build_index_schema


class TestBuildIndexSchema:
    def test_should_return_index_with_correct_name(self) -> None:
        index = build_index_schema()
        assert index.name == "calendar-context"

    def test_should_define_all_required_fields(self) -> None:
        index = build_index_schema()
        field_names = {f.name for f in index.fields}
        expected = {
            "id",
            "user_id",
            "content",
            "embedding",
            "source_type",
            "source_id",
            "timestamp",
            "last_modified",
        }
        assert field_names == expected

    def test_should_set_id_as_key_field(self) -> None:
        index = build_index_schema()
        id_field = next(f for f in index.fields if f.name == "id")
        assert id_field.key is True

    def test_should_set_user_id_as_filterable_not_searchable(self) -> None:
        index = build_index_schema()
        user_id_field = next(f for f in index.fields if f.name == "user_id")
        assert user_id_field.filterable is True
        assert not user_id_field.searchable

    def test_should_set_content_as_searchable(self) -> None:
        index = build_index_schema()
        content_field = next(f for f in index.fields if f.name == "content")
        assert content_field.searchable is True

    def test_should_configure_embedding_with_1536_dimensions(self) -> None:
        index = build_index_schema()
        embedding_field = next(f for f in index.fields if f.name == "embedding")
        assert embedding_field.vector_search_dimensions == 1536

    def test_should_configure_hnsw_vector_search(self) -> None:
        index = build_index_schema()
        vs = index.vector_search
        assert vs is not None
        assert vs.algorithms is not None
        assert len(vs.algorithms) == 1
        assert vs.algorithms[0].name == "default-hnsw"
        assert vs.profiles is not None
        assert len(vs.profiles) == 1
        assert vs.profiles[0].name == "default-vector-profile"

    def test_should_set_timestamp_as_filterable_and_sortable(self) -> None:
        index = build_index_schema()
        ts_field = next(f for f in index.fields if f.name == "timestamp")
        assert ts_field.filterable is True
        assert ts_field.sortable is True

    def test_should_set_last_modified_as_filterable(self) -> None:
        index = build_index_schema()
        lm_field = next(f for f in index.fields if f.name == "last_modified")
        assert lm_field.filterable is True

    def test_should_set_source_type_as_filterable(self) -> None:
        index = build_index_schema()
        st_field = next(f for f in index.fields if f.name == "source_type")
        assert st_field.filterable is True

    def test_should_set_source_id_as_filterable(self) -> None:
        index = build_index_schema()
        si_field = next(f for f in index.fields if f.name == "source_id")
        assert si_field.filterable is True

    def test_should_assign_vector_profile_to_embedding(self) -> None:
        index = build_index_schema()
        embedding_field = next(f for f in index.fields if f.name == "embedding")
        assert embedding_field.vector_search_profile_name == "default-vector-profile"


class TestConfigKeyRemoval:
    def test_settings_has_no_azure_search_key(self) -> None:
        from app.core.config import Settings

        assert "azure_search_key" not in Settings.model_fields

    def test_settings_has_no_azure_content_safety_key(self) -> None:
        from app.core.config import Settings

        assert "azure_content_safety_key" not in Settings.model_fields


class TestCreateIndex:
    @patch("app.search.index.SearchIndexClient")
    @patch("app.search.index.DefaultAzureCredential")
    async def test_should_call_create_or_update_index(
        self, mock_cred_cls: MagicMock, mock_client_cls: MagicMock
    ) -> None:
        from app.search.index import create_index

        mock_client = AsyncMock()
        mock_client.create_or_update_index = AsyncMock(
            return_value=build_index_schema()
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        mock_cred = AsyncMock()
        mock_cred_cls.return_value = mock_cred

        result = await create_index()

        mock_client.create_or_update_index.assert_awaited_once()
        assert result.name == "calendar-context"

    @patch("app.search.index.SearchIndexClient")
    @patch("app.search.index.DefaultAzureCredential")
    async def test_should_use_default_azure_credential(
        self, mock_cred_cls: MagicMock, mock_client_cls: MagicMock
    ) -> None:
        from app.search.index import create_index

        mock_client = AsyncMock()
        mock_client.create_or_update_index = AsyncMock(
            return_value=build_index_schema()
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        mock_cred = AsyncMock()
        mock_cred_cls.return_value = mock_cred

        await create_index()

        mock_cred_cls.assert_called_once()
        mock_client_cls.assert_called_once()
        # Verify credential was passed to client
        call_kwargs = mock_client_cls.call_args
        assert call_kwargs.kwargs.get("credential") is mock_cred


class TestSearchClientLifecycle:
    @pytest.fixture(autouse=True)
    def _reset(self) -> None:
        from app.search.service import reset_search_client

        reset_search_client()

    @patch("app.search.service.settings")
    @patch("app.search.service.DefaultAzureCredential")
    @patch("app.search.service.SearchClient")
    def test_get_search_client_returns_search_client(
        self,
        mock_client_cls: MagicMock,
        mock_cred_cls: MagicMock,
        mock_settings: MagicMock,
    ) -> None:
        from app.search.service import get_search_client

        mock_settings.azure_search_endpoint = "https://test.search.windows.net"
        mock_settings.azure_managed_identity_client_id = ""
        mock_client_cls.return_value = MagicMock()
        result = get_search_client()
        assert result is mock_client_cls.return_value

    @patch("app.search.service.settings")
    @patch("app.search.service.DefaultAzureCredential")
    @patch("app.search.service.SearchClient")
    def test_get_search_client_returns_same_instance(
        self,
        mock_client_cls: MagicMock,
        mock_cred_cls: MagicMock,
        mock_settings: MagicMock,
    ) -> None:
        from app.search.service import get_search_client

        mock_settings.azure_search_endpoint = "https://test.search.windows.net"
        mock_settings.azure_managed_identity_client_id = ""
        mock_client_cls.return_value = MagicMock()
        first = get_search_client()
        second = get_search_client()
        assert first is second
        mock_client_cls.assert_called_once()

    @patch("app.search.service.settings")
    @patch("app.search.service.DefaultAzureCredential")
    @patch("app.search.service.SearchClient")
    async def test_close_search_client_calls_close(
        self,
        mock_client_cls: MagicMock,
        mock_cred_cls: MagicMock,
        mock_settings: MagicMock,
    ) -> None:
        from app.search.service import close_search_client, get_search_client

        mock_settings.azure_search_endpoint = "https://test.search.windows.net"
        mock_settings.azure_managed_identity_client_id = ""
        mock_client = AsyncMock()
        mock_client_cls.return_value = mock_client
        mock_cred = AsyncMock()
        mock_cred_cls.return_value = mock_cred

        get_search_client()
        await close_search_client()

        mock_client.close.assert_awaited_once()
        mock_cred.close.assert_awaited_once()

    @patch("app.search.service.settings")
    @patch("app.search.service.DefaultAzureCredential")
    @patch("app.search.service.SearchClient")
    async def test_close_search_client_clears_singleton(
        self,
        mock_client_cls: MagicMock,
        mock_cred_cls: MagicMock,
        mock_settings: MagicMock,
    ) -> None:
        from app.search.service import close_search_client, get_search_client

        mock_settings.azure_search_endpoint = "https://test.search.windows.net"
        mock_settings.azure_managed_identity_client_id = ""
        mock_client_cls.return_value = AsyncMock()
        mock_cred_cls.return_value = AsyncMock()

        get_search_client()
        await close_search_client()

        # Next call should create a new instance
        mock_client_cls.reset_mock()
        get_search_client()
        mock_client_cls.assert_called_once()

    @patch("app.search.service.settings")
    def test_should_reject_empty_endpoint(self, mock_settings: MagicMock) -> None:
        from app.search.service import get_search_client

        mock_settings.azure_search_endpoint = ""

        with pytest.raises(RuntimeError, match="AZURE_SEARCH_ENDPOINT"):
            get_search_client()

    async def test_close_search_client_safe_when_no_client(self) -> None:
        from app.search.service import close_search_client

        # Should not raise
        await close_search_client()


class _AsyncSearchResults:
    """Helper to simulate AsyncSearchItemPaged."""

    def __init__(self, items: list[dict[str, Any]]) -> None:
        self._items = items

    def __aiter__(self) -> _AsyncSearchResults:
        self._iter = iter(self._items)
        return self

    async def __anext__(self) -> dict[str, Any]:
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration from None


class TestSearch:
    @pytest.fixture(autouse=True)
    def _reset(self) -> None:
        from app.search.service import reset_search_client

        reset_search_client()

    def _setup_mock_client(self) -> AsyncMock:
        mock_client = AsyncMock()
        mock_client.search = AsyncMock(return_value=_AsyncSearchResults([]))
        return mock_client

    @patch("app.search.service.get_search_client")
    async def test_should_always_filter_by_user_id(
        self, mock_get_client: MagicMock
    ) -> None:
        from app.search.service import search

        mock_client = self._setup_mock_client()
        mock_get_client.return_value = mock_client

        await search(user_id="user-123", query_text="meeting")

        call_kwargs = mock_client.search.call_args.kwargs
        assert "user_id eq 'user-123'" in call_kwargs["filter"]

    @patch("app.search.service.get_search_client")
    async def test_should_perform_text_only_search_when_no_vector(
        self, mock_get_client: MagicMock
    ) -> None:
        from app.search.service import search

        mock_client = self._setup_mock_client()
        mock_get_client.return_value = mock_client

        await search(user_id="user-123", query_text="meeting")

        call_kwargs = mock_client.search.call_args.kwargs
        assert call_kwargs["search_text"] == "meeting"
        assert call_kwargs.get("vector_queries") is None

    @patch("app.search.service.get_search_client")
    async def test_should_perform_hybrid_search_with_vector(
        self, mock_get_client: MagicMock
    ) -> None:
        from app.search.service import search

        mock_client = self._setup_mock_client()
        mock_get_client.return_value = mock_client

        vector = [0.1] * 1536
        await search(user_id="user-123", query_text="meeting", query_vector=vector)

        call_kwargs = mock_client.search.call_args.kwargs
        assert call_kwargs["search_text"] == "meeting"
        assert call_kwargs["vector_queries"] is not None
        assert len(call_kwargs["vector_queries"]) == 1

    @patch("app.search.service.get_search_client")
    async def test_should_filter_by_source_type_when_provided(
        self, mock_get_client: MagicMock
    ) -> None:
        from app.search.service import search

        mock_client = self._setup_mock_client()
        mock_get_client.return_value = mock_client

        await search(user_id="user-123", query_text="meeting", source_type="event")

        call_kwargs = mock_client.search.call_args.kwargs
        assert "source_type eq 'event'" in call_kwargs["filter"]

    @patch("app.search.service.get_search_client")
    async def test_should_return_search_results_as_dicts(
        self, mock_get_client: MagicMock
    ) -> None:
        from app.search.service import search

        mock_client = AsyncMock()
        mock_client.search = AsyncMock(
            return_value=_AsyncSearchResults(
                [
                    {
                        "id": "doc1",
                        "content": "Team standup",
                        "source_type": "event",
                    },
                    {
                        "id": "doc2",
                        "content": "1:1 with manager",
                        "source_type": "event",
                    },
                ]
            )
        )
        mock_get_client.return_value = mock_client

        results = await search(user_id="user-123", query_text="standup")

        assert len(results) == 2
        assert results[0]["id"] == "doc1"
        assert results[1]["content"] == "1:1 with manager"

    async def test_should_reject_empty_user_id(self) -> None:
        from app.search.service import search

        with pytest.raises(ValueError, match="user_id"):
            await search(user_id="", query_text="meeting")

    @patch("app.search.service.get_search_client")
    async def test_should_escape_odata_special_chars_in_user_id(
        self, mock_get_client: MagicMock
    ) -> None:
        from app.search.service import search

        mock_client = self._setup_mock_client()
        mock_get_client.return_value = mock_client

        await search(user_id="user'inject", query_text="test")

        call_kwargs = mock_client.search.call_args.kwargs
        assert "user''inject" in call_kwargs["filter"]

    @patch("app.search.service.get_search_client")
    async def test_should_escape_odata_special_chars_in_source_type(
        self, mock_get_client: MagicMock
    ) -> None:
        from app.search.service import search

        mock_client = self._setup_mock_client()
        mock_get_client.return_value = mock_client

        await search(
            user_id="user-123",
            query_text="test",
            source_type="type'bad",
        )

        call_kwargs = mock_client.search.call_args.kwargs
        assert "type''bad" in call_kwargs["filter"]

    @patch("app.search.service.get_search_client")
    async def test_should_respect_top_parameter(
        self, mock_get_client: MagicMock
    ) -> None:
        from app.search.service import search

        mock_client = self._setup_mock_client()
        mock_get_client.return_value = mock_client

        await search(user_id="user-123", query_text="meeting", top=10)

        call_kwargs = mock_client.search.call_args.kwargs
        assert call_kwargs["top"] == 10


class TestUpsertDocuments:
    @pytest.fixture(autouse=True)
    def _reset(self) -> None:
        from app.search.service import reset_search_client

        reset_search_client()

    @patch("app.search.service.get_search_client")
    async def test_should_set_user_id_on_all_documents(
        self, mock_get_client: MagicMock
    ) -> None:
        from app.search.service import upsert_documents

        mock_client = AsyncMock()
        mock_result = MagicMock()
        mock_result.succeeded = True
        mock_result.key = "doc1"
        mock_client.merge_or_upload_documents = AsyncMock(return_value=[mock_result])
        mock_get_client.return_value = mock_client

        docs = [{"id": "doc1", "content": "test", "user_id": "attacker-id"}]
        await upsert_documents(user_id="real-user", documents=docs)

        call_args = mock_client.merge_or_upload_documents.call_args
        uploaded_docs = call_args.args[0]
        assert uploaded_docs[0]["user_id"] == "real-user"
        # Original dict should not be mutated
        assert docs[0]["user_id"] == "attacker-id"

    @patch("app.search.service.get_search_client")
    async def test_should_call_merge_or_upload_documents(
        self, mock_get_client: MagicMock
    ) -> None:
        from app.search.service import upsert_documents

        mock_client = AsyncMock()
        mock_result = MagicMock()
        mock_result.succeeded = True
        mock_result.key = "doc1"
        mock_client.merge_or_upload_documents = AsyncMock(return_value=[mock_result])
        mock_get_client.return_value = mock_client

        docs = [{"id": "doc1", "content": "test"}]
        await upsert_documents(user_id="user-123", documents=docs)

        mock_client.merge_or_upload_documents.assert_awaited_once()

    @patch("app.search.service.get_search_client")
    async def test_should_return_succeeded_keys(
        self, mock_get_client: MagicMock
    ) -> None:
        from app.search.service import upsert_documents

        mock_client = AsyncMock()
        result_ok = MagicMock()
        result_ok.succeeded = True
        result_ok.key = "doc1"
        result_fail = MagicMock()
        result_fail.succeeded = False
        result_fail.key = "doc2"
        mock_client.merge_or_upload_documents = AsyncMock(
            return_value=[result_ok, result_fail]
        )
        mock_get_client.return_value = mock_client

        keys = await upsert_documents(
            user_id="user-123",
            documents=[
                {"id": "doc1", "content": "a"},
                {"id": "doc2", "content": "b"},
            ],
        )

        assert keys == ["doc1"]

    async def test_should_reject_empty_user_id(self) -> None:
        from app.search.service import upsert_documents

        with pytest.raises(ValueError, match="user_id"):
            await upsert_documents(user_id="", documents=[{"id": "doc1"}])


class TestDeleteDocuments:
    @pytest.fixture(autouse=True)
    def _reset(self) -> None:
        from app.search.service import reset_search_client

        reset_search_client()

    @patch("app.search.service.get_search_client")
    async def test_should_call_delete_documents_with_ids(
        self, mock_get_client: MagicMock
    ) -> None:
        from app.search.service import delete_documents

        mock_client = AsyncMock()
        mock_result = MagicMock()
        mock_result.succeeded = True
        mock_result.key = "doc1"
        mock_client.delete_documents = AsyncMock(return_value=[mock_result])
        mock_get_client.return_value = mock_client

        await delete_documents(user_id="user-123", document_ids=["doc1"])

        call_args = mock_client.delete_documents.call_args
        assert call_args.args[0] == [{"id": "doc1"}]

    @patch("app.search.service.get_search_client")
    async def test_should_return_deleted_keys(self, mock_get_client: MagicMock) -> None:
        from app.search.service import delete_documents

        mock_client = AsyncMock()
        r1 = MagicMock(succeeded=True, key="doc1")
        r2 = MagicMock(succeeded=True, key="doc2")
        mock_client.delete_documents = AsyncMock(return_value=[r1, r2])
        mock_get_client.return_value = mock_client

        keys = await delete_documents(user_id="user-123", document_ids=["doc1", "doc2"])

        assert keys == ["doc1", "doc2"]

    async def test_should_reject_empty_user_id(self) -> None:
        from app.search.service import delete_documents

        with pytest.raises(ValueError, match="user_id"):
            await delete_documents(user_id="", document_ids=["doc1"])


# ---------------------------------------------------------------------------
# Retry behavior on upsert/delete
# ---------------------------------------------------------------------------


def _make_http_response_error(status_code: int = 429) -> HttpResponseError:
    """Build an Azure HttpResponseError for testing."""
    error = HttpResponseError(message=f"HTTP {status_code}")
    error.status_code = status_code
    return error


class TestUpsertDocumentsRetry:
    @pytest.fixture(autouse=True)
    def _reset(self) -> None:
        from app.search.service import reset_search_client

        reset_search_client()

    @patch("app.search.service.get_search_client")
    @patch("asyncio.sleep", new_callable=AsyncMock)
    @patch("app.search.service.settings")
    async def test_should_retry_upsert_on_transient_error(
        self,
        mock_settings: MagicMock,
        mock_sleep: AsyncMock,
        mock_get_client: MagicMock,
    ) -> None:
        from app.search.service import upsert_documents

        mock_settings.embedding_max_retries = 3
        mock_settings.embedding_retry_initial_delay = 1.0

        mock_result = MagicMock(succeeded=True, key="doc1")
        mock_client = AsyncMock()
        mock_client.merge_or_upload_documents = AsyncMock(
            side_effect=[_make_http_response_error(429), [mock_result]]
        )
        mock_get_client.return_value = mock_client

        result = await upsert_documents(
            user_id="user-123", documents=[{"id": "doc1", "content": "test"}]
        )

        assert result == ["doc1"]
        assert mock_client.merge_or_upload_documents.await_count == 2

    @patch("app.search.service.get_search_client")
    @patch("asyncio.sleep", new_callable=AsyncMock)
    @patch("app.search.service.settings")
    async def test_should_raise_upsert_after_max_retries(
        self,
        mock_settings: MagicMock,
        mock_sleep: AsyncMock,
        mock_get_client: MagicMock,
    ) -> None:
        from app.search.service import upsert_documents

        mock_settings.embedding_max_retries = 3
        mock_settings.embedding_retry_initial_delay = 1.0

        mock_client = AsyncMock()
        mock_client.merge_or_upload_documents = AsyncMock(
            side_effect=_make_http_response_error(429)
        )
        mock_get_client.return_value = mock_client

        with pytest.raises(HttpResponseError):
            await upsert_documents(
                user_id="user-123", documents=[{"id": "doc1", "content": "test"}]
            )

        assert mock_client.merge_or_upload_documents.await_count == 3

    @patch("app.search.service.get_search_client")
    @patch("asyncio.sleep", new_callable=AsyncMock)
    @patch("app.search.service.settings")
    async def test_should_retry_on_service_request_error(
        self,
        mock_settings: MagicMock,
        mock_sleep: AsyncMock,
        mock_get_client: MagicMock,
    ) -> None:
        from app.search.service import upsert_documents

        mock_settings.embedding_max_retries = 3
        mock_settings.embedding_retry_initial_delay = 1.0

        mock_result = MagicMock(succeeded=True, key="doc1")
        mock_client = AsyncMock()
        mock_client.merge_or_upload_documents = AsyncMock(
            side_effect=[ServiceRequestError("connection reset"), [mock_result]]
        )
        mock_get_client.return_value = mock_client

        result = await upsert_documents(
            user_id="user-123", documents=[{"id": "doc1", "content": "test"}]
        )

        assert result == ["doc1"]
