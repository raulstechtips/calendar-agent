"use client";

import { SendHorizonal } from "lucide-react";
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
    <div className="flex gap-2 border-t bg-background p-4">
      <Textarea
        ref={textareaRef}
        aria-label="Chat message"
        placeholder="Ask about your calendar..."
        className="min-h-10 max-h-32 resize-none"
        disabled={isStreaming}
        onKeyDown={handleKeyDown}
      />
      <Button
        aria-label="Send message"
        size="icon"
        disabled={isStreaming}
        onClick={handleSubmit}
      >
        <SendHorizonal />
      </Button>
    </div>
  );
}
