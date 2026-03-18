"use client";

import { useEffect, useRef, useState } from "react";

import { cn } from "@/lib/utils";
import { ScrollArea } from "@/components/ui/scroll-area";

const HOUR_HEIGHT = 64;
const HOURS = Array.from({ length: 24 }, (_, i) => i);
const WORKING_HOUR_START = 9;
const WORKING_HOUR_END = 17; // 5 PM (exclusive — hours 9-16 get the tint)

interface TimeGridProps {
  children: React.ReactNode;
  columns: number;
}

export { HOUR_HEIGHT };

export default function TimeGrid({ children, columns }: TimeGridProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to current hour on mount
  useEffect(() => {
    const now = new Date();
    const scrollTop = Math.max(0, (now.getHours() - 1) * HOUR_HEIGHT);
    // ScrollArea puts the viewport as a child div
    const viewport = scrollRef.current?.querySelector(
      "[data-slot='scroll-area-viewport']",
    );
    if (viewport) {
      viewport.scrollTop = scrollTop;
    }
  }, []);

  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const id = window.setInterval(() => setNow(new Date()), 60_000);
    return () => window.clearInterval(id);
  }, []);
  const currentMinutes = now.getHours() * 60 + now.getMinutes();
  const currentTimeTop = (currentMinutes / 60) * HOUR_HEIGHT;

  return (
    <ScrollArea ref={scrollRef} className="flex-1">
      <div className="relative flex" style={{ minHeight: 24 * HOUR_HEIGHT }}>
        {/* Time labels column */}
        <div className="sticky left-0 z-10 w-16 shrink-0 border-r border-border/50 bg-background">
          {HOURS.map((hour) => (
            <div
              key={hour}
              className={cn(
                "relative border-b border-border/40 text-right text-[11px] text-muted-foreground",
                hour >= WORKING_HOUR_START &&
                  hour < WORKING_HOUR_END &&
                  "bg-primary/[0.03]",
              )}
              style={{ height: HOUR_HEIGHT }}
            >
              <span className="absolute -top-2 right-2 font-medium">
                {formatHourLabel(hour)}
              </span>
            </div>
          ))}
        </div>

        {/* Grid area */}
        <div className="relative flex-1">
          {/* Hour rows with working hours band */}
          {HOURS.map((hour) => (
            <div
              key={hour}
              className={cn(
                "relative border-b border-border/40",
                hour >= WORKING_HOUR_START &&
                  hour < WORKING_HOUR_END &&
                  "bg-primary/[0.03]",
              )}
              style={{ height: HOUR_HEIGHT }}
            >
              {/* Half-hour dashed line */}
              <div className="absolute left-0 right-0 top-1/2 border-t border-dashed border-border/25" />
            </div>
          ))}

          {/* Column dividers for week view */}
          {columns > 1 && (
            <div
              className="pointer-events-none absolute inset-0 grid"
              style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}
            >
              {Array.from({ length: columns }, (_, i) => (
                <div
                  key={i}
                  className={cn("h-full", i > 0 && "border-l border-border/50")}
                />
              ))}
            </div>
          )}

          {/* Current time indicator */}
          <div
            className="pointer-events-none absolute left-0 right-0 z-20 flex items-center"
            style={{ top: currentTimeTop }}
          >
            <div className="size-2.5 rounded-full bg-destructive shadow-sm shadow-destructive/50" />
            <div className="h-0.5 flex-1 bg-destructive shadow-sm shadow-destructive/50" />
          </div>

          {/* Events overlay */}
          {children}
        </div>
      </div>
    </ScrollArea>
  );
}

function formatHourLabel(hour: number): string {
  if (hour === 0) return "12 AM";
  if (hour === 12) return "12 PM";
  if (hour < 12) return `${hour} AM`;
  return `${hour - 12} PM`;
}
