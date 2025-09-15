"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { resolveApiUrl, defaultApiHeaders } from "@/lib/config";
import { fetchJson } from "@/lib/fetchJson";
import { StatusBadge } from "@/components/ds/StatusBadge";
import { ClayCard } from "@/components/ds/ClayCard";
import { ClayButton } from "@/components/ds/ClayButton";

interface RunSummary {
  nodes_total: number;
  nodes_completed: number;
  nodes_failed: number;
  artifacts_total: number;
  events_total: number;
  duration_ms?: number | null;
}

interface RunOut {
  id: string;
  title: string;
  status: string;
  started_at?: string | null;
  ended_at?: string | null;
  summary?: RunSummary | null;
}

export default function RunDetailsPage() {
  const params = useParams<{ id: string }>();
  const runId = params?.id;

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery<RunOut>({
    queryKey: ["run", runId],
    enabled: !!runId,
    queryFn: ({ signal }) =>
      fetchJson<RunOut>(resolveApiUrl(`/runs/${runId}`), {
        signal,
        headers: defaultApiHeaders(),
      }),
  });

  return (
    <main className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">Run</h1>
        <div className="flex items-center gap-2">
          <Link href="/runs" className="inline-flex items-center rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 shadow-sm transition hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-focus">
            Tous les runs
          </Link>
          <ClayButton type="button" onClick={() => refetch()} disabled={isFetching} aria-busy={isFetching}>
            Rafraîchir
          </ClayButton>
        </div>
      </div>

      {isLoading && <p role="status" aria-live="polite">Chargement…</p>}
      {isError && (
        <ClayCard role="alert" className="p-4">
          <p className="font-medium">Erreur lors du chargement du run</p>
          <p className="text-sm opacity-80">{(error as Error)?.message || "API indisponible"}</p>
        </ClayCard>
      )}

      {data && (
        <ClayCard className="space-y-2 p-4">
          <h2 className="text-lg font-medium">{data.title || data.id}</h2>
          <div className="opacity-80 flex items-center gap-2">
            <span>Statut:</span>
            <StatusBadge status={data.status} />
            {data.started_at ? (
              <span className="text-sm">• démarré le {new Date(data.started_at).toLocaleString()}</span>
            ) : null}
          </div>
          {data.summary && (
            <ul className="grid grid-cols-2 md:grid-cols-3 gap-2 text-sm">
              <li className="clay-card rounded-2xl p-2">Nœuds: {data.summary.nodes_total}</li>
              <li className="clay-card rounded-2xl p-2">Terminés: {data.summary.nodes_completed}</li>
              <li className="clay-card rounded-2xl p-2">Échecs: {data.summary.nodes_failed}</li>
              <li className="clay-card rounded-2xl p-2">Artifacts: {data.summary.artifacts_total}</li>
              <li className="clay-card rounded-2xl p-2">Événements: {data.summary.events_total}</li>
              {typeof data.summary.duration_ms === "number" && (
                <li className="clay-card rounded-2xl p-2">Durée: {Math.round(data.summary.duration_ms / 1000)}s</li>
              )}
            </ul>
          )}
        </ClayCard>
      )}
    </main>
  );
}
