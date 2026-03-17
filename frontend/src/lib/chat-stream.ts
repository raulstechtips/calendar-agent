/**
 * SSE streaming client for the chat endpoint.
 * Pure functions — no React dependency.
 */

// ---------------------------------------------------------------------------
// SSE Event Types (discriminated union matching backend protocol)
// ---------------------------------------------------------------------------

export interface TokenEvent {
  type: "token";
  content: string;
}

export interface DoneEvent {
  type: "done";
  thread_id: string;
}

export interface ErrorEvent {
  type: "error";
  content: string;
}

export interface BlockedEvent {
  type: "blocked";
  content: string;
}

export interface ConfirmationEvent {
  type: "confirmation";
  action: string;
  action_id: string;
  details: Record<string, unknown>;
}

export interface ScopeRequiredEvent {
  type: "scope_required";
  scope: string;
}

export type ChatSSEEvent =
  | TokenEvent
  | DoneEvent
  | ErrorEvent
  | BlockedEvent
  | ConfirmationEvent
  | ScopeRequiredEvent;

// ---------------------------------------------------------------------------
// Chat message and state types (used by useChat and components)
// ---------------------------------------------------------------------------

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
}

export interface PendingConfirmation {
  actionId: string;
  action: string;
  details: Record<string, unknown>;
  status: "pending" | "confirmed" | "cancelled";
}

export interface ScopeRequired {
  scope: string;
}

// ---------------------------------------------------------------------------
// Error class
// ---------------------------------------------------------------------------

export class ChatStreamError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(`Chat stream error (${status}): ${message}`);
    this.name = "ChatStreamError";
  }
}

// ---------------------------------------------------------------------------
// Streaming client
// ---------------------------------------------------------------------------

interface StreamChatParams {
  message: string;
  threadId: string | null;
  signal?: AbortSignal;
}

/** Stream chat responses from the backend as parsed SSE events. */
export async function* streamChat(
  params: StreamChatParams,
): AsyncGenerator<ChatSSEEvent> {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message: params.message,
      thread_id: params.threadId,
    }),
    signal: params.signal,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new ChatStreamError(response.status, text);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new ChatStreamError(0, "No response body");
  }

  const decoder = new TextDecoder();
  let buffer = "";

  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      // Keep the last incomplete line in the buffer
      buffer = lines.pop() ?? "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const json = line.slice(6).trim();
          if (json) {
            try {
              yield JSON.parse(json) as ChatSSEEvent;
            } catch {
              // Skip malformed SSE events rather than aborting the stream
            }
          }
        }
      }
    }

    // Process any remaining data in buffer
    if (buffer.startsWith("data: ")) {
      const json = buffer.slice(6).trim();
      if (json) {
        try {
          yield JSON.parse(json) as ChatSSEEvent;
        } catch {
          // Skip malformed trailing data
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
