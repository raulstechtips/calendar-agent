"use client";

import { Bot, User } from "lucide-react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import type { ChatMessage as ChatMessageType } from "@/lib/chat-stream";
import { renderMarkdown } from "@/lib/render-markdown";
import { cn } from "@/lib/utils";

interface ChatMessageProps {
  message: ChatMessageType;
  isStreaming?: boolean;
}

export default function ChatMessage({
  message,
  isStreaming,
}: ChatMessageProps) {
  const isUser = message.role === "user";

  // Hide empty bubbles that aren't actively streaming (phantom bubble fix)
  if (!message.content && !isStreaming) {
    return null;
  }

  return (
    <div
      className={cn(
        "flex gap-2.5 px-5 py-2.5",
        isUser ? "justify-end" : "justify-start",
      )}
    >
      {!isUser && (
        <Avatar size="sm" className="mt-5 shrink-0">
          <AvatarFallback className="bg-primary/10">
            <Bot className="size-3.5 text-primary" />
          </AvatarFallback>
        </Avatar>
      )}
      <div
        className={cn(
          "flex max-w-[80%] flex-col gap-1",
          isUser ? "items-end" : "items-start",
        )}
      >
        <span className="px-1 text-[11px] font-medium uppercase tracking-wider text-muted-foreground/70">
          {isUser ? "You" : "Assistant"}
        </span>
        <div
          className={cn(
            "rounded-2xl px-4 py-3 text-sm leading-relaxed",
            isUser
              ? "rounded-br-md bg-primary text-primary-foreground shadow-md shadow-primary/20"
              : "rounded-bl-md border border-border/50 bg-card text-foreground shadow-sm",
          )}
        >
          {message.content
            ? renderMarkdown(message.content)
            : isStreaming && (
                <span
                  aria-label="Assistant is typing"
                  className="inline-flex gap-1"
                >
                  <span className="size-1.5 animate-bounce rounded-full bg-current [animation-delay:0ms]" />
                  <span className="size-1.5 animate-bounce rounded-full bg-current [animation-delay:150ms]" />
                  <span className="size-1.5 animate-bounce rounded-full bg-current [animation-delay:300ms]" />
                </span>
              )}
        </div>
      </div>
      {isUser && (
        <Avatar size="sm" className="mt-5 shrink-0">
          <AvatarFallback className="bg-primary text-primary-foreground">
            <User className="size-3.5" />
          </AvatarFallback>
        </Avatar>
      )}
    </div>
  );
}
