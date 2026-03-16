import { describe, expect, it, vi } from "vitest";

import {
  type ChatSSEEvent,
  ChatStreamError,
  streamChat,
} from "./chat-stream";

/** Helper: create a ReadableStream from an array of string chunks. */
function mockStream(chunks: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  let index = 0;
  return new ReadableStream({
    pull(controller) {
      if (index < chunks.length) {
        controller.enqueue(encoder.encode(chunks[index]!));
        index++;
      } else {
        controller.close();
      }
    },
  });
}

/** Helper: create a mock Response with a body stream. */
function mockResponse(
  chunks: string[],
  status = 200,
): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    body: mockStream(chunks),
    text: async () => chunks.join(""),
  } as unknown as Response;
}

/** Collect all events from the async generator. */
async function collectEvents(
  params: Parameters<typeof streamChat>[0],
): Promise<ChatSSEEvent[]> {
  const events: ChatSSEEvent[] = [];
  for await (const event of streamChat(params)) {
    events.push(event);
  }
  return events;
}

const defaultParams = {
  message: "hello",
  threadId: null,
  token: "test-token",
};

describe("streamChat", () => {
  it("should parse token events from SSE stream", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        mockResponse([
          'data: {"type":"token","content":"Hello"}\n\n',
          'data: {"type":"token","content":" world"}\n\n',
          'data: {"type":"done","thread_id":"user-123:session-abc"}\n\n',
        ]),
      ),
    );

    const events = await collectEvents(defaultParams);

    expect(events).toEqual([
      { type: "token", content: "Hello" },
      { type: "token", content: " world" },
      { type: "done", thread_id: "user-123:session-abc" },
    ]);
  });

  it("should parse error events", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        mockResponse([
          'data: {"type":"error","content":"An error occurred"}\n\n',
          'data: {"type":"done","thread_id":"user-123:session-abc"}\n\n',
        ]),
      ),
    );

    const events = await collectEvents(defaultParams);

    expect(events[0]).toEqual({
      type: "error",
      content: "An error occurred",
    });
  });

  it("should parse blocked events", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        mockResponse([
          'data: {"type":"blocked","content":"I can only help with calendar tasks."}\n\n',
          'data: {"type":"done","thread_id":"user-123:session-abc"}\n\n',
        ]),
      ),
    );

    const events = await collectEvents(defaultParams);

    expect(events[0]).toEqual({
      type: "blocked",
      content: "I can only help with calendar tasks.",
    });
  });

  it("should handle SSE data split across chunks", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        mockResponse([
          'data: {"type":"tok',
          'en","content":"split"}\n\n',
          'data: {"type":"done","thread_id":"t1"}\n\n',
        ]),
      ),
    );

    const events = await collectEvents(defaultParams);

    expect(events[0]).toEqual({ type: "token", content: "split" });
    expect(events[1]).toEqual({ type: "done", thread_id: "t1" });
  });

  it("should handle multiple events in a single chunk", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        mockResponse([
          'data: {"type":"token","content":"a"}\n\ndata: {"type":"token","content":"b"}\n\ndata: {"type":"done","thread_id":"t1"}\n\n',
        ]),
      ),
    );

    const events = await collectEvents(defaultParams);

    expect(events).toHaveLength(3);
    expect(events[0]).toEqual({ type: "token", content: "a" });
    expect(events[1]).toEqual({ type: "token", content: "b" });
  });

  it("should throw ChatStreamError on non-ok response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        mockResponse(["Unauthorized"], 401),
      ),
    );

    await expect(collectEvents(defaultParams)).rejects.toThrow(
      ChatStreamError,
    );
    await expect(collectEvents(defaultParams)).rejects.toThrow(
      /401/,
    );
  });

  it("should throw ChatStreamError when response body is missing", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        body: null,
        text: async () => "",
      }),
    );

    await expect(collectEvents(defaultParams)).rejects.toThrow(
      ChatStreamError,
    );
  });

  it("should send correct request with auth header and body", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      mockResponse([
        'data: {"type":"done","thread_id":"t1"}\n\n',
      ]),
    );
    vi.stubGlobal("fetch", fetchMock);

    await collectEvents({
      message: "test message",
      threadId: "user-abc:session-xyz",
      token: "my-token",
    });

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/chat"),
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({
          "Content-Type": "application/json",
          Authorization: "Bearer my-token",
        }),
        body: JSON.stringify({
          message: "test message",
          thread_id: "user-abc:session-xyz",
        }),
      }),
    );
  });

  it("should pass AbortSignal to fetch when provided", async () => {
    const controller = new AbortController();
    const fetchMock = vi.fn().mockResolvedValue(
      mockResponse([
        'data: {"type":"done","thread_id":"t1"}\n\n',
      ]),
    );
    vi.stubGlobal("fetch", fetchMock);

    await collectEvents({ ...defaultParams, signal: controller.signal });

    expect(fetchMock).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        signal: controller.signal,
      }),
    );
  });

  it("should ignore non-data SSE lines", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        mockResponse([
          ': this is a comment\n\n',
          'data: {"type":"token","content":"hi"}\n\n',
          'event: heartbeat\n\n',
          'data: {"type":"done","thread_id":"t1"}\n\n',
        ]),
      ),
    );

    const events = await collectEvents(defaultParams);

    expect(events).toHaveLength(2);
    expect(events[0]).toEqual({ type: "token", content: "hi" });
  });
});
