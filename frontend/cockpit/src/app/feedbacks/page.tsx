"use client";

import * as React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { FeedbackPanel } from "@/components/FeedbackPanel";
import { ClayCard } from "@/components/ds/ClayCard";
import { ClayButton } from "@/components/ds/ClayButton";

type Item = {
  id: string;
  title: string;
  criticity: "critical" | "major" | "minor";
  createdAt: string;
  runId?: string;
  sourceAnchor?: string;
  summary?: string;
};

export default function FeedbacksPage() {
  const qc = useQueryClient();
  const [selected, setSelected] = React.useState<Item | null>(null);
  const [open, setOpen] = React.useState(false);
  const [q, setQ] = React.useState("");
  const [filters, setFilters] = React.useState<{ critical: boolean; major: boolean; minor: boolean }>({
    critical: true,
    major: true,
    minor: true,
  });

  const query = useQuery({
    queryKey: ["feedbacks:list", { q, filters }],
    queryFn: async ({ queryKey }) => {
      const [, params] = queryKey as any;
      const url = new URL("/api/feedbacks-feed", window.location.origin);
      const active: string[] = [];
      for (const k of ["critical", "major", "minor"] as const) if (params.filters[k]) active.push(k);
      if (active.length) url.searchParams.set("criticity", active.join(","));
      if (params.q && params.q.trim()) url.searchParams.set("q", params.q.trim());
      const r = await fetch(url.toString());
      if (!r.ok) throw new Error(r.statusText);
      const j = (await r.json()) as { items: Item[] };
      return j.items;
    },
  });

  const resolve = useMutation({
    mutationFn: async (id: string) => {
      const r = await fetch(`/api/feedbacks/${id}/resolve`, { method: "POST" });
      if (!r.ok) throw new Error(r.statusText);
      return (await r.json()) as { ok: true };
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["feedbacks:list"] });
      setOpen(false);
    },
  });

  // Raccourci clavier: Ctrl/Cmd + Shift + C pour ouvrir le dernier feedback critique
  React.useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const isEditable = (el: any) => el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.isContentEditable);
      if (isEditable(e.target)) return;
      const key = e.key.toLowerCase();
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && key === 'c') {
        e.preventDefault();
        const data = query.data || [];
        const critical = data.filter((i) => i.criticity === 'critical');
        if (critical.length > 0) {
          setSelected(critical[0]);
          setOpen(true);
        }
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [query.data]);

  return (
    <main className="p-6 space-y-4">
      <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">Feedbacks</h1>

      <div className="flex flex-wrap items-center gap-2" role="region" aria-label="Filtres des feedbacks">
        <label htmlFor="feedback-q" className="sr-only">Rechercher un feedback</label>
        <input
          id="feedback-q"
          className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-slate-900 shadow-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-focus"
          placeholder="Rechercher (id, titre, résumé)"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        {(["critical", "major", "minor"] as const).map((c) => (
          <button
            key={c}
            type="button"
            onClick={() => setFilters((f) => ({ ...f, [c]: !f[c] }))}
            aria-pressed={filters[c]}
            className={`px-2 py-1 rounded border ${filters[c] ? (c === "critical" ? "bg-destructive text-destructive-foreground" : c === "major" ? "bg-warning text-warning-foreground" : "bg-muted") : "bg-background"}`}
          >
            {c}
          </button>
        ))}
        <ClayButton type="button" size="sm" onClick={() => setFilters({ critical: true, major: true, minor: true })}>Tous</ClayButton>
      </div>

      {query.isLoading ? (
        <div className="h-24 animate-pulse rounded bg-muted" role="status" aria-label="Chargement des feedbacks" />
      ) : query.isError ? (
        <ClayCard role="alert" className="p-3">Erreur de chargement</ClayCard>
      ) : query.data && query.data.length === 0 ? (
        <ClayCard role="status" aria-live="polite" className="p-3">Aucun feedback</ClayCard>
      ) : (
        <ul role="list" className="space-y-2">
          {query.data?.map((f) => (
            <ClayCard as="li" key={f.id} className="p-3 flex items-center justify-between">
              <div>
                <p className="font-medium">{f.title}</p>
                <p className="text-sm text-muted-foreground">{new Date(f.createdAt).toLocaleString()}</p>
              </div>
              <div className="flex items-center gap-2">
                {f.resolved && (
                  <span className="inline-flex items-center rounded bg-muted px-2 py-0.5 text-xs">Résolu</span>
                )}
                <ClayButton size="sm"
                  onClick={() => {
                    setSelected(f);
                    setOpen(true);
                  }}
                  aria-expanded={open}
                  aria-controls="feedback-panel"
                >
                  Ouvrir
                </ClayButton>
              </div>
            </ClayCard>
          ))}
        </ul>
      )}

      <div id="feedback-panel">
        <FeedbackPanel
          open={open}
          onOpenChange={setOpen}
          item={selected as any}
          resolving={resolve.isPending}
          onResolve={(id) => resolve.mutate(id)}
        />
      </div>
    </main>
  );
}
