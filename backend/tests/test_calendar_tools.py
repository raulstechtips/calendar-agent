"""Tests for Google Calendar tools — credential handling, read tools, write tools."""

import json
import time
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.tools.calendar_tools import (
    CALENDAR_SCOPE,
    SCOPE_ERROR_SENTINEL,
    _build_service,  # pyright: ignore[reportPrivateUsage]
    _get_credentials,  # pyright: ignore[reportPrivateUsage]
    _refresh_token_for_tool,  # pyright: ignore[reportPrivateUsage]
    calendar_tools,
    create_event,
    delete_event,
    get_calendars_info,
    get_current_datetime,
    search_events,
    update_event,
)
from app.auth.token_storage import StoredToken, TokenEncryptionError, TokenNotFoundError

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FAKE_USER_ID = "google-sub-test-123"


def _make_stored_token(
    *, expired: bool = False, access_token: str = "valid-access-token"
) -> StoredToken:
    """Create a StoredToken for testing."""
    return StoredToken(
        access_token=access_token,
        refresh_token="valid-refresh-token",
        expires_at=int(time.time()) - 100 if expired else int(time.time()) + 3600,
        scopes=["https://www.googleapis.com/auth/calendar.events"],
    )


def _mock_calendar_service() -> MagicMock:
    """Create a mock Google Calendar API service."""
    service = MagicMock()
    return service


@pytest.fixture(autouse=True)
def _patch_settings(monkeypatch: pytest.MonkeyPatch) -> None:  # pyright: ignore[reportUnusedFunction]
    """Ensure Google OAuth settings are available for all tests."""
    monkeypatch.setattr(
        "app.agents.tools.calendar_tools.settings",
        MagicMock(
            google_client_id="test-client-id",
            google_client_secret="test-client-secret",
        ),
    )


# ---------------------------------------------------------------------------
# Credential helper tests
# ---------------------------------------------------------------------------


class TestGetCredentials:
    async def test_should_return_credentials_with_valid_token(self) -> None:
        token = _make_stored_token()
        with patch(
            "app.agents.tools.calendar_tools.get_token",
            new_callable=AsyncMock,
            return_value=token,
        ):
            result = await _get_credentials(FAKE_USER_ID)
            assert not isinstance(result, str)
            assert result.token == "valid-access-token"

    async def test_should_return_error_when_no_token_found(self) -> None:
        with patch(
            "app.agents.tools.calendar_tools.get_token",
            new_callable=AsyncMock,
            side_effect=TokenNotFoundError("No token"),
        ):
            result = await _get_credentials(FAKE_USER_ID)
            assert isinstance(result, str)
            assert "sign in" in result.lower()

    async def test_should_return_error_when_decryption_fails(self) -> None:
        with patch(
            "app.agents.tools.calendar_tools.get_token",
            new_callable=AsyncMock,
            side_effect=TokenEncryptionError("Bad key"),
        ):
            result = await _get_credentials(FAKE_USER_ID)
            assert isinstance(result, str)
            assert "re-authenticate" in result.lower()

    async def test_should_refresh_expired_token(self) -> None:
        expired_token = _make_stored_token(expired=True)
        refreshed_token = _make_stored_token(access_token="refreshed-access-token")

        with (
            patch(
                "app.agents.tools.calendar_tools.get_token",
                new_callable=AsyncMock,
                return_value=expired_token,
            ),
            patch(
                "app.agents.tools.calendar_tools._refresh_token_for_tool",
                new_callable=AsyncMock,
                return_value=refreshed_token,
            ),
        ):
            result = await _get_credentials(FAKE_USER_ID)
            assert not isinstance(result, str)
            assert result.token == "refreshed-access-token"

    async def test_should_skip_refresh_if_another_coroutine_already_refreshed(
        self,
    ) -> None:
        expired_token = _make_stored_token(expired=True)
        fresh_token = _make_stored_token(access_token="already-refreshed")

        # First call returns expired, second call (inside lock) returns fresh
        with patch(
            "app.agents.tools.calendar_tools.get_token",
            new_callable=AsyncMock,
            side_effect=[expired_token, fresh_token],
        ):
            result = await _get_credentials(FAKE_USER_ID)
            assert not isinstance(result, str)
            assert result.token == "already-refreshed"

    async def test_should_return_error_when_refresh_fails(self) -> None:
        expired_token = _make_stored_token(expired=True)

        with (
            patch(
                "app.agents.tools.calendar_tools.get_token",
                new_callable=AsyncMock,
                return_value=expired_token,
            ),
            patch(
                "app.agents.tools.calendar_tools._refresh_token_for_tool",
                new_callable=AsyncMock,
                return_value="Google token refresh failed — please re-authenticate.",
            ),
        ):
            result = await _get_credentials(FAKE_USER_ID)
            assert isinstance(result, str)
            assert "re-authenticate" in result.lower()


class TestRefreshTokenForTool:
    async def test_should_refresh_and_store_new_token(self) -> None:
        stored = _make_stored_token(expired=True)
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "access_token": "new-access-token",
            "expires_in": 3600,
        }

        with (
            patch(
                "app.agents.tools.calendar_tools.requests.post",
                return_value=mock_response,
            ),
            patch(
                "app.agents.tools.calendar_tools.store_token",
                new_callable=AsyncMock,
            ) as mock_store,
        ):
            result = await _refresh_token_for_tool(FAKE_USER_ID, stored)
            assert isinstance(result, StoredToken)
            assert result.access_token == "new-access-token"
            mock_store.assert_called_once()

    async def test_should_return_error_on_network_failure(self) -> None:
        stored = _make_stored_token(expired=True)

        import requests as req

        with patch(
            "app.agents.tools.calendar_tools.requests.post",
            side_effect=req.RequestException("Connection error"),
        ):
            result = await _refresh_token_for_tool(FAKE_USER_ID, stored)
            assert isinstance(result, str)
            assert "network error" in result.lower()

    async def test_should_use_scopes_from_google_refresh_response(self) -> None:
        stored = _make_stored_token(expired=True)
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "access_token": "new-access-token",
            "expires_in": 3600,
            "scope": "openid email profile https://www.googleapis.com/auth/calendar.events",
        }

        with (
            patch(
                "app.agents.tools.calendar_tools.requests.post",
                return_value=mock_response,
            ),
            patch(
                "app.agents.tools.calendar_tools.store_token",
                new_callable=AsyncMock,
            ) as mock_store,
        ):
            result = await _refresh_token_for_tool(FAKE_USER_ID, stored)
            assert isinstance(result, StoredToken)
            assert result.scopes == [
                "openid",
                "email",
                "profile",
                "https://www.googleapis.com/auth/calendar.events",
            ]
            mock_store.assert_called_once()

    async def test_should_preserve_stored_scopes_when_google_omits_scope(self) -> None:
        stored = _make_stored_token(expired=True)
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "access_token": "new-access-token",
            "expires_in": 3600,
            # No "scope" field in response
        }

        with (
            patch(
                "app.agents.tools.calendar_tools.requests.post",
                return_value=mock_response,
            ),
            patch(
                "app.agents.tools.calendar_tools.store_token",
                new_callable=AsyncMock,
            ),
        ):
            result = await _refresh_token_for_tool(FAKE_USER_ID, stored)
            assert isinstance(result, StoredToken)
            assert result.scopes == stored.scopes

    async def test_should_return_error_on_google_rejection(self) -> None:
        stored = _make_stored_token(expired=True)
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 400
        mock_response.text = "invalid_grant"

        with patch(
            "app.agents.tools.calendar_tools.requests.post",
            return_value=mock_response,
        ):
            result = await _refresh_token_for_tool(FAKE_USER_ID, stored)
            assert isinstance(result, str)
            assert "re-authenticate" in result.lower()


class TestBuildService:
    async def test_should_build_service_with_valid_credentials(self) -> None:
        token = _make_stored_token()
        with (
            patch(
                "app.agents.tools.calendar_tools.get_token",
                new_callable=AsyncMock,
                return_value=token,
            ),
            patch(
                "app.agents.tools.calendar_tools.build",
                return_value=MagicMock(),
            ) as mock_build,
        ):
            result = await _build_service(FAKE_USER_ID)
            assert not isinstance(result, str)
            mock_build.assert_called_once()

    async def test_should_return_error_when_credentials_fail(self) -> None:
        with patch(
            "app.agents.tools.calendar_tools.get_token",
            new_callable=AsyncMock,
            side_effect=TokenNotFoundError("No token"),
        ):
            result = await _build_service(FAKE_USER_ID)
            assert isinstance(result, str)

    async def test_should_return_scope_sentinel_when_calendar_scope_missing(
        self,
    ) -> None:
        identity_only_token = StoredToken(
            access_token="valid-access",
            refresh_token="valid-refresh",
            expires_at=int(time.time()) + 3600,
            scopes=["openid", "email", "profile"],
        )
        with patch(
            "app.agents.tools.calendar_tools.get_token",
            new_callable=AsyncMock,
            return_value=identity_only_token,
        ):
            result = await _build_service(FAKE_USER_ID)
            assert result == SCOPE_ERROR_SENTINEL

    async def test_should_proceed_when_calendar_scope_present(self) -> None:
        token = _make_stored_token()  # includes calendar.events scope
        with (
            patch(
                "app.agents.tools.calendar_tools.get_token",
                new_callable=AsyncMock,
                return_value=token,
            ),
            patch(
                "app.agents.tools.calendar_tools.build",
                return_value=MagicMock(),
            ),
        ):
            result = await _build_service(FAKE_USER_ID)
            assert not isinstance(result, str)


class TestHttpErrorDetection:
    def _make_http_error(self, status: int, content: bytes) -> Any:
        """Create a mock HttpError."""
        from googleapiclient.errors import HttpError

        resp = MagicMock()
        resp.status = status
        return HttpError(resp=resp, content=content)

    async def test_should_return_scope_sentinel_on_403_insufficient_permissions(
        self,
    ) -> None:
        error = self._make_http_error(
            403,
            b'{"error": {"errors": [{"reason": "insufficientPermissions"}]}}',
        )
        service = MagicMock()
        service.calendars.return_value.get.return_value.execute.side_effect = error

        with patch(
            "app.agents.tools.calendar_tools._build_service",
            new_callable=AsyncMock,
            return_value=service,
        ):
            result = await get_current_datetime.ainvoke(  # type: ignore[union-attr]
                {"user_id": FAKE_USER_ID}
            )
            assert result == SCOPE_ERROR_SENTINEL

    async def test_should_propagate_non_permission_http_errors(self) -> None:
        error = self._make_http_error(404, b'{"error": {"message": "Not found"}}')
        service = MagicMock()
        service.calendars.return_value.get.return_value.execute.side_effect = error

        with patch(
            "app.agents.tools.calendar_tools._build_service",
            new_callable=AsyncMock,
            return_value=service,
        ):
            result = await get_current_datetime.ainvoke(  # type: ignore[union-attr]
                {"user_id": FAKE_USER_ID}
            )
            assert isinstance(result, str)
            assert result != SCOPE_ERROR_SENTINEL
            assert "Failed" in result


# ---------------------------------------------------------------------------
# Read tool tests
# ---------------------------------------------------------------------------


def _patch_service(mock_service: MagicMock) -> Any:
    """Patch _build_service to return a mock."""
    return patch(
        "app.agents.tools.calendar_tools._build_service",
        new_callable=AsyncMock,
        return_value=mock_service,
    )


class TestGetCurrentDatetime:
    async def test_should_return_formatted_datetime(self) -> None:
        service = _mock_calendar_service()
        service.calendars().get().execute.return_value = {
            "timeZone": "America/New_York"
        }

        with _patch_service(service):
            result = await get_current_datetime.ainvoke(
                {"user_id": FAKE_USER_ID},
            )
            assert "Current datetime:" in result
            assert "America/New_York" in result

    async def test_should_return_error_on_api_failure(self) -> None:
        service = _mock_calendar_service()
        service.calendars().get().execute.side_effect = Exception("API Error")

        with _patch_service(service):
            result = await get_current_datetime.ainvoke(
                {"user_id": FAKE_USER_ID},
            )
            assert "Failed to get current datetime" in result

    async def test_should_return_error_when_no_credentials(self) -> None:
        with patch(
            "app.agents.tools.calendar_tools._build_service",
            new_callable=AsyncMock,
            return_value="No Google token found — please sign in.",
        ):
            result = await get_current_datetime.ainvoke(
                {"user_id": FAKE_USER_ID},
            )
            assert "No Google token found" in result


class TestGetCalendarsInfo:
    async def test_should_return_calendar_list_as_json(self) -> None:
        service = _mock_calendar_service()
        service.calendarList().list().execute.return_value = {
            "items": [
                {
                    "id": "primary",
                    "summary": "My Calendar",
                    "timeZone": "America/Chicago",
                },
                {
                    "id": "holidays@group.v.calendar.google.com",
                    "summary": "Holidays",
                    "timeZone": "UTC",
                },
            ]
        }

        with _patch_service(service):
            result = await get_calendars_info.ainvoke(
                {"user_id": FAKE_USER_ID},
            )
            parsed = json.loads(result)
            assert len(parsed) == 2
            assert parsed[0]["id"] == "primary"
            assert parsed[1]["summary"] == "Holidays"

    async def test_should_return_error_on_api_failure(self) -> None:
        service = _mock_calendar_service()
        service.calendarList().list().execute.side_effect = Exception("API Error")

        with _patch_service(service):
            result = await get_calendars_info.ainvoke(
                {"user_id": FAKE_USER_ID},
            )
            assert "Failed to get calendars info" in result


class TestSearchEvents:
    async def test_should_return_simplified_events(self) -> None:
        service = _mock_calendar_service()
        service.events().list().execute.return_value = {
            "items": [
                {
                    "id": "event1",
                    "summary": "Team Standup",
                    "start": {"dateTime": "2026-03-15T09:00:00-05:00"},
                    "end": {"dateTime": "2026-03-15T09:30:00-05:00"},
                    "creator": {"email": "alice@example.com"},
                    "htmlLink": "https://calendar.google.com/event?eid=123",
                },
            ]
        }

        calendars_info = json.dumps(
            [{"id": "primary", "summary": "My Cal", "timeZone": "America/Chicago"}]
        )

        with _patch_service(service):
            result = await search_events.ainvoke(
                {
                    "calendars_info": calendars_info,
                    "min_datetime": "2026-03-15 00:00:00",
                    "max_datetime": "2026-03-16 00:00:00",
                    "user_id": FAKE_USER_ID,
                },
            )
            parsed = json.loads(result)
            assert len(parsed) == 1
            assert parsed[0]["summary"] == "Team Standup"
            assert parsed[0]["id"] == "event1"

    async def test_should_return_no_events_message(self) -> None:
        service = _mock_calendar_service()
        service.events().list().execute.return_value = {"items": []}

        calendars_info = json.dumps(
            [{"id": "primary", "summary": "My Cal", "timeZone": "UTC"}]
        )

        with _patch_service(service):
            result = await search_events.ainvoke(
                {
                    "calendars_info": calendars_info,
                    "min_datetime": "2026-03-15 00:00:00",
                    "max_datetime": "2026-03-16 00:00:00",
                    "user_id": FAKE_USER_ID,
                },
            )
            assert "No events found" in result

    async def test_should_return_error_on_invalid_calendars_info(self) -> None:
        service = _mock_calendar_service()

        with _patch_service(service):
            result = await search_events.ainvoke(
                {
                    "calendars_info": "not-valid-json",
                    "min_datetime": "2026-03-15 00:00:00",
                    "max_datetime": "2026-03-16 00:00:00",
                    "user_id": FAKE_USER_ID,
                },
            )
            assert "Invalid calendars_info" in result


# ---------------------------------------------------------------------------
# Write tool tests (human-in-the-loop with interrupt)
# ---------------------------------------------------------------------------


class TestCreateEvent:
    async def test_should_interrupt_with_event_details(self) -> None:
        service = _mock_calendar_service()
        service.events().insert().execute.return_value = {
            "summary": "Lunch with Alice",
            "htmlLink": "https://calendar.google.com/event?eid=new",
        }

        with (
            patch(
                "app.agents.tools.calendar_tools.interrupt",
            ) as mock_interrupt,
            _patch_service(service),
        ):
            await create_event.ainvoke(
                {
                    "summary": "Lunch with Alice",
                    "start_datetime": "2026-03-20 12:00:00",
                    "end_datetime": "2026-03-20 13:00:00",
                    "timezone": "America/New_York",
                    "user_id": FAKE_USER_ID,
                },
            )
            call_args = mock_interrupt.call_args[0][0]
            assert call_args["action"] == "create_event"
            assert call_args["summary"] == "Lunch with Alice"
            assert call_args["start"] == "2026-03-20 12:00:00"
            assert call_args["end"] == "2026-03-20 13:00:00"
            assert call_args["timezone"] == "America/New_York"

    async def test_should_create_event_after_confirmation(self) -> None:
        service = _mock_calendar_service()
        service.events().insert().execute.return_value = {
            "summary": "Lunch with Alice",
            "htmlLink": "https://calendar.google.com/event?eid=new",
        }

        with (
            patch(
                "app.agents.tools.calendar_tools.interrupt",
            ) as mock_interrupt,
            _patch_service(service),
        ):
            result = await create_event.ainvoke(
                {
                    "summary": "Lunch with Alice",
                    "start_datetime": "2026-03-20 12:00:00",
                    "end_datetime": "2026-03-20 13:00:00",
                    "timezone": "America/New_York",
                    "user_id": FAKE_USER_ID,
                },
            )

            mock_interrupt.assert_called_once()
            call_args = mock_interrupt.call_args[0][0]
            assert call_args["action"] == "create_event"
            assert call_args["summary"] == "Lunch with Alice"
            assert "Event created" in result

    async def test_should_handle_create_api_error(self) -> None:
        service = _mock_calendar_service()
        service.events().insert().execute.side_effect = Exception("Quota exceeded")

        with (
            patch("app.agents.tools.calendar_tools.interrupt"),
            _patch_service(service),
        ):
            result = await create_event.ainvoke(
                {
                    "summary": "Meeting",
                    "start_datetime": "2026-03-20 14:00:00",
                    "end_datetime": "2026-03-20 15:00:00",
                    "timezone": "UTC",
                    "user_id": FAKE_USER_ID,
                },
            )
            assert "Failed to create event" in result


class TestUpdateEvent:
    async def test_should_interrupt_with_event_details(self) -> None:
        service = _mock_calendar_service()
        service.events().get().execute.return_value = {
            "summary": "Old Title",
            "start": {"dateTime": "2026-03-20T10:00:00Z", "timeZone": "UTC"},
            "end": {"dateTime": "2026-03-20T11:00:00Z", "timeZone": "UTC"},
        }
        service.events().update().execute.return_value = {
            "summary": "Updated Title",
            "htmlLink": "https://calendar.google.com/event?eid=123",
        }

        with (
            patch("app.agents.tools.calendar_tools.interrupt") as mock_interrupt,
            _patch_service(service),
        ):
            await update_event.ainvoke(
                {
                    "event_id": "event123",
                    "summary": "Updated Title",
                    "user_id": FAKE_USER_ID,
                },
            )
            call_args = mock_interrupt.call_args[0][0]
            assert call_args["action"] == "update_event"
            assert call_args["event_id"] == "event123"
            assert call_args["summary"] == "Updated Title"

    async def test_should_update_event_after_confirmation(self) -> None:
        service = _mock_calendar_service()
        service.events().get().execute.return_value = {
            "summary": "Old Title",
            "start": {"dateTime": "2026-03-20T10:00:00-05:00", "timeZone": "UTC"},
            "end": {"dateTime": "2026-03-20T11:00:00-05:00", "timeZone": "UTC"},
        }
        service.events().update().execute.return_value = {
            "summary": "New Title",
            "htmlLink": "https://calendar.google.com/event?eid=123",
        }

        with (
            patch("app.agents.tools.calendar_tools.interrupt"),
            _patch_service(service),
        ):
            result = await update_event.ainvoke(
                {
                    "event_id": "event123",
                    "summary": "New Title",
                    "user_id": FAKE_USER_ID,
                },
            )
            assert "Event updated" in result

    async def test_should_handle_update_api_error(self) -> None:
        service = _mock_calendar_service()
        service.events().get().execute.side_effect = Exception("Not found")

        with (
            patch("app.agents.tools.calendar_tools.interrupt"),
            _patch_service(service),
        ):
            result = await update_event.ainvoke(
                {
                    "event_id": "missing",
                    "summary": "Nope",
                    "user_id": FAKE_USER_ID,
                },
            )
            assert "Failed to update event" in result


class TestDeleteEvent:
    async def test_should_interrupt_with_event_details(self) -> None:
        service = _mock_calendar_service()
        service.events().delete().execute.return_value = None

        with (
            patch("app.agents.tools.calendar_tools.interrupt") as mock_interrupt,
            _patch_service(service),
        ):
            await delete_event.ainvoke(
                {
                    "event_id": "event123",
                    "user_id": FAKE_USER_ID,
                },
            )
            call_args = mock_interrupt.call_args[0][0]
            assert call_args["action"] == "delete_event"
            assert call_args["event_id"] == "event123"
            assert call_args["calendar_id"] == "primary"

    async def test_should_delete_event_after_confirmation(self) -> None:
        service = _mock_calendar_service()
        service.events().delete().execute.return_value = None

        with (
            patch("app.agents.tools.calendar_tools.interrupt"),
            _patch_service(service),
        ):
            result = await delete_event.ainvoke(
                {
                    "event_id": "event123",
                    "user_id": FAKE_USER_ID,
                },
            )
            assert "deleted successfully" in result

    async def test_should_handle_delete_api_error(self) -> None:
        service = _mock_calendar_service()
        service.events().delete().execute.side_effect = Exception("Forbidden")

        with (
            patch("app.agents.tools.calendar_tools.interrupt"),
            _patch_service(service),
        ):
            result = await delete_event.ainvoke(
                {
                    "event_id": "event123",
                    "user_id": FAKE_USER_ID,
                },
            )
            assert "Failed to delete event" in result


# ---------------------------------------------------------------------------
# Config and integration tests
# ---------------------------------------------------------------------------


class TestConfig:
    def test_settings_should_not_have_azure_openai_api_key(self) -> None:
        from app.core.config import Settings

        field_names = set(Settings.model_fields.keys())
        assert "azure_openai_api_key" not in field_names

    def test_settings_should_have_managed_identity_client_id(self) -> None:
        from app.core.config import Settings

        assert "azure_managed_identity_client_id" in Settings.model_fields
        field = Settings.model_fields["azure_managed_identity_client_id"]
        assert field.default == ""


class TestCalendarToolsList:
    def test_should_export_six_tools(self) -> None:
        assert len(calendar_tools) == 6

    def test_should_contain_expected_tool_names(self) -> None:
        names = {t.name for t in calendar_tools}
        assert names == {
            "get_current_datetime",
            "get_calendars_info",
            "search_events",
            "create_event",
            "update_event",
            "delete_event",
        }


class TestGetLlm:
    def test_should_use_token_provider_not_api_key(self) -> None:
        with (
            patch("app.agents.calendar_agent.DefaultAzureCredential") as mock_cred_cls,
            patch(
                "app.agents.calendar_agent.get_bearer_token_provider",
                return_value=lambda: "fake-token",
            ) as mock_provider,
            patch("app.agents.calendar_agent.AzureChatOpenAI") as mock_llm_cls,
        ):
            mock_cred_cls.return_value = MagicMock()
            from app.agents.calendar_agent import get_llm

            get_llm()

            mock_cred_cls.assert_called_once()
            mock_provider.assert_called_once()
            call_kwargs = mock_llm_cls.call_args.kwargs
            assert "azure_ad_token_provider" in call_kwargs
            assert "api_key" not in call_kwargs
