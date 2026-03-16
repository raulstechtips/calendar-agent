/**
 * Centralized API client for backend calls.
 * Server-only — uses auth() which reads cookies.
 */
import { auth } from "../../auth";

function getApiBaseUrl(): string {
  return process.env.INTERNAL_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
}

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/** Send an authenticated request to the backend API. */
export async function apiClient(
  path: string,
  options: RequestInit = {},
): Promise<Response> {
  const session = await auth();

  if (!session?.user) {
    throw new ApiError("Not authenticated", 401);
  }

  if (session.error === "RefreshTokenError") {
    throw new ApiError("Session expired — re-authentication required", 401);
  }

  if (!session.idToken) {
    throw new ApiError("Missing ID token in session", 401);
  }

  const { headers: customHeaders, ...rest } = options;

  return fetch(`${getApiBaseUrl()}${path}`, {
    ...rest,
    headers: {
      ...(customHeaders as Record<string, string>),
      Authorization: `Bearer ${session.idToken}`,
    },
  });
}

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  picture: string | null;
  granted_scopes: string[];
}

/** Fetch the authenticated user's profile from the backend. */
export async function getUserProfile(): Promise<UserProfile> {
  const response = await apiClient("/api/users/me");

  if (!response.ok) {
    const text = await response.text();
    throw new ApiError(text, response.status);
  }

  return (await response.json()) as UserProfile;
}
