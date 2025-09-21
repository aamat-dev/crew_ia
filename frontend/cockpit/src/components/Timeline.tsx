"use client";
import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { RunsTimeline, type Run as TimelineRun } from "@/components/timeline/RunsTimeline";
import { RunDrawer, type RunDrawerFallback } from "@/features/runs/RunDrawer";
import { fetchRuns, normalizeRunStatus } from "@/lib/api";
import type { Status } from "@/ui/theme";

const ALL_STATUSES: Status[] = ["queued", "running", "completed", "failed", "paused"];

type TimelineQueryKey = ["runs:timeline", { q: string; statuses: Status[] }];

export function Timeline() {
  const [q, setQ] = React.useState("");
  const [filters, setFilters] = React.useState<Record<Status, boolean>>({
    queued: true,
    running: true,
    completed: true,
    failed: true,
    paused: true,
  });
  const [selectedRunId, setSelectedRunId] = React.useState<string | null>(null);
  const [selectedRunMeta, setSelectedRunMeta] = React.useState<RunDrawerFallback | null>(null);

  const activeStatuses = React.useMemo(() => ALL_STATUSES.filter((status) => filters[status]), [filters]);

  const runsQuery = useQuery({
    queryKey: ["runs:timeline", { q, statuses: activeStatuses }] as TimelineQueryKey,
    queryFn: ({ signal }) => fetchRuns({ limit: 200, orderBy: "started_at", orderDir: "desc" }, { signal }),
    refetchInterval: 10_000,
    staleTime: 10_000,
  });

  const runs = React.useMemo<TimelineRun[]>(() => {
    const queryString = q.trim().toLowerCase();
    const items = runsQuery.data?.items ?? [];
    return items
      .map((run) => ({
        id: run.id,
        title: run.title || run.id,
        status: normalizeRunStatus(run.status),
        startedAt: run.started_at ?? undefined,
        endedAt: run.ended_at ?? undefined,
      }))
      .filter((run) => {
        if (!activeStatuses.includes(run.status)) return false;
        if (queryString) {
          const haystack = `${run.title} ${run.id}`.toLowerCase();
          if (!haystack.includes(queryString)) return false;
        }
        return true;
      });
  }, [runsQuery.data, activeStatuses, q]);

  const toggle = (status: Status) => {
    setFilters((current) => ({ ...current, [status]: !current[status] }));
  };

  const handleDetails = (id: string) => {
    const run = runs.find((item) => item.id === id);
    if (!run) return;
    setSelectedRunId(id);
    setSelectedRunMeta({
      id,
      title: run.title,
      status: run.status,
      startedAt: run.startedAt ?? null,
      endedAt: run.endedAt ?? null,
    });
  };

  return (
    <section aria-label="Historique des runs" className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <label className="sr-only" htmlFor="timeline-q">
          Rechercher un run
        </label>
        <input
          id="timeline-q"
          className="px-3 py-2 rounded-2xl border border-slate-700 bg-[#2A2D36] shadow-[inset_0_2px_6px_rgba(255,255,255,0.04)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--ring))] text-slate-100 placeholder:text-slate-400"
          placeholder="Rechercher (id, titre)"
          value={q}
          onChange={(event) => setQ(event.target.value)}
        />
        {ALL_STATUSES.map((status) => (
          <button
            key={status}
            type="button"
            onClick={() => toggle(status)}
            aria-pressed={filters[status]}
            className={`px-2 py-1 rounded-2xl border ${filters[status] ? "bg-indigo-600/20 text-slate-100 border-indigo-600/40" : "bg-[#2A2D36] border-slate-700 text-slate-300"}`}
          >
            {status}
          </button>
        ))}
        <button
          type="button"
          onClick={() => setFilters({ queued: true, running: true, completed: true, failed: true, paused: true })}
          className="px-2 py-1 rounded-2xl border border-slate-700 bg-[#2A2D36] text-slate-300"
        >
          Tous
        </button>
      </div>

      {runsQuery.isLoading ? (
        <div className="h-48 animate-pulse rounded bg-muted" role="status" aria-label="Chargement de la timeline" />
      ) : runsQuery.isError ? (
        <div role="alert" className="clay-card p-3">
          Erreur de chargement de la timeline
        </div>
      ) : runs.length === 0 ? (
        <div role="status" aria-live="polite" className="clay-card p-3">
          Aucun run
        </div>
      ) : (
        <RunsTimeline runs={runs} onRetry={undefined} onDetails={handleDetails} />
      )}

      <RunDrawer
        runId={selectedRunId}
        fallback={selectedRunMeta}
        open={Boolean(selectedRunId)}
        onClose={() => {
          setSelectedRunId(null);
          setSelectedRunMeta(null);
        }}
      />
    </section>
  );
}

export default Timeline;
