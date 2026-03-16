"use client";

import { AlertCircle } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

interface ChatErrorProps {
  error: Error;
  reset: () => void;
}

export default function ChatError({ error, reset }: ChatErrorProps) {
  return (
    <div className="flex h-full flex-col items-center justify-center p-8">
      <Alert variant="destructive" className="max-w-md">
        <AlertCircle />
        <AlertTitle>Something went wrong</AlertTitle>
        <AlertDescription>
          {error.message || "An unexpected error occurred in the chat."}
        </AlertDescription>
      </Alert>
      <Button onClick={reset} variant="outline" className="mt-4">
        Try again
      </Button>
    </div>
  );
}
