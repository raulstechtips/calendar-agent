import { Suspense } from "react";

import CalendarShell from "@/components/calendar/CalendarShell";
import { Skeleton } from "@/components/ui/skeleton";

export default function CalendarPage() {
  return (
    <Suspense fallback={<CalendarPageSkeleton />}>
      <CalendarShell />
    </Suspense>
  );
}

function CalendarPageSkeleton() {
  return (
    <div className="flex flex-1 flex-col gap-2 p-4">
      <div className="flex items-center justify-between">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-8 w-28" />
      </div>
      <Skeleton className="flex-1" />
    </div>
  );
}
