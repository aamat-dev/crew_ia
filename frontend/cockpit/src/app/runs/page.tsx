"use client";

import { useQuery } from "@tanstack/react-query";
import { resolveApiUrl, defaultApiHeaders } from "@/lib/config";
import { fetchJson } from "@/lib/fetchJson";
import { EmptyState } from "@/components/EmptyState";
import Link from "next/link";

interface RunListItem {
  id: string;
  title: string;
  status: string;
  started_at?: string;
  ended_at?: string | null;
}

interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
  links?: Record<string, string> | null;
}

export default function RunsPage() {
  const { data, isLoading, isError, error, refetch, isFetching } = useQuery<Page<RunListItem>>({
    queryKey: ["runs", { limit: 20 }],
    queryFn: ({ signal }) =>
      fetchJson<Page<RunListItem>>(resolveApiUrl(`/runs?limit=20`), {
        signal,
        headers: defaultApiHeaders(),
      }),
  });

  return (
    <main role="main" className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Runs</h1>
        <button
          type="button"
          onClick={() => refetch()}
          disabled={isFetching}
          className="glass px-3 py-1 rounded-md border focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          aria-busy={isFetching}
        >
          Rafraîchir
        </button>
      </div>

      {isLoading && (
        <p role="status" aria-live="polite">Chargement des runs…</p>
      )}
      {isError && (
        <div role="alert" className="glass p-4 rounded-md border">
          <p className="font-medium">Erreur lors du chargement des runs</p>
          <p className="text-sm opacity-80">{(error as Error)?.message || "API indisponible"}</p>
        </div>
      )}

      {data && data.items.length === 0 && (
        <EmptyState title="Aucun run" description="Lancez une tâche pour démarrer un run." ctaHref="/tasks" ctaLabel="Lancer une tâche" />
      )}

      {data && data.items.length > 0 && (
        <ol role="list" className="space-y-2">
          {data.items.map((r) => (
            <li key={r.id} className="glass p-3 rounded-md border">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">
                    <Link
                      href={`/runs/${r.id}`}
                      className="hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded"
                    >
                      {r.title || r.id}
                    </Link>
                  </p>
                  <p className="text-sm opacity-80">
                    {r.status}
                    {r.started_at ? ` • démarré le ${new Date(r.started_at).toLocaleString()}` : ""}
                  </p>
                </div>
                {/* Placeholder for future link to details when available */}
              </div>
            </li>
          ))}
        </ol>
      )}
    </main>
  );
}
