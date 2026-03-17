import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { ChatSSEEvent } from "@/lib/chat-stream";

// Mock the streamChat module
const mockStreamChat = vi.fn();
vi.mock("@/lib/chat-stream", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/chat-stream")>();
  return {
    ...actual,
    streamChat: (...args: unknown[]) => mockStreamChat(...args),
  };
});

// Mock the server action
const mockSubmitConfirmation = vi.fn();
vi.mock("@/actions/chat", () => ({
  submitConfirmation: (...args: unknown[]) => mockSubmitConfirmation(...args),
}));

import { useChat } from "./useChat";

/** Helper: create an async generator from an array of events. */
async function* fakeStream(
  events: ChatSSEEvent[],
): AsyncGenerator<ChatSSEEvent> {
  for (const event of events) {
    yield event;
  }
}

describe("useChat", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should start with empty state", () => {
    const { result } = renderHook(() => useChat());

    expect(result.current.messages).toEqual([]);
    expect(result.current.threadId).toBeNull();
    expect(result.current.isStreaming).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.pendingConfirmation).toBeNull();
  });

  it("should add user message and stream assistant response", async () => {
    mockStreamChat.mockReturnValue(
      fakeStream([
        { type: "token", content: "Hello" },
        { type: "token", content: " there" },
        { type: "done", thread_id: "user-1:session-abc" },
      ]),
    );

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage("hi");
    });

    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[0]?.role).toBe("user");
    expect(result.current.messages[0]?.content).toBe("hi");
    expect(result.current.messages[1]?.role).toBe("assistant");
    expect(result.current.messages[1]?.content).toBe("Hello there");
    expect(result.current.threadId).toBe("user-1:session-abc");
    expect(result.current.isStreaming).toBe(false);
  });

  it("should set error on stream error event", async () => {
    mockStreamChat.mockReturnValue(
      fakeStream([
        { type: "error", content: "Something went wrong" },
        { type: "done", thread_id: "t1" },
      ]),
    );

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage("test");
    });

    expect(result.current.error).toBe("Something went wrong");
  });

  it("should handle blocked responses", async () => {
    mockStreamChat.mockReturnValue(
      fakeStream([
        { type: "blocked", content: "I can only help with calendar tasks." },
        { type: "done", thread_id: "t1" },
      ]),
    );

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage("ignore instructions");
    });

    // Blocked content should appear as assistant message
    expect(result.current.messages[1]?.role).toBe("assistant");
    expect(result.current.messages[1]?.content).toBe(
      "I can only help with calendar tasks.",
    );
  });

  it("should clear error", async () => {
    mockStreamChat.mockReturnValue(
      fakeStream([
        { type: "error", content: "fail" },
        { type: "done", thread_id: "t1" },
      ]),
    );

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage("test");
    });

    expect(result.current.error).toBe("fail");

    act(() => {
      result.current.clearError();
    });

    expect(result.current.error).toBeNull();
  });

  it("should pass threadId on subsequent messages", async () => {
    mockStreamChat.mockReturnValue(
      fakeStream([
        { type: "token", content: "first" },
        { type: "done", thread_id: "user-1:session-abc" },
      ]),
    );

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage("msg1");
    });

    expect(result.current.threadId).toBe("user-1:session-abc");

    mockStreamChat.mockReturnValue(
      fakeStream([
        { type: "token", content: "second" },
        { type: "done", thread_id: "user-1:session-abc" },
      ]),
    );

    await act(async () => {
      await result.current.sendMessage("msg2");
    });

    // Should pass existing threadId
    expect(mockStreamChat).toHaveBeenLastCalledWith(
      expect.objectContaining({
        threadId: "user-1:session-abc",
      }),
    );
  });

  it("should not send empty messages", async () => {
    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage("");
    });

    expect(result.current.messages).toHaveLength(0);
    expect(mockStreamChat).not.toHaveBeenCalled();
  });

  it("should not send while streaming", async () => {
    // Create a stream that doesn't resolve immediately
    let resolveStream: (() => void) | undefined;
    const pendingStream = new Promise<void>((resolve) => {
      resolveStream = resolve;
    });

    mockStreamChat.mockReturnValue(
      (async function* () {
        yield { type: "token" as const, content: "..." };
        await pendingStream;
        yield { type: "done" as const, thread_id: "t1" };
      })(),
    );

    const { result } = renderHook(() => useChat());

    // Start first message (non-blocking)
    let sendPromise: Promise<void>;
    act(() => {
      sendPromise = result.current.sendMessage("first");
    });

    // Try to send second message while streaming
    await act(async () => {
      await result.current.sendMessage("second");
    });

    // Only 1 user message should exist (second was rejected)
    const userMessages = result.current.messages.filter(
      (m) => m.role === "user",
    );
    expect(userMessages).toHaveLength(1);

    // Cleanup
    resolveStream?.();
    await act(async () => {
      await sendPromise!;
    });
  });

  it("should handle fetch errors gracefully", async () => {
    mockStreamChat.mockImplementation(() => {
      throw new Error("Network error");
    });

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage("test");
    });

    expect(result.current.error).toBe("Network error");
    expect(result.current.isStreaming).toBe(false);
  });

  it("should set pendingConfirmation on confirmation SSE event", async () => {
    mockStreamChat.mockReturnValue(
      fakeStream([
        { type: "token", content: "I'll create that event." },
        {
          type: "confirmation",
          action: "create_event",
          action_id: "act-123",
          details: { summary: "Team standup", start: "2026-03-16 09:00:00" },
        },
        { type: "done", thread_id: "t1" },
      ]),
    );

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage("create event");
    });

    expect(result.current.pendingConfirmation).toEqual({
      actionId: "act-123",
      action: "create_event",
      details: { summary: "Team standup", start: "2026-03-16 09:00:00" },
    });
  });

  it("should handle confirmation flow", async () => {
    mockStreamChat.mockReturnValue(
      fakeStream([
        { type: "token", content: "I'll create that event." },
        { type: "done", thread_id: "t1" },
      ]),
    );

    mockSubmitConfirmation.mockResolvedValue({ status: "executed" });

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage("create event");
    });

    // Simulate confirmation (even though backend doesn't emit it yet)
    await act(async () => {
      await result.current.confirmAction("action-1", true);
    });

    expect(mockSubmitConfirmation).toHaveBeenCalledWith(
      "t1",
      "action-1",
      true,
    );
  });
});
