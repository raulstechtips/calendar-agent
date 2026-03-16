"use client";

import { CalendarOff } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { useSession } from "next-auth/react";
import { useMemo, useState } from "react";

import {
  formatISODate,
  getDayRange,
  getWeekRange,
  parseDate,
  type CalendarEvent,
  type CalendarViewType,
} from "@/lib/calendar";
import { useCalendarEvents } from "@/hooks/useCalendarEvents";

import CalendarScopePrompt from "./CalendarScopePrompt";
import CalendarSkeleton from "./CalendarSkeleton";
import CalendarToolbar from "./CalendarToolbar";
import DayView from "./DayView";
import EventDetailDialog from "./EventDetailDialog";
import WeekView from "./WeekView";

export default function CalendarShell() {
  const { data: session, status } = useSession();
  const searchParams = useSearchParams();

  const rawView = searchParams.get("view");
  const view: CalendarViewType = rawView === "day" ? "day" : "week";
  const dateParam = searchParams.get("date") ?? undefined;
  const currentDate = useMemo(() => parseDate(dateParam), [dateParam]);

  const { timeMin, timeMax } = useMemo(() => {
    const range =
      view === "day" ? getDayRange(currentDate) : getWeekRange(currentDate);
    return {
      timeMin: range.start.toISOString(),
      timeMax: range.end.toISOString(),
    };
  }, [view, currentDate]);

  const accessToken = session?.accessToken;
  const { events, isLoading, error } = useCalendarEvents(
    accessToken,
    timeMin,
    timeMax,
  );

  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(
    null,
  );

  // Auth loading
  if (status === "loading") {
    return <CalendarSkeleton />;
  }

  // Calendar scope not granted
  if (error === "scope_required") {
    return <CalendarScopePrompt />;
  }

  const dateString = dateParam ?? formatISODate(new Date());

  return (
    <div className="flex h-full flex-col">
      <CalendarToolbar view={view} currentDate={dateString} />

      {isLoading ? (
        <CalendarSkeleton />
      ) : error ? (
        <div className="flex flex-1 items-center justify-center p-8">
          <p className="text-sm text-destructive">
            Failed to load calendar events. Please try again.
          </p>
        </div>
      ) : events.length === 0 ? (
        <div className="flex flex-1 flex-col items-center justify-center gap-2 p-8">
          <CalendarOff className="size-10 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">
            No events in this time range.
          </p>
        </div>
      ) : view === "day" ? (
        <DayView events={events} date={currentDate} onEventClick={setSelectedEvent} />
      ) : (
        <WeekView
          events={events}
          weekStart={getWeekRange(currentDate).start}
          onEventClick={setSelectedEvent}
        />
      )}

      <EventDetailDialog
        event={selectedEvent}
        open={selectedEvent !== null}
        onClose={() => setSelectedEvent(null)}
      />
    </div>
  );
}
