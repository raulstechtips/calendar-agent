"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback } from "react";

import {
  formatDateLabel,
  formatISODate,
  parseDate,
  type CalendarViewType,
} from "@/lib/calendar";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";

interface CalendarToolbarProps {
  view: CalendarViewType;
  currentDate: string;
}

export default function CalendarToolbar({
  view,
  currentDate,
}: CalendarToolbarProps) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const updateParams = useCallback(
    (updates: Record<string, string>) => {
      const params = new URLSearchParams(searchParams.toString());
      for (const [key, value] of Object.entries(updates)) {
        params.set(key, value);
      }
      router.push(`/calendar?${params.toString()}`);
    },
    [router, searchParams],
  );

  const navigateDate = useCallback(
    (direction: number) => {
      const date = parseDate(currentDate);
      const days = view === "week" ? 7 * direction : direction;
      const newDate = new Date(date);
      newDate.setDate(newDate.getDate() + days);
      updateParams({ date: formatISODate(newDate) });
    },
    [currentDate, view, updateParams],
  );

  const goToToday = useCallback(() => {
    updateParams({ date: formatISODate(new Date()) });
  }, [updateParams]);

  const date = parseDate(currentDate);
  const label = formatDateLabel(date, view);
  const viewLabel = view === "week" ? "week" : "day";

  return (
    <div className="flex items-center justify-between border-b border-border/60 px-5 py-3">
      <div className="flex items-center gap-3">
        <Button variant="outline" size="sm" className="font-medium shadow-sm" onClick={goToToday}>
          Today
        </Button>
        <div className="flex items-center gap-0.5">
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={() => navigateDate(-1)}
            aria-label={`Previous ${viewLabel}`}
          >
            <ChevronLeft />
          </Button>
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={() => navigateDate(1)}
            aria-label={`Next ${viewLabel}`}
          >
            <ChevronRight />
          </Button>
        </div>
        <h2 className="text-lg font-semibold tracking-tight">{label}</h2>
      </div>
      <Tabs
        value={view}
        onValueChange={(value) => updateParams({ view: value as string })}
      >
        <TabsList>
          <TabsTrigger value="day">Day</TabsTrigger>
          <TabsTrigger value="week">Week</TabsTrigger>
        </TabsList>
      </Tabs>
    </div>
  );
}
