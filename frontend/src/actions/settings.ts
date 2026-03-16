"use server";

import { revokeGoogleAccess, updateUserPreferences } from "@/lib/api";
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
    const message = err instanceof Error ? err.message : "Revoke failed";
    return { success: false, error: message };
  }
}

/** Validate and save user preferences. */
export async function savePreferences(
  formData: FormData,
): Promise<SavePreferencesResult> {
  const timezone = formData.get("timezone");
  const defaultCalendar = formData.get("default_calendar");

  if (typeof timezone !== "string" || timezone.length === 0 || timezone.length > 100) {
    return { success: false, error: "Invalid timezone" };
  }

  if (
    typeof defaultCalendar !== "string" ||
    defaultCalendar.length === 0 ||
    defaultCalendar.length > 100
  ) {
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
