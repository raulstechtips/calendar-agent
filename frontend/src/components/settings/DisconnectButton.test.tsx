import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

vi.mock("next-auth/react", () => ({
  signOut: vi.fn(),
}));

vi.mock("@/actions/settings", () => ({
  revokeAccess: vi.fn(),
}));

import { signOut } from "next-auth/react";
import { revokeAccess } from "@/actions/settings";
import type { Mock } from "vitest";
import { DisconnectButton } from "./DisconnectButton";

const mockedRevokeAccess = revokeAccess as unknown as Mock;
const mockedSignOut = signOut as unknown as Mock;

describe("DisconnectButton", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render disconnect button", () => {
    render(<DisconnectButton />);
    expect(
      screen.getByRole("button", { name: /disconnect/i }),
    ).toBeInTheDocument();
  });

  it("should show confirmation state on first click", async () => {
    const user = userEvent.setup();
    render(<DisconnectButton />);

    await user.click(screen.getByRole("button", { name: /disconnect/i }));

    expect(screen.getByText(/are you sure/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /confirm/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /cancel/i }),
    ).toBeInTheDocument();
  });

  it("should call revokeAccess and signOut on confirm", async () => {
    const user = userEvent.setup();
    mockedRevokeAccess.mockResolvedValue({ success: true });

    render(<DisconnectButton />);

    await user.click(screen.getByRole("button", { name: /disconnect/i }));
    await user.click(screen.getByRole("button", { name: /confirm/i }));

    expect(mockedRevokeAccess).toHaveBeenCalledOnce();
    expect(mockedSignOut).toHaveBeenCalledWith({ redirectTo: "/login" });
  });

  it("should reset to initial state on cancel", async () => {
    const user = userEvent.setup();
    render(<DisconnectButton />);

    await user.click(screen.getByRole("button", { name: /disconnect/i }));
    expect(screen.getByText(/are you sure/i)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /cancel/i }));
    expect(screen.queryByText(/are you sure/i)).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /disconnect/i }),
    ).toBeInTheDocument();
  });

  it("should show error when revoke fails", async () => {
    const user = userEvent.setup();
    mockedRevokeAccess.mockResolvedValue({
      success: false,
      error: "Network error",
    });

    render(<DisconnectButton />);

    await user.click(screen.getByRole("button", { name: /disconnect/i }));
    await user.click(screen.getByRole("button", { name: /confirm/i }));

    expect(await screen.findByText(/network error/i)).toBeInTheDocument();
    expect(mockedSignOut).not.toHaveBeenCalled();
  });
});
