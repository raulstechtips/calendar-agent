"use server";

import { ApiError, revokeGoogleAccess, updateUserPreferences } from "@/lib/api";
import type { UserPreferences } from "@/lib/api";

interface ActionResult {
  success: boolean;
  error?: string;
}

interface SavePreferencesResult extends ActionResult {
  preferences?: UserPreferences;
}

/** Revoke Google OAuth access and clear backend tokens. */
export async function revokeAccess(): Promise<ActionResult> {
  try {
    await revokeGoogleAccess();
    return { success: true };
  } catch (err) {
    // Token already gone (404) or session expired (401) — user is effectively
    // disconnected, so treat as idempotent success and allow sign-out.
    if (err instanceof ApiError && (err.status === 404 || err.status === 401)) {
      return { success: true };
    }
    const message = err instanceof Error ? err.message : "Revoke failed";
    return { success: false, error: message };
  }
}

/** Validate and save user preferences. */
export async function savePreferences(
  formData: FormData,
): Promise<SavePreferencesResult> {
  const timezoneRaw = formData.get("timezone");
  const defaultCalendarRaw = formData.get("default_calendar");

  const timezone = typeof timezoneRaw === "string" ? timezoneRaw.trim() : "";
  const defaultCalendar =
    typeof defaultCalendarRaw === "string" ? defaultCalendarRaw.trim() : "";

  if (timezone.length === 0 || timezone.length > 100) {
    return { success: false, error: "Invalid timezone" };
  }

  if (defaultCalendar.length === 0 || defaultCalendar.length > 100) {
    return { success: false, error: "Invalid calendar name" };
  }

  try {
    const preferences = await updateUserPreferences({
      timezone,
      default_calendar: defaultCalendar,
    });
    return { success: true, preferences };
  } catch (err) {
    const message = err instanceof Error ? err.message : "Save failed";
    return { success: false, error: message };
  }
}
