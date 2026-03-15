/**
 * Refresh a Google OAuth access token using the refresh token.
 * Called from the Auth.js JWT callback when the access token expires.
 * Auth.js v5 has no built-in refresh — this follows the official recommended pattern.
 */
import type { JWT } from "next-auth/jwt";

const GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token";

export async function refreshAccessToken(token: JWT): Promise<JWT> {
  try {
    const response = await fetch(GOOGLE_TOKEN_URL, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        client_id: process.env.AUTH_GOOGLE_ID ?? "",
        client_secret: process.env.AUTH_GOOGLE_SECRET ?? "",
        grant_type: "refresh_token",
        refresh_token: (token.refreshToken as string) ?? "",
      }),
    });

    if (!response.ok) {
      return { ...token, error: "RefreshTokenError" as const };
    }

    const refreshed: {
      access_token: string;
      expires_in: number;
      refresh_token?: string;
      scope?: string;
      token_type: string;
    } = await response.json();

    return {
      ...token,
      accessToken: refreshed.access_token,
      expiresAt: Math.floor(Date.now() / 1000) + refreshed.expires_in,
      refreshToken: refreshed.refresh_token ?? token.refreshToken,
      error: undefined,
    };
  } catch {
    return { ...token, error: "RefreshTokenError" as const };
  }
}
