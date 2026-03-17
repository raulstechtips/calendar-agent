"""Google Calendar tools for the LangGraph ReAct agent.

Custom @tool wrappers that resolve per-user OAuth credentials from Redis
at call time, since langchain-google-community's CalendarBaseTool binds
credentials at instantiation (incompatible with multi-user).
"""

import asyncio
import json
import logging
import re
from datetime import datetime
from typing import Annotated, Any
from zoneinfo import ZoneInfo

from googleapiclient.errors import HttpError
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from langgraph.types import interrupt

from app.auth.google_credentials import SCOPE_ERROR_SENTINEL, build_calendar_service

logger = logging.getLogger(__name__)


def _is_insufficient_permissions(e: HttpError) -> bool:
    """Check if an HttpError is a 403 insufficientPermissions response."""
    return e.resp.status == 403 and b"insufficientPermissions" in (e.content or b"")


# ---------------------------------------------------------------------------
# Read-only tools
# ---------------------------------------------------------------------------


@tool
async def get_current_datetime(
    user_id: Annotated[str, InjectedState("user_id")],
) -> str:
    """Get the current date/time in the user's primary calendar timezone."""
    service = await build_calendar_service(user_id)
    if isinstance(service, str):
        return service

    try:
        loop = asyncio.get_running_loop()
        calendar = await loop.run_in_executor(
            None,
            lambda: service.calendars().get(calendarId="primary").execute(),
        )
        tz_name = calendar.get("timeZone", "UTC")
        tz = ZoneInfo(tz_name)
        now = datetime.now(tz)
        return f"Current datetime: {now.strftime('%Y-%m-%d %H:%M:%S')} ({tz_name})"
    except HttpError as e:
        if _is_insufficient_permissions(e):
            logger.warning("403 insufficientPermissions for user %s", user_id)
            return SCOPE_ERROR_SENTINEL
        return f"Failed to get current datetime: {e}"
    except Exception as e:
        return f"Failed to get current datetime: {e}"


@tool
async def get_calendars_info(
    user_id: Annotated[str, InjectedState("user_id")],
) -> str:
    """Get the user's Google Calendars as JSON. Call this before search_events."""
    service = await build_calendar_service(user_id)
    if isinstance(service, str):
        return service

    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            lambda: service.calendarList().list().execute(),
        )
        calendars = [
            {
                "id": item["id"],
                "summary": item.get("summary", ""),
                "timeZone": item.get("timeZone", "UTC"),
            }
            for item in result.get("items", [])
        ]
        return json.dumps(calendars)
    except HttpError as e:
        if _is_insufficient_permissions(e):
            logger.warning("403 insufficientPermissions for user %s", user_id)
            return SCOPE_ERROR_SENTINEL
        return f"Failed to get calendars info: {e}"
    except Exception as e:
        return f"Failed to get calendars info: {e}"


@tool(parse_docstring=True)
async def search_events(
    calendars_info: str,
    min_datetime: str,
    max_datetime: str,
    user_id: Annotated[str, InjectedState("user_id")],
    max_results: int = 10,
    query: str | None = None,
) -> str:
    """Search for events across the user's Google Calendars.

    Args:
        calendars_info: JSON from get_calendars_info with calendar IDs.
        min_datetime: Start of search window in 'YYYY-MM-DD HH:MM:SS' format.
        max_datetime: End of search window in 'YYYY-MM-DD HH:MM:SS' format.
        max_results: Maximum number of events to return per calendar (default 10).
        query: Optional text to filter events by (matches summary, description, etc.).
    """
    service = await build_calendar_service(user_id)
    if isinstance(service, str):
        return service

    try:
        calendars_data: list[dict[str, str]] = json.loads(calendars_info)
    except (json.JSONDecodeError, TypeError):
        return "Invalid calendars_info JSON — call get_calendars_info first."

    all_events: list[dict[str, str | None]] = []
    loop = asyncio.get_running_loop()

    for cal in calendars_data:
        cal_id = cal.get("id", "primary")
        tz_name = cal.get("timeZone", "UTC")

        try:
            tz = ZoneInfo(tz_name)
            time_min = (
                datetime.strptime(min_datetime, "%Y-%m-%d %H:%M:%S")
                .replace(tzinfo=tz)
                .isoformat()
            )
            time_max = (
                datetime.strptime(max_datetime, "%Y-%m-%d %H:%M:%S")
                .replace(tzinfo=tz)
                .isoformat()
            )
        except (ValueError, KeyError) as e:
            return f"Invalid datetime format (use 'YYYY-MM-DD HH:MM:SS'): {e}"

        try:

            def _list_events(
                _service: Any = service,
                _cal_id: str = cal_id,
                _time_min: str = time_min,
                _time_max: str = time_max,
                _max_results: int = max_results,
                _query: str | None = query,
            ) -> dict[str, Any]:
                request = _service.events().list(
                    calendarId=_cal_id,
                    timeMin=_time_min,
                    timeMax=_time_max,
                    maxResults=_max_results,
                    singleEvents=True,
                    orderBy="startTime",
                    **({"q": _query} if _query else {}),
                )
                return request.execute()  # type: ignore[no-any-return]

            result = await loop.run_in_executor(None, _list_events)

            for event in result.get("items", []):
                all_events.append(
                    {
                        "id": event.get("id"),
                        "summary": event.get("summary"),
                        "start": event.get("start", {}).get("dateTime")
                        or event.get("start", {}).get("date"),
                        "end": event.get("end", {}).get("dateTime")
                        or event.get("end", {}).get("date"),
                        "creator": event.get("creator", {}).get("email"),
                        "htmlLink": event.get("htmlLink"),
                    }
                )
        except HttpError as e:
            if _is_insufficient_permissions(e):
                logger.warning("403 insufficientPermissions for user %s", user_id)
                return SCOPE_ERROR_SENTINEL
            logger.warning("Failed to list events for calendar %s: %s", cal_id, e)
        except Exception as e:
            logger.warning("Failed to list events for calendar %s: %s", cal_id, e)

    if not all_events:
        return "No events found in the specified time range."
    return json.dumps(all_events)


# ---------------------------------------------------------------------------
# Write tools (require human-in-the-loop confirmation)
# ---------------------------------------------------------------------------


def _is_all_day(start: str, end: str) -> bool:
    """Check if a datetime string pair represents an all-day event (date-only)."""
    date_pattern = r"^\d{4}-\d{2}-\d{2}$"
    return bool(re.match(date_pattern, start) and re.match(date_pattern, end))


@tool(parse_docstring=True)
async def create_event(
    summary: str,
    start_datetime: str,
    end_datetime: str,
    timezone: str,
    user_id: Annotated[str, InjectedState("user_id")],
    description: str | None = None,
    location: str | None = None,
    attendees: list[str] | None = None,
    calendar_id: str = "primary",
) -> str:
    """Create a new event on the user's Google Calendar.

    Args:
        summary: Title of the event.
        start_datetime: Start in 'YYYY-MM-DD HH:MM:SS' or 'YYYY-MM-DD' for all-day.
        end_datetime: End in 'YYYY-MM-DD HH:MM:SS' or 'YYYY-MM-DD' for all-day.
        timezone: IANA timezone (e.g. 'America/New_York'). Required for timed events.
        description: Optional event description.
        location: Optional event location.
        attendees: Optional list of email addresses to invite.
        calendar_id: Calendar ID to create the event on (default: 'primary').
    """
    event_details = {
        "action": "create_event",
        "summary": summary,
        "start": start_datetime,
        "end": end_datetime,
        "timezone": timezone,
        "description": description,
        "location": location,
        "attendees": attendees,
        "calendar_id": calendar_id,
    }
    interrupt(event_details)

    service = await build_calendar_service(user_id)
    if isinstance(service, str):
        return service

    try:
        if _is_all_day(start_datetime, end_datetime):
            start_body: dict[str, str] = {"date": start_datetime}
            end_body: dict[str, str] = {"date": end_datetime}
        else:
            fmt = "%Y-%m-%d %H:%M:%S"
            tz = ZoneInfo(timezone)
            start_body = {
                "dateTime": datetime.strptime(start_datetime, fmt)
                .replace(tzinfo=tz)
                .isoformat(),
                "timeZone": timezone,
            }
            end_body = {
                "dateTime": datetime.strptime(end_datetime, fmt)
                .replace(tzinfo=tz)
                .isoformat(),
                "timeZone": timezone,
            }

        body: dict[str, Any] = {
            "summary": summary,
            "start": start_body,
            "end": end_body,
        }
        if description:
            body["description"] = description
        if location:
            body["location"] = location
        if attendees:
            body["attendees"] = [{"email": email} for email in attendees]
        body["extendedProperties"] = {"private": {"createdByAgent": "calendar-agent"}}

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            lambda: (
                service.events().insert(calendarId=calendar_id, body=body).execute()
            ),
        )
        link = result.get("htmlLink", "success")
        return f"Event created: {result.get('summary', summary)} — {link}"
    except HttpError as e:
        if _is_insufficient_permissions(e):
            logger.warning("403 insufficientPermissions for user %s", user_id)
            return SCOPE_ERROR_SENTINEL
        return f"Failed to create event: {e}"
    except Exception as e:
        return f"Failed to create event: {e}"


@tool(parse_docstring=True)
async def update_event(
    event_id: str,
    user_id: Annotated[str, InjectedState("user_id")],
    summary: str | None = None,
    start_datetime: str | None = None,
    end_datetime: str | None = None,
    timezone: str | None = None,
    description: str | None = None,
    location: str | None = None,
    attendees: list[str] | None = None,
    calendar_id: str = "primary",
) -> str:
    """Update an existing event on the user's Google Calendar.

    Args:
        event_id: The ID of the event to update (from search_events).
        summary: New title for the event.
        start_datetime: New start time. Both start and end required.
        end_datetime: New end time. Both start and end required.
        timezone: IANA timezone for the new times.
        description: New event description.
        location: New event location.
        attendees: New list of attendee email addresses (replaces existing).
        calendar_id: Calendar ID containing the event (default: 'primary').
    """
    event_details = {
        "action": "update_event",
        "event_id": event_id,
        "summary": summary,
        "start": start_datetime,
        "end": end_datetime,
        "timezone": timezone,
        "description": description,
        "location": location,
        "attendees": attendees,
        "calendar_id": calendar_id,
    }
    interrupt(event_details)

    service = await build_calendar_service(user_id)
    if isinstance(service, str):
        return service

    try:
        loop = asyncio.get_running_loop()

        # Fetch existing event
        existing = await loop.run_in_executor(
            None,
            lambda: (
                service.events().get(calendarId=calendar_id, eventId=event_id).execute()
            ),
        )

        # Apply updates
        if summary is not None:
            existing["summary"] = summary
        if description is not None:
            existing["description"] = description
        if location is not None:
            existing["location"] = location
        if start_datetime and end_datetime:
            tz_name = timezone or existing.get("start", {}).get("timeZone", "UTC")
            if _is_all_day(start_datetime, end_datetime):
                existing["start"] = {"date": start_datetime}
                existing["end"] = {"date": end_datetime}
            else:
                fmt = "%Y-%m-%d %H:%M:%S"
                tz = ZoneInfo(tz_name)
                existing["start"] = {
                    "dateTime": datetime.strptime(start_datetime, fmt)
                    .replace(tzinfo=tz)
                    .isoformat(),
                    "timeZone": tz_name,
                }
                existing["end"] = {
                    "dateTime": datetime.strptime(end_datetime, fmt)
                    .replace(tzinfo=tz)
                    .isoformat(),
                    "timeZone": tz_name,
                }
        if attendees is not None:
            existing["attendees"] = [{"email": email} for email in attendees]

        result = await loop.run_in_executor(
            None,
            lambda: (
                service.events()
                .update(calendarId=calendar_id, eventId=event_id, body=existing)
                .execute()
            ),
        )
        link = result.get("htmlLink", "success")
        return f"Event updated: {result.get('summary', '')} — {link}"
    except HttpError as e:
        if _is_insufficient_permissions(e):
            logger.warning("403 insufficientPermissions for user %s", user_id)
            return SCOPE_ERROR_SENTINEL
        return f"Failed to update event: {e}"
    except Exception as e:
        return f"Failed to update event: {e}"


@tool(parse_docstring=True)
async def delete_event(
    event_id: str,
    user_id: Annotated[str, InjectedState("user_id")],
    calendar_id: str = "primary",
) -> str:
    """Delete an event from the user's Google Calendar.

    Args:
        event_id: The ID of the event to delete (from search_events).
        calendar_id: Calendar ID containing the event (default: 'primary').
    """
    event_details = {
        "action": "delete_event",
        "event_id": event_id,
        "calendar_id": calendar_id,
    }
    interrupt(event_details)

    service = await build_calendar_service(user_id)
    if isinstance(service, str):
        return service

    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: (
                service.events()
                .delete(calendarId=calendar_id, eventId=event_id)
                .execute()
            ),
        )
        return "Event deleted successfully."
    except HttpError as e:
        if _is_insufficient_permissions(e):
            logger.warning("403 insufficientPermissions for user %s", user_id)
            return SCOPE_ERROR_SENTINEL
        return f"Failed to delete event: {e}"
    except Exception as e:
        return f"Failed to delete event: {e}"


# ---------------------------------------------------------------------------
# Exported tools list for binding to the agent
# ---------------------------------------------------------------------------

calendar_tools: list[Any] = [
    get_current_datetime,
    get_calendars_info,
    search_events,
    create_event,
    update_event,
    delete_event,
]
