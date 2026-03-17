import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { ChatSSEEvent } from "@/lib/chat-stream";

// Mock useSession from next-auth/react
vi.mock("next-auth/react", () => ({
  useSession: () => ({
    data: { idToken: "test-token" },
    status: "authenticated",
  }),
}));

// Mock streamChat
const mockStreamChat = vi.fn();
vi.mock("@/lib/chat-stream", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/chat-stream")>();
  return {
    ...actual,
    streamChat: (...args: unknown[]) => mockStreamChat(...args),
  };
});

// Mock server action
vi.mock("@/actions/chat", () => ({
  submitConfirmation: vi.fn(),
}));

import ChatShell from "./ChatShell";

async function* fakeStream(
  events: ChatSSEEvent[],
): AsyncGenerator<ChatSSEEvent> {
  for (const event of events) {
    yield event;
  }
}

describe("ChatShell", () => {
  it("should render empty state with input", () => {
    render(<ChatShell />);

    expect(
      screen.getByRole("textbox", { name: /chat message/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/start a conversation/i),
    ).toBeInTheDocument();
  });

  it("should display messages after sending", async () => {
    mockStreamChat.mockReturnValue(
      fakeStream([
        { type: "token", content: "Hi there!" },
        { type: "done", thread_id: "t1" },
      ]),
    );

    const user = userEvent.setup();
    render(<ChatShell />);

    const input = screen.getByRole("textbox", { name: /chat message/i });
    await user.type(input, "hello{Enter}");

    expect(await screen.findByText("hello")).toBeInTheDocument();
    expect(await screen.findByText("Hi there!")).toBeInTheDocument();
  });

  it("should display error state", async () => {
    mockStreamChat.mockReturnValue(
      fakeStream([
        { type: "error", content: "Something went wrong" },
        { type: "done", thread_id: "t1" },
      ]),
    );

    const user = userEvent.setup();
    render(<ChatShell />);

    const input = screen.getByRole("textbox", { name: /chat message/i });
    await user.type(input, "test{Enter}");

    expect(
      await screen.findByText("Something went wrong"),
    ).toBeInTheDocument();
  });

  it("should display confirmation card when stream emits confirmation event", async () => {
    mockStreamChat.mockReturnValue(
      fakeStream([
        { type: "token", content: "I'll create that for you." },
        {
          type: "confirmation",
          action: "create_event",
          action_id: "act-1",
          details: {
            action: "create_event",
            summary: "Team standup",
            start: "2026-03-15 09:00:00",
            end: "2026-03-15 09:30:00",
            timezone: "America/New_York",
            calendar_id: "primary",
          },
        },
        { type: "done", thread_id: "t1" },
      ]),
    );

    const user = userEvent.setup();
    render(<ChatShell />);

    const input = screen.getByRole("textbox", { name: /chat message/i });
    await user.type(input, "create a standup{Enter}");

    // Should show the confirmation card with formatted content
    expect(await screen.findByText("Create Event")).toBeInTheDocument();
    expect(await screen.findByText("Team standup")).toBeInTheDocument();
    expect(
      await screen.findByRole("button", { name: /approve/i }),
    ).toBeInTheDocument();
    expect(
      await screen.findByRole("button", { name: /reject/i }),
    ).toBeInTheDocument();
  });
});
