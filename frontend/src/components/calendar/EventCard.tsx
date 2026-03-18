"use client";

import { Bot } from "lucide-react";

import { cn } from "@/lib/utils";
import type { CalendarEvent } from "@/lib/calendar";
import { Badge } from "@/components/ui/badge";

interface EventCardProps {
  event: CalendarEvent;
  onClick: () => void;
  style?: React.CSSProperties;
}

export default function EventCard({ event, onClick, style }: EventCardProps) {
  const timeLabel = event.isAllDay
    ? "All day"
    : formatTimeRange(event.start, event.end);

  return (
    <button
      type="button"
      onClick={onClick}
      style={style}
      className={cn(
        "w-full cursor-pointer rounded-md border-l-[3px] bg-card px-2.5 py-1.5 text-left text-xs shadow-sm transition-all duration-150",
        "hover:shadow-md focus-visible:ring-2 focus-visible:ring-ring",
        "outline-none overflow-hidden",
        event.isAiCreated
          ? "border-l-primary"
          : "border-l-border",
      )}
      aria-label={`${event.summary}, ${timeLabel}`}
    >
      <div className="flex items-center gap-1">
        <span className="truncate font-medium text-foreground">{event.summary}</span>
        {event.isAiCreated && (
          <Badge variant="secondary" className="h-5 shrink-0 px-1.5 text-[10px]">
            <Bot className="size-3" data-icon="inline-start" />
            AI
          </Badge>
        )}
      </div>
      <div className="truncate text-muted-foreground">{timeLabel}</div>
    </button>
  );
}

function formatTimeRange(startISO: string, endISO: string): string {
  const start = new Date(startISO);
  const end = new Date(endISO);
  const fmt = new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    minute: "2-digit",
  });
  return `${fmt.format(start)} – ${fmt.format(end)}`;
}
