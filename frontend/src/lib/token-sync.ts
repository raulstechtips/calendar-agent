/**
 * Sync OAuth tokens from the Auth.js JWT callback to the backend Redis store.
 * Uses direct fetch() — NOT apiClient() — to avoid circular auth() calls.
 */
import type { JWT } from "next-auth/jwt";

const BACKEND_URL =
  process.env.INTERNAL_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function syncTokenToBackend(token: JWT): Promise<void> {
  const { idToken, accessToken, refreshToken, expiresAt, scope } = token;

  if (!idToken || !accessToken || !refreshToken || !expiresAt) {
    return;
  }

  const scopes =
    typeof scope === "string" ? scope.split(" ").filter(Boolean) : [];

  if (scopes.length === 0) {
    return;
  }

  const body = JSON.stringify({
    access_token: accessToken,
    refresh_token: refreshToken,
    expires_at: expiresAt,
    scopes,
  });

  const doSync = (): Promise<Response> =>
    fetch(`${BACKEND_URL}/api/auth/callback`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${idToken}`,
      },
      body,
    });

  for (let attempt = 1; attempt <= 2; attempt += 1) {
    try {
      const response = await doSync();
      if (response.ok) return;
      if (attempt === 2) {
        console.error(`[token-sync] Failed after retry: ${response.status}`);
      }
    } catch {
      if (attempt === 2) {
        console.error("[token-sync] Failed after retry: network error");
      }
    }
  }
}
