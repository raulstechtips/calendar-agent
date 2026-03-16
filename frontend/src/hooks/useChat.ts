"use client";

import { useCallback, useEffect, useReducer, useRef } from "react";

import { submitConfirmation } from "@/actions/chat";
import {
  type ChatMessage,
  type ChatSSEEvent,
  type PendingConfirmation,
  streamChat,
} from "@/lib/chat-stream";

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

interface ChatState {
  messages: ChatMessage[];
  threadId: string | null;
  isStreaming: boolean;
  error: string | null;
  pendingConfirmation: PendingConfirmation | null;
}

const initialState: ChatState = {
  messages: [],
  threadId: null,
  isStreaming: false,
  error: null,
  pendingConfirmation: null,
};

// ---------------------------------------------------------------------------
// Actions (discriminated union)
// ---------------------------------------------------------------------------

type ChatAction =
  | { type: "SEND_MESSAGE"; message: ChatMessage; assistantId: string }
  | { type: "APPEND_TOKEN"; content: string }
  | { type: "STREAM_DONE"; threadId: string }
  | { type: "STREAM_ERROR"; error: string }
  | { type: "BLOCKED"; content: string }
  | { type: "CONFIRMATION_RECEIVED"; confirmation: PendingConfirmation }
  | { type: "CONFIRMATION_RESOLVED" }
  | { type: "CLEAR_ERROR" };

function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case "SEND_MESSAGE":
      return {
        ...state,
        messages: [
          ...state.messages,
          action.message,
          { id: action.assistantId, role: "assistant", content: "" },
        ],
        isStreaming: true,
        error: null,
      };

    case "APPEND_TOKEN": {
      const msgs = [...state.messages];
      const last = msgs[msgs.length - 1];
      if (last?.role === "assistant") {
        msgs[msgs.length - 1] = {
          ...last,
          content: last.content + action.content,
        };
      }
      return { ...state, messages: msgs };
    }

    case "STREAM_DONE":
      return { ...state, isStreaming: false, threadId: action.threadId };

    case "STREAM_ERROR":
      return { ...state, isStreaming: false, error: action.error };

    case "BLOCKED": {
      const msgs = [...state.messages];
      const last = msgs[msgs.length - 1];
      if (last?.role === "assistant") {
        msgs[msgs.length - 1] = { ...last, content: action.content };
      }
      return { ...state, messages: msgs };
    }

    case "CONFIRMATION_RECEIVED":
      return { ...state, pendingConfirmation: action.confirmation };

    case "CONFIRMATION_RESOLVED":
      return { ...state, pendingConfirmation: null };

    case "CLEAR_ERROR":
      return { ...state, error: null };

    default:
      return state;
  }
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export interface UseChatReturn {
  messages: ChatMessage[];
  threadId: string | null;
  isStreaming: boolean;
  error: string | null;
  pendingConfirmation: PendingConfirmation | null;
  sendMessage: (text: string) => Promise<void>;
  confirmAction: (actionId: string, approved: boolean) => Promise<void>;
  clearError: () => void;
}

/** Chat state management hook with SSE streaming. */
export function useChat(token: string): UseChatReturn {
  const [state, dispatch] = useReducer(chatReducer, initialState);
  const abortRef = useRef<AbortController | null>(null);
  const streamingRef = useRef(false);

  // Abort any in-flight stream on unmount
  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || streamingRef.current) return;

      // Abort previous stream if any
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      const userMsg: ChatMessage = {
        id: `user-${crypto.randomUUID()}`,
        role: "user",
        content: trimmed,
      };
      const assistantId = `assistant-${crypto.randomUUID()}`;

      dispatch({ type: "SEND_MESSAGE", message: userMsg, assistantId });
      streamingRef.current = true;

      try {
        const stream = streamChat({
          message: trimmed,
          threadId: state.threadId,
          token,
          signal: controller.signal,
        });

        for await (const event of stream) {
          if (controller.signal.aborted) break;
          handleEvent(event, dispatch);
        }
      } catch (err) {
        if ((err as Error).name !== "AbortError") {
          dispatch({
            type: "STREAM_ERROR",
            error: (err as Error).message || "An unexpected error occurred",
          });
        }
      } finally {
        streamingRef.current = false;
      }
    },
    [state.threadId, token],
  );

  const confirmAction = useCallback(
    async (actionId: string, approved: boolean) => {
      if (!state.threadId) return;
      try {
        const result = await submitConfirmation(state.threadId, actionId, approved);
        if (result.status.startsWith("error:")) {
          dispatch({ type: "STREAM_ERROR", error: result.status });
        } else {
          dispatch({ type: "CONFIRMATION_RESOLVED" });
        }
      } catch (err) {
        dispatch({
          type: "STREAM_ERROR",
          error: (err as Error).message || "Confirmation failed",
        });
      }
    },
    [state.threadId],
  );

  const clearError = useCallback(() => {
    dispatch({ type: "CLEAR_ERROR" });
  }, []);

  return {
    messages: state.messages,
    threadId: state.threadId,
    isStreaming: state.isStreaming,
    error: state.error,
    pendingConfirmation: state.pendingConfirmation,
    sendMessage,
    confirmAction,
    clearError,
  };
}

// ---------------------------------------------------------------------------
// Event handler
// ---------------------------------------------------------------------------

function handleEvent(
  event: ChatSSEEvent,
  dispatch: React.Dispatch<ChatAction>,
): void {
  switch (event.type) {
    case "token":
      dispatch({ type: "APPEND_TOKEN", content: event.content });
      break;
    case "done":
      dispatch({ type: "STREAM_DONE", threadId: event.thread_id });
      break;
    case "error":
      dispatch({ type: "STREAM_ERROR", error: event.content });
      break;
    case "blocked":
      dispatch({ type: "BLOCKED", content: event.content });
      break;
  }
}
