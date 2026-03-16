"use client";

import { useCallback, useEffect, useRef } from "react";

import { ScrollArea } from "@/components/ui/scroll-area";
import type { ChatMessage as ChatMessageType, PendingConfirmation } from "@/lib/chat-stream";

import ChatMessage from "./ChatMessage";
import ConfirmationCard from "./ConfirmationCard";

interface ChatThreadProps {
  messages: ChatMessageType[];
  isStreaming: boolean;
  pendingConfirmation: PendingConfirmation | null;
  onApprove: () => void;
  onReject: () => void;
}

export default function ChatThread({
  messages,
  isStreaming,
  pendingConfirmation,
  onApprove,
  onReject,
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
            onApprove={onApprove}
            onReject={onReject}
          />
        )}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
}
