"use client";

import { Check, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

interface ConfirmationCardProps {
  action: string;
  details: Record<string, unknown>;
  onApprove: () => void;
  onReject: () => void;
  disabled?: boolean;
}

export default function ConfirmationCard({
  action,
  details,
  onApprove,
  onReject,
  disabled,
}: ConfirmationCardProps) {
  return (
    <Card size="sm" className="mx-4 my-2 max-w-md">
      <CardHeader>
        <CardTitle>Confirm: {action}</CardTitle>
      </CardHeader>
      <CardContent>
        <dl className="space-y-1 text-sm">
          {Object.entries(details).map(([key, value]) =>
            value != null ? (
              <div key={key} className="flex gap-2">
                <dt className="font-medium text-muted-foreground">{key}:</dt>
                <dd>{typeof value === "object" ? JSON.stringify(value) : String(value)}</dd>
              </div>
            ) : null,
          )}
        </dl>
      </CardContent>
      <CardFooter className="gap-2">
        <Button
          size="sm"
          onClick={onApprove}
          disabled={disabled}
          aria-label="Approve"
        >
          <Check data-icon="inline-start" />
          Approve
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={onReject}
          disabled={disabled}
          aria-label="Reject"
        >
          <X data-icon="inline-start" />
          Reject
        </Button>
      </CardFooter>
    </Card>
  );
}
