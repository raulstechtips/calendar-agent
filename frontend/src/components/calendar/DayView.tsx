"use client";

import {
  clipToDay,
  getEventPosition,
  type CalendarEvent,
} from "@/lib/calendar";

import EventCard from "./EventCard";
import TimeGrid, { HOUR_HEIGHT } from "./TimeGrid";

interface DayViewProps {
  events: CalendarEvent[];
  date: Date;
  onEventClick: (event: CalendarEvent) => void;
}

export default function DayView({ events, date, onEventClick }: DayViewProps) {
  const allDayEvents = events.filter((e) => e.isAllDay);
  const timedEvents = events.filter((e) => !e.isAllDay);

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      {/* All-day section */}
      {allDayEvents.length > 0 && (
        <div className="border-b px-4 py-2">
          <div className="ml-16 flex flex-wrap gap-1">
            {allDayEvents.map((event) => (
              <EventCard
                key={event.id}
                event={event}
                onClick={() => onEventClick(event)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Time grid with events */}
      <TimeGrid columns={1}>
        <div className="absolute inset-0">
          {timedEvents.map((event) => {
            const { clippedStart, clippedEnd } = clipToDay(
              event.start,
              event.end,
              date,
            );
            const { top, height } = getEventPosition(
              clippedStart,
              clippedEnd,
              HOUR_HEIGHT,
            );
            return (
              <div
                key={event.id}
                className="absolute left-1 right-1"
                style={{ top, height }}
              >
                <EventCard
                  event={event}
                  onClick={() => onEventClick(event)}
                  style={{ height: "100%" }}
                />
              </div>
            );
          })}
        </div>
      </TimeGrid>
    </div>
  );
}
