import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { CalendarResult } from "@/lib/calendar";

// Mock next-auth/react
const mockUseSession = vi.fn();
vi.mock("next-auth/react", () => ({
  useSession: () => mockUseSession(),
  signIn: vi.fn(),
}));

// Mock next/navigation
const mockSearchParams = new URLSearchParams();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  useSearchParams: () => mockSearchParams,
}));

// Mock fetchCalendarEvents
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

import CalendarShell from "./CalendarShell";

describe("CalendarShell", () => {
  it("should show skeleton while auth is loading", () => {
    mockUseSession.mockReturnValue({ data: null, status: "loading" });

    render(<CalendarShell />);

    // Skeleton elements should be present
    const skeletons = document.querySelectorAll("[data-slot='skeleton']");
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it("should show scope prompt when calendar scope not granted", async () => {
    mockUseSession.mockReturnValue({
      data: { accessToken: "test-token" },
      status: "authenticated",
    });

    mockFetchCalendarEvents.mockResolvedValue({
      ok: false,
      error: "scope_required",
      message: "Calendar access not granted.",
    });

    render(<CalendarShell />);

    expect(
      await screen.findByText(/calendar access required/i),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /grant calendar access/i }),
    ).toBeInTheDocument();
  });

  it("should show empty state when no events", async () => {
    mockUseSession.mockReturnValue({
      data: { accessToken: "test-token" },
      status: "authenticated",
    });

    mockFetchCalendarEvents.mockResolvedValue({
      ok: true,
      events: [],
    });

    render(<CalendarShell />);

    expect(
      await screen.findByText(/no events in this time range/i),
    ).toBeInTheDocument();
  });

  it("should render events when fetched successfully", async () => {
    mockUseSession.mockReturnValue({
      data: { accessToken: "test-token" },
      status: "authenticated",
    });

    mockFetchCalendarEvents.mockResolvedValue({
      ok: true,
      events: [
        {
          id: "e1",
          summary: "Team Standup",
          start: "2026-03-16T10:00:00-04:00",
          end: "2026-03-16T10:30:00-04:00",
          isAllDay: false,
          isAiCreated: false,
        },
      ],
    });

    render(<CalendarShell />);

    expect(await screen.findByText("Team Standup")).toBeInTheDocument();
  });

  it("should show error state on API error", async () => {
    mockUseSession.mockReturnValue({
      data: { accessToken: "test-token" },
      status: "authenticated",
    });

    mockFetchCalendarEvents.mockResolvedValue({
      ok: false,
      error: "api_error",
      message: "Failed to fetch.",
    });

    render(<CalendarShell />);

    expect(
      await screen.findByText(/failed to load calendar events/i),
    ).toBeInTheDocument();
  });

  it("should open event detail dialog on event click", async () => {
    mockUseSession.mockReturnValue({
      data: { accessToken: "test-token" },
      status: "authenticated",
    });

    mockFetchCalendarEvents.mockResolvedValue({
      ok: true,
      events: [
        {
          id: "e1",
          summary: "Team Standup",
          description: "Daily sync meeting",
          start: "2026-03-16T10:00:00-04:00",
          end: "2026-03-16T10:30:00-04:00",
          isAllDay: false,
          isAiCreated: false,
        },
      ],
    });

    const user = userEvent.setup();
    render(<CalendarShell />);

    // Wait for events to load
    const eventButton = await screen.findByRole("button", {
      name: /team standup/i,
    });
    await user.click(eventButton);

    // Dialog should show event details
    await waitFor(() => {
      expect(screen.getByText("Daily sync meeting")).toBeInTheDocument();
    });
  });
});
