"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchJson } from "@/lib/http";
import { KpiCard } from "@/components/kpi/KpiCard";
import { ThroughputChart } from "@/components/charts/ThroughputChart";
import { LatencyChart } from "@/components/charts/LatencyChart";
import { FeedbackChart } from "@/components/charts/FeedbackChart";

interface AgentPoint {
  date: string;
  value: number;
}

interface RunPoint {
  date: string;
  p50: number;
  p95: number;
}

interface FeedbackPoint {
  date: string;
  positive: number;
  neutral: number;
  negative: number;
}

function DashboardContent() {
  const { data: agents = [] } = useQuery<AgentPoint[]>({
    queryKey: ["agents"],
    queryFn: ({ signal }) => fetchJson<AgentPoint[]>("/api/agents", { signal }),
  });

  const { data: runs = [] } = useQuery<RunPoint[]>({
    queryKey: ["runs"],
    queryFn: ({ signal }) => fetchJson<RunPoint[]>("/api/runs", { signal }),
  });

  const { data: feedbacks = [] } = useQuery<FeedbackPoint[]>({
    queryKey: ["feedbacks"],
    queryFn: ({ signal }) => fetchJson<FeedbackPoint[]>("/api/feedbacks", { signal }),
  });

  const agentsCount = agents.at(-1)?.value ?? 0;
  const latencyP50 = runs.at(-1)?.p50 ?? 0;
  const positiveRate = feedbacks.at(-1)?.positive ?? 0;

  return (
    <main className="p-6 space-y-8">
      <h1 className="text-2xl font-semibold">Dashboard</h1>
      <p data-testid="dashboard-welcome">Bienvenue sur le cockpit.</p>

      <section
        className="grid gap-4 md:grid-cols-3"
        aria-label="Indicateurs clés"
      >
        <KpiCard title="Agents actifs" value={agentsCount} />
        <KpiCard title="Latence p50" value={latencyP50} />
        <KpiCard title="Feedback positif (%)" value={positiveRate} />
      </section>

      <section className="space-y-8" aria-label="Graphiques">
        <ThroughputChart data={agents} />
        <LatencyChart data={runs} />
        <FeedbackChart data={feedbacks} />
      </section>
    </main>
  );
}

export default function DashboardPage() {
  return <DashboardContent />;
}

