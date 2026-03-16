"""Tests for the context embedding pipeline."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_event(
    *,
    event_id: str = "evt-1",
    summary: str = "Team Standup",
    start_dt: str = "2026-03-16T09:00:00-04:00",
    end_dt: str = "2026-03-16T09:30:00-04:00",
    location: str | None = None,
    attendees: list[dict[str, str]] | None = None,
    description: str | None = None,
    all_day: bool = False,
) -> dict[str, Any]:
    """Build a Google Calendar event dict for testing."""
    event: dict[str, Any] = {"id": event_id, "summary": summary}
    if all_day:
        event["start"] = {"date": start_dt}
        event["end"] = {"date": end_dt}
    else:
        event["start"] = {"dateTime": start_dt}
        event["end"] = {"dateTime": end_dt}
    if location is not None:
        event["location"] = location
    if attendees is not None:
        event["attendees"] = attendees
    if description is not None:
        event["description"] = description
    return event


FROZEN_NOW = datetime(2026, 3, 16, 12, 0, 0, tzinfo=UTC)


class TestEmbeddingsClientLifecycle:
    @pytest.fixture(autouse=True)
    def _reset(self) -> None:
        from app.search.embeddings import reset_embeddings_client

        reset_embeddings_client()

    @patch("app.search.embeddings.AzureOpenAIEmbeddings")
    @patch("app.search.embeddings.get_bearer_token_provider")
    @patch("app.search.embeddings.DefaultAzureCredential")
    def test_should_create_client_with_correct_config(
        self,
        mock_cred_cls: MagicMock,
        mock_token_provider: MagicMock,
        mock_embeddings_cls: MagicMock,
    ) -> None:
        from app.core.config import settings
        from app.search.embeddings import get_embeddings_client

        mock_cred = MagicMock()
        mock_cred_cls.return_value = mock_cred
        mock_token_provider.return_value = lambda: "fake-token"
        mock_embeddings_cls.return_value = MagicMock()

        client = get_embeddings_client()

        mock_cred_cls.assert_called_once()
        mock_token_provider.assert_called_once_with(
            mock_cred, "https://cognitiveservices.azure.com/.default"
        )
        mock_embeddings_cls.assert_called_once()
        call_kwargs = mock_embeddings_cls.call_args.kwargs
        assert call_kwargs["azure_endpoint"] == settings.azure_openai_endpoint
        assert call_kwargs["deployment"] == settings.azure_openai_embed_deployment
        assert call_kwargs["openai_api_version"] == settings.azure_openai_api_version
        assert client is mock_embeddings_cls.return_value

    @patch("app.search.embeddings.AzureOpenAIEmbeddings")
    @patch("app.search.embeddings.get_bearer_token_provider")
    @patch("app.search.embeddings.DefaultAzureCredential")
    def test_should_return_same_instance_on_subsequent_calls(
        self,
        mock_cred_cls: MagicMock,
        mock_token_provider: MagicMock,
        mock_embeddings_cls: MagicMock,
    ) -> None:
        from app.search.embeddings import get_embeddings_client

        mock_embeddings_cls.return_value = MagicMock()

        first = get_embeddings_client()
        second = get_embeddings_client()

        assert first is second
        mock_embeddings_cls.assert_called_once()

    @patch("app.search.embeddings.AzureOpenAIEmbeddings")
    @patch("app.search.embeddings.get_bearer_token_provider")
    @patch("app.search.embeddings.DefaultAzureCredential")
    def test_should_create_new_instance_after_close(
        self,
        mock_cred_cls: MagicMock,
        mock_token_provider: MagicMock,
        mock_embeddings_cls: MagicMock,
    ) -> None:
        from app.search.embeddings import close_embeddings_client, get_embeddings_client

        mock_cred = MagicMock()
        mock_cred_cls.return_value = mock_cred
        mock_embeddings_cls.return_value = MagicMock()

        get_embeddings_client()
        close_embeddings_client()

        mock_embeddings_cls.reset_mock()
        mock_cred_cls.reset_mock()

        get_embeddings_client()
        mock_embeddings_cls.assert_called_once()

    def test_should_be_safe_to_close_when_no_client(self) -> None:
        from app.search.embeddings import close_embeddings_client

        close_embeddings_client()


class TestFormatEventText:
    def test_should_include_title(self) -> None:
        from app.search.embeddings import format_event_text

        event = _make_event(summary="Team Standup")
        text = format_event_text(event)
        assert "Title: Team Standup" in text

    def test_should_include_start_and_end_times(self) -> None:
        from app.search.embeddings import format_event_text

        event = _make_event(
            start_dt="2026-03-16T09:00:00-04:00",
            end_dt="2026-03-16T09:30:00-04:00",
        )
        text = format_event_text(event)
        assert "When:" in text
        assert "2026-03-16T09:00:00-04:00" in text
        assert "2026-03-16T09:30:00-04:00" in text

    def test_should_include_location_when_present(self) -> None:
        from app.search.embeddings import format_event_text

        event = _make_event(location="Conference Room A")
        text = format_event_text(event)
        assert "Location: Conference Room A" in text

    def test_should_include_attendees_when_present(self) -> None:
        from app.search.embeddings import format_event_text

        event = _make_event(
            attendees=[
                {"email": "alice@example.com"},
                {"email": "bob@example.com"},
            ]
        )
        text = format_event_text(event)
        assert "Attendees:" in text
        assert "alice@example.com" in text
        assert "bob@example.com" in text

    def test_should_include_description_when_present(self) -> None:
        from app.search.embeddings import format_event_text

        event = _make_event(description="Daily standup meeting")
        text = format_event_text(event)
        assert "Description: Daily standup meeting" in text

    def test_should_handle_all_day_events(self) -> None:
        from app.search.embeddings import format_event_text

        event = _make_event(
            start_dt="2026-03-16",
            end_dt="2026-03-17",
            all_day=True,
        )
        text = format_event_text(event)
        assert "When:" in text
        assert "2026-03-16" in text

    def test_should_handle_missing_optional_fields(self) -> None:
        from app.search.embeddings import format_event_text

        event = _make_event()
        text = format_event_text(event)
        assert "Title:" in text
        assert "When:" in text
        assert "Location:" not in text
        assert "Attendees:" not in text
        assert "Description:" not in text

    def test_should_use_untitled_for_missing_summary(self) -> None:
        from app.search.embeddings import format_event_text

        event = _make_event()
        del event["summary"]
        text = format_event_text(event)
        assert "Title: (untitled)" in text


class TestBuildSearchDocument:
    @patch(
        "app.search.embeddings._utc_now",
        return_value=FROZEN_NOW,
    )
    def test_should_set_id_to_event_id(self, _mock_now: MagicMock) -> None:
        from app.search.embeddings import build_search_document

        event = _make_event(event_id="cal-event-123")
        doc = build_search_document(event, "some content", [0.1] * 1536)
        assert doc["id"] == "cal-event-123"

    @patch(
        "app.search.embeddings._utc_now",
        return_value=FROZEN_NOW,
    )
    def test_should_set_source_type_to_event(self, _mock_now: MagicMock) -> None:
        from app.search.embeddings import build_search_document

        event = _make_event()
        doc = build_search_document(event, "content", [0.1] * 1536)
        assert doc["source_type"] == "event"

    @patch(
        "app.search.embeddings._utc_now",
        return_value=FROZEN_NOW,
    )
    def test_should_set_content_to_formatted_text(self, _mock_now: MagicMock) -> None:
        from app.search.embeddings import build_search_document

        event = _make_event()
        doc = build_search_document(event, "formatted text here", [0.1] * 1536)
        assert doc["content"] == "formatted text here"

    @patch(
        "app.search.embeddings._utc_now",
        return_value=FROZEN_NOW,
    )
    def test_should_set_embedding_from_vector(self, _mock_now: MagicMock) -> None:
        from app.search.embeddings import build_search_document

        embedding = [0.5] * 1536
        event = _make_event()
        doc = build_search_document(event, "content", embedding)
        assert doc["embedding"] == embedding

    @patch(
        "app.search.embeddings._utc_now",
        return_value=FROZEN_NOW,
    )
    def test_should_set_timestamp_from_event_start(self, _mock_now: MagicMock) -> None:
        from app.search.embeddings import build_search_document

        event = _make_event(start_dt="2026-03-16T09:00:00-04:00")
        doc = build_search_document(event, "content", [0.1] * 1536)
        assert doc["timestamp"] == "2026-03-16T09:00:00-04:00"

    @patch(
        "app.search.embeddings._utc_now",
        return_value=FROZEN_NOW,
    )
    def test_should_set_last_modified_to_current_utc(
        self, _mock_now: MagicMock
    ) -> None:
        from app.search.embeddings import build_search_document

        event = _make_event()
        doc = build_search_document(event, "content", [0.1] * 1536)
        assert doc["last_modified"] == "2026-03-16T12:00:00+00:00"


class TestProcessEvents:
    @pytest.fixture(autouse=True)
    def _reset(self) -> None:
        from app.search.embeddings import reset_embeddings_client

        reset_embeddings_client()

    @patch("app.search.embeddings.upsert_documents", new_callable=AsyncMock)
    @patch("app.search.embeddings.get_embeddings_client")
    async def test_should_embed_and_upsert_events(
        self, mock_get_client: MagicMock, mock_upsert: AsyncMock
    ) -> None:
        from app.search.embeddings import process_events

        mock_client = AsyncMock()
        mock_client.aembed_documents = AsyncMock(
            return_value=[[0.1] * 1536, [0.2] * 1536]
        )
        mock_get_client.return_value = mock_client
        mock_upsert.return_value = ["evt-1", "evt-2"]

        events = [_make_event(event_id="evt-1"), _make_event(event_id="evt-2")]
        result = await process_events(user_id="user-123", events=events)

        assert result == ["evt-1", "evt-2"]
        mock_client.aembed_documents.assert_awaited_once()
        mock_upsert.assert_awaited_once()

    @patch("app.search.embeddings.upsert_documents", new_callable=AsyncMock)
    @patch("app.search.embeddings.get_embeddings_client")
    async def test_should_call_aembed_documents_with_formatted_texts(
        self, mock_get_client: MagicMock, mock_upsert: AsyncMock
    ) -> None:
        from app.search.embeddings import format_event_text, process_events

        mock_client = AsyncMock()
        mock_client.aembed_documents = AsyncMock(return_value=[[0.1] * 1536])
        mock_get_client.return_value = mock_client
        mock_upsert.return_value = ["evt-1"]

        events = [_make_event(event_id="evt-1", summary="Test Event")]
        await process_events(user_id="user-123", events=events)

        expected_text = format_event_text(events[0])
        call_args = mock_client.aembed_documents.call_args
        assert call_args.args[0] == [expected_text]

    @patch("app.search.embeddings.upsert_documents", new_callable=AsyncMock)
    @patch("app.search.embeddings.get_embeddings_client")
    async def test_should_return_upserted_document_ids(
        self, mock_get_client: MagicMock, mock_upsert: AsyncMock
    ) -> None:
        from app.search.embeddings import process_events

        mock_client = AsyncMock()
        mock_client.aembed_documents = AsyncMock(return_value=[[0.1] * 1536])
        mock_get_client.return_value = mock_client
        mock_upsert.return_value = ["evt-1"]

        result = await process_events(
            user_id="user-123", events=[_make_event(event_id="evt-1")]
        )
        assert result == ["evt-1"]

    async def test_should_reject_empty_user_id(self) -> None:
        from app.search.embeddings import process_events

        with pytest.raises(ValueError, match="user_id"):
            await process_events(user_id="", events=[_make_event()])

    async def test_should_return_empty_list_for_empty_events(self) -> None:
        from app.search.embeddings import process_events

        result = await process_events(user_id="user-123", events=[])
        assert result == []

    @patch("app.search.embeddings.get_embeddings_client")
    async def test_should_propagate_embedding_errors(
        self, mock_get_client: MagicMock
    ) -> None:
        from app.search.embeddings import process_events

        mock_client = AsyncMock()
        mock_client.aembed_documents = AsyncMock(
            side_effect=RuntimeError("Azure OpenAI unavailable")
        )
        mock_get_client.return_value = mock_client

        with pytest.raises(RuntimeError, match="Azure OpenAI unavailable"):
            await process_events(user_id="user-123", events=[_make_event()])


class TestDeleteEvents:
    @patch("app.search.embeddings.delete_documents", new_callable=AsyncMock)
    async def test_should_call_delete_documents_with_source_ids(
        self, mock_delete: AsyncMock
    ) -> None:
        from app.search.embeddings import delete_events

        mock_delete.return_value = ["evt-1", "evt-2"]

        await delete_events(user_id="user-123", source_ids=["evt-1", "evt-2"])

        mock_delete.assert_awaited_once_with("user-123", ["evt-1", "evt-2"])

    @patch("app.search.embeddings.delete_documents", new_callable=AsyncMock)
    async def test_should_return_deleted_ids(self, mock_delete: AsyncMock) -> None:
        from app.search.embeddings import delete_events

        mock_delete.return_value = ["evt-1"]

        result = await delete_events(user_id="user-123", source_ids=["evt-1"])
        assert result == ["evt-1"]

    async def test_should_reject_empty_user_id(self) -> None:
        from app.search.embeddings import delete_events

        with pytest.raises(ValueError, match="user_id"):
            await delete_events(user_id="", source_ids=["evt-1"])

    async def test_should_return_empty_list_for_empty_ids(self) -> None:
        from app.search.embeddings import delete_events

        result = await delete_events(user_id="user-123", source_ids=[])
        assert result == []
