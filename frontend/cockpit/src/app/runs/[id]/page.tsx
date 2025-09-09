"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { resolveApiUrl, defaultApiHeaders } from "@/lib/config";
import { fetchJson } from "@/lib/fetchJson";

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
        <h1 className="text-2xl font-semibold">Run</h1>
        <div className="flex items-center gap-2">
          <Link
            href="/runs"
            className="glass px-3 py-1 rounded-md border focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            Tous les runs
          </Link>
          <button
            type="button"
            onClick={() => refetch()}
            disabled={isFetching}
            aria-busy={isFetching}
            className="glass px-3 py-1 rounded-md border focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            Rafraîchir
          </button>
        </div>
      </div>

      {isLoading && <p role="status" aria-live="polite">Chargement…</p>}
      {isError && (
        <div role="alert" className="glass p-4 rounded-md border">
          <p className="font-medium">Erreur lors du chargement du run</p>
          <p className="text-sm opacity-80">{(error as Error)?.message || "API indisponible"}</p>
        </div>
      )}

      {data && (
        <section className="space-y-2 glass p-4 rounded-md border">
          <h2 className="text-lg font-medium">{data.title || data.id}</h2>
          <p className="opacity-80">
            Statut: {data.status}
            {data.started_at ? ` • démarré le ${new Date(data.started_at).toLocaleString()}` : ""}
          </p>
          {data.summary && (
            <ul className="grid grid-cols-2 md:grid-cols-3 gap-2 text-sm">
              <li className="glass rounded p-2">Nœuds: {data.summary.nodes_total}</li>
              <li className="glass rounded p-2">Terminés: {data.summary.nodes_completed}</li>
              <li className="glass rounded p-2">Échecs: {data.summary.nodes_failed}</li>
              <li className="glass rounded p-2">Artifacts: {data.summary.artifacts_total}</li>
              <li className="glass rounded p-2">Événements: {data.summary.events_total}</li>
              {typeof data.summary.duration_ms === "number" && (
                <li className="glass rounded p-2">Durée: {Math.round(data.summary.duration_ms / 1000)}s</li>
              )}
            </ul>
          )}
        </section>
      )}
    </main>
  );
}

