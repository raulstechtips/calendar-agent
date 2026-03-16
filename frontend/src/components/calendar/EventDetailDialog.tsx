"use client";

import {
  Bot,
  Calendar,
  Clock,
  ExternalLink,
  MapPin,
  Users,
} from "lucide-react";

import type { CalendarEvent } from "@/lib/calendar";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface EventDetailDialogProps {
  event: CalendarEvent | null;
  open: boolean;
  onClose: () => void;
}

export default function EventDetailDialog({
  event,
  open,
  onClose,
}: EventDetailDialogProps) {
  if (!event) return null;

  const timeLabel = event.isAllDay
    ? "All day"
    : formatDetailTime(event.start, event.end);

  const dateLabel = new Date(event.start).toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  });

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-md">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <DialogTitle>{event.summary}</DialogTitle>
            {event.isAiCreated && (
              <Badge variant="secondary">
                <Bot className="size-3" data-icon="inline-start" />
                AI Created
              </Badge>
            )}
          </div>
          <DialogDescription>{dateLabel}</DialogDescription>
        </DialogHeader>

        <div className="space-y-3">
          {/* Time */}
          <div className="flex items-center gap-2 text-sm">
            <Clock className="size-4 shrink-0 text-muted-foreground" />
            <span>{timeLabel}</span>
          </div>

          {/* Location */}
          {event.location && (
            <div className="flex items-center gap-2 text-sm">
              <MapPin className="size-4 shrink-0 text-muted-foreground" />
              <span>{event.location}</span>
            </div>
          )}

          {/* Description */}
          {event.description && (
            <div className="flex gap-2 text-sm">
              <Calendar className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
              <p className="whitespace-pre-wrap text-muted-foreground">
                {event.description}
              </p>
            </div>
          )}

          {/* Attendees */}
          {event.attendees && event.attendees.length > 0 && (
            <div className="flex gap-2 text-sm">
              <Users className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
              <div className="space-y-1">
                {event.attendees.map((attendee) => (
                  <div key={attendee.email} className="flex items-center gap-1">
                    <span>{attendee.displayName ?? attendee.email}</span>
                    {attendee.responseStatus && (
                      <span className="text-xs text-muted-foreground">
                        ({attendee.responseStatus})
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Google Calendar link */}
          {event.htmlLink && (
            <a
              href={event.htmlLink}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
            >
              Open in Google Calendar
              <ExternalLink className="size-3" />
            </a>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

function formatDetailTime(startISO: string, endISO: string): string {
  const start = new Date(startISO);
  const end = new Date(endISO);
  const fmt = new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    minute: "2-digit",
  });
  return `${fmt.format(start)} – ${fmt.format(end)}`;
}
