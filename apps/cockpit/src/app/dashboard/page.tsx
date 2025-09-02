"use client";
import { useEffect } from "react";
import { useQueries } from "@tanstack/react-query";
import { Activity, ThumbsUp, Timer } from "lucide-react";
import { KpiCard } from "@/components/kpi/KpiCard";
import { ThroughputChart } from "@/components/charts/ThroughputChart";
import { LatencyChart } from "@/components/charts/LatencyChart";
import { FeedbackChart } from "@/components/charts/FeedbackChart";
import { Skeleton } from "@/components/ds/Skeleton";
import { useToast } from "@/components/ds/Toast";

export default function DashboardPage() {
  const toast = useToast();

  const [throughput, latency, feedback] = useQueries({
    queries: [
      {
        queryKey: ["throughput"],
        queryFn: () => fetch("/api/agents").then((r) => r.json()),
      },
      {
        queryKey: ["latency"],
        queryFn: () => fetch("/api/runs").then((r) => r.json()),
      },
      {
        queryKey: ["feedback"],
        queryFn: () => fetch("/api/feedbacks").then((r) => r.json()),
      },
    ],
  });

  useEffect(() => {
    if (throughput.isError) toast("Erreur de chargement du débit");
    if (latency.isError) toast("Erreur de chargement de la latence");
    if (feedback.isError) toast("Erreur de chargement des feedbacks");
  }, [throughput.isError, latency.isError, feedback.isError, toast]);

  const throughputData = throughput.data || [];
  const latencyData = latency.data || [];
  const feedbackData = feedback.data || [];

  const throughputLast = throughputData.at(-1)?.value ?? 0;
  const throughputPrev = throughputData.at(-2)?.value ?? throughputLast;
  const throughputDelta = throughputPrev
    ? ((throughputLast - throughputPrev) / throughputPrev) * 100
    : 0;

  const latencyLast = latencyData.at(-1)?.p95 ?? 0;
  const latencyPrev = latencyData.at(-2)?.p95 ?? latencyLast;
  const latencyDelta = latencyPrev
    ? ((latencyLast - latencyPrev) / latencyPrev) * 100
    : 0;

  const feedbackLast = feedbackData.at(-1);
  const feedbackPrev = feedbackData.at(-2) || feedbackLast;
  const feedbackLastRatio = feedbackLast
    ? (feedbackLast.positive /
        (feedbackLast.positive + feedbackLast.neutral + feedbackLast.negative)) *
      100
    : 0;
  const feedbackPrevRatio = feedbackPrev
    ? (feedbackPrev.positive /
        (feedbackPrev.positive + feedbackPrev.neutral + feedbackPrev.negative)) *
      100
    : feedbackLastRatio;
  const feedbackDelta = feedbackLastRatio - feedbackPrevRatio;

  const kpisReady =
    !throughput.isLoading &&
    !latency.isLoading &&
    !feedback.isLoading &&
    !throughput.isError &&
    !latency.isError &&
    !feedback.isError;

  return (
    <main className="space-y-4 p-4">
      <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {kpisReady ? (
          <>
            <KpiCard
              title="Débit"
              value={throughputLast}
              delta={throughputDelta}
              icon={Activity}
            />
            <KpiCard
              title="Latence p95"
              value={`${latencyLast}ms`}
              delta={latencyDelta}
              icon={Timer}
            />
            <KpiCard
              title="Feedback positif"
              value={`${feedbackLastRatio.toFixed(0)}%`}
              delta={feedbackDelta}
              icon={ThumbsUp}
            />
          </>
        ) : (
          <>
            <Skeleton className="h-24" />
            <Skeleton className="h-24" />
            <Skeleton className="h-24" />
          </>
        )}
      </div>

      <div className="grid gap-4 grid-cols-1 lg:grid-cols-3">
        {throughput.isLoading ? (
          <Skeleton className="h-64" />
        ) : (
          <ThroughputChart data={throughputData} />
        )}
        {latency.isLoading ? (
          <Skeleton className="h-64" />
        ) : (
          <LatencyChart data={latencyData} />
        )}
        {feedback.isLoading ? (
          <Skeleton className="h-64" />
        ) : (
          <FeedbackChart data={feedbackData} />
        )}
      </div>
    </main>
  );
}

