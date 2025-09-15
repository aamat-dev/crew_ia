"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { resolveApiUrl, defaultApiHeaders } from "@/lib/config";
import { fetchJson } from "@/lib/fetchJson";
import { EmptyState } from "@/components/EmptyState";
import { KpiCard } from "@/components/kpi/KpiCard";
import { ChartsPanel } from "@/components/ChartsPanel";
import { StatusBadge } from "@/components/ds/StatusBadge";

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
      <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">Dashboard</h1>
      <p data-testid="dashboard-welcome">Bienvenue sur le cockpit.</p>

      <section aria-label="Indicateurs clés" className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {isLoading ? (
          <>
            <KpiCard title="Runs aujourd'hui" loading />
            <KpiCard title="Agents actifs" loading />
            <KpiCard title="Taux succès" loading />
            <KpiCard title="Latence médiane" loading />
          </>
        ) : isError ? (
          <>
            <KpiCard title="Runs aujourd'hui" noData hint="Erreur de chargement" />
            <KpiCard title="Agents actifs" noData hint="Erreur de chargement" />
            <KpiCard title="Taux succès" noData hint="Erreur de chargement" />
            <KpiCard title="Latence médiane" noData hint="Erreur de chargement" />
          </>
        ) : (
          <>
            <KpiCard
              title="Runs aujourd'hui"
              value={data ? (typeof data.total === "number" ? data.total : data.items.length) : 0}
            />
            <KpiCard
              title="Agents actifs"
              value={9}
              delta={0}
              unit={""}
            />
            <KpiCard
              title="Taux succès"
              value={94}
              delta={2}
              unit="%"
            />
            <KpiCard title="Latence médiane" value={2.4} delta={-0.3} unit="s" />
          </>
        )}
      </section>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <div className="xl:col-span-2 space-y-6">
          <ChartsPanel />
          <section className="space-y-3" aria-label="Derniers runs">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-medium">Derniers runs</h2>
            <Link
              href="/runs"
            className="inline-flex items-center rounded-xl border border-slate-200 bg-white px-3 py-1 shadow-sm transition hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-focus"
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
              <li key={r.id} className="clay-card p-3">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">{r.title || r.id}</p>
                    <p className="text-sm opacity-80">
                      {r.started_at ? new Date(r.started_at).toLocaleString() : ""}
                    </p>
                  </div>
                  <StatusBadge status={r.status as any} />
                </div>
              </li>
            ))}
          </ol>
        )}
          </section>
        </div>
        <div className="space-y-6">
          <section className="clay-card p-4" aria-label="Charge agents">
            <h3 className="mb-3 text-sm font-medium text-slate-900">Charge agents</h3>
            {[{ label: "Superviseurs", v: 78, color: "bg-indigo-600" }, { label: "Managers", v: 52, color: "bg-cyan-500" }, { label: "Exécutants", v: 34, color: "bg-emerald-500" }].map(({ label, v, color }) => (
              <div key={label} className="mb-3">
                <div className="mb-1 flex items-center justify-between text-sm text-slate-600">
                  <span>{label}</span>
                  <span>{v}%</span>
                </div>
                <div className="h-2 w-full rounded bg-slate-100">
                  <div className={`h-2 rounded ${color}`} style={{ width: `${v}%` }} />
                </div>
              </div>
            ))}
          </section>
          <section className="space-y-3" aria-label="Annonces">
            <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-emerald-800 shadow-sm">
              <p className="font-medium">Déploiement réussi</p>
              <p className="text-sm">La version 1.2 a été déployée avec succès.</p>
            </div>
            <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-amber-800 shadow-sm">
              <p className="font-medium">Attention quota</p>
              <p className="text-sm">Le quota API approche 80% ce mois-ci.</p>
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
