/** Formatting utilities for human-in-the-loop confirmation details. */

export interface FormattedDetail {
  label: string;
  value: string;
}

const ACTION_LABELS: Record<string, string> = {
  create_event: "Create Event",
  update_event: "Update Event",
  delete_event: "Delete Event",
};

const INTERNAL_FIELDS = new Set([
  "action",
  "calendar_id",
  "event_id",
  "timezone",
]);

/** Map a backend action name to a human-readable label. */
export function getActionLabel(action: string): string {
  if (action in ACTION_LABELS) {
    return ACTION_LABELS[action] as string;
  }
  return action
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

function formatDateTime(raw: string, timezone?: string): string {
  try {
    // Backend sends "YYYY-MM-DD HH:MM:SS" — convert to ISO for Date parsing
    const iso = raw.replace(" ", "T");
    const date = new Date(iso);
    if (isNaN(date.getTime())) return raw;

    return new Intl.DateTimeFormat("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
      timeZone: timezone ?? undefined,
    }).format(date);
  } catch {
    return raw;
  }
}

/** Format raw backend confirmation details into human-readable fields. */
export function formatConfirmationDetails(
  _action: string,
  details: Record<string, unknown>,
): FormattedDetail[] {
  const fields: FormattedDetail[] = [];
  const tz =
    typeof details["timezone"] === "string" ? details["timezone"] : undefined;

  if (typeof details["summary"] === "string") {
    fields.push({ label: "Event", value: details["summary"] });
  }

  if (typeof details["start"] === "string") {
    fields.push({ label: "Start", value: formatDateTime(details["start"], tz) });
  }

  if (typeof details["end"] === "string") {
    fields.push({ label: "End", value: formatDateTime(details["end"], tz) });
  }

  if (typeof details["description"] === "string") {
    fields.push({ label: "Description", value: details["description"] });
  }

  if (typeof details["location"] === "string") {
    fields.push({ label: "Location", value: details["location"] });
  }

  if (Array.isArray(details["attendees"]) && details["attendees"].length > 0) {
    fields.push({
      label: "Attendees",
      value: (details["attendees"] as string[]).join(", "),
    });
  }

  // Add any remaining non-internal, non-null fields not already handled
  for (const [key, value] of Object.entries(details)) {
    if (INTERNAL_FIELDS.has(key)) continue;
    if (value == null) continue;
    const knownKeys = new Set([
      "summary",
      "start",
      "end",
      "description",
      "location",
      "attendees",
    ]);
    if (knownKeys.has(key)) continue;
    fields.push({ label: key, value: String(value) });
  }

  return fields;
}
