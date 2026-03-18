"use client";

import { useState } from "react";
import { Calendar, Loader2 } from "lucide-react";
import { signIn } from "next-auth/react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function CalendarScopePrompt() {
  const [isPending, setIsPending] = useState(false);

  return (
    <div className="flex h-full items-center justify-center bg-background p-8">
      <Card className="max-w-lg shadow-lg">
        <CardHeader>
          <div className="mx-auto mb-3 flex size-14 items-center justify-center rounded-2xl bg-primary shadow-md shadow-primary/25">
            <Calendar className="size-7 text-primary-foreground" />
          </div>
          <CardTitle className="text-center">Calendar Access Required</CardTitle>
          <CardDescription className="text-center">
            Grant calendar access so we can display your Google Calendar events.
            This allows read and write access for the AI assistant to manage
            your schedule.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex justify-center">
          <Button
            disabled={isPending}
            onClick={() => {
              setIsPending(true);
              void signIn(
                "google",
                { redirectTo: "/calendar" },
                {
                  scope:
                    "openid email profile https://www.googleapis.com/auth/calendar.events https://www.googleapis.com/auth/calendar.readonly",
                },
              );
            }}
          >
            {isPending && <Loader2 className="animate-spin" data-icon="inline-start" />}
            Grant Calendar Access
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
