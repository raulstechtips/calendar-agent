import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import ScopeRequiredCard from "./ScopeRequiredCard";

describe("ScopeRequiredCard", () => {
  it("should render title and description", () => {
    render(<ScopeRequiredCard onGrant={vi.fn()} />);

    expect(screen.getByText(/calendar access required/i)).toBeInTheDocument();
    expect(screen.getByText(/grant calendar permissions/i)).toBeInTheDocument();
  });

  it("should render grant button", () => {
    render(<ScopeRequiredCard onGrant={vi.fn()} />);

    expect(
      screen.getByRole("button", { name: /grant calendar access/i }),
    ).toBeInTheDocument();
  });

  it("should call onGrant when button is clicked", async () => {
    const user = userEvent.setup();
    const onGrant = vi.fn();
    render(<ScopeRequiredCard onGrant={onGrant} />);

    await user.click(
      screen.getByRole("button", { name: /grant calendar access/i }),
    );

    expect(onGrant).toHaveBeenCalledOnce();
  });
});
