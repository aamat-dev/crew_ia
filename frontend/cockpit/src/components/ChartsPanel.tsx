"use client";
import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import dynamic from "next/dynamic";
import { fetchRuns, fetchRun, fetchFeedbacks, type RunListItem, type FeedbackItem } from "@/lib/api";

const Fallback = () => <div className="h-64 animate-pulse rounded bg-muted" role="status" aria-label="Chargement du graphique" />;
const ThroughputChart = dynamic(() => import("@/components/charts/ThroughputChart").then((m) => m.ThroughputChart), {
  ssr: false,
  loading: Fallback,
});
const LatencyChart = dynamic(() => import("@/components/charts/LatencyChart").then((m) => m.LatencyChart), {
  ssr: false,
  loading: Fallback,
});
const FeedbackChart = dynamic(() => import("@/components/charts/FeedbackChart").then((m) => m.FeedbackChart), {
  ssr: false,
  loading: Fallback,
});

function quantile(values: number[], q: number): number {
  if (values.length === 0) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const pos = (sorted.length - 1) * q;
  const base = Math.floor(pos);
  const rest = pos - base;
  if (sorted[base + 1] !== undefined) {
    return sorted[base] + rest * (sorted[base + 1] - sorted[base]);
  }
  return sorted[base];
}

function classifyFeedback(feedback: FeedbackItem): "positive" | "neutral" | "negative" {
  const score = feedback.score ?? 0;
  if (score >= 70) return "positive";
  if (score >= 40) return "neutral";
  return "negative";
}

export function ChartsPanel() {
  const runsQuery = useQuery({
    queryKey: ["charts", "runs"],
    queryFn: ({ signal }) => fetchRuns({ limit: 50, orderBy: "started_at", orderDir: "desc" }, { signal }),
    staleTime: 60_000,
  });

  const feedbacksQuery = useQuery({
    queryKey: ["charts", "feedbacks"],
    queryFn: ({ signal }) => fetchFeedbacks({ limit: 200, orderBy: "created_at", orderDir: "desc" }, { signal }),
    staleTime: 60_000,
  });

  const recentRunIds = React.useMemo(() => {
    const items = runsQuery.data?.items ?? [];
    return items.slice(0, 20).map((run) => run.id);
  }, [runsQuery.data]);

  const summariesQuery = useQuery({
    queryKey: ["charts", "runs", "summaries", recentRunIds],
    queryFn: async ({ signal }) => {
      const ids = recentRunIds;
      const results = await Promise.all(ids.map((id) => fetchRun(id, { signal })));
      return results;
    },
    enabled: recentRunIds.length > 0,
    staleTime: 60_000,
  });

  const throughputData = React.useMemo(() => {
    const items = runsQuery.data?.items ?? [];
    const counts = new Map<string, number>();
    items.forEach((run: RunListItem) => {
      if (!run.started_at) return;
      const key = run.started_at.slice(0, 10);
      counts.set(key, (counts.get(key) ?? 0) + 1);
    });
    return Array.from(counts.entries())
      .sort((a, b) => a[0].localeCompare(b[0]))
      .slice(-10)
      .map(([date, value]) => ({
        date: new Date(date).toLocaleDateString("fr-FR", { weekday: "short", day: "numeric" }),
        value,
      }));
  }, [runsQuery.data]);

  const latencyData = React.useMemo(() => {
    const summaries = summariesQuery.data ?? [];
    const perDay = new Map<string, number[]>();
    summaries.forEach((run) => {
      const started = run.started_at;
      const duration = run.summary?.duration_ms;
      if (!started || !duration) return;
      const key = started.slice(0, 10);
      const values = perDay.get(key) ?? [];
      values.push(duration);
      perDay.set(key, values);
    });
    return Array.from(perDay.entries())
      .sort((a, b) => a[0].localeCompare(b[0]))
      .slice(-10)
      .map(([date, durations]) => ({
        date: new Date(date).toLocaleDateString("fr-FR", { weekday: "short", day: "numeric" }),
        p50: Math.round(quantile(durations, 0.5) / 1000),
        p95: Math.round(quantile(durations, 0.95) / 1000),
      }));
  }, [summariesQuery.data]);

  const feedbackData = React.useMemo(() => {
    const items = feedbacksQuery.data?.items ?? [];
    const perDay = new Map<string, { positive: number; neutral: number; negative: number }>();
    items.forEach((feedback) => {
      const created = feedback.created_at;
      if (!created) return;
      const key = created.slice(0, 10);
      const bucket = perDay.get(key) ?? { positive: 0, neutral: 0, negative: 0 };
      bucket[classifyFeedback(feedback)] += 1;
      perDay.set(key, bucket);
    });
    return Array.from(perDay.entries())
      .sort((a, b) => a[0].localeCompare(b[0]))
      .slice(-10)
      .map(([date, counts]) => ({
        date: new Date(date).toLocaleDateString("fr-FR", { weekday: "short", day: "numeric" }),
        ...counts,
      }));
  }, [feedbacksQuery.data]);

  return (
    <section className="space-y-4" aria-label="Graphiques de performances et feedbacks">
      <h2 className="text-lg font-medium text-slate-100">Graphiques</h2>
      <div className="grid gap-4 md:grid-cols-3">
        <div className="surface shadow-card p-4">
          <h3 className="text-sm font-medium mb-2">Throughput (runs/jour)</h3>
          {runsQuery.isLoading ? (
            <Fallback />
          ) : throughputData.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-sm text-muted-foreground" role="status">
              Aucune donnée
            </div>
          ) : (
            <ThroughputChart data={throughputData} label="Runs par jour (10 derniers points)" />
          )}
        </div>

        <div className="surface shadow-card p-4">
          <h3 className="text-sm font-medium mb-2">Durée médiane vs p95 (s)</h3>
          {summariesQuery.isLoading ? (
            <Fallback />
          ) : latencyData.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-sm text-muted-foreground" role="status">
              Aucune donnée
            </div>
          ) : (
            <LatencyChart data={latencyData} label="Durées d'exécution (secondes)" />
          )}
        </div>

        <div className="surface shadow-card p-4">
          <h3 className="text-sm font-medium mb-2">Feedbacks (positif/neutre/négatif)</h3>
          {feedbacksQuery.isLoading ? (
            <Fallback />
          ) : feedbackData.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-sm text-muted-foreground" role="status">
              Aucune donnée
            </div>
          ) : (
            <FeedbackChart data={feedbackData} label="Feedbacks par jour (10 derniers points)" />
          )}
        </div>
      </div>
    </section>
  );
}

export default ChartsPanel;
