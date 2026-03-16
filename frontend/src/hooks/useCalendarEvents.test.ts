import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { CalendarEvent, CalendarResult } from "@/lib/calendar";

// Mock the calendar module
const mockFetchCalendarEvents = vi.fn<
  (
    accessToken: string,
    timeMin: string,
    timeMax: string,
    signal?: AbortSignal,
  ) => Promise<CalendarResult>
>();
vi.mock("@/lib/calendar", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/calendar")>();
  return {
    ...actual,
    fetchCalendarEvents: (
      ...args: [string, string, string, AbortSignal?]
    ) => mockFetchCalendarEvents(...args),
  };
});

import { useCalendarEvents } from "./useCalendarEvents";

const mockEvent: CalendarEvent = {
  id: "event1",
  summary: "Test Event",
  start: "2026-03-16T10:00:00-04:00",
  end: "2026-03-16T11:00:00-04:00",
  isAllDay: false,
  isAiCreated: false,
};

describe("useCalendarEvents", () => {
  const timeMin = "2026-03-16T00:00:00Z";
  const timeMax = "2026-03-23T00:00:00Z";

  beforeEach(() => {
    mockFetchCalendarEvents.mockReset();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should start in loading state when access token is provided", () => {
    mockFetchCalendarEvents.mockReturnValue(new Promise(() => {})); // never resolves

    const { result } = renderHook(() =>
      useCalendarEvents("test-token", timeMin, timeMax),
    );

    expect(result.current.isLoading).toBe(true);
    expect(result.current.events).toEqual([]);
    expect(result.current.error).toBeNull();
  });

  it("should not fetch when access token is undefined", () => {
    const { result } = renderHook(() =>
      useCalendarEvents(undefined, timeMin, timeMax),
    );

    expect(result.current.isLoading).toBe(false);
    expect(mockFetchCalendarEvents).not.toHaveBeenCalled();
  });

  it("should return events on successful fetch", async () => {
    mockFetchCalendarEvents.mockResolvedValue({
      ok: true,
      events: [mockEvent],
    });

    const { result } = renderHook(() =>
      useCalendarEvents("test-token", timeMin, timeMax),
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.events).toEqual([mockEvent]);
    expect(result.current.error).toBeNull();
  });

  it("should set scope_required error on 403", async () => {
    mockFetchCalendarEvents.mockResolvedValue({
      ok: false,
      error: "scope_required",
      message: "Calendar access not granted.",
    });

    const { result } = renderHook(() =>
      useCalendarEvents("test-token", timeMin, timeMax),
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBe("scope_required");
    expect(result.current.events).toEqual([]);
  });

  it("should set api_error on failure", async () => {
    mockFetchCalendarEvents.mockResolvedValue({
      ok: false,
      error: "api_error",
      message: "Failed to fetch.",
    });

    const { result } = renderHook(() =>
      useCalendarEvents("test-token", timeMin, timeMax),
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBe("api_error");
  });

  it("should refetch when date range changes", async () => {
    mockFetchCalendarEvents.mockResolvedValue({
      ok: true,
      events: [mockEvent],
    });

    const { result, rerender } = renderHook(
      ({ timeMin, timeMax }: { timeMin: string; timeMax: string }) =>
        useCalendarEvents("test-token", timeMin, timeMax),
      { initialProps: { timeMin, timeMax } },
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mockFetchCalendarEvents).toHaveBeenCalledTimes(1);

    // Change date range
    rerender({
      timeMin: "2026-03-23T00:00:00Z",
      timeMax: "2026-03-30T00:00:00Z",
    });

    await waitFor(() => {
      expect(mockFetchCalendarEvents).toHaveBeenCalledTimes(2);
    });
  });

  it("should support refetch callback", async () => {
    mockFetchCalendarEvents.mockResolvedValue({
      ok: true,
      events: [mockEvent],
    });

    const { result } = renderHook(() =>
      useCalendarEvents("test-token", timeMin, timeMax),
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mockFetchCalendarEvents).toHaveBeenCalledTimes(1);

    // Trigger refetch
    act(() => {
      result.current.refetch();
    });

    await waitFor(() => {
      expect(mockFetchCalendarEvents).toHaveBeenCalledTimes(2);
    });
  });
});
