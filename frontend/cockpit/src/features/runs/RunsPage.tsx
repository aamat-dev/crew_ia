"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { HeaderBar } from "@/ui/HeaderBar";
import { TimelineItem } from "@/ui/TimelineItem";
import { NoticeCard } from "@/ui/NoticeCard";
import { RunDrawer } from "@/features/runs/RunDrawer";
import { RunFilters, type DateRange } from "@/features/runs/RunFilters";
import { fetchRuns, normalizeRunStatus, type RunListItem } from "@/lib/api";
import type { Status } from "@/ui/theme";

const PAGE_SIZE = 10;
const DEFAULT_STATUSES: Status[] = ["running", "completed", "queued", "failed", "paused"];

interface UiRun {
  id: string;
  title: string;
  status: Status;
  startedAt?: string | null;
  endedAt?: string | null;
}

function formatDateTime(value?: string | null): string {
  if (!value) return "Date inconnue";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

export function RunsPage() {
  const [selectedStatuses, setSelectedStatuses] = React.useState<Status[]>(DEFAULT_STATUSES);
  const [query, setQuery] = React.useState("");
  const [dateRange, setDateRange] = React.useState<DateRange>({});
  const [page, setPage] = React.useState(1);
  const [selectedRunId, setSelectedRunId] = React.useState<string | null>(null);
  const [selectedRunMeta, setSelectedRunMeta] = React.useState<UiRun | null>(null);

  const runsQuery = useQuery({
    queryKey: ["runs", { limit: 200 }],
    queryFn: ({ signal }) => fetchRuns({ limit: 200, orderBy: "started_at", orderDir: "desc" }, { signal }),
    refetchInterval: 30_000,
    staleTime: 30_000,
  });

  const runs = React.useMemo<UiRun[]>(() => {
    const items = runsQuery.data?.items ?? [];
    return items.map((run: RunListItem) => ({
      id: run.id,
      title: run.title || run.id,
      status: normalizeRunStatus(run.status),
      startedAt: run.started_at ?? null,
      endedAt: run.ended_at ?? null,
    }));
  }, [runsQuery.data]);

  const filteredRuns = React.useMemo(() => {
    const q = query.trim().toLowerCase();
    const fromTimestamp = dateRange.from ? new Date(`${dateRange.from}T00:00:00Z`).getTime() : null;
    const toTimestamp = dateRange.to ? new Date(`${dateRange.to}T23:59:59Z`).getTime() : null;

    return runs.filter((run) => {
      if (!selectedStatuses.includes(run.status)) return false;

      if (q) {
        const haystack = `${run.title} ${run.id}`.toLowerCase();
        if (!haystack.includes(q)) return false;
      }

      if (fromTimestamp && run.startedAt) {
        if (new Date(run.startedAt).getTime() < fromTimestamp) return false;
      }

      if (toTimestamp && run.startedAt) {
        if (new Date(run.startedAt).getTime() > toTimestamp) return false;
      }

      return true;
    });
  }, [runs, selectedStatuses, query, dateRange]);

  const visibleRuns = React.useMemo(() => filteredRuns.slice(0, page * PAGE_SIZE), [filteredRuns, page]);
  const hasMore = visibleRuns.length < filteredRuns.length;

  const skeletons = React.useMemo(
    () =>
      Array.from({ length: 3 }).map((_, index) => (
        <div key={`skeleton-${index}`} className="surface shadow-card p-4 animate-pulse">
          <div className="h-5 w-48 rounded bg-slate-700/40" />
          <div className="mt-3 h-4 w-32 rounded bg-slate-700/30" />
        </div>
      )),
    []
  );

  const handleOpenDetails = (run: UiRun) => {
    setSelectedRunId(run.id);
    setSelectedRunMeta(run);
  };

  return (
    <div className="space-y-6">
      <HeaderBar title="Runs" breadcrumb="Pilotage & historique" />
      <RunFilters
        selectedStatuses={selectedStatuses}
        onStatusesChange={(value) => {
          setPage(1);
          setSelectedStatuses(value);
        }}
        query={query}
        onQueryChange={(value) => {
          setPage(1);
          setQuery(value);
        }}
        dateRange={dateRange}
        onDateRangeChange={(value) => {
          setPage(1);
          setDateRange(value);
        }}
      />
      <section className="space-y-3" aria-label="Liste des runs">
        {runsQuery.isLoading ? (
          skeletons
        ) : runsQuery.isError ? (
          <NoticeCard
            type="error"
            title="Erreur de chargement"
            message="Impossible de récupérer l'historique des runs depuis l'API."
          />
        ) : visibleRuns.length === 0 ? (
          <NoticeCard
            type="warning"
            message="Aucun run ne correspond à ces filtres. Ajustez la recherche pour visualiser l'historique."
          />
        ) : (
          visibleRuns.map((run) => (
            <TimelineItem
              key={run.id}
              title={run.title}
              date={formatDateTime(run.startedAt)}
              status={run.status}
              onRetry={undefined}
              onDetails={() => handleOpenDetails(run)}
            />
          ))
        )}
        {hasMore && !runsQuery.isLoading ? (
          <div className="flex justify-center pt-2">
            <button
              type="button"
              onClick={() => setPage((value) => value + 1)}
              className="rounded-full bg-[var(--accent-cyan-500)] px-4 py-2 text-sm font-medium text-white shadow-card transition hover:shadow-lg"
            >
              Charger plus
            </button>
          </div>
        ) : null}
      </section>
      <RunDrawer
        runId={selectedRunId}
        fallback={selectedRunMeta}
        open={Boolean(selectedRunId)}
        onClose={() => {
          setSelectedRunId(null);
          setSelectedRunMeta(null);
        }}
      />
    </div>
  );
}

export default RunsPage;
