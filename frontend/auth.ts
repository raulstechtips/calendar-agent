/**
 * Auth.js v5 configuration with Google OAuth provider.
 * Requests offline access for refresh tokens and captures OAuth tokens
 * in the JWT for downstream use by the backend agent.
 */
import NextAuth, { type DefaultSession } from "next-auth";
import Google from "next-auth/providers/google";
import { refreshAccessToken } from "./src/lib/google-auth";
import { syncTokenToBackend } from "./src/lib/token-sync";

declare module "next-auth" {
  interface Session {
    accessToken?: string;
    idToken?: string;
    error?: "RefreshTokenError";
    user: {
      id: string;
    } & DefaultSession["user"];
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    accessToken?: string;
    idToken?: string;
    refreshToken?: string;
    expiresAt?: number;
    scope?: string;
    error?: "RefreshTokenError";
  }
}

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [
    Google({
      authorization: {
        params: {
          access_type: "offline",
          prompt: "consent",
          // Enables scope merging for incremental consent (issue #11)
          include_granted_scopes: "true",
          scope: "openid email profile",
        },
      },
    }),
  ],
  pages: {
    signIn: "/login",
  },
  callbacks: {
    async jwt({ token, account }) {
      // Initial sign-in: capture tokens from Google OAuth response
      if (account) {
        const updatedToken = {
          ...token,
          accessToken: account.access_token,
          idToken: account.id_token,
          refreshToken: account.refresh_token,
          expiresAt: account.expires_at,
          scope: account.scope,
          error: undefined,
        };
        // Await sync for sign-in/consent — this is the only moment we get
        // the calendar-scoped refresh token from Google (#94)
        await syncTokenToBackend(updatedToken).catch((err) => {
          console.error("[auth] Token sync failed after sign-in:", err);
        });
        return updatedToken;
      }

      // Token still valid (with 60-second buffer): return as-is
      if (
        typeof token.expiresAt === "number" &&
        Date.now() < (token.expiresAt - 60) * 1000
      ) {
        return token;
      }

      // Token expired: refresh via Google's token endpoint.
      // Concurrent expired-token requests each refresh independently — Google tolerates this.
      const refreshed = await refreshAccessToken(token);
      if (!refreshed.error) {
        syncTokenToBackend(refreshed).catch(() => {});
      }
      return refreshed;
    },
    session({ session, token }) {
      if (token.sub) {
        session.user.id = token.sub;
      }
      if (typeof token.accessToken === "string") {
        session.accessToken = token.accessToken;
      }
      if (typeof token.idToken === "string") {
        session.idToken = token.idToken;
      }
      if (token.error) {
        session.error = token.error;
      }
      return session;
    },
    authorized({ auth: session }) {
      if (session?.error === "RefreshTokenError") return false;
      return !!session?.user;
    },
  },
});
