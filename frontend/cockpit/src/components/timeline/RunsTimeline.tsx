"use client";
import * as React from "react";
import { useVirtualizer } from "@tanstack/react-virtual";
import { TimelineItem } from "@/components/ui/TimelineItem";

export type Run = {
  id: string;
  title: string;
  status: "queued" | "running" | "completed" | "failed" | "paused";
  startedAt?: string;
  endedAt?: string;
};

interface RunsTimelineProps {
  runs: Run[];
  onDetails?: (id: string) => void;
  onRetry?: (id: string) => void;
}

export function RunsTimeline({ runs, onDetails, onRetry }: RunsTimelineProps) {
  const parentRef = React.useRef<HTMLDivElement>(null);
  const rowVirtualizer = useVirtualizer({
    count: runs.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 96,
    overscan: 5,
  });

  const formatDate = (iso?: string) =>
    iso ? new Date(iso).toLocaleString() : "N/A";

  return (
    <div ref={parentRef} className="h-[60vh] overflow-auto md:h-96" role="list" aria-label="Historique des exécutions">
      <div
        style={{
          height: `${rowVirtualizer.getTotalSize()}px`,
          position: "relative",
        }}
      >
        {rowVirtualizer.getVirtualItems().map((virtualRow) => {
          const run = runs[virtualRow.index];
          const canRetry = (run.status === "failed" || run.status === "completed") && Boolean(onRetry);

          return (
            <div
              key={run.id}
              data-index={virtualRow.index}
              ref={rowVirtualizer.measureElement}
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                width: "100%",
                transform: `translateY(${virtualRow.start}px)`,
              }}
              className="my-2"
              role="listitem"
              tabIndex={0}
            >
              <TimelineItem
                title={run.title}
                date={`Début: ${formatDate(run.startedAt)} – Fin: ${formatDate(run.endedAt)}`}
                status={run.status}
                onRetry={canRetry ? () => onRetry?.(run.id) : undefined}
                onDetails={onDetails ? () => onDetails(run.id) : undefined}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}
