import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import type { Session } from "next-auth";
import type { Mock } from "vitest";

vi.mock("../../auth", () => ({
  auth: vi.fn(),
}));

const { auth } = await import("../../auth");
const mockedAuth = auth as unknown as Mock<() => Promise<Session | null>>;

function makeSession(overrides: Partial<Session> = {}): Session {
  return {
    user: { id: "user-123", name: "Test User", email: "test@example.com" },
    expires: new Date(Date.now() + 3600_000).toISOString(),
    idToken: "test-google-id-token",
    ...overrides,
  };
}

function mockFetch(
  body: unknown = {},
  status = 200,
): ReturnType<typeof vi.fn> {
  return vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(body),
    text: () => Promise.resolve(JSON.stringify(body)),
  });
}

describe("apiClient", () => {
  beforeEach(() => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "https://backend.example.com");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it("should send Authorization header with idToken from session", async () => {
    mockedAuth.mockResolvedValue(makeSession());
    const fetchMock = mockFetch();
    vi.stubGlobal("fetch", fetchMock);

    const { apiClient } = await import("./api");
    await apiClient("/api/users/me");

    const [, options] = fetchMock.mock.calls[0] as [string, RequestInit];
    const headers = options.headers as Record<string, string>;
    expect(headers["Authorization"]).toBe("Bearer test-google-id-token");
  });

  it("should use NEXT_PUBLIC_API_URL as base URL", async () => {
    mockedAuth.mockResolvedValue(makeSession());
    const fetchMock = mockFetch();
    vi.stubGlobal("fetch", fetchMock);

    const { apiClient } = await import("./api");
    await apiClient("/api/users/me");

    const [url] = fetchMock.mock.calls[0] as [string];
    expect(url).toBe("https://backend.example.com/api/users/me");
  });

  it("should fall back to localhost:8000 when NEXT_PUBLIC_API_URL is not set", async () => {
    vi.unstubAllEnvs();
    mockedAuth.mockResolvedValue(makeSession());
    const fetchMock = mockFetch();
    vi.stubGlobal("fetch", fetchMock);

    const { apiClient } = await import("./api");
    await apiClient("/api/some/path");

    const [url] = fetchMock.mock.calls[0] as [string];
    expect(url).toBe("http://localhost:8000/api/some/path");
  });

  it("should throw when session has no idToken", async () => {
    mockedAuth.mockResolvedValue(makeSession({ idToken: undefined }));

    const { apiClient } = await import("./api");
    await expect(apiClient("/api/users/me")).rejects.toThrow(
      /missing.*id.*token/i,
    );
  });

  it("should throw when session is null", async () => {
    mockedAuth.mockResolvedValue(null);

    const { apiClient } = await import("./api");
    await expect(apiClient("/api/users/me")).rejects.toThrow(
      /not authenticated/i,
    );
  });

  it("should throw when session has RefreshTokenError", async () => {
    mockedAuth.mockResolvedValue(
      makeSession({ error: "RefreshTokenError" }),
    );

    const { apiClient } = await import("./api");
    await expect(apiClient("/api/users/me")).rejects.toThrow(
      /session expired/i,
    );
  });

  it("should forward custom headers alongside Authorization", async () => {
    mockedAuth.mockResolvedValue(makeSession());
    const fetchMock = mockFetch();
    vi.stubGlobal("fetch", fetchMock);

    const { apiClient } = await import("./api");
    await apiClient("/api/chat", {
      headers: { "Content-Type": "application/json" },
    });

    const [, options] = fetchMock.mock.calls[0] as [string, RequestInit];
    const headers = options.headers as Record<string, string>;
    expect(headers["Authorization"]).toBe("Bearer test-google-id-token");
    expect(headers["Content-Type"]).toBe("application/json");
  });

  it("should pass through request options (method, body)", async () => {
    mockedAuth.mockResolvedValue(makeSession());
    const fetchMock = mockFetch();
    vi.stubGlobal("fetch", fetchMock);

    const body = JSON.stringify({ message: "hello" });
    const { apiClient } = await import("./api");
    await apiClient("/api/chat", { method: "POST", body });

    const [, options] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(options.method).toBe("POST");
    expect(options.body).toBe(body);
  });
});

describe("getUserProfile", () => {
  beforeEach(() => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "https://backend.example.com");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it("should return parsed user profile on 200", async () => {
    const profile = {
      id: "user-123",
      email: "test@example.com",
      name: "Test User",
      picture: null,
      granted_scopes: [],
    };
    mockedAuth.mockResolvedValue(makeSession());
    vi.stubGlobal("fetch", mockFetch(profile));

    const { getUserProfile } = await import("./api");
    const result = await getUserProfile();

    expect(result).toEqual(profile);
  });

  it("should throw ApiError on non-ok response", async () => {
    mockedAuth.mockResolvedValue(makeSession());
    vi.stubGlobal(
      "fetch",
      mockFetch({ detail: "Invalid token" }, 401),
    );

    const { ApiError, getUserProfile } = await import("./api");
    const error = await getUserProfile().catch((e: unknown) => e);

    expect(error).toBeInstanceOf(ApiError);
    expect((error as InstanceType<typeof ApiError>).status).toBe(401);
  });
});
