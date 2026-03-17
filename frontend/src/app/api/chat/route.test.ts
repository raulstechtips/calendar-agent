import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { Session } from "next-auth";
import type { Mock } from "vitest";

vi.mock("../../../../auth", () => ({
  auth: vi.fn(),
}));

const { auth } = await import("../../../../auth");
const mockedAuth = auth as unknown as Mock<() => Promise<Session | null>>;

function makeSession(overrides: Partial<Session> = {}): Session {
  return {
    user: { id: "user-123", name: "Test User", email: "test@example.com" },
    expires: new Date(Date.now() + 3600_000).toISOString(),
    idToken: "test-google-id-token",
    ...overrides,
  };
}

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

describe("POST /api/chat", () => {
  beforeEach(() => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "https://backend.internal.example.com");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it("should return 401 when session is null", async () => {
    mockedAuth.mockResolvedValue(null);

    const { POST } = await import("./route");
    const request = new Request("http://localhost:3000/api/chat", {
      method: "POST",
      body: JSON.stringify({ message: "hi", thread_id: null }),
    });

    const response = await POST(request);
    expect(response.status).toBe(401);
  });

  it("should return 401 when session has RefreshTokenError", async () => {
    mockedAuth.mockResolvedValue(
      makeSession({ error: "RefreshTokenError" }),
    );

    const { POST } = await import("./route");
    const request = new Request("http://localhost:3000/api/chat", {
      method: "POST",
      body: JSON.stringify({ message: "hi", thread_id: null }),
    });

    const response = await POST(request);
    expect(response.status).toBe(401);
  });

  it("should return 401 when idToken is missing", async () => {
    mockedAuth.mockResolvedValue(makeSession({ idToken: undefined }));

    const { POST } = await import("./route");
    const request = new Request("http://localhost:3000/api/chat", {
      method: "POST",
      body: JSON.stringify({ message: "hi", thread_id: null }),
    });

    const response = await POST(request);
    expect(response.status).toBe(401);
  });

  it("should return 400 when request body is not valid JSON", async () => {
    mockedAuth.mockResolvedValue(makeSession());

    const { POST } = await import("./route");
    const request = new Request("http://localhost:3000/api/chat", {
      method: "POST",
      body: "not json",
    });

    const response = await POST(request);
    expect(response.status).toBe(400);
  });

  it("should proxy request to backend with correct URL, headers, and body", async () => {
    mockedAuth.mockResolvedValue(makeSession());
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      body: mockStream([
        'data: {"type":"done","thread_id":"t1"}\n\n',
      ]),
    });
    vi.stubGlobal("fetch", fetchMock);

    const { POST } = await import("./route");
    const request = new Request("http://localhost:3000/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: "hello", thread_id: "t1" }),
    });

    await POST(request);

    expect(fetchMock).toHaveBeenCalledWith(
      "https://backend.internal.example.com/api/chat",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({
          "Content-Type": "application/json",
          Authorization: "Bearer test-google-id-token",
        }),
        body: JSON.stringify({ message: "hello", thread_id: "t1" }),
      }),
    );
  });

  it("should return SSE stream from backend", async () => {
    mockedAuth.mockResolvedValue(makeSession());
    const sseChunks = [
      'data: {"type":"token","content":"Hi"}\n\n',
      'data: {"type":"done","thread_id":"t1"}\n\n',
    ];
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        body: mockStream(sseChunks),
      }),
    );

    const { POST } = await import("./route");
    const request = new Request("http://localhost:3000/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: "hello", thread_id: null }),
    });

    const response = await POST(request);

    expect(response.status).toBe(200);
    expect(response.headers.get("Content-Type")).toBe("text/event-stream");
    expect(response.headers.get("Cache-Control")).toBe("no-cache");

    const text = await response.text();
    expect(text).toContain('"type":"token"');
    expect(text).toContain('"type":"done"');
  });

  it("should return 502 when upstream fetch rejects", async () => {
    mockedAuth.mockResolvedValue(makeSession());
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new Error("connect ECONNREFUSED")),
    );

    const { POST } = await import("./route");
    const request = new Request("http://localhost:3000/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: "hello", thread_id: null }),
    });

    const response = await POST(request);

    expect(response.status).toBe(502);
    expect(await response.text()).toBe("Upstream unavailable");
  });

  it("should forward upstream error status to client", async () => {
    mockedAuth.mockResolvedValue(makeSession());
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 429,
        text: () => Promise.resolve("Rate limited"),
      }),
    );

    const { POST } = await import("./route");
    const request = new Request("http://localhost:3000/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: "hello", thread_id: null }),
    });

    const response = await POST(request);

    expect(response.status).toBe(429);
    expect(await response.text()).toBe("Rate limited");
  });

  it("should prefer INTERNAL_API_URL over NEXT_PUBLIC_API_URL", async () => {
    vi.stubEnv("INTERNAL_API_URL", "http://backend:8000");
    mockedAuth.mockResolvedValue(makeSession());
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      body: mockStream([
        'data: {"type":"done","thread_id":"t1"}\n\n',
      ]),
    });
    vi.stubGlobal("fetch", fetchMock);

    const { POST } = await import("./route");
    const request = new Request("http://localhost:3000/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: "hello", thread_id: null }),
    });

    await POST(request);

    const [url] = fetchMock.mock.calls[0] as [string];
    expect(url).toBe("http://backend:8000/api/chat");
  });
});
