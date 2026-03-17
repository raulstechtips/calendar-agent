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

/** Title-case a snake_case string (e.g. "some_field" → "Some Field"). */
function titleCase(input: string): string {
  return input
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

/** Map a backend action name to a human-readable label. */
export function getActionLabel(action: string): string {
  if (action in ACTION_LABELS) {
    return ACTION_LABELS[action] as string;
  }
  return titleCase(action);
}

function formatDateTime(raw: string): string {
  try {
    // Backend sends "YYYY-MM-DD HH:MM:SS" — wall-clock time in the event's
    // timezone. Parse components manually and store as UTC to avoid the
    // browser interpreting the string in its local timezone.
    const match = raw.match(/^(\d{4})-(\d{2})-(\d{2})\s(\d{2}):(\d{2}):(\d{2})$/);
    if (!match) return raw;

    const [, y, mo, d, h, mi] = match;
    const date = new Date(Date.UTC(+y!, +mo! - 1, +d!, +h!, +mi!));
    if (isNaN(date.getTime())) return raw;

    // Format as UTC so the displayed time matches the backend's wall-clock
    // values exactly, regardless of the user's browser timezone.
    return new Intl.DateTimeFormat("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
      timeZone: "UTC",
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

  if (typeof details["summary"] === "string") {
    fields.push({ label: "Event", value: details["summary"] });
  }

  if (typeof details["start"] === "string") {
    fields.push({ label: "Start", value: formatDateTime(details["start"]) });
  }

  if (typeof details["end"] === "string") {
    fields.push({ label: "End", value: formatDateTime(details["end"]) });
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
  const knownKeys = new Set([
    "summary",
    "start",
    "end",
    "description",
    "location",
    "attendees",
  ]);
  for (const [key, value] of Object.entries(details)) {
    if (INTERNAL_FIELDS.has(key)) continue;
    if (value == null) continue;
    if (knownKeys.has(key)) continue;
    fields.push({ label: titleCase(key), value: String(value) });
  }

  return fields;
}
