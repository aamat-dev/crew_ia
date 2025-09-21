"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { FeedbackPanel, type FeedbackItem, type Criticity } from "@/components/FeedbackPanel";
import { ClayCard } from "@/components/ds/ClayCard";
import { ClayButton } from "@/components/ds/ClayButton";
import { fetchFeedbacks } from "@/lib/api";

function classify(score?: number | null): Criticity {
  if (typeof score !== "number") return "major";
  if (score <= 40) return "critical";
  if (score <= 70) return "major";
  return "minor";
}

function toFeedbackItem(entry: Awaited<ReturnType<typeof fetchFeedbacks>>["items"][number]): FeedbackItem {
  return {
    id: entry.id,
    criticity: classify(entry.score),
    createdAt: entry.created_at ?? undefined,
    runId: entry.run_id,
    nodeId: entry.node_id ?? undefined,
    score: entry.score ?? undefined,
    comment: entry.comment ?? undefined,
    source: entry.source ?? undefined,
  };
}

type FeedbackFilters = { critical: boolean; major: boolean; minor: boolean };
type FeedbacksQueryKey = ["feedbacks:list", { q: string; filters: FeedbackFilters }];

export default function FeedbacksPage() {
  const [selected, setSelected] = React.useState<FeedbackItem | null>(null);
  const [open, setOpen] = React.useState(false);
  const [q, setQ] = React.useState("");
  const [filters, setFilters] = React.useState<FeedbackFilters>({
    critical: true,
    major: true,
    minor: true,
  });

  const query = useQuery<FeedbackItem[], Error, FeedbackItem[], FeedbacksQueryKey>({
    queryKey: ["feedbacks:list", { q, filters }] as FeedbacksQueryKey,
    queryFn: async ({ queryKey, signal }) => {
      const [, params] = queryKey;
      const data = await fetchFeedbacks({ limit: 200, orderBy: "created_at", orderDir: "desc" }, { signal });
      const active = (Object.keys(params.filters) as Array<keyof FeedbackFilters>)
        .filter((key) => params.filters[key]);
      const lowerQ = params.q.trim().toLowerCase();
      return data.items
        .map(toFeedbackItem)
        .filter((item) => {
          if (active.length && !active.includes(item.criticity)) return false;
          if (!lowerQ) return true;
          const haystack = `${item.id} ${item.comment ?? ""} ${item.runId ?? ""}`.toLowerCase();
          return haystack.includes(lowerQ);
        });
    },
  });

  // Raccourci clavier: Ctrl/Cmd + Shift + C pour ouvrir le dernier feedback critique
  React.useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const isEditable = (element: EventTarget | null): element is HTMLElement => {
        return (
          element instanceof HTMLElement &&
          (element.tagName === "INPUT" || element.tagName === "TEXTAREA" || element.isContentEditable)
        );
      };
      if (isEditable(event.target)) return;
      const key = event.key.toLowerCase();
      if ((event.ctrlKey || event.metaKey) && event.shiftKey && key === "c") {
        event.preventDefault();
        const data = query.data || [];
        const critical = data.find((i) => i.criticity === "critical");
        if (critical) {
          setSelected(critical);
          setOpen(true);
        }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [query.data]);

  return (
    <main className="p-6 space-y-4">
      <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">Feedbacks</h1>

      <div className="flex flex-wrap items-center gap-2" role="region" aria-label="Filtres des feedbacks">
        <label htmlFor="feedback-q" className="sr-only">
          Rechercher un feedback
        </label>
        <input
          id="feedback-q"
          className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-slate-900 shadow-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-focus"
          placeholder="Rechercher (id, commentaire, run)"
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
        <ClayButton type="button" size="sm" onClick={() => setFilters({ critical: true, major: true, minor: true })}>
          Tous
        </ClayButton>
      </div>

      {query.isLoading ? (
        <div className="h-24 animate-pulse rounded bg-muted" role="status" aria-label="Chargement des feedbacks" />
      ) : query.isError ? (
        <ClayCard role="alert" className="p-3">
          Erreur de chargement
        </ClayCard>
      ) : query.data && query.data.length === 0 ? (
        <ClayCard role="status" aria-live="polite" className="p-3">
          Aucun feedback
        </ClayCard>
      ) : (
        <ul role="list" className="space-y-2">
          {query.data?.map((f) => (
            <ClayCard as="li" key={f.id} className="p-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">{f.comment || f.id}</p>
                  <p className="text-sm text-muted-foreground">{f.createdAt ? new Date(f.createdAt).toLocaleString() : "Date inconnue"}</p>
                </div>
                <div className="flex items-center gap-2">
                  <ClayButton
                    size="sm"
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
              </div>
            </ClayCard>
          ))}
        </ul>
      )}

      <div id="feedback-panel">
        <FeedbackPanel open={open} onOpenChange={setOpen} item={selected} />
      </div>
    </main>
  );
}
