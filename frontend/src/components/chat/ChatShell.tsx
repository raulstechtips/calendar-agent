"use client";

import { AlertCircle } from "lucide-react";
import { signIn, useSession } from "next-auth/react";

import {
  Alert,
  AlertDescription,
  AlertAction,
} from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { useChat } from "@/hooks/useChat";

import ChatInput from "./ChatInput";
import ChatThread from "./ChatThread";

export default function ChatShell() {
  const { status } = useSession();

  const {
    messages,
    isStreaming,
    error,
    pendingConfirmation,
    scopeRequired,
    sendMessage,
    confirmAction,
    clearError,
  } = useChat();

  if (status === "loading") {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

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
        scopeRequired={scopeRequired}
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
        onSend={sendMessage}
        onGrantScope={() => {
          void signIn(
            "google",
            { redirectTo: "/chat" },
            {
              scope:
                "openid email profile https://www.googleapis.com/auth/calendar.events https://www.googleapis.com/auth/calendar.readonly",
            },
          );
        }}
      />
      <ChatInput onSend={sendMessage} isStreaming={isStreaming} />
    </div>
  );
}
