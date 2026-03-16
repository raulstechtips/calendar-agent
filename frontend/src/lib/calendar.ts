/**
 * Google Calendar API client and date helpers for the calendar view.
 * Used from browser — fetches directly from Google Calendar API
 * with the user's OAuth access token.
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface CalendarEvent {
  id: string;
  summary: string;
  description?: string;
  location?: string;
  start: string;
  end: string;
  isAllDay: boolean;
  htmlLink?: string;
  attendees?: Array<{
    email: string;
    displayName?: string;
    responseStatus?: string;
  }>;
  isAiCreated: boolean;
}

export type CalendarViewType = "day" | "week";

export type CalendarResult =
  | { ok: true; events: CalendarEvent[] }
  | {
      ok: false;
      error: "scope_required" | "auth_error" | "api_error";
      message: string;
    };

// ---------------------------------------------------------------------------
// Google Calendar API types (subset of response)
// ---------------------------------------------------------------------------

interface GoogleEventDateTime {
  dateTime?: string;
  date?: string;
  timeZone?: string;
}

interface GoogleAttendee {
  email?: string;
  displayName?: string;
  responseStatus?: string;
}

interface GoogleEvent {
  id?: string;
  summary?: string;
  description?: string;
  location?: string;
  start?: GoogleEventDateTime;
  end?: GoogleEventDateTime;
  htmlLink?: string;
  attendees?: GoogleAttendee[];
  extendedProperties?: {
    private?: Record<string, string>;
  };
}

interface GoogleEventsResponse {
  items?: GoogleEvent[];
}

// ---------------------------------------------------------------------------
// API fetch
// ---------------------------------------------------------------------------

const GOOGLE_CALENDAR_BASE =
  "https://www.googleapis.com/calendar/v3/calendars/primary/events";

/** Fetch calendar events directly from the Google Calendar API. */
export async function fetchCalendarEvents(
  accessToken: string,
  timeMin: string,
  timeMax: string,
  signal?: AbortSignal,
): Promise<CalendarResult> {
  const url = new URL(GOOGLE_CALENDAR_BASE);
  url.searchParams.set("timeMin", timeMin);
  url.searchParams.set("timeMax", timeMax);
  url.searchParams.set("singleEvents", "true");
  url.searchParams.set("orderBy", "startTime");
  url.searchParams.set("maxResults", "250");

  try {
    const response = await fetch(url, {
      headers: { Authorization: `Bearer ${accessToken}` },
      signal,
    });

    if (response.status === 403) {
      return {
        ok: false,
        error: "scope_required",
        message:
          "Calendar access not granted. Please grant calendar permissions.",
      };
    }

    if (response.status === 401) {
      return {
        ok: false,
        error: "auth_error",
        message: "Authentication expired. Please sign in again.",
      };
    }

    if (!response.ok) {
      return {
        ok: false,
        error: "api_error",
        message: `Google Calendar API error: ${response.status}`,
      };
    }

    const data = (await response.json()) as GoogleEventsResponse;
    const events = (data.items ?? []).map(mapGoogleEvent);
    return { ok: true, events };
  } catch {
    return {
      ok: false,
      error: "api_error",
      message: "Failed to fetch calendar events.",
    };
  }
}

function mapGoogleEvent(event: GoogleEvent): CalendarEvent {
  const startDateTime = event.start?.dateTime;
  const startDate = event.start?.date;
  const endDateTime = event.end?.dateTime;
  const endDate = event.end?.date;

  return {
    id: event.id ?? "",
    summary: event.summary ?? "(No title)",
    description: event.description,
    location: event.location,
    start: startDateTime ?? startDate ?? "",
    end: endDateTime ?? endDate ?? "",
    isAllDay: !startDateTime && !!startDate,
    htmlLink: event.htmlLink,
    attendees: event.attendees
      ?.filter(
        (a): a is { email: string; displayName?: string; responseStatus?: string } =>
          typeof a.email === "string",
      )
      .map((a) => ({
        email: a.email,
        displayName: a.displayName,
        responseStatus: a.responseStatus,
      })),
    isAiCreated:
      event.extendedProperties?.private?.["createdByAgent"] === "calendar-agent",
  };
}

// ---------------------------------------------------------------------------
// Date helpers
// ---------------------------------------------------------------------------

/** Add (or subtract) days from a date. Returns a new Date. */
export function addDays(date: Date, days: number): Date {
  const result = new Date(date);
  result.setDate(result.getDate() + days);
  return result;
}

/** Check if two dates are the same calendar day. */
export function isSameDay(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

/** Get start (midnight) and end (next midnight) for a given day. */
export function getDayRange(date: Date): { start: Date; end: Date } {
  const start = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const end = new Date(
    date.getFullYear(),
    date.getMonth(),
    date.getDate() + 1,
  );
  return { start, end };
}

/** Get the Monday–Sunday range for the week containing the given date. */
export function getWeekRange(date: Date): { start: Date; end: Date } {
  const day = date.getDay(); // 0=Sun, 1=Mon, ...
  // Offset to Monday: if Sunday (0), go back 6; otherwise go back (day - 1)
  const mondayOffset = day === 0 ? -6 : 1 - day;
  const start = new Date(
    date.getFullYear(),
    date.getMonth(),
    date.getDate() + mondayOffset,
  );
  const end = addDays(start, 7);
  return { start, end };
}

/** Format a date label for display in the toolbar. */
export function formatDateLabel(date: Date, view: CalendarViewType): string {
  if (view === "day") {
    return date.toLocaleDateString("en-US", {
      weekday: "long",
      month: "long",
      day: "numeric",
      year: "numeric",
    });
  }

  // Week view: show range "Mar 16 – 22, 2026"
  const { start, end: nextMonday } = getWeekRange(date);
  const sunday = addDays(nextMonday, -1);

  if (start.getMonth() === sunday.getMonth()) {
    const month = start.toLocaleDateString("en-US", { month: "short" });
    return `${month} ${start.getDate()} – ${sunday.getDate()}, ${start.getFullYear()}`;
  }

  // Cross-month: "Mar 30 – Apr 5, 2026"
  const startStr = start.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
  const endStr = sunday.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
  return `${startStr} – ${endStr}, ${sunday.getFullYear()}`;
}

/** Calculate top offset and height for a timed event in the grid. */
export function getEventPosition(
  startISO: string,
  endISO: string,
  hourHeight: number,
): { top: number; height: number } {
  const start = new Date(startISO);
  const end = new Date(endISO);

  const startMinutes = start.getHours() * 60 + start.getMinutes();
  let endMinutes = end.getHours() * 60 + end.getMinutes();

  // Clamp cross-midnight events to end of day (24:00)
  if (endMinutes <= startMinutes && end.getTime() > start.getTime()) {
    endMinutes = 24 * 60;
  }

  const durationMinutes = Math.max(endMinutes - startMinutes, 0);
  const top = (startMinutes / 60) * hourHeight;
  const height = Math.max((durationMinutes / 60) * hourHeight, 16); // min 16px

  return { top, height };
}

/** Parse a date string from URL params, falling back to today. */
export function parseDate(dateString: string | undefined): Date {
  if (!dateString) return new Date();
  const parsed = new Date(dateString + "T00:00:00");
  if (isNaN(parsed.getTime())) return new Date();
  return parsed;
}

/** Format a Date as YYYY-MM-DD for URL params. */
export function formatISODate(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}
