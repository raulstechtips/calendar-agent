"use server";

import { apiClient } from "@/lib/api";

/** Confirm or reject a pending write operation. */
export async function submitConfirmation(
  threadId: string,
  actionId: string,
  approved: boolean,
): Promise<{ status: string }> {
  // Validate inputs at the Server Action boundary
  if (
    typeof threadId !== "string" ||
    threadId.length === 0 ||
    threadId.length > 200
  ) {
    return { status: "error: invalid thread ID" };
  }
  if (
    typeof actionId !== "string" ||
    actionId.length === 0 ||
    actionId.length > 200
  ) {
    return { status: "error: invalid action ID" };
  }
  if (typeof approved !== "boolean") {
    return { status: "error: approved must be a boolean" };
  }

  const response = await apiClient("/api/chat/confirm", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      thread_id: threadId,
      action_id: actionId,
      approved,
    }),
  });

  if (!response.ok) {
    const text = await response.text();
    return { status: `error: ${text}` };
  }

  return (await response.json()) as { status: string };
}
