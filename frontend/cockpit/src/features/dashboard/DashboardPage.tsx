"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Activity, GaugeCircle, PlayCircle, Users } from "lucide-react";
import { HeaderBar } from "@/ui/HeaderBar";
import { KpiCard } from "@/ui/KpiCard";
import { MetricChartCard } from "@/ui/MetricChartCard";
import { NoticeCard } from "@/ui/NoticeCard";
import { TimelineItem } from "@/ui/TimelineItem";
import { RunDrawer, type RunDrawerFallback } from "@/features/runs/RunDrawer";
import {
  fetchAgents,
  fetchFeedbacks,
  fetchRun,
  fetchRuns,
  normalizeRunStatus,
  type Agent,
  type FeedbackItem,
  type RunListItem,
} from "@/lib/api";
import type { Status } from "@/ui/theme";
import { cn } from "@/lib/utils";

const containerVariants = {
  initial: {},
  animate: {
    transition: { staggerChildren: 0.08, delayChildren: 0.12 },
  },
};

function startOfTodayIso(): string {
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  return now.toISOString();
}

function formatRole(value: string): string {
  const cleaned = value.replace(/[_-]+/g, " ").trim();
  if (!cleaned) return "(non défini)";
  return cleaned.charAt(0).toUpperCase() + cleaned.slice(1);
}

function accentForRole(role: string): "indigo" | "cyan" | "emerald" {
  const normalized = role.toLowerCase();
  if (normalized.includes("manager")) return "cyan";
  if (normalized.includes("exec")) return "emerald";
  if (normalized.includes("executor")) return "emerald";
  return "indigo";
}

function formatTimelineDate(value?: string | null): string {
  if (!value) return "Date inconnue";
  try {
    const date = new Date(value);
    const now = new Date();
    const isToday = date.toDateString() === now.toDateString();
    const formatter = new Intl.DateTimeFormat("fr-FR", {
      day: "numeric",
      month: "short",
    });
    const timeFormatter = new Intl.DateTimeFormat("fr-FR", {
      hour: "2-digit",
      minute: "2-digit",
    });
    const label = isToday ? "Aujourd'hui" : formatter.format(date);
    return `${label} • ${timeFormatter.format(date)}`;
  } catch {
    return value;
  }
}

function formatDuration(ms?: number | null): string {
  if (!ms || Number.isNaN(ms)) return "—";
  const seconds = Math.round(ms / 1000);
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  const remaining = seconds % 60;
  return remaining ? `${minutes}m ${remaining}s` : `${minutes}m`;
}

function computeMedian(values: number[]): number | null {
  if (values.length === 0) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  if (sorted.length % 2 === 0) {
    return Math.round((sorted[mid - 1] + sorted[mid]) / 2);
  }
  return sorted[mid];
}

function classifyFeedback(feedback: FeedbackItem): "critical" | "major" | "minor" {
  const score = feedback.score ?? 0;
  if (score <= 40) return "critical";
  if (score <= 70) return "major";
  return "minor";
}

export function DashboardPage() {
  const [selectedRunId, setSelectedRunId] = React.useState<string | null>(null);
  const [selectedRunMeta, setSelectedRunMeta] = React.useState<RunDrawerFallback | null>(null);

  const startToday = React.useMemo(() => startOfTodayIso(), []);

  const runsQuery = useQuery({
    queryKey: ["dashboard", "runs", { limit: 50 }],
    queryFn: ({ signal }) => fetchRuns({ limit: 50, orderBy: "started_at", orderDir: "desc" }, { signal }),
    refetchInterval: 30_000,
    staleTime: 30_000,
  });

  const runsTodayQuery = useQuery({
    queryKey: ["dashboard", "runs", "today"],
    queryFn: ({ signal }) => fetchRuns({ limit: 1, startedFrom: startToday }, { signal }),
    refetchInterval: 60_000,
    staleTime: 60_000,
  });

  const runsCompletedQuery = useQuery({
    queryKey: ["dashboard", "runs", "completed"],
    queryFn: ({ signal }) => fetchRuns({ limit: 1, status: "completed" }, { signal }),
    staleTime: 60_000,
  });

  const agentsStatsQuery = useQuery({
    queryKey: ["dashboard", "agents", "count"],
    queryFn: ({ signal }) => fetchAgents({ limit: 1, isActive: true }, { signal }),
    staleTime: 60_000,
  });

  const agentsQuery = useQuery({
    queryKey: ["dashboard", "agents", { limit: 200 }],
    queryFn: ({ signal }) => fetchAgents({ limit: 200, orderBy: "name", orderDir: "asc" }, { signal }),
    staleTime: 60_000,
  });

  const feedbacksQuery = useQuery({
    queryKey: ["dashboard", "feedbacks", { limit: 100 }],
    queryFn: ({ signal }) => fetchFeedbacks({ limit: 100, orderBy: "created_at", orderDir: "desc" }, { signal }),
    staleTime: 60_000,
  });

  const recentRunIds = React.useMemo(() => {
    const items = runsQuery.data?.items ?? [];
    return items.slice(0, 5).map((run) => run.id);
  }, [runsQuery.data]);

  const durationsQuery = useQuery({
    queryKey: ["dashboard", "runs", "summaries", recentRunIds],
    queryFn: async ({ signal }) => {
      const ids = recentRunIds;
      const results = await Promise.all(ids.map((id) => fetchRun(id, { signal })));
      return results;
    },
    enabled: recentRunIds.length > 0,
    staleTime: 60_000,
  });

  const runsToday = runsTodayQuery.data?.total ?? 0;
  const totalRuns = runsQuery.data?.total ?? 0;
  const completedRuns = runsCompletedQuery.data?.total ?? 0;
  const activeAgents = agentsStatsQuery.data?.total ?? 0;

  const durationValues = React.useMemo(() => {
    const summaries = durationsQuery.data ?? [];
    return summaries
      .map((run) => run.summary?.duration_ms)
      .filter((value): value is number => typeof value === "number" && value > 0);
  }, [durationsQuery.data]);

  const medianDurationMs = computeMedian(durationValues);

  const kpis = [
    {
      label: "Runs (24h)",
      value: runsToday,
      icon: <PlayCircle className="h-5 w-5" />,
      accent: "indigo" as const,
      loading: runsTodayQuery.isLoading,
      noData: runsTodayQuery.isError,
    },
    {
      label: "Agents actifs",
      value: activeAgents,
      icon: <Users className="h-5 w-5" />,
      accent: "cyan" as const,
      loading: agentsStatsQuery.isLoading,
      noData: agentsStatsQuery.isError,
    },
    {
      label: "Taux de succès",
      value: totalRuns > 0 ? Math.round((completedRuns / totalRuns) * 100) : undefined,
      unit: "%",
      icon: <GaugeCircle className="h-5 w-5" />,
      accent: "emerald" as const,
      loading: runsQuery.isLoading || runsCompletedQuery.isLoading,
      noData: totalRuns === 0 || runsQuery.isError,
    },
    {
      label: "Durée médiane",
      value: medianDurationMs ? formatDuration(medianDurationMs) : undefined,
      icon: <Activity className="h-5 w-5" />,
      accent: "amber" as const,
      loading: durationsQuery.isLoading || runsQuery.isLoading,
      noData: !medianDurationMs && durationsQuery.isSuccess,
    },
  ];

  const throughputData = React.useMemo(() => {
    const items = runsQuery.data?.items ?? [];
    const bucket = new Map<string, number>();
    items.forEach((run) => {
      if (!run.started_at) return;
      const key = run.started_at.slice(0, 10);
      bucket.set(key, (bucket.get(key) ?? 0) + 1);
    });
    return Array.from(bucket.entries())
      .sort((a, b) => a[0].localeCompare(b[0]))
      .slice(-7)
      .map(([date, count]) => ({
        label: new Date(date).toLocaleDateString("fr-FR", { weekday: "short", day: "numeric" }),
        count,
      }));
  }, [runsQuery.data]);

  const feedbackDistribution = React.useMemo(() => {
    const items = feedbacksQuery.data?.items ?? [];
    const counts = { critical: 0, major: 0, minor: 0 };
    items.forEach((fb) => {
      counts[classifyFeedback(fb)] += 1;
    });
    return [
      { label: "Critique", count: counts.critical },
      { label: "Majeur", count: counts.major },
      { label: "Mineur", count: counts.minor },
    ];
  }, [feedbacksQuery.data]);

  const agentLoad = React.useMemo(() => {
    const items = (agentsQuery.data?.items ?? []).filter((agent: Agent) => agent.is_active);
    const total = activeAgents || items.length;
    if (!total) return [] as Array<{ label: string; percent: number; gradient: string; count: number }>;
    const counts = new Map<string, number>();
    items.forEach((agent) => {
      counts.set(agent.role, (counts.get(agent.role) ?? 0) + 1);
    });
    return Array.from(counts.entries())
      .map(([role, count]) => {
        const percent = Math.round((count / total) * 100);
        const accent = accentForRole(role);
        return {
          label: formatRole(role),
          percent,
          count,
          gradient: `from-[var(--accent-${accent}-500)] to-[var(--accent-${accent}-400)]`,
        };
      })
      .sort((a, b) => b.percent - a.percent);
  }, [agentsQuery.data, activeAgents]);

  const timelineRuns = React.useMemo(() => {
    const items = runsQuery.data?.items ?? [];
    return items.slice(0, 6).map((run: RunListItem) => ({
      id: run.id,
      title: run.title || run.id,
      status: normalizeRunStatus(run.status),
      startedAt: run.started_at,
    }));
  }, [runsQuery.data]);

  const handleOpenRun = (run: { id: string; title: string; status: Status; startedAt?: string | null }) => {
    setSelectedRunId(run.id);
    setSelectedRunMeta({
      id: run.id,
      title: run.title,
      status: run.status,
      startedAt: run.startedAt ?? null,
    });
  };

  return (
    <div className="space-y-6">
      <HeaderBar title="Dashboard" breadcrumb="Vue générale" />
      <motion.div
        className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4"
        variants={containerVariants}
        initial="initial"
        animate="animate"
      >
        {kpis.map((kpi) => (
          <KpiCard
            key={kpi.label}
            label={kpi.label}
            value={kpi.value}
            unit={kpi.unit}
            accent={kpi.accent}
            icon={kpi.icon}
            loading={kpi.loading}
            noData={kpi.noData}
          />
        ))}
      </motion.div>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <div className="xl:col-span-2">
          {runsQuery.isError ? (
            <NoticeCard type="error" message="Impossible de calculer le débit des runs." />
          ) : (
            <MetricChartCard
              title="Runs par jour"
              type="area"
              data={throughputData}
              xKey="label"
              yKey="count"
              accent="indigo"
            />
          )}
        </div>
        <div>
          {feedbacksQuery.isError ? (
            <NoticeCard type="error" message="Impossible de charger les feedbacks récents." />
          ) : (
            <MetricChartCard
              title="Feedbacks par sévérité"
              type="bar"
              data={feedbackDistribution}
              xKey="label"
              yKey="count"
              accent="cyan"
            />
          )}
        </div>
      </section>

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-2">
          <div className="space-y-3">
            <h2 className="text-lg font-semibold text-[color:var(--text)]">Derniers runs</h2>
            <div className="space-y-3">
              {runsQuery.isLoading ? (
                <div className="grid gap-3">
                  {Array.from({ length: 3 }).map((_, index) => (
                    <div key={`timeline-skeleton-${index}`} className="surface shadow-card p-4 animate-pulse">
                      <div className="h-5 w-48 rounded bg-slate-700/40" />
                      <div className="mt-3 h-4 w-32 rounded bg-slate-700/30" />
                    </div>
                  ))}
                </div>
              ) : timelineRuns.length === 0 ? (
                <NoticeCard type="warning" message="Aucun run récent pour le moment." />
              ) : (
                timelineRuns.map((run) => (
                  <TimelineItem
                    key={run.id}
                    title={run.title}
                    date={formatTimelineDate(run.startedAt)}
                    status={run.status}
                    onRetry={undefined}
                    onDetails={() => handleOpenRun(run)}
                  />
                ))
              )}
            </div>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            <NoticeCard
              type="success"
              title="API"
              message="L'API FastAPI répond correctement et les runs sont synchronisés."
            />
            <NoticeCard
              type="warning"
              title="Surveillance"
              message="Pensez à vérifier les feedbacks critiques pour maintenir la qualité."
            />
          </div>
        </div>
        <aside className="space-y-4">
          <div className="surface shadow-card p-4">
            <h3 className="text-sm font-semibold text-[color:var(--text)] uppercase tracking-wide">Répartition des agents actifs</h3>
            <div className="mt-4 space-y-4">
              {agentsQuery.isLoading ? (
                Array.from({ length: 3 }).map((_, index) => (
                  <div key={`agent-load-${index}`} className="space-y-2">
                    <div className="h-4 w-3/4 rounded bg-slate-700/40 animate-pulse" />
                    <div className="h-3 w-full rounded-full bg-slate-800" />
                  </div>
                ))
              ) : agentLoad.length === 0 ? (
                <p className="text-sm text-secondary">Aucun agent actif pour le moment.</p>
              ) : (
                agentLoad.map((item) => (
                  <div key={item.label} className="space-y-2">
                    <div className="flex items-center justify-between text-sm text-secondary">
                      <span>
                        {item.label} <span className="text-xs">({item.count})</span>
                      </span>
                      <span>{item.percent}%</span>
                    </div>
                    <div className="h-3 w-full rounded-full bg-slate-800">
                      <div
                        className={cn("h-3 rounded-full bg-gradient-to-r", item.gradient)}
                        style={{ width: `${Math.min(item.percent, 100)}%` }}
                      />
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
          <div className="surface shadow-card p-4 space-y-3">
            <h3 className="text-sm font-semibold text-[color:var(--text)] uppercase tracking-wide">Feedbacks critiques</h3>
            {feedbacksQuery.isLoading ? (
              <p className="text-sm text-secondary">Chargement…</p>
            ) : feedbacksQuery.isError ? (
              <p className="text-sm text-secondary">Échec du chargement des feedbacks.</p>
            ) : (
              (feedbacksQuery.data?.items ?? [])
                .filter((fb) => classifyFeedback(fb) === "critical")
                .slice(0, 3)
                .map((fb) => (
                  <div key={fb.id} className="rounded-xl bg-slate-900/40 p-3 text-sm text-secondary">
                    <p className="font-medium text-[color:var(--text)]">{fb.comment || fb.id}</p>
                    <p className="text-xs opacity-70">Score: {fb.score ?? "N/A"}</p>
                  </div>
                ))
            )}
          </div>
        </aside>
      </section>

      <RunDrawer
        runId={selectedRunId}
        fallback={selectedRunMeta}
        open={Boolean(selectedRunId)}
        onClose={() => {
          setSelectedRunId(null);
          setSelectedRunMeta(null);
        }}
      />
    </div>
  );
}

export default DashboardPage;
