"use client";

import { Calendar } from "lucide-react";

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
  return (
    <Card size="sm" className="mx-4 my-2 max-w-md">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Calendar className="size-4" />
          Calendar Access Required
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">
          Grant calendar permissions so I can view and manage your events.
        </p>
      </CardContent>
      <CardFooter>
        <Button size="sm" onClick={onGrant}>
          Grant Calendar Access
        </Button>
      </CardFooter>
    </Card>
  );
}
