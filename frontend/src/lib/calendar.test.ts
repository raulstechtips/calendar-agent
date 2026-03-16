import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  addDays,
  fetchCalendarEvents,
  formatDateLabel,
  formatISODate,
  getDayRange,
  getEventPosition,
  getWeekRange,
  isSameDay,
  parseDate,
  type CalendarEvent,
} from "./calendar";

// ---------------------------------------------------------------------------
// Date helpers
// ---------------------------------------------------------------------------

describe("addDays", () => {
  it("should add positive days", () => {
    const date = new Date(2026, 2, 16); // March 16, 2026
    const result = addDays(date, 3);
    expect(result.getDate()).toBe(19);
    expect(result.getMonth()).toBe(2);
  });

  it("should subtract days with negative value", () => {
    const date = new Date(2026, 2, 16);
    const result = addDays(date, -5);
    expect(result.getDate()).toBe(11);
  });

  it("should not mutate the original date", () => {
    const date = new Date(2026, 2, 16);
    addDays(date, 3);
    expect(date.getDate()).toBe(16);
  });
});

describe("isSameDay", () => {
  it("should return true for same day", () => {
    const a = new Date(2026, 2, 16, 10, 30);
    const b = new Date(2026, 2, 16, 22, 0);
    expect(isSameDay(a, b)).toBe(true);
  });

  it("should return false for different days", () => {
    const a = new Date(2026, 2, 16);
    const b = new Date(2026, 2, 17);
    expect(isSameDay(a, b)).toBe(false);
  });
});

describe("getDayRange", () => {
  it("should return midnight to next midnight", () => {
    const date = new Date(2026, 2, 16, 14, 30);
    const { start, end } = getDayRange(date);
    expect(start.getHours()).toBe(0);
    expect(start.getMinutes()).toBe(0);
    expect(start.getDate()).toBe(16);
    expect(end.getDate()).toBe(17);
    expect(end.getHours()).toBe(0);
  });
});

describe("getWeekRange", () => {
  it("should return Monday to next Monday", () => {
    // March 16, 2026 is a Monday
    const date = new Date(2026, 2, 16);
    const { start, end } = getWeekRange(date);
    expect(start.getDay()).toBe(1); // Monday
    expect(start.getDate()).toBe(16);
    expect(end.getDate()).toBe(23); // Next Monday
  });

  it("should go back to Monday if given a Wednesday", () => {
    // March 18, 2026 is a Wednesday
    const date = new Date(2026, 2, 18);
    const { start, end } = getWeekRange(date);
    expect(start.getDay()).toBe(1); // Monday
    expect(start.getDate()).toBe(16);
    expect(end.getDate()).toBe(23);
  });

  it("should handle Sunday by going back to previous Monday", () => {
    // March 22, 2026 is a Sunday
    const date = new Date(2026, 2, 22);
    const { start } = getWeekRange(date);
    expect(start.getDay()).toBe(1);
    expect(start.getDate()).toBe(16);
  });
});

describe("formatDateLabel", () => {
  it("should format day view label", () => {
    const date = new Date(2026, 2, 16);
    const label = formatDateLabel(date, "day");
    expect(label).toContain("March");
    expect(label).toContain("16");
    expect(label).toContain("2026");
  });

  it("should format week view label as a range", () => {
    const date = new Date(2026, 2, 16); // Monday
    const label = formatDateLabel(date, "week");
    expect(label).toContain("16");
    expect(label).toContain("22");
  });
});

describe("getEventPosition", () => {
  const hourHeight = 64;

  it("should position a 10am-11am event", () => {
    const { top, height } = getEventPosition(
      "2026-03-16T10:00:00-04:00",
      "2026-03-16T11:00:00-04:00",
      hourHeight,
    );
    expect(top).toBe(10 * hourHeight);
    expect(height).toBe(hourHeight);
  });

  it("should handle 30-minute events", () => {
    const { height } = getEventPosition(
      "2026-03-16T10:00:00-04:00",
      "2026-03-16T10:30:00-04:00",
      hourHeight,
    );
    expect(height).toBe(hourHeight / 2);
  });

  it("should enforce minimum height", () => {
    const { height } = getEventPosition(
      "2026-03-16T10:00:00-04:00",
      "2026-03-16T10:10:00-04:00",
      hourHeight,
    );
    // 10 minutes = ~10.67px, but minimum should be usable
    expect(height).toBeGreaterThanOrEqual(16);
  });

  it("should clamp cross-midnight events to end of day", () => {
    // 23:00 to 01:00 next day — should render from 23:00 to 24:00 (end of grid)
    const { top, height } = getEventPosition(
      "2026-03-16T23:00:00-04:00",
      "2026-03-17T01:00:00-04:00",
      hourHeight,
    );
    expect(top).toBe(23 * hourHeight);
    expect(height).toBe(hourHeight); // 1 hour (clamped to midnight)
  });
});

describe("formatISODate", () => {
  it("should format a date as YYYY-MM-DD", () => {
    const date = new Date(2026, 2, 16);
    expect(formatISODate(date)).toBe("2026-03-16");
  });

  it("should zero-pad single-digit months and days", () => {
    const date = new Date(2026, 0, 5); // Jan 5
    expect(formatISODate(date)).toBe("2026-01-05");
  });
});

describe("parseDate", () => {
  it("should parse ISO date string", () => {
    const date = parseDate("2026-03-16");
    expect(date.getFullYear()).toBe(2026);
    expect(date.getMonth()).toBe(2); // 0-indexed
    expect(date.getDate()).toBe(16);
  });

  it("should return today for undefined", () => {
    const date = parseDate(undefined);
    const today = new Date();
    expect(isSameDay(date, today)).toBe(true);
  });

  it("should return today for invalid string", () => {
    const date = parseDate("not-a-date");
    const today = new Date();
    expect(isSameDay(date, today)).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// fetchCalendarEvents
// ---------------------------------------------------------------------------

describe("fetchCalendarEvents", () => {
  const mockAccessToken = "ya29.test-access-token";
  const timeMin = "2026-03-16T00:00:00Z";
  const timeMax = "2026-03-23T00:00:00Z";

  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should map Google API response to CalendarEvent array", async () => {
    const googleResponse = {
      kind: "calendar#events",
      items: [
        {
          id: "event1",
          summary: "Team Standup",
          description: "Daily sync",
          location: "Room 101",
          start: { dateTime: "2026-03-16T10:00:00-04:00" },
          end: { dateTime: "2026-03-16T10:30:00-04:00" },
          htmlLink: "https://calendar.google.com/event?eid=event1",
          attendees: [
            {
              email: "alice@example.com",
              displayName: "Alice",
              responseStatus: "accepted",
            },
          ],
        },
      ],
    };

    vi.mocked(fetch).mockResolvedValue(
      new Response(JSON.stringify(googleResponse), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    const result = await fetchCalendarEvents(mockAccessToken, timeMin, timeMax);

    expect(result.ok).toBe(true);
    if (!result.ok) return;

    expect(result.events).toHaveLength(1);
    const event = result.events[0] as CalendarEvent;
    expect(event.id).toBe("event1");
    expect(event.summary).toBe("Team Standup");
    expect(event.description).toBe("Daily sync");
    expect(event.location).toBe("Room 101");
    expect(event.start).toBe("2026-03-16T10:00:00-04:00");
    expect(event.end).toBe("2026-03-16T10:30:00-04:00");
    expect(event.isAllDay).toBe(false);
    expect(event.isAiCreated).toBe(false);
    expect(event.htmlLink).toBe(
      "https://calendar.google.com/event?eid=event1",
    );
    expect(event.attendees).toEqual([
      {
        email: "alice@example.com",
        displayName: "Alice",
        responseStatus: "accepted",
      },
    ]);
  });

  it("should handle all-day events", async () => {
    const googleResponse = {
      items: [
        {
          id: "allday1",
          summary: "Company Holiday",
          start: { date: "2026-03-20" },
          end: { date: "2026-03-21" },
        },
      ],
    };

    vi.mocked(fetch).mockResolvedValue(
      new Response(JSON.stringify(googleResponse), { status: 200 }),
    );

    const result = await fetchCalendarEvents(mockAccessToken, timeMin, timeMax);

    expect(result.ok).toBe(true);
    if (!result.ok) return;

    expect(result.events[0]?.isAllDay).toBe(true);
    expect(result.events[0]?.start).toBe("2026-03-20");
    expect(result.events[0]?.end).toBe("2026-03-21");
  });

  it("should detect AI-created events via extendedProperties", async () => {
    const googleResponse = {
      items: [
        {
          id: "ai1",
          summary: "AI-Scheduled Meeting",
          start: { dateTime: "2026-03-16T14:00:00-04:00" },
          end: { dateTime: "2026-03-16T15:00:00-04:00" },
          extendedProperties: {
            private: { createdByAgent: "calendar-agent" },
          },
        },
      ],
    };

    vi.mocked(fetch).mockResolvedValue(
      new Response(JSON.stringify(googleResponse), { status: 200 }),
    );

    const result = await fetchCalendarEvents(mockAccessToken, timeMin, timeMax);

    expect(result.ok).toBe(true);
    if (!result.ok) return;

    expect(result.events[0]?.isAiCreated).toBe(true);
  });

  it("should return scope_required on 403", async () => {
    vi.mocked(fetch).mockResolvedValue(
      new Response(JSON.stringify({ error: { code: 403 } }), { status: 403 }),
    );

    const result = await fetchCalendarEvents(mockAccessToken, timeMin, timeMax);

    expect(result.ok).toBe(false);
    if (result.ok) return;
    expect(result.error).toBe("scope_required");
  });

  it("should return auth_error on 401", async () => {
    vi.mocked(fetch).mockResolvedValue(
      new Response(JSON.stringify({ error: { code: 401 } }), { status: 401 }),
    );

    const result = await fetchCalendarEvents(mockAccessToken, timeMin, timeMax);

    expect(result.ok).toBe(false);
    if (result.ok) return;
    expect(result.error).toBe("auth_error");
  });

  it("should return api_error on network failure", async () => {
    vi.mocked(fetch).mockRejectedValue(new Error("Network error"));

    const result = await fetchCalendarEvents(mockAccessToken, timeMin, timeMax);

    expect(result.ok).toBe(false);
    if (result.ok) return;
    expect(result.error).toBe("api_error");
  });

  it("should return empty events array when no events", async () => {
    const googleResponse = { items: [] };

    vi.mocked(fetch).mockResolvedValue(
      new Response(JSON.stringify(googleResponse), { status: 200 }),
    );

    const result = await fetchCalendarEvents(mockAccessToken, timeMin, timeMax);

    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.events).toEqual([]);
  });

  it("should pass correct query parameters to Google API", async () => {
    vi.mocked(fetch).mockResolvedValue(
      new Response(JSON.stringify({ items: [] }), { status: 200 }),
    );

    await fetchCalendarEvents(mockAccessToken, timeMin, timeMax);

    expect(fetch).toHaveBeenCalledOnce();
    const calledUrl = vi.mocked(fetch).mock.calls[0]?.[0];
    expect(calledUrl).toBeInstanceOf(URL);
    const url = calledUrl as URL;
    expect(url.origin).toBe("https://www.googleapis.com");
    expect(url.pathname).toBe(
      "/calendar/v3/calendars/primary/events",
    );
    expect(url.searchParams.get("timeMin")).toBe(timeMin);
    expect(url.searchParams.get("timeMax")).toBe(timeMax);
    expect(url.searchParams.get("singleEvents")).toBe("true");
    expect(url.searchParams.get("orderBy")).toBe("startTime");
    expect(url.searchParams.get("maxResults")).toBe("250");
  });

  it("should pass Authorization header with Bearer token", async () => {
    vi.mocked(fetch).mockResolvedValue(
      new Response(JSON.stringify({ items: [] }), { status: 200 }),
    );

    await fetchCalendarEvents(mockAccessToken, timeMin, timeMax);

    const calledInit = vi.mocked(fetch).mock.calls[0]?.[1];
    expect(calledInit?.headers).toEqual(
      expect.objectContaining({
        Authorization: `Bearer ${mockAccessToken}`,
      }),
    );
  });

  it("should support abort signal", async () => {
    const controller = new AbortController();
    controller.abort();

    vi.mocked(fetch).mockRejectedValue(new DOMException("Aborted", "AbortError"));

    const result = await fetchCalendarEvents(
      mockAccessToken,
      timeMin,
      timeMax,
      controller.signal,
    );

    expect(result.ok).toBe(false);
    if (result.ok) return;
    expect(result.error).toBe("api_error");
  });
});
