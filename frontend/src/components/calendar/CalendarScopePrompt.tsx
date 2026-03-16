"use client";

import { Calendar } from "lucide-react";
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
  return (
    <div className="flex h-full items-center justify-center p-8">
      <Card className="max-w-md">
        <CardHeader>
          <div className="mx-auto mb-2 flex size-12 items-center justify-center rounded-full bg-primary/10">
            <Calendar className="size-6 text-primary" />
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
            onClick={() =>
              void signIn(
                "google",
                { redirectTo: "/calendar" },
                {
                  scope:
                    "openid email profile https://www.googleapis.com/auth/calendar.events",
                },
              )
            }
          >
            Grant Calendar Access
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
