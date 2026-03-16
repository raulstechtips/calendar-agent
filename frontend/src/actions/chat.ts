"use server";

import { apiClient } from "@/lib/api";

/** Confirm or reject a pending write operation. */
export async function submitConfirmation(
  threadId: string,
  actionId: string,
  approved: boolean,
): Promise<{ status: string }> {
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
