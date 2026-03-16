import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import ConfirmationCard from "./ConfirmationCard";

const defaultProps = {
  action: "create_event",
  details: {
    summary: "Team standup",
    start: "2026-03-15 09:00:00",
    end: "2026-03-15 09:30:00",
  } as Record<string, unknown>,
  onApprove: vi.fn(),
  onReject: vi.fn(),
};

describe("ConfirmationCard", () => {
  it("should render action details", () => {
    render(<ConfirmationCard {...defaultProps} />);

    expect(screen.getByText(/create_event/i)).toBeInTheDocument();
    expect(screen.getByText(/Team standup/)).toBeInTheDocument();
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
});
