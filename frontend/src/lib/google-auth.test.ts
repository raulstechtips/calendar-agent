import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { refreshAccessToken } from "./google-auth";
import type { JWT } from "next-auth/jwt";

const GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token";

const baseToken: JWT = {
  accessToken: "old-access-token",
  idToken: "old-id-token",
  refreshToken: "test-refresh-token",
  expiresAt: 1000,
  scope: "openid email profile",
};

function mockFetchSuccess(
  body: Record<string, unknown>,
  status = 200,
): ReturnType<typeof vi.fn> {
  return vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(body),
  });
}

describe("refreshAccessToken", () => {
  beforeEach(() => {
    vi.stubEnv("AUTH_GOOGLE_ID", "test-client-id");
    vi.stubEnv("AUTH_GOOGLE_SECRET", "test-client-secret");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it("should return refreshed token on successful response", async () => {
    const mockFetch = mockFetchSuccess({
      access_token: "new-access-token",
      expires_in: 3600,
      scope: "openid email profile",
      token_type: "Bearer",
    });
    vi.stubGlobal("fetch", mockFetch);

    const now = Math.floor(Date.now() / 1000);
    const result = await refreshAccessToken(baseToken);

    expect(result.accessToken).toBe("new-access-token");
    expect(result.expiresAt).toBeGreaterThanOrEqual(now + 3599);
    expect(result.expiresAt).toBeLessThanOrEqual(now + 3601);
    expect(result.error).toBeUndefined();
  });

  it("should preserve existing refresh token when Google does not return a new one", async () => {
    const mockFetch = mockFetchSuccess({
      access_token: "new-access-token",
      expires_in: 3600,
      token_type: "Bearer",
    });
    vi.stubGlobal("fetch", mockFetch);

    const result = await refreshAccessToken(baseToken);

    expect(result.refreshToken).toBe("test-refresh-token");
  });

  it("should use new refresh token when Google returns one", async () => {
    const mockFetch = mockFetchSuccess({
      access_token: "new-access-token",
      expires_in: 3600,
      refresh_token: "rotated-refresh-token",
      token_type: "Bearer",
    });
    vi.stubGlobal("fetch", mockFetch);

    const result = await refreshAccessToken(baseToken);

    expect(result.refreshToken).toBe("rotated-refresh-token");
  });

  it("should return error token when Google returns HTTP error", async () => {
    const mockFetch = mockFetchSuccess(
      { error: "invalid_grant" },
      400,
    );
    vi.stubGlobal("fetch", mockFetch);

    const result = await refreshAccessToken(baseToken);

    expect(result.error).toBe("RefreshTokenError");
    expect(result.refreshToken).toBe("test-refresh-token");
  });

  it("should return error token when fetch throws network error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new Error("Network failure")),
    );

    const result = await refreshAccessToken(baseToken);

    expect(result.error).toBe("RefreshTokenError");
    expect(result.refreshToken).toBe("test-refresh-token");
  });

  it("should return error when refreshToken is undefined", async () => {
    const mockFetch = mockFetchSuccess({ error: "invalid_grant" }, 400);
    vi.stubGlobal("fetch", mockFetch);

    const tokenWithoutRefresh: JWT = { ...baseToken, refreshToken: undefined };
    const result = await refreshAccessToken(tokenWithoutRefresh);

    expect(result.error).toBe("RefreshTokenError");
  });

  it("should return error when credentials are missing", async () => {
    vi.unstubAllEnvs();

    const result = await refreshAccessToken(baseToken);

    expect(result.error).toBe("RefreshTokenError");
  });

  it("should capture id_token from refresh response", async () => {
    const mockFetch = mockFetchSuccess({
      access_token: "new-access-token",
      expires_in: 3600,
      id_token: "new-id-token",
      token_type: "Bearer",
    });
    vi.stubGlobal("fetch", mockFetch);

    const result = await refreshAccessToken(baseToken);

    expect(result.idToken).toBe("new-id-token");
  });

  it("should preserve existing idToken when refresh omits id_token", async () => {
    const mockFetch = mockFetchSuccess({
      access_token: "new-access-token",
      expires_in: 3600,
      token_type: "Bearer",
    });
    vi.stubGlobal("fetch", mockFetch);

    const result = await refreshAccessToken(baseToken);

    expect(result.idToken).toBe("old-id-token");
  });

  it("should send correct parameters to Google token endpoint", async () => {
    const mockFetch = mockFetchSuccess({
      access_token: "new-access-token",
      expires_in: 3600,
      token_type: "Bearer",
    });
    vi.stubGlobal("fetch", mockFetch);

    await refreshAccessToken(baseToken);

    expect(mockFetch).toHaveBeenCalledOnce();
    const [url, options] = mockFetch.mock.calls[0] as [string, RequestInit];
    expect(url).toBe(GOOGLE_TOKEN_URL);
    expect(options.method).toBe("POST");

    const headers = options.headers as Record<string, string>;
    expect(headers["Content-Type"]).toBe("application/x-www-form-urlencoded");

    const body = new URLSearchParams(options.body as string);
    expect(body.get("client_id")).toBe("test-client-id");
    expect(body.get("client_secret")).toBe("test-client-secret");
    expect(body.get("grant_type")).toBe("refresh_token");
    expect(body.get("refresh_token")).toBe("test-refresh-token");
  });
});
