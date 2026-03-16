"use client";

import { AlertCircle } from "lucide-react";

import {
  Alert,
  AlertDescription,
  AlertAction,
} from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { useChat } from "@/hooks/useChat";

import ChatInput from "./ChatInput";
import ChatThread from "./ChatThread";

interface ChatShellProps {
  token: string;
}

export default function ChatShell({ token }: ChatShellProps) {
  const {
    messages,
    isStreaming,
    error,
    pendingConfirmation,
    sendMessage,
    confirmAction,
    clearError,
  } = useChat(token);

  return (
    <div className="flex h-full flex-col">
      {error && (
        <Alert variant="destructive" className="m-4">
          <AlertCircle />
          <AlertDescription>{error}</AlertDescription>
          <AlertAction>
            <Button variant="ghost" size="icon-xs" onClick={clearError}>
              <span className="sr-only">Dismiss</span>
              &times;
            </Button>
          </AlertAction>
        </Alert>
      )}
      <ChatThread
        messages={messages}
        isStreaming={isStreaming}
        pendingConfirmation={pendingConfirmation}
        onApprove={() => {
          if (pendingConfirmation) {
            void confirmAction(pendingConfirmation.actionId, true);
          }
        }}
        onReject={() => {
          if (pendingConfirmation) {
            void confirmAction(pendingConfirmation.actionId, false);
          }
        }}
      />
      <ChatInput onSend={sendMessage} isStreaming={isStreaming} />
    </div>
  );
}
