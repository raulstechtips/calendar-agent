import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { ChatMessage as ChatMessageType } from "@/lib/chat-stream";

import ChatMessage from "./ChatMessage";

const userMessage: ChatMessageType = {
  id: "user-1",
  role: "user",
  content: "Hello, can you check my calendar?",
};

const assistantMessage: ChatMessageType = {
  id: "assistant-1",
  role: "assistant",
  content: "Sure! Let me check your calendar for today.",
};

describe("ChatMessage", () => {
  it("should render user message content", () => {
    render(<ChatMessage message={userMessage} />);

    expect(
      screen.getByText("Hello, can you check my calendar?"),
    ).toBeInTheDocument();
  });

  it("should render assistant message content", () => {
    render(<ChatMessage message={assistantMessage} />);

    expect(
      screen.getByText("Sure! Let me check your calendar for today."),
    ).toBeInTheDocument();
  });

  it("should display 'You' label for user messages", () => {
    render(<ChatMessage message={userMessage} />);

    expect(screen.getByText("You")).toBeInTheDocument();
  });

  it("should display 'Assistant' label for assistant messages", () => {
    render(<ChatMessage message={assistantMessage} />);

    expect(screen.getByText("Assistant")).toBeInTheDocument();
  });

  it("should show streaming indicator for empty assistant message", () => {
    const emptyAssistant: ChatMessageType = {
      id: "assistant-2",
      role: "assistant",
      content: "",
    };
    render(<ChatMessage message={emptyAssistant} isStreaming />);

    expect(screen.getByLabelText("Assistant is typing")).toBeInTheDocument();
  });
});
