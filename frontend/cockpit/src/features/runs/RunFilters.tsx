"use client";

import * as React from "react";
import { Search } from "lucide-react";
import { Status, baseFocusRing } from "@/ui/theme";
import { cn } from "@/lib/utils";

export interface DateRange {
  from?: string;
  to?: string;
}

export interface RunFiltersProps {
  selectedStatuses: Status[];
  onStatusesChange: (statuses: Status[]) => void;
  query: string;
  onQueryChange: (value: string) => void;
  dateRange: DateRange;
  onDateRangeChange: (range: DateRange) => void;
}

const ALL_STATUSES: Status[] = ["running", "completed", "queued", "failed"];

export function RunFilters({ selectedStatuses, onStatusesChange, query, onQueryChange, dateRange, onDateRangeChange }: RunFiltersProps) {
  const toggleStatus = (status: Status) => {
    if (selectedStatuses.includes(status)) {
      onStatusesChange(selectedStatuses.filter((value) => value !== status));
    } else {
      onStatusesChange([...selectedStatuses, status]);
    }
  };

  const handleDateChange = (field: keyof DateRange, value: string) => {
    onDateRangeChange({ ...dateRange, [field]: value || undefined });
  };

  return (
    <section className="surface shadow-card p-4 space-y-3" aria-label="Filtres des runs">
      <div className="flex flex-wrap items-center gap-3">
        <label className="flex flex-1 min-w-[200px] items-center gap-2 surface-muted rounded-xl px-3 py-2" aria-label="Rechercher un run">
          <Search className="h-4 w-4 text-secondary" aria-hidden />
          <input
            type="search"
            value={query}
            onChange={(event) => onQueryChange(event.target.value)}
            placeholder="Nom, ID ou agent"
            className="w-full bg-transparent text-sm text-[color:var(--text)] placeholder:text-secondary focus:outline-none"
          />
        </label>
        <div className="flex items-center gap-2">
          <label className="text-xs uppercase tracking-wide text-secondary" htmlFor="runs-from">
            Du
          </label>
          <input
            id="runs-from"
            type="date"
            value={dateRange.from ?? ""}
            onChange={(event) => handleDateChange("from", event.target.value)}
            className={cn(
              "rounded-xl border border-slate-700 bg-transparent px-3 py-2 text-sm text-[color:var(--text)]",
              baseFocusRing
            )}
          />
          <label className="text-xs uppercase tracking-wide text-secondary" htmlFor="runs-to">
            Au
          </label>
          <input
            id="runs-to"
            type="date"
            value={dateRange.to ?? ""}
            onChange={(event) => handleDateChange("to", event.target.value)}
            className={cn(
              "rounded-xl border border-slate-700 bg-transparent px-3 py-2 text-sm text-[color:var(--text)]",
              baseFocusRing
            )}
          />
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        {ALL_STATUSES.map((status) => {
          const active = selectedStatuses.includes(status);
          return (
            <button
              key={status}
              type="button"
              onClick={() => toggleStatus(status)}
              className={cn(
                "rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide transition",
                baseFocusRing,
                active
                  ? "bg-indigo-500/20 text-[color:var(--text)] border border-indigo-500/40"
                  : "border border-slate-700 text-secondary"
              )}
            >
              {status}
            </button>
          );
        })}
        <button
          type="button"
          onClick={() => onStatusesChange(ALL_STATUSES)}
          className={cn(
            "rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide border border-slate-700 text-secondary",
            baseFocusRing
          )}
        >
          Tous
        </button>
      </div>
    </section>
  );
}

export default RunFilters;
