import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

vi.mock("next-auth/react", () => ({
  signIn: vi.fn(),
}));

import { signIn } from "next-auth/react";
import { ScopeManager } from "./ScopeManager";

describe("ScopeManager", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render granted scopes as badges", () => {
    render(
      <ScopeManager
        scopes={[
          "openid",
          "email",
          "profile",
          "https://www.googleapis.com/auth/calendar.events",
        ]}
      />,
    );

    expect(screen.getByText("Google Calendar")).toBeInTheDocument();
    expect(screen.getByText("Email")).toBeInTheDocument();
  });

  it("should show grant button for missing calendar scope", () => {
    render(<ScopeManager scopes={["openid", "email", "profile"]} />);

    expect(
      screen.getByRole("button", { name: /grant calendar access/i }),
    ).toBeInTheDocument();
  });

  it("should hide grant button when calendar scope is already granted", () => {
    render(
      <ScopeManager
        scopes={[
          "openid",
          "email",
          "profile",
          "https://www.googleapis.com/auth/calendar.events",
        ]}
      />,
    );

    expect(
      screen.queryByRole("button", { name: /grant calendar access/i }),
    ).not.toBeInTheDocument();
  });

  it("should call signIn with correct scope on grant button click", async () => {
    const user = userEvent.setup();
    render(<ScopeManager scopes={["openid", "email", "profile"]} />);

    await user.click(
      screen.getByRole("button", { name: /grant calendar access/i }),
    );

    expect(signIn).toHaveBeenCalledWith(
      "google",
      { redirectTo: "/settings" },
      {
        scope:
          "openid email profile https://www.googleapis.com/auth/calendar.events",
      },
    );
  });

  it("should show grant button for missing gmail scope", () => {
    render(<ScopeManager scopes={["openid", "email", "profile"]} />);

    expect(
      screen.getByRole("button", { name: /grant gmail access/i }),
    ).toBeInTheDocument();
  });

  it("should hide grant button when gmail scope is already granted", () => {
    render(
      <ScopeManager
        scopes={[
          "openid",
          "email",
          "profile",
          "https://www.googleapis.com/auth/gmail.metadata",
        ]}
      />,
    );

    expect(
      screen.queryByRole("button", { name: /grant gmail access/i }),
    ).not.toBeInTheDocument();
  });
});
