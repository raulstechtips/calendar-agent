import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

vi.mock("@/actions/settings", () => ({
  savePreferences: vi.fn(),
}));

import { savePreferences } from "@/actions/settings";
import type { Mock } from "vitest";
import { PreferencesForm } from "./PreferencesForm";

const mockedSavePreferences = savePreferences as unknown as Mock;

describe("PreferencesForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render with initial timezone value", () => {
    render(
      <PreferencesForm
        preferences={{ timezone: "America/New_York", default_calendar: "primary" }}
      />,
    );

    const timezoneInput = screen.getByLabelText(/timezone/i);
    expect(timezoneInput).toBeInTheDocument();
  });

  it("should render with initial calendar value", () => {
    render(
      <PreferencesForm
        preferences={{ timezone: "UTC", default_calendar: "work" }}
      />,
    );

    const calendarInput = screen.getByLabelText(/default calendar/i);
    expect(calendarInput).toHaveValue("work");
  });

  it("should show success message after save", async () => {
    const user = userEvent.setup();
    mockedSavePreferences.mockResolvedValue({
      success: true,
      preferences: { timezone: "UTC", default_calendar: "primary" },
    });

    render(
      <PreferencesForm
        preferences={{ timezone: "UTC", default_calendar: "primary" }}
      />,
    );

    await user.click(screen.getByRole("button", { name: /save/i }));

    expect(await screen.findByText(/saved/i)).toBeInTheDocument();
  });

  it("should show error message on failure", async () => {
    const user = userEvent.setup();
    mockedSavePreferences.mockResolvedValue({
      success: false,
      error: "Server error",
    });

    render(
      <PreferencesForm
        preferences={{ timezone: "UTC", default_calendar: "primary" }}
      />,
    );

    await user.click(screen.getByRole("button", { name: /save/i }));

    expect(await screen.findByText(/server error/i)).toBeInTheDocument();
  });
});
