"use client";

import * as React from "react";
import { HeaderBar } from "@/ui/HeaderBar";
import { TimelineItem } from "@/ui/TimelineItem";
import { NoticeCard } from "@/ui/NoticeCard";
import { Run } from "@/features/runs/types";
import { RunDrawer } from "@/features/runs/RunDrawer";
import { RunFilters, DateRange } from "@/features/runs/RunFilters";
import { Status } from "@/ui/theme";
import { baseFocusRing } from "@/ui/theme";
import { cn } from "@/lib/utils";

const RUN_FIXTURES: Run[] = [
  {
    id: "run-1042",
    title: "Analyse batch clients",
    status: "running",
    date: "2024-11-18 09:45",
    duration: "12m",
    throughput: 42,
    successRate: 86,
    agents: [
      { id: "ag-1", name: "Ava", role: "Superviseur" },
      { id: "ag-2", name: "Noah", role: "Manager" },
      { id: "ag-7", name: "Léa", role: "Exécutant" },
    ],
    logs: [
      { timestamp: "09:45:02", message: "Run démarré" },
      { timestamp: "09:47:11", message: "Étape 1 terminée" },
      { timestamp: "09:49:32", message: "4 warnings détectés" },
    ],
    description: "Traitement des rapports clients pour la zone EU.",
  },
  {
    id: "run-1039",
    title: "Synthèse veille concurrentielle",
    status: "completed",
    date: "2024-11-17 18:22",
    duration: "18m",
    throughput: 28,
    successRate: 92,
    agents: [
      { id: "ag-3", name: "Maya", role: "Superviseur" },
      { id: "ag-8", name: "Eliott", role: "Manager" },
    ],
    logs: [
      { timestamp: "18:05:01", message: "Run démarré" },
      { timestamp: "18:14:47", message: "Consolidation des insights" },
      { timestamp: "18:22:10", message: "Livraison effectuée" },
    ],
  },
  {
    id: "run-1037",
    title: "Génération reporting Q3",
    status: "failed",
    date: "2024-11-17 14:03",
    duration: "7m",
    throughput: 12,
    successRate: 45,
    agents: [
      { id: "ag-5", name: "Sacha", role: "Manager" },
      { id: "ag-6", name: "Mina", role: "Exécutant" },
    ],
    logs: [
      { timestamp: "14:01:12", message: "Connexion à la base" },
      { timestamp: "14:02:27", message: "Erreur API partenaires" },
    ],
    errors: [
      "Échec de la requête GraphQL: 429 Too Many Requests",
      "Synchronisation CRM interrompue",
    ],
  },
  {
    id: "run-1034",
    title: "Simulation charge agents",
    status: "queued",
    date: "2024-11-17 11:45",
    duration: "--",
    throughput: 0,
    successRate: 0,
    agents: [
      { id: "ag-2", name: "Noah", role: "Manager" },
      { id: "ag-9", name: "Jules", role: "Exécutant" },
    ],
    logs: [{ timestamp: "11:45:12", message: "Run en attente de ressources" }],
  },
  {
    id: "run-1032",
    title: "Audit conformité RGPD",
    status: "completed",
    date: "2024-11-16 20:11",
    duration: "26m",
    throughput: 30,
    successRate: 97,
    agents: [
      { id: "ag-4", name: "Émile", role: "Superviseur" },
      { id: "ag-6", name: "Mina", role: "Exécutant" },
      { id: "ag-7", name: "Léa", role: "Exécutant" },
    ],
    logs: [
      { timestamp: "19:45:00", message: "Chargement du référentiel" },
      { timestamp: "19:55:12", message: "Vérification des anomalies" },
      { timestamp: "20:11:03", message: "Export PDF généré" },
    ],
  },
  {
    id: "run-1031",
    title: "Préparation onboarding clients",
    status: "running",
    date: "2024-11-16 16:42",
    duration: "9m",
    throughput: 18,
    successRate: 79,
    agents: [
      { id: "ag-1", name: "Ava", role: "Superviseur" },
      { id: "ag-8", name: "Eliott", role: "Manager" },
    ],
    logs: [
      { timestamp: "16:42:04", message: "Chargement des playbooks" },
      { timestamp: "16:45:18", message: "3 tâches en progression" },
    ],
  },
  {
    id: "run-1027",
    title: "Veille réglementaire",
    status: "queued",
    date: "2024-11-16 10:05",
    duration: "--",
    throughput: 0,
    successRate: 0,
    agents: [{ id: "ag-10", name: "Malo", role: "Exécutant" }],
    logs: [{ timestamp: "10:05:33", message: "En attente de validation" }],
  },
];

const PAGE_SIZE = 6;

export function RunsPage() {
  const [selectedStatuses, setSelectedStatuses] = React.useState<Status[]>(["running", "completed", "queued", "failed"]);
  const [query, setQuery] = React.useState("");
  const [dateRange, setDateRange] = React.useState<DateRange>({});
  const [page, setPage] = React.useState(1);
  const [loading, setLoading] = React.useState(true);
  const [selectedRun, setSelectedRun] = React.useState<Run | null>(null);

  React.useEffect(() => {
    setLoading(true);
    const timer = window.setTimeout(() => setLoading(false), 400);
    return () => window.clearTimeout(timer);
  }, [selectedStatuses, query, dateRange, page]);

  const filteredRuns = React.useMemo(() => {
    return RUN_FIXTURES.filter((run) => {
      if (!selectedStatuses.includes(run.status)) {
        return false;
      }
      if (query && !`${run.title} ${run.id} ${run.agents.map((agent) => agent.name).join(" ")}`.toLowerCase().includes(query.toLowerCase())) {
        return false;
      }
      if (dateRange.from && new Date(run.date) < new Date(dateRange.from)) {
        return false;
      }
      if (dateRange.to && new Date(run.date) > new Date(dateRange.to)) {
        return false;
      }
      return true;
    });
  }, [selectedStatuses, query, dateRange]);

  const visibleRuns = filteredRuns.slice(0, page * PAGE_SIZE);
  const hasMore = visibleRuns.length < filteredRuns.length;

  const skeletons = Array.from({ length: 3 }).map((_, index) => (
    <div key={`skeleton-${index}`} className="surface shadow-card p-4 animate-pulse">
      <div className="h-5 w-48 rounded bg-slate-700/40" />
      <div className="mt-3 h-4 w-32 rounded bg-slate-700/30" />
    </div>
  ));

  return (
    <div className="space-y-6">
      <HeaderBar title="Runs" breadcrumb="Pilotage & historique" />
      <RunFilters
        selectedStatuses={selectedStatuses}
        onStatusesChange={(value) => {
          setPage(1);
          setSelectedStatuses(value);
        }}
        query={query}
        onQueryChange={(value) => {
          setPage(1);
          setQuery(value);
        }}
        dateRange={dateRange}
        onDateRangeChange={(value) => {
          setPage(1);
          setDateRange(value);
        }}
      />
      <section className="space-y-3" aria-label="Liste des runs">
        {loading ? (
          skeletons
        ) : visibleRuns.length === 0 ? (
          <NoticeCard type="warning" message="Aucun run ne correspond à ces filtres. Ajustez la recherche pour visualiser l'historique." />
        ) : (
          visibleRuns.map((run) => (
            <TimelineItem
              key={run.id}
              title={run.title}
              date={run.date}
              status={run.status}
              description={run.description}
              onRetry={() => setSelectedRun(run)}
              onDetails={() => setSelectedRun(run)}
            />
          ))
        )}
        {hasMore && !loading ? (
          <div className="flex justify-center pt-2">
            <button
              type="button"
              onClick={() => setPage((value) => value + 1)}
              className={cn(
                "rounded-full bg-[var(--accent-cyan-500)] px-4 py-2 text-sm font-medium text-white shadow-card transition hover:shadow-lg",
                baseFocusRing
              )}
            >
              Charger plus
            </button>
          </div>
        ) : null}
      </section>
      <RunDrawer
        run={selectedRun}
        open={Boolean(selectedRun)}
        onClose={() => setSelectedRun(null)}
        onRetry={(run) => console.log("Relancer", run.id)}
        onStop={(run) => console.log("Stopper", run.id)}
      />
    </div>
  );
}

export default RunsPage;
