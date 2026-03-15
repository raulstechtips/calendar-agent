import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { syncTokenToBackend } from "./token-sync";
import type { JWT } from "next-auth/jwt";

const BACKEND_URL = "http://localhost:8000";

const baseToken: JWT = {
  idToken: "test-id-token",
  accessToken: "test-access-token",
  refreshToken: "test-refresh-token",
  expiresAt: 9999999999,
  scope: "openid email profile",
};

function mockFetchSuccess(status = 204): ReturnType<typeof vi.fn> {
  return vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
  });
}

describe("syncTokenToBackend", () => {
  beforeEach(() => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", BACKEND_URL);
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it("should POST tokens to backend with correct URL, headers, and body", async () => {
    const mockFetch = mockFetchSuccess();
    vi.stubGlobal("fetch", mockFetch);

    await syncTokenToBackend(baseToken);

    expect(mockFetch).toHaveBeenCalledOnce();
    const [url, options] = mockFetch.mock.calls[0] as [string, RequestInit];
    expect(url).toBe(`${BACKEND_URL}/api/auth/callback`);
    expect(options.method).toBe("POST");

    const headers = options.headers as Record<string, string>;
    expect(headers["Content-Type"]).toBe("application/json");

    const body = JSON.parse(options.body as string) as Record<string, unknown>;
    expect(body.access_token).toBe("test-access-token");
    expect(body.refresh_token).toBe("test-refresh-token");
    expect(body.expires_at).toBe(9999999999);
    expect(body.scopes).toEqual(["openid", "email", "profile"]);
  });

  it("should use idToken as Bearer authorization", async () => {
    const mockFetch = mockFetchSuccess();
    vi.stubGlobal("fetch", mockFetch);

    await syncTokenToBackend(baseToken);

    const [, options] = mockFetch.mock.calls[0] as [string, RequestInit];
    const headers = options.headers as Record<string, string>;
    expect(headers["Authorization"]).toBe("Bearer test-id-token");
  });

  it("should split scope string into scopes array", async () => {
    const mockFetch = mockFetchSuccess();
    vi.stubGlobal("fetch", mockFetch);

    const tokenWithCalendar = {
      ...baseToken,
      scope: "openid email profile calendar.events",
    };
    await syncTokenToBackend(tokenWithCalendar);

    const [, options] = mockFetch.mock.calls[0] as [string, RequestInit];
    const body = JSON.parse(options.body as string) as Record<string, unknown>;
    expect(body.scopes).toEqual([
      "openid",
      "email",
      "profile",
      "calendar.events",
    ]);
  });

  it("should skip sync when scope is undefined", async () => {
    const mockFetch = mockFetchSuccess();
    vi.stubGlobal("fetch", mockFetch);

    await syncTokenToBackend({ ...baseToken, scope: undefined });

    expect(mockFetch).not.toHaveBeenCalled();
  });

  it("should skip sync when scope is empty string", async () => {
    const mockFetch = mockFetchSuccess();
    vi.stubGlobal("fetch", mockFetch);

    await syncTokenToBackend({ ...baseToken, scope: "" });

    expect(mockFetch).not.toHaveBeenCalled();
  });

  it("should skip sync when idToken is missing", async () => {
    const mockFetch = mockFetchSuccess();
    vi.stubGlobal("fetch", mockFetch);

    await syncTokenToBackend({ ...baseToken, idToken: undefined });

    expect(mockFetch).not.toHaveBeenCalled();
  });

  it("should skip sync when accessToken is missing", async () => {
    const mockFetch = mockFetchSuccess();
    vi.stubGlobal("fetch", mockFetch);

    await syncTokenToBackend({ ...baseToken, accessToken: undefined });

    expect(mockFetch).not.toHaveBeenCalled();
  });

  it("should skip sync when refreshToken is missing", async () => {
    const mockFetch = mockFetchSuccess();
    vi.stubGlobal("fetch", mockFetch);

    await syncTokenToBackend({ ...baseToken, refreshToken: undefined });

    expect(mockFetch).not.toHaveBeenCalled();
  });

  it("should skip sync when expiresAt is missing", async () => {
    const mockFetch = mockFetchSuccess();
    vi.stubGlobal("fetch", mockFetch);

    await syncTokenToBackend({ ...baseToken, expiresAt: undefined });

    expect(mockFetch).not.toHaveBeenCalled();
  });

  it("should retry once on non-ok response", async () => {
    const mockFetch = vi
      .fn()
      .mockResolvedValueOnce({ ok: false, status: 500 })
      .mockResolvedValueOnce({ ok: true, status: 204 });
    vi.stubGlobal("fetch", mockFetch);

    await syncTokenToBackend(baseToken);

    expect(mockFetch).toHaveBeenCalledTimes(2);
  });

  it("should retry once on network error", async () => {
    const mockFetch = vi
      .fn()
      .mockRejectedValueOnce(new Error("Network failure"))
      .mockResolvedValueOnce({ ok: true, status: 204 });
    vi.stubGlobal("fetch", mockFetch);

    await syncTokenToBackend(baseToken);

    expect(mockFetch).toHaveBeenCalledTimes(2);
  });

  it("should make exactly 2 calls when first returns non-ok and retry throws", async () => {
    const mockFetch = vi
      .fn()
      .mockResolvedValueOnce({ ok: false, status: 500 })
      .mockRejectedValueOnce(new Error("Network failure"));
    vi.stubGlobal("fetch", mockFetch);

    await expect(syncTokenToBackend(baseToken)).resolves.toBeUndefined();
    expect(mockFetch).toHaveBeenCalledTimes(2);
  });

  it("should not throw when retry also fails", async () => {
    const mockFetch = vi
      .fn()
      .mockRejectedValueOnce(new Error("Network failure"))
      .mockRejectedValueOnce(new Error("Network failure again"));
    vi.stubGlobal("fetch", mockFetch);

    await expect(syncTokenToBackend(baseToken)).resolves.toBeUndefined();
  });

  it("should not retry on success", async () => {
    const mockFetch = mockFetchSuccess();
    vi.stubGlobal("fetch", mockFetch);

    await syncTokenToBackend(baseToken);

    expect(mockFetch).toHaveBeenCalledOnce();
  });
});
