import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import ChatInput from "./ChatInput";

describe("ChatInput", () => {
  it("should render textarea and send button", () => {
    render(<ChatInput onSend={vi.fn()} isStreaming={false} />);

    expect(
      screen.getByRole("textbox", { name: /chat message/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /send/i }),
    ).toBeInTheDocument();
  });

  it("should call onSend when send button is clicked", async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} isStreaming={false} />);

    const input = screen.getByRole("textbox", { name: /chat message/i });
    await user.type(input, "hello world");
    await user.click(screen.getByRole("button", { name: /send/i }));

    expect(onSend).toHaveBeenCalledWith("hello world");
  });

  it("should call onSend when Enter is pressed", async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} isStreaming={false} />);

    const input = screen.getByRole("textbox", { name: /chat message/i });
    await user.type(input, "hello{Enter}");

    expect(onSend).toHaveBeenCalledWith("hello");
  });

  it("should not send on Shift+Enter (allows newline)", async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} isStreaming={false} />);

    const input = screen.getByRole("textbox", { name: /chat message/i });
    await user.type(input, "line1{Shift>}{Enter}{/Shift}line2");

    expect(onSend).not.toHaveBeenCalled();
  });

  it("should not send empty message", async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} isStreaming={false} />);

    await user.click(screen.getByRole("button", { name: /send/i }));

    expect(onSend).not.toHaveBeenCalled();
  });

  it("should disable input and button while streaming", () => {
    render(<ChatInput onSend={vi.fn()} isStreaming={true} />);

    expect(
      screen.getByRole("textbox", { name: /chat message/i }),
    ).toBeDisabled();
    expect(screen.getByRole("button", { name: /send/i })).toBeDisabled();
  });

  it("should clear input after sending", async () => {
    const user = userEvent.setup();
    render(<ChatInput onSend={vi.fn()} isStreaming={false} />);

    const input = screen.getByRole("textbox", { name: /chat message/i });
    await user.type(input, "hello{Enter}");

    expect(input).toHaveValue("");
  });
});
