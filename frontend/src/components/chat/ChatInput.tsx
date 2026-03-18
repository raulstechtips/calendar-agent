"use client";

import { Loader2, SendHorizonal } from "lucide-react";
import { useRef, type KeyboardEvent } from "react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

interface ChatInputProps {
  onSend: (message: string) => void;
  isStreaming: boolean;
}

export default function ChatInput({ onSend, isStreaming }: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  function handleSubmit() {
    const value = textareaRef.current?.value.trim();
    if (!value) return;
    onSend(value);
    if (textareaRef.current) {
      textareaRef.current.value = "";
    }
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }

  return (
    <div className="flex items-end gap-2 border-t border-border/40 bg-card/80 px-5 py-3 backdrop-blur-sm">
      <Textarea
        ref={textareaRef}
        aria-label="Chat message"
        placeholder="Ask about your calendar..."
        className="min-h-11 max-h-32 resize-none rounded-xl border border-border/60 bg-background px-4 py-3 text-sm shadow-sm transition-shadow focus-visible:shadow-md focus-visible:ring-1 focus-visible:ring-primary"
        disabled={isStreaming}
        onKeyDown={handleKeyDown}
      />
      <Button
        aria-label="Send message"
        size="icon"
        className="size-11 shrink-0 rounded-xl shadow-sm"
        disabled={isStreaming}
        onClick={handleSubmit}
      >
        {isStreaming ? (
          <Loader2 className="animate-spin" />
        ) : (
          <SendHorizonal className="size-4" />
        )}
      </Button>
    </div>
  );
}
