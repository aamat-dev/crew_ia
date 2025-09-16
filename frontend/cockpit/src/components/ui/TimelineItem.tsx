"use client";
import * as React from "react";
import { Info, RotateCw } from "lucide-react";
import StatusBadge from "@/components/ui/StatusBadge";
import { cn } from "@/lib/utils";

type Status = 'completed'|'running'|'queued'|'failed'|'paused';

export interface TimelineItemProps {
  title: string;
  date: string;
  status: Status;
  onRetry?: () => void;
  onDetails?: () => void;
}

const STATUS_ACCENT: Record<Status, string> = {
  completed: "from-emerald-500 to-emerald-400",
  running: "from-indigo-500 to-indigo-400",
  queued: "from-amber-500 to-amber-400",
  failed: "from-rose-500 to-rose-400",
  paused: "from-slate-500 to-slate-400",
};

export function TimelineItem({ title, date, status, onRetry, onDetails }: TimelineItemProps) {
  return (
    <div className={cn("clay-card p-4", "relative overflow-hidden")}
      role="listitem" tabIndex={0}
    >
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className={cn("grid h-10 w-10 place-content-center rounded-xl text-white bg-gradient-to-br", STATUS_ACCENT[status])} aria-hidden>
            <span className="h-3 w-3 rounded-full bg-white/90" />
          </span>
          <div className="flex flex-col">
            <span className="font-medium text-slate-100">{title}</span>
            <span className="text-sm text-slate-400">{date}</span>
          </div>
        </div>
        <StatusBadge status={status} />
      </div>
      <div className="mt-3 flex gap-2">
        {onRetry && (
          <button onClick={onRetry} className="rounded-xl border border-slate-700 bg-[#2A2D36] p-2 text-slate-200 hover:bg-indigo-600/15 focus:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--ring))]">
            <RotateCw className="h-4 w-4" />
            <span className="sr-only">Relancer</span>
          </button>
        )}
        {onDetails && (
          <button onClick={onDetails} className="rounded-xl border border-slate-700 bg-[#2A2D36] p-2 text-slate-200 hover:bg-indigo-600/15 focus:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--ring))]">
            <Info className="h-4 w-4" />
            <span className="sr-only">Détails</span>
          </button>
        )}
      </div>
    </div>
  );
}

export default TimelineItem;

