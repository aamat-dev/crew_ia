"use client";
import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { ThroughputChart } from "@/components/charts/ThroughputChart";
import { LatencyChart } from "@/components/charts/LatencyChart";
import { FeedbackChart } from "@/components/charts/FeedbackChart";
import { useToast } from "@/components/ds/Toast";
import { ClayCard } from "@/components/ds/ClayCard";

export function ChartsPanel() {
  const toast = useToast();

  const agents = useQuery({
    queryKey: ["chart:agents"],
    queryFn: async () => {
      const r = await fetch("/api/agents");
      if (!r.ok) throw new Error(r.statusText);
      return (await r.json()) as Array<{ date: string; value: number }>;
    },
    staleTime: 60_000,
  });

  const runs = useQuery({
    queryKey: ["chart:runs"],
    queryFn: async () => {
      const r = await fetch("/api/runs");
      if (!r.ok) throw new Error(r.statusText);
      return (await r.json()) as Array<{ date: string; p50: number; p95: number }>;
    },
    staleTime: 60_000,
  });

  const feedbacks = useQuery({
    queryKey: ["chart:feedbacks"],
    queryFn: async () => {
      const r = await fetch("/api/feedbacks");
      if (!r.ok) throw new Error(r.statusText);
      return (await r.json()) as Array<{ date: string; positive: number; neutral: number; negative: number }>;
    },
    staleTime: 60_000,
  });

  React.useEffect(() => {
    const err = agents.error || runs.error || feedbacks.error;
    if (err) toast((err as Error).message || "Erreur de chargement des graphiques", "error");
  }, [agents.error, runs.error, feedbacks.error, toast]);

  const loading = agents.isLoading || runs.isLoading || feedbacks.isLoading;

  return (
    <section className="space-y-4" aria-label="Graphiques de performances et feedbacks">
      <h2 className="text-lg font-medium text-slate-900">Graphiques</h2>
      <div className="grid gap-4 md:grid-cols-3">
        <ClayCard className="p-4">
          <h3 className="text-sm font-medium mb-2">Throughput (runs/heure)</h3>
          {agents.isLoading ? (
            <div className="h-64 animate-pulse rounded bg-muted" role="status" aria-label="Chargement du graphique throughput" />
          ) : agents.isError || !agents.data?.length ? (
            <div className="h-64 flex items-center justify-center text-sm text-muted-foreground" role="status">Aucune donnée</div>
          ) : (
            <ThroughputChart data={agents.data} label="Graphique du débit de runs par heure" />
          )}
        </ClayCard>

        <ClayCard className="p-4">
          <h3 className="text-sm font-medium mb-2">Latence moyenne</h3>
          {runs.isLoading ? (
            <div className="h-64 animate-pulse rounded bg-muted" role="status" aria-label="Chargement du graphique de latence" />
          ) : runs.isError || !runs.data?.length ? (
            <div className="h-64 flex items-center justify-center text-sm text-muted-foreground" role="status">Aucune donnée</div>
          ) : (
            <LatencyChart data={runs.data} label="Graphique de latence (p50/p95)" />
          )}
        </ClayCard>

        <ClayCard className="p-4">
          <h3 className="text-sm font-medium mb-2">Feedbacks (critique/major/minor)</h3>
          {feedbacks.isLoading ? (
            <div className="h-64 animate-pulse rounded bg-muted" role="status" aria-label="Chargement du graphique des feedbacks" />
          ) : feedbacks.isError || !feedbacks.data?.length ? (
            <div className="h-64 flex items-center justify-center text-sm text-muted-foreground" role="status">Aucune donnée</div>
          ) : (
            <FeedbackChart data={feedbacks.data} label="Graphique de répartition des feedbacks" />
          )}
        </ClayCard>
      </div>
    </section>
  );
}

export default ChartsPanel;
