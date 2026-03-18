"use client";

import { useState } from "react";
import { Calendar, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

interface ScopeRequiredCardProps {
  onGrant: () => void;
}

export default function ScopeRequiredCard({ onGrant }: ScopeRequiredCardProps) {
  const [isPending, setIsPending] = useState(false);

  return (
    <Card size="sm" className="mx-5 my-2 max-w-md border-l-[3px] border-l-primary">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Calendar className="size-5" />
          Calendar Access Required
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">
          Grant calendar permissions so I can view and manage your events.
        </p>
      </CardContent>
      <CardFooter>
        <Button
          size="sm"
          disabled={isPending}
          onClick={() => {
            setIsPending(true);
            onGrant();
          }}
        >
          {isPending && <Loader2 className="animate-spin" data-icon="inline-start" />}
          Grant Calendar Access
        </Button>
      </CardFooter>
    </Card>
  );
}
