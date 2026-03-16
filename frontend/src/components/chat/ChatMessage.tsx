"use client";

import { Bot, User } from "lucide-react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import type { ChatMessage as ChatMessageType } from "@/lib/chat-stream";
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

  return (
    <div
      className={cn(
        "flex gap-3 px-4 py-3",
        isUser ? "justify-end" : "justify-start",
      )}
    >
      {!isUser && (
        <Avatar size="sm">
          <AvatarFallback>
            <Bot className="size-3.5" />
          </AvatarFallback>
        </Avatar>
      )}
      <div
        className={cn(
          "flex max-w-[80%] flex-col gap-1",
          isUser ? "items-end" : "items-start",
        )}
      >
        <span className="text-xs text-muted-foreground">
          {isUser ? "You" : "Assistant"}
        </span>
        <div
          className={cn(
            "rounded-lg px-3 py-2 text-sm",
            isUser
              ? "bg-primary text-primary-foreground"
              : "bg-muted text-foreground",
          )}
        >
          {message.content || (isStreaming && (
            <span
              aria-label="Assistant is typing"
              className="inline-flex gap-1"
            >
              <span className="size-1.5 animate-bounce rounded-full bg-current [animation-delay:0ms]" />
              <span className="size-1.5 animate-bounce rounded-full bg-current [animation-delay:150ms]" />
              <span className="size-1.5 animate-bounce rounded-full bg-current [animation-delay:300ms]" />
            </span>
          ))}
        </div>
      </div>
      {isUser && (
        <Avatar size="sm">
          <AvatarFallback>
            <User className="size-3.5" />
          </AvatarFallback>
        </Avatar>
      )}
    </div>
  );
}
