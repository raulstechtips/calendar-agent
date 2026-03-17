"use client";

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

interface ChatThreadProps {
  messages: ChatMessageType[];
  isStreaming: boolean;
  pendingConfirmation: PendingConfirmation | null;
  scopeRequired: ScopeRequired | null;
  onApprove: () => void;
  onReject: () => void;
  onGrantScope: () => void;
}

export default function ChatThread({
  messages,
  isStreaming,
  pendingConfirmation,
  scopeRequired,
  onApprove,
  onReject,
  onGrantScope,
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
      <div className="flex flex-1 items-center justify-center p-8">
        <p className="text-muted-foreground">
          Start a conversation with your calendar assistant.
        </p>
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
