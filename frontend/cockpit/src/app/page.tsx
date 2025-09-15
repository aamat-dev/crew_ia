"use client";

import Link from "next/link";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchJson } from "@/lib/fetchJson";
import { resolveApiUrl, defaultApiHeaders } from "@/lib/config";
import { useToast } from "@/components/ds/Toast";
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

export default function Home() {
  const toast = useToast();
  const [posting, setPosting] = useState(false);

  const { data, isLoading, isError } = useQuery<Page<RunListItem>>({
    queryKey: ["home:runs", { limit: 5 }],
    queryFn: ({ signal }) =>
      fetchJson<Page<RunListItem>>(resolveApiUrl(`/runs?limit=5`), {
        signal,
        headers: defaultApiHeaders(),
      }),
  });

  const launchDemoTask = async () => {
    try {
      setPosting(true);
      const res = await fetch(resolveApiUrl("/tasks"), {
        method: "POST",
        headers: { ...defaultApiHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({ title: "Démonstration", task_spec: { type: "demo" } }),
      });
      if (!res.ok) {
        const msg = res.statusText || `HTTP ${res.status}`;
        throw new Error(msg);
      }
      toast("Tâche lancée", "default");
    } catch (e) {
      toast((e as Error).message || "Échec du lancement", "error");
    } finally {
      setPosting(false);
    }
  };

  return (
    <main className="p-6 space-y-8">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold">Bienvenue</h1>
        <p className="opacity-80">Votre cockpit pour runs, tasks et réglages.</p>
      </header>

      <section className="space-y-3" aria-label="Actions rapides">
        <h2 className="text-lg font-medium">Actions rapides</h2>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={launchDemoTask}
            disabled={posting}
            aria-busy={posting}
            className="glass px-3 py-1 rounded-md border focus:outline-none focus-visible:ring-2 focus-visible:ring-focus"
          >
            Lancer une tâche de démo
          </button>
          <Link
            href="/tasks"
            className="glass px-3 py-1 rounded-md border focus:outline-none focus-visible:ring-2 focus-visible:ring-focus"
          >
            Gérer les tâches
          </Link>
          <Link
            href="/settings"
            className="glass px-3 py-1 rounded-md border focus:outline-none focus-visible:ring-2 focus-visible:ring-focus"
          >
            Paramètres
          </Link>
        </div>
      </section>

      <section className="space-y-3" aria-label="Derniers runs">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-medium">Derniers runs</h2>
          <Link
            href="/runs"
            className="glass px-3 py-1 rounded-md border focus:outline-none focus-visible:ring-2 focus-visible:ring-focus"
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
          <EmptyState
            title="Aucun run"
            description="Lancez une tâche pour démarrer un run."
            ctaHref="/tasks"
            ctaLabel="Lancer une tâche"
          />
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
