"use client";

import { MessageSquare } from "lucide-react";
import { useCallback, useEffect, useRef } from "react";

import { ScrollArea } from "@/components/ui/scroll-area";
import type {
  ChatMessage as ChatMessageType,
  PendingConfirmation,
  ScopeRequired,
} from "@/lib/chat-stream";

import ChatMessage from "./ChatMessage";
import ConfirmationCard from "./ConfirmationCard";
import ScopeRequiredCard from "./ScopeRequiredCard";

const SUGGESTIONS = [
  "What's on my schedule today?",
  "Find a free slot this week",
  "Schedule a 30-min focus block",
] as const;

interface ChatThreadProps {
  messages: ChatMessageType[];
  isStreaming: boolean;
  pendingConfirmation: PendingConfirmation | null;
  scopeRequired: ScopeRequired | null;
  onApprove: () => void;
  onReject: () => void;
  onGrantScope: () => void;
  onSend?: (message: string) => void;
}

export default function ChatThread({
  messages,
  isStreaming,
  pendingConfirmation,
  scopeRequired,
  onApprove,
  onReject,
  onGrantScope,
  onSend,
}: ChatThreadProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const rafRef = useRef<number>(0);

  // Throttle scroll to once per animation frame to avoid jank during streaming
  const scrollToBottom = useCallback(() => {
    cancelAnimationFrame(rafRef.current);
    rafRef.current = requestAnimationFrame(() => {
      bottomRef.current?.scrollIntoView?.({ behavior: "smooth" });
    });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Cleanup pending RAF on unmount
  useEffect(() => {
    return () => cancelAnimationFrame(rafRef.current);
  }, []);

  if (messages.length === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-6 p-8">
        <div className="flex size-16 items-center justify-center rounded-2xl bg-primary/10 shadow-sm">
          <MessageSquare className="size-7 text-primary" />
        </div>
        <div className="text-center">
          <h2 className="text-xl font-semibold tracking-tight text-foreground">
            How can I help with your calendar?
          </h2>
          <p className="mt-1.5 text-sm text-muted-foreground">
            Start a conversation with your calendar assistant.
          </p>
        </div>
        {onSend && (
          <div className="flex flex-wrap justify-center gap-2 pt-2">
            {SUGGESTIONS.map((suggestion) => (
              <button
                key={suggestion}
                type="button"
                onClick={() => onSend(suggestion)}
                className="rounded-lg border border-border/60 bg-card px-4 py-2.5 text-sm text-foreground shadow-sm transition-all hover:border-primary/30 hover:shadow-md"
              >
                {suggestion}
              </button>
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <ScrollArea className="flex-1">
      <div role="log" aria-live="polite" className="py-4">
        {messages.map((message, index) => (
          <ChatMessage
            key={message.id}
            message={message}
            isStreaming={
              isStreaming &&
              index === messages.length - 1 &&
              message.role === "assistant"
            }
          />
        ))}
        {pendingConfirmation && (
          <ConfirmationCard
            action={pendingConfirmation.action}
            details={pendingConfirmation.details}
            status={pendingConfirmation.status}
            onApprove={onApprove}
            onReject={onReject}
            // Defense-in-depth: buttons are only rendered when status is
            // "pending", but disabled ensures safety if that logic changes.
            disabled={pendingConfirmation.status !== "pending"}
          />
        )}
        {scopeRequired && <ScopeRequiredCard onGrant={onGrantScope} />}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
}
