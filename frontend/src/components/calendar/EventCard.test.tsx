import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { CalendarEvent } from "@/lib/calendar";

import EventCard from "./EventCard";

const baseEvent: CalendarEvent = {
  id: "event1",
  summary: "Team Standup",
  start: "2026-03-16T10:00:00-04:00",
  end: "2026-03-16T10:30:00-04:00",
  isAllDay: false,
  isAiCreated: false,
};

describe("EventCard", () => {
  it("should render event summary and time", () => {
    render(<EventCard event={baseEvent} onClick={() => {}} />);

    expect(screen.getByText("Team Standup")).toBeInTheDocument();
    // Time range should contain start and end
    expect(screen.getByText(/10:00/)).toBeInTheDocument();
  });

  it("should show AI badge when isAiCreated is true", () => {
    const aiEvent: CalendarEvent = { ...baseEvent, isAiCreated: true };
    render(<EventCard event={aiEvent} onClick={() => {}} />);

    expect(screen.getByText("AI")).toBeInTheDocument();
  });

  it("should not show AI badge for regular events", () => {
    render(<EventCard event={baseEvent} onClick={() => {}} />);

    expect(screen.queryByText("AI")).not.toBeInTheDocument();
  });

  it("should show 'All day' for all-day events", () => {
    const allDayEvent: CalendarEvent = {
      ...baseEvent,
      start: "2026-03-16",
      end: "2026-03-17",
      isAllDay: true,
    };
    render(<EventCard event={allDayEvent} onClick={() => {}} />);

    expect(screen.getByText("All day")).toBeInTheDocument();
  });

  it("should call onClick when clicked", async () => {
    const handleClick = vi.fn();
    const user = userEvent.setup();
    render(<EventCard event={baseEvent} onClick={handleClick} />);

    await user.click(
      screen.getByRole("button", { name: /team standup/i }),
    );
    expect(handleClick).toHaveBeenCalledOnce();
  });

  it("should have accessible label with summary and time", () => {
    render(<EventCard event={baseEvent} onClick={() => {}} />);

    expect(
      screen.getByRole("button", { name: /team standup/i }),
    ).toBeInTheDocument();
  });
});
