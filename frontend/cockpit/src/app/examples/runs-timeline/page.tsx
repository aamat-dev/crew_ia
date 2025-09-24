"use client";
import * as React from "react";
import { RunsTimeline, Run } from "@/components/timeline/RunsTimeline";
import { useToast } from "@/components/ds/Toast";

const mockRuns: Run[] = [
  {
    id: "1",
    title: "Import des données",
    status: "running",
    startedAt: new Date().toISOString(),
  },
  {
    id: "2",
    title: "Analyse des logs",
    status: "queued",
  },
  {
    id: "3",
    title: "Génération du rapport",
    status: "failed",
    startedAt: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
    endedAt: new Date(Date.now() - 1000 * 30).toISOString(),
  },
  {
    id: "4",
    title: "Nettoyage",
    status: "completed",
    startedAt: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
    endedAt: new Date(Date.now() - 1000 * 60 * 60 * 1.5).toISOString(),
  },
];

export default function RunsTimelineExample() {
  const toast = useToast();
  const handler = (action: string) => (id: string) =>
    toast(`${action} ${id}`);

  return (
    <RunsTimeline
      runs={mockRuns}
      onRetry={handler("retry")}
      onDetails={handler("details")}
    />
  );
}
