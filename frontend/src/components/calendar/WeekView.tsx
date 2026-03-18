"use client";

import {
  addDays,
  clipToDay,
  computeEventLanes,
  getEventPosition,
  isSameDay,
  overlapsDay,
  type CalendarEvent,
} from "@/lib/calendar";
import { cn } from "@/lib/utils";

import EventCard from "./EventCard";
import TimeGrid, { HOUR_HEIGHT } from "./TimeGrid";

interface WeekViewProps {
  events: CalendarEvent[];
  weekStart: Date;
  onEventClick: (event: CalendarEvent) => void;
}

const DAYS_IN_WEEK = 7;

export default function WeekView({
  events,
  weekStart,
  onEventClick,
}: WeekViewProps) {
  const days = Array.from({ length: DAYS_IN_WEEK }, (_, i) =>
    addDays(weekStart, i),
  );
  const today = new Date();

  const allDayEvents = events.filter((e) => e.isAllDay);
  const timedEvents = events.filter((e) => !e.isAllDay);

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      {/* Day headers */}
      <div className="flex border-b border-border/60">
        <div className="w-16 shrink-0 border-r border-border/50" />
        <div className="grid flex-1" style={{ gridTemplateColumns: `repeat(${DAYS_IN_WEEK}, 1fr)` }}>
          {days.map((day, i) => (
            <div
              key={i}
              className={cn(
                "border-l border-border/30 px-1 py-2.5 text-center first:border-l-0",
                isSameDay(day, today) && "bg-primary/[0.06]",
              )}
            >
              <div className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                {day.toLocaleDateString("en-US", { weekday: "short" })}
              </div>
              <div
                className={cn(
                  "mx-auto mt-1 flex size-8 items-center justify-center rounded-full text-sm font-semibold",
                  isSameDay(day, today)
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "text-foreground",
                )}
              >
                {day.getDate()}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* All-day section */}
      {allDayEvents.length > 0 && (
        <div className="flex border-b">
          <div className="w-16 shrink-0 border-r" />
          <div
            className="grid flex-1 gap-0.5 p-1"
            style={{ gridTemplateColumns: `repeat(${DAYS_IN_WEEK}, 1fr)` }}
          >
            {days.map((day, i) => {
              const dayAllDay = allDayEvents.filter((e) =>
                overlapsDay(e.start, e.end, day),
              );
              return (
                <div key={i} className="flex flex-col gap-0.5">
                  {dayAllDay.map((event) => (
                    <EventCard
                      key={event.id}
                      event={event}
                      onClick={() => onEventClick(event)}
                    />
                  ))}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Time grid with events */}
      <TimeGrid columns={DAYS_IN_WEEK}>
        <div
          className="absolute inset-0 grid"
          style={{ gridTemplateColumns: `repeat(${DAYS_IN_WEEK}, 1fr)` }}
        >
          {days.map((day, i) => {
            const dayEvents = timedEvents.filter((e) =>
              overlapsDay(e.start, e.end, day),
            );
            const lanedEvents = computeEventLanes(dayEvents);
            return (
              <div key={i} className="relative px-0.5">
                {lanedEvents.map(({ event, lane, totalLanes }) => {
                  const { clippedStart, clippedEnd } = clipToDay(
                    event.start,
                    event.end,
                    day,
                  );
                  const { top, height } = getEventPosition(
                    clippedStart,
                    clippedEnd,
                    HOUR_HEIGHT,
                  );
                  const widthPercent = 100 / totalLanes;
                  const leftPercent = lane * widthPercent;
                  return (
                    <div
                      key={event.id}
                      className="absolute"
                      style={{
                        top,
                        height,
                        left: `${leftPercent}%`,
                        width: `${widthPercent}%`,
                        paddingLeft: 1,
                        paddingRight: 1,
                      }}
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
            );
          })}
        </div>
      </TimeGrid>
    </div>
  );
}
