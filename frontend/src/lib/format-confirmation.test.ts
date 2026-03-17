import { describe, expect, it } from "vitest";

import {
  formatConfirmationDetails,
  getActionLabel,
} from "./format-confirmation";

describe("getActionLabel", () => {
  it("should return 'Create Event' for create_event", () => {
    expect(getActionLabel("create_event")).toBe("Create Event");
  });

  it("should return 'Update Event' for update_event", () => {
    expect(getActionLabel("update_event")).toBe("Update Event");
  });

  it("should return 'Delete Event' for delete_event", () => {
    expect(getActionLabel("delete_event")).toBe("Delete Event");
  });

  it("should return title-cased fallback for unknown actions", () => {
    expect(getActionLabel("some_other_action")).toBe("Some Other Action");
  });
});

describe("formatConfirmationDetails", () => {
  it("should format create_event details with summary and times", () => {
    const details: Record<string, unknown> = {
      action: "create_event",
      summary: "Team standup",
      start: "2026-03-15 09:00:00",
      end: "2026-03-15 09:30:00",
      timezone: "America/New_York",
      description: null,
      location: null,
      attendees: null,
      calendar_id: "primary",
    };

    const result = formatConfirmationDetails("create_event", details);

    // Should contain Event label with summary
    const eventField = result.find((f) => f.label === "Event");
    expect(eventField).toBeDefined();
    expect(eventField?.value).toBe("Team standup");

    // Should contain Start and End
    const startField = result.find((f) => f.label === "Start");
    expect(startField).toBeDefined();
    expect(startField?.value).toContain("Mar");

    const endField = result.find((f) => f.label === "End");
    expect(endField).toBeDefined();
  });

  it("should skip null values", () => {
    const details: Record<string, unknown> = {
      action: "create_event",
      summary: "Lunch",
      start: "2026-03-15 12:00:00",
      end: "2026-03-15 13:00:00",
      timezone: "UTC",
      description: null,
      location: null,
      attendees: null,
      calendar_id: "primary",
    };

    const result = formatConfirmationDetails("create_event", details);

    expect(result.find((f) => f.label === "Description")).toBeUndefined();
    expect(result.find((f) => f.label === "Location")).toBeUndefined();
    expect(result.find((f) => f.label === "Attendees")).toBeUndefined();
  });

  it("should skip internal fields", () => {
    const details: Record<string, unknown> = {
      action: "create_event",
      summary: "Lunch",
      start: "2026-03-15 12:00:00",
      end: "2026-03-15 13:00:00",
      timezone: "UTC",
      calendar_id: "primary",
    };

    const result = formatConfirmationDetails("create_event", details);
    const labels = result.map((f) => f.label);

    expect(labels).not.toContain("calendar_id");
    expect(labels).not.toContain("timezone");
    expect(labels).not.toContain("action");
    expect(labels).not.toContain("event_id");
  });

  it("should format attendees as comma-separated list", () => {
    const details: Record<string, unknown> = {
      action: "create_event",
      summary: "Sync",
      start: "2026-03-15 14:00:00",
      end: "2026-03-15 15:00:00",
      timezone: "UTC",
      attendees: ["alice@example.com", "bob@example.com"],
      calendar_id: "primary",
    };

    const result = formatConfirmationDetails("create_event", details);
    const attendeesField = result.find((f) => f.label === "Attendees");

    expect(attendeesField).toBeDefined();
    expect(attendeesField?.value).toBe("alice@example.com, bob@example.com");
  });

  it("should include description and location when present", () => {
    const details: Record<string, unknown> = {
      action: "create_event",
      summary: "Meeting",
      start: "2026-03-15 10:00:00",
      end: "2026-03-15 11:00:00",
      timezone: "UTC",
      description: "Quarterly review",
      location: "Room 42",
      calendar_id: "primary",
    };

    const result = formatConfirmationDetails("create_event", details);

    expect(result.find((f) => f.label === "Description")?.value).toBe(
      "Quarterly review",
    );
    expect(result.find((f) => f.label === "Location")?.value).toBe("Room 42");
  });

  it("should handle delete_event with minimal fields", () => {
    const details: Record<string, unknown> = {
      action: "delete_event",
      event_id: "abc123",
      calendar_id: "primary",
    };

    const result = formatConfirmationDetails("delete_event", details);

    // Should have no fields (all are internal)
    expect(result.length).toBe(0);
  });
});
