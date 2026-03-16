import { Skeleton } from "@/components/ui/skeleton";

export default function CalendarSkeleton() {
  return (
    <div className="flex flex-1 flex-col gap-2 p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Skeleton className="h-8 w-16" />
          <Skeleton className="h-8 w-8" />
          <Skeleton className="h-8 w-8" />
          <Skeleton className="h-5 w-40" />
        </div>
        <Skeleton className="h-8 w-28" />
      </div>
      <div className="flex flex-1 gap-2">
        <div className="flex w-16 flex-col gap-4 pt-2">
          {Array.from({ length: 8 }, (_, i) => (
            <Skeleton key={i} className="h-3 w-10" />
          ))}
        </div>
        <div className="flex-1 space-y-4">
          {Array.from({ length: 4 }, (_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      </div>
    </div>
  );
}
