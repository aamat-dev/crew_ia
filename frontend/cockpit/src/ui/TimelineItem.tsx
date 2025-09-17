"use client";

import * as React from "react";
import { RefreshCcw, Info } from "lucide-react";
import { Status, statusGradient, baseFocusRing } from "@/ui/theme";
import { StatusBadge } from "@/ui/StatusBadge";
import { cn } from "@/lib/utils";

export interface TimelineItemProps {
  title: string;
  date: string;
  status: Status;
  onRetry?: () => void;
  onDetails?: () => void;
  description?: string;
}

export function TimelineItem({ title, date, status, onRetry, onDetails, description }: TimelineItemProps) {
  return (
    <article className="surface shadow-card p-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between hover:shadow-md transition">
      <div className="flex flex-1 items-start gap-4">
        <span
          aria-hidden
          className={cn(
            "grid h-10 w-10 shrink-0 place-content-center rounded-xl text-white bg-gradient-to-br",
            statusGradient(status)
          )}
        />
        <div className="space-y-1">
          <h3 className="text-base font-semibold text-[color:var(--text)]">{title}</h3>
          <p className="text-sm text-secondary">{date}</p>
          {description ? <p className="text-xs text-secondary">{description}</p> : null}
        </div>
      </div>
      <div className="flex items-center gap-3">
        <StatusBadge status={status} />
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onRetry}
            disabled={!onRetry}
            className={cn(
              "h-9 w-9 rounded-full surface shadow-card grid place-content-center text-[color:var(--text)] transition",
              baseFocusRing,
              !onRetry && "opacity-40 cursor-not-allowed"
            )}
            aria-label="Relancer le run"
          >
            <RefreshCcw className="h-4 w-4" aria-hidden />
          </button>
          <button
            type="button"
            onClick={onDetails}
            disabled={!onDetails}
            className={cn(
              "h-9 w-9 rounded-full surface shadow-card grid place-content-center text-[color:var(--text)] transition",
              baseFocusRing,
              !onDetails && "opacity-40 cursor-not-allowed"
            )}
            aria-label="Voir les détails"
          >
            <Info className="h-4 w-4" aria-hidden />
          </button>
        </div>
      </div>
    </article>
  );
}

export default TimelineItem;
