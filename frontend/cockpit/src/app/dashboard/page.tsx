"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { resolveApiUrl, defaultApiHeaders } from "@/lib/config";
import { fetchJson } from "@/lib/fetchJson";
import { EmptyState } from "@/components/EmptyState";
import { KpiCard } from "@/components/kpi/KpiCard";
import { ChartsPanel } from "@/components/ChartsPanel";
import { StatusBadge } from "@/components/ds/StatusBadge";
import { ClayCard } from "@/components/ds/ClayCard";
import { ClayLinkButton } from "@/components/ds/ClayLinkButton";
import { motion, useReducedMotion } from "framer-motion";
import { Activity, GaugeCircle, PlayCircle, Users } from "lucide-react";

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
    <main className="p-4 md:p-6 space-y-6 md:space-y-8">
      <h1 className="text-3xl font-extrabold tracking-tight text-slate-100">Dashboard</h1>
      <p data-testid="dashboard-welcome">Bienvenue sur le cockpit.</p>

      <section aria-label="Indicateurs clés" className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <motion.div
          className="contents"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ staggerChildren: 0.06, delayChildren: 0.05 }}
        >
          {(isLoading || isError) ? (
            Array.from({ length: 4 }).map((_, i) => (
              <KpiCard key={i} label={["Runs aujourd'hui","Agents actifs","Taux succès","Latence médiane"][i] || ""} loading={isLoading} noData={isError} />
            ))
          ) : (
            [
              <KpiCard key="k1" label="Runs aujourd'hui" value={data ? (typeof data.total === "number" ? data.total : data.items.length) : 0} accent="indigo" icon={PlayCircle} />,
              <KpiCard key="k2" label="Agents actifs" value={9} delta={0} unit="" accent="cyan" icon={Users} />,
              <KpiCard key="k3" label="Taux succès" value={94} delta={2} unit="%" accent="emerald" icon={GaugeCircle} />,
              <KpiCard key="k4" label="Latence médiane" value={2.4} delta={-0.3} unit="s" accent="amber" icon={Activity} />,
            ]
          )}
        </motion.div>
      </section>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <div className="xl:col-span-2 space-y-6">
          <ChartsPanel />
          <section className="space-y-3" aria-label="Derniers runs">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-medium">Derniers runs</h2>
          <ClayLinkButton href="/runs" size="sm">Voir tous les runs</ClayLinkButton>
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
              <ClayCard as="li" key={r.id} className="p-3">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">{r.title || r.id}</p>
                    <p className="text-sm opacity-80">
                      {r.started_at ? new Date(r.started_at).toLocaleString() : ""}
                    </p>
                  </div>
                  <StatusBadge status={r.status as any} />
                </div>
              </ClayCard>
            ))}
          </ol>
        )}
          </section>
        </div>
        <div className="space-y-6">
          <ClayCard className="p-4" aria-label="Charge agents">
            <h3 className="mb-3 text-sm font-medium text-slate-200">Charge agents</h3>
            {[{ label: "Superviseurs", v: 78, color: "bg-indigo-500" }, { label: "Managers", v: 52, color: "bg-cyan-500" }, { label: "Exécutants", v: 34, color: "bg-emerald-500" }].map(({ label, v, color }) => (
              <div key={label} className="mb-3">
                <div className="mb-1 flex items-center justify-between text-sm text-slate-400">
                  <span>{label}</span>
                  <span>{v}%</span>
                </div>
                <div className="h-2 w-full rounded bg-slate-800">
                  <div className={`h-2 rounded ${color}`} style={{ width: `${v}%` }} />
                </div>
              </div>
            ))}
          </ClayCard>
          <section className="space-y-3" aria-label="Annonces">
            <ClayCard className="border-emerald-500/30 text-emerald-200">
              <p className="font-medium">✅ Déploiement réussi</p>
              <p className="text-sm">La version 1.2 a été déployée avec succès.</p>
            </ClayCard>
            <ClayCard className="border-amber-500/30 text-amber-200">
              <p className="font-medium">⚠️ Attention quota</p>
              <p className="text-sm">Le quota API approche 80% ce mois-ci.</p>
            </ClayCard>
          </section>
        </div>
      </div>
    </main>
  );
}
