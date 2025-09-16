"use client";
import * as React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useToast } from "@/components/ds/Toast";
import { RunsTimeline, Run } from "@/components/timeline/RunsTimeline";

type Status = Run["status"];

const ALL: Status[] = ["queued", "running", "completed", "failed", "paused"];

export function Timeline() {
  const qc = useQueryClient();
  const toast = useToast();
  const [q, setQ] = React.useState("");
  const [filters, setFilters] = React.useState<Record<Status, boolean>>({
    queued: true,
    running: true,
    completed: true,
    failed: true,
    paused: true,
  });

  const activeStatuses = ALL.filter((s) => filters[s]);

  const query = useQuery({
    queryKey: ["runs:timeline", { q, status: activeStatuses }],
    queryFn: async ({ queryKey }) => {
      const [, params] = queryKey as any;
      const s = (params.status as Status[]).join(",");
      const url = new URL(`/api/runs-feed`, window.location.origin);
      if (q.trim()) url.searchParams.set("q", q.trim());
      if (s) url.searchParams.set("status", s);
      const r = await fetch(url.toString());
      if (!r.ok) throw new Error(r.statusText);
      const data = (await r.json()) as { items: Run[] };
      return data.items;
    },
    refetchInterval: 10_000,
  });

  const pause = useMutation({
    mutationFn: async (id: string) => {
      const r = await fetch(`/api/runs/${id}/pause`, { method: "POST" });
      if (!r.ok) throw new Error(r.statusText);
      return (await r.json()) as { ok: true };
    },
    onSuccess: () => {
      toast("Run mis en pause");
      qc.invalidateQueries({ queryKey: ["runs:timeline"] });
    },
    onError: (e) => toast((e as Error).message || "Échec mise en pause", "error"),
  });

  const resume = useMutation({
    mutationFn: async (id: string) => {
      const r = await fetch(`/api/runs/${id}/resume`, { method: "POST" });
      if (!r.ok) throw new Error(r.statusText);
      return (await r.json()) as { ok: true };
    },
    onSuccess: () => {
      toast("Run repris");
      qc.invalidateQueries({ queryKey: ["runs:timeline"] });
    },
    onError: (e) => toast((e as Error).message || "Échec reprise", "error"),
  });

  const toggle = (s: Status) => setFilters((f) => ({ ...f, [s]: !f[s] }));

  return (
    <section aria-label="Historique des runs" className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        {/* Recherche */}
        <label className="sr-only" htmlFor="timeline-q">Rechercher un run</label>
        <input
          id="timeline-q"
          className="px-3 py-2 rounded-2xl border border-slate-700 bg-[#2A2D36] shadow-[inset_0_2px_6px_rgba(255,255,255,0.04)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--ring))] text-slate-100 placeholder:text-slate-400"
          placeholder="Rechercher (id, titre)"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        {/* Filtres par état */}
        {ALL.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => toggle(s)}
            aria-pressed={filters[s]}
            className={`px-2 py-1 rounded-2xl border ${filters[s] ? "bg-indigo-600/20 text-slate-100 border-indigo-600/40" : "bg-[#2A2D36] border-slate-700 text-slate-300"}`}
          >
            {s}
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

      {query.isLoading ? (
        <div className="h-48 animate-pulse rounded bg-muted" role="status" aria-label="Chargement de la timeline" />
      ) : query.isError ? (
        <div role="alert" className="clay-card p-3">Erreur de chargement de la timeline</div>
      ) : query.data && query.data.length === 0 ? (
        <div role="status" aria-live="polite" className="clay-card p-3">Aucun run</div>
      ) : (
        <RunsTimeline
          runs={query.data || []}
          onPause={(id) => pause.mutate(id)}
          onResume={(id) => resume.mutate(id)}
          onCancel={() => {}}
          onRetry={() => {}}
        />
      )}
    </section>
  );
}

export default Timeline;
