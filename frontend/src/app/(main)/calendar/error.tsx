"use client";

import { AlertCircle } from "lucide-react";

import { Alert, AlertDescription, AlertAction } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

interface ErrorPageProps {
  error: Error;
  reset: () => void;
}

export default function CalendarError({ error, reset }: ErrorPageProps) {
  return (
    <div className="flex h-full items-center justify-center p-8">
      <Alert variant="destructive" className="max-w-md">
        <AlertCircle />
        <AlertDescription>
          {error.message || "Something went wrong loading the calendar."}
        </AlertDescription>
        <AlertAction>
          <Button variant="outline" size="sm" onClick={reset}>
            Try again
          </Button>
        </AlertAction>
      </Alert>
    </div>
  );
}
