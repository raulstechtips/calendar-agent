import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import ConfirmationCard from "./ConfirmationCard";

const defaultProps = {
  action: "create_event",
  details: {
    action: "create_event",
    summary: "Team standup",
    start: "2026-03-15 09:00:00",
    end: "2026-03-15 09:30:00",
    timezone: "America/New_York",
    calendar_id: "primary",
  } as Record<string, unknown>,
  status: "pending" as const,
  onApprove: vi.fn(),
  onReject: vi.fn(),
};

describe("ConfirmationCard", () => {
  it("should render action label with icon", () => {
    render(<ConfirmationCard {...defaultProps} />);

    expect(screen.getByText("Create Event")).toBeInTheDocument();
  });

  it("should render formatted event name", () => {
    render(<ConfirmationCard {...defaultProps} />);

    expect(screen.getByText("Team standup")).toBeInTheDocument();
  });

  it("should render formatted date/time", () => {
    render(<ConfirmationCard {...defaultProps} />);

    // Should show formatted dates, not raw strings
    const startField = screen.getByText("Start:");
    expect(startField).toBeInTheDocument();
    // The formatted date should contain "Mar" (month abbreviation)
    expect(startField.nextElementSibling?.textContent).toContain("Mar");
  });

  it("should hide internal fields", () => {
    render(<ConfirmationCard {...defaultProps} />);

    expect(screen.queryByText("calendar_id:")).not.toBeInTheDocument();
    expect(screen.queryByText("timezone:")).not.toBeInTheDocument();
    expect(screen.queryByText("action:")).not.toBeInTheDocument();
  });

  it("should call onApprove when approve button is clicked", async () => {
    const user = userEvent.setup();
    const onApprove = vi.fn();
    render(<ConfirmationCard {...defaultProps} onApprove={onApprove} />);

    await user.click(screen.getByRole("button", { name: /approve/i }));

    expect(onApprove).toHaveBeenCalledOnce();
  });

  it("should call onReject when reject button is clicked", async () => {
    const user = userEvent.setup();
    const onReject = vi.fn();
    render(<ConfirmationCard {...defaultProps} onReject={onReject} />);

    await user.click(screen.getByRole("button", { name: /reject/i }));

    expect(onReject).toHaveBeenCalledOnce();
  });

  it("should disable buttons when disabled prop is true", () => {
    render(<ConfirmationCard {...defaultProps} disabled />);

    expect(screen.getByRole("button", { name: /approve/i })).toBeDisabled();
    expect(screen.getByRole("button", { name: /reject/i })).toBeDisabled();
  });

  it("should show Confirmed badge when status is confirmed", () => {
    render(<ConfirmationCard {...defaultProps} status="confirmed" />);

    expect(screen.getByText("Confirmed")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /approve/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /reject/i }),
    ).not.toBeInTheDocument();
  });

  it("should show Cancelled badge when status is cancelled", () => {
    render(<ConfirmationCard {...defaultProps} status="cancelled" />);

    expect(screen.getByText("Cancelled")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /approve/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /reject/i }),
    ).not.toBeInTheDocument();
  });

  it("should render Update Event label for update_event action", () => {
    render(
      <ConfirmationCard
        {...defaultProps}
        action="update_event"
        details={{
          action: "update_event",
          event_id: "abc",
          summary: "Renamed meeting",
          calendar_id: "primary",
        }}
      />,
    );

    expect(screen.getByText("Update Event")).toBeInTheDocument();
    expect(screen.getByText("Renamed meeting")).toBeInTheDocument();
  });

  it("should render Delete Event label for delete_event action", () => {
    render(
      <ConfirmationCard
        {...defaultProps}
        action="delete_event"
        details={{
          action: "delete_event",
          event_id: "abc",
          calendar_id: "primary",
        }}
      />,
    );

    expect(screen.getByText("Delete Event")).toBeInTheDocument();
  });
});
