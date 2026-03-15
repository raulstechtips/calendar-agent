/**
 * Refresh a Google OAuth access token using the refresh token.
 * Called from the Auth.js JWT callback when the access token expires.
 * Auth.js v5 has no built-in refresh — this follows the official recommended pattern.
 */
import type { JWT } from "next-auth/jwt";

const GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token";

export async function refreshAccessToken(token: JWT): Promise<JWT> {
  try {
    const clientId = process.env.AUTH_GOOGLE_ID;
    const clientSecret = process.env.AUTH_GOOGLE_SECRET;
    if (!clientId || !clientSecret) {
      throw new Error("Missing AUTH_GOOGLE_ID or AUTH_GOOGLE_SECRET");
    }

    const response = await fetch(GOOGLE_TOKEN_URL, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        client_id: clientId,
        client_secret: clientSecret,
        grant_type: "refresh_token",
        refresh_token: token.refreshToken ?? "",
      }),
    });

    if (!response.ok) {
      return { ...token, error: "RefreshTokenError" as const };
    }

    const refreshed: Record<string, unknown> = await response.json();
    if (typeof refreshed.access_token !== "string" || typeof refreshed.expires_in !== "number") {
      return { ...token, error: "RefreshTokenError" as const };
    }

    return {
      ...token,
      accessToken: refreshed.access_token,
      expiresAt: Math.floor(Date.now() / 1000) + refreshed.expires_in,
      refreshToken: (typeof refreshed.refresh_token === "string" ? refreshed.refresh_token : token.refreshToken),
      error: undefined,
    };
  } catch {
    return { ...token, error: "RefreshTokenError" as const };
  }
}
