import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import LoginPage from "./page";

vi.mock("../../../../auth", () => ({
  signIn: vi.fn(),
}));

describe("LoginPage", () => {
  it('renders the "Sign in with Google" button', () => {
    render(<LoginPage />);
    expect(
      screen.getByRole("button", { name: /sign in with google/i }),
    ).toBeInTheDocument();
  });

  it("renders the app title", () => {
    render(<LoginPage />);
    expect(
      screen.getByRole("heading", { name: /calendar assistant/i }),
    ).toBeInTheDocument();
  });

  it("renders the sign-in description", () => {
    render(<LoginPage />);
    expect(
      screen.getByText(/sign in to manage your calendar with ai/i),
    ).toBeInTheDocument();
  });
});
