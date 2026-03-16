"use client";

import { useActionState } from "react";
import { savePreferences } from "@/actions/settings";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import type { UserPreferences } from "@/lib/api";

interface PreferencesFormProps {
  preferences: UserPreferences;
}

interface FormState {
  success: boolean | null;
  error?: string;
}

const TIMEZONES = (() => {
  try {
    return Intl.supportedValuesOf("timeZone");
  } catch {
    return ["UTC"];
  }
})();

export function PreferencesForm({ preferences }: PreferencesFormProps) {
  const [state, formAction, isPending] = useActionState<FormState, FormData>(
    async (_prev, formData) => {
      const result = await savePreferences(formData);
      return { success: result.success, error: result.error };
    },
    { success: null },
  );

  return (
    <form action={formAction} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="timezone">Timezone</Label>
        <select
          id="timezone"
          name="timezone"
          defaultValue={preferences.timezone}
          className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
        >
          {[...new Set([preferences.timezone, ...TIMEZONES])].map((tz) => (
            <option key={tz} value={tz}>
              {tz.replace(/_/g, " ")}
            </option>
          ))}
        </select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="default_calendar">Default Calendar</Label>
        <input
          id="default_calendar"
          name="default_calendar"
          type="text"
          defaultValue={preferences.default_calendar}
          className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
        />
      </div>

      {state.success === true && (
        <Alert>
          <AlertDescription>Preferences saved successfully.</AlertDescription>
        </Alert>
      )}

      {state.error && (
        <Alert variant="destructive">
          <AlertDescription>{state.error}</AlertDescription>
        </Alert>
      )}

      <Button type="submit" disabled={isPending}>
        {isPending ? "Saving..." : "Save Preferences"}
      </Button>
    </form>
  );
}
