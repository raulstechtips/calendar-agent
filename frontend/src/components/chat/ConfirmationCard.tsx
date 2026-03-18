"use client";

import { useState } from "react";
import {
  CalendarCog,
  CalendarPlus,
  CalendarX2,
  Check,
  Loader2,
  X,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  formatConfirmationDetails,
  getActionLabel,
} from "@/lib/format-confirmation";

const ACTION_ICONS: Record<string, typeof CalendarPlus> = {
  create_event: CalendarPlus,
  update_event: CalendarCog,
  delete_event: CalendarX2,
};

interface ConfirmationCardProps {
  action: string;
  details: Record<string, unknown>;
  status: "pending" | "confirmed" | "cancelled";
  onApprove: () => void;
  onReject: () => void;
  disabled?: boolean;
}

export default function ConfirmationCard({
  action,
  details,
  status,
  onApprove,
  onReject,
  disabled,
}: ConfirmationCardProps) {
  const [isPending, setIsPending] = useState(false);
  const Icon = ACTION_ICONS[action] ?? CalendarPlus;
  const fields = formatConfirmationDetails(action, details);
  const isDisabled = disabled || isPending;

  return (
    <Card size="sm" className="mx-5 my-2 max-w-md border-l-[3px] border-l-primary">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Icon className="size-5" />
          {getActionLabel(action)}
        </CardTitle>
      </CardHeader>
      {fields.length > 0 && (
        <CardContent>
          <dl className="space-y-1 text-sm">
            {fields.map((field) => (
              <div key={field.label} className="flex gap-2">
                <dt className="font-medium text-muted-foreground">
                  {field.label}:
                </dt>
                <dd>{field.value}</dd>
              </div>
            ))}
          </dl>
        </CardContent>
      )}
      <CardFooter className="gap-2">
        {status === "pending" && (
          <>
            <Button
              size="sm"
              onClick={() => {
                setIsPending(true);
                onApprove();
              }}
              disabled={isDisabled}
              aria-label="Approve"
            >
              {isPending ? (
                <Loader2 className="animate-spin" data-icon="inline-start" />
              ) : (
                <Check data-icon="inline-start" />
              )}
              Approve
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={onReject}
              disabled={isDisabled}
              aria-label="Reject"
            >
              <X data-icon="inline-start" />
              Reject
            </Button>
          </>
        )}
        {status === "confirmed" && (
          <Badge>
            <Check data-icon="inline-start" />
            Confirmed
          </Badge>
        )}
        {status === "cancelled" && (
          <Badge variant="outline">
            <X data-icon="inline-start" />
            Cancelled
          </Badge>
        )}
      </CardFooter>
    </Card>
  );
}
