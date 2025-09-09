"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { resolveApiUrl, defaultApiHeaders } from "@/lib/config";
import { fetchJson } from "@/lib/fetchJson";
import { EmptyState } from "@/components/EmptyState";

interface RunListItem {
  id: string;
  title: string;
  status: string;
  started_at?: string;
}

interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export default function DashboardPage() {
  const { data, isLoading, isError } = useQuery<Page<RunListItem>>({
    queryKey: ["runs:latest", { limit: 5 }],
    queryFn: ({ signal }) =>
      fetchJson<Page<RunListItem>>(resolveApiUrl(`/runs?limit=5`), {
        signal,
        headers: defaultApiHeaders(),
      }),
  });

  return (
    <main className="p-6 space-y-8">
      <h1 className="text-2xl font-semibold">Dashboard</h1>
      <p data-testid="dashboard-welcome">Bienvenue sur le cockpit.</p>

      <section className="space-y-3" aria-label="Derniers runs">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-medium">Derniers runs</h2>
          <Link
            href="/runs"
            className="glass px-3 py-1 rounded-md border focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            Voir tous les runs
          </Link>
        </div>

        {isLoading && <p role="status" aria-live="polite">Chargement…</p>}
        {isError && (
          <div role="alert" className="glass p-4 rounded-md border">
            <p className="font-medium">Impossible de charger les runs récents</p>
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
                    <p className="font-medium">{r.title || r.id}</p>
                    <p className="text-sm opacity-80">
                      {r.status}
                      {r.started_at ? ` • ${new Date(r.started_at).toLocaleString()}` : ""}
                    </p>
                  </div>
                </div>
              </li>
            ))}
          </ol>
        )}
      </section>
    </main>
  );
}
