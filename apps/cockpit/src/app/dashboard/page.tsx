"use client";


import { useQuery } from "@tanstack/react-query";
import { fetchJson } from "@/lib/http";
import { KpiCard } from "@/components/kpi/KpiCard";

function DashboardContent() {
  useQuery({
    queryKey: ["agents"],
    queryFn: ({ signal }) => fetchJson("/api/agents", { signal }),
  });

  useQuery({
    queryKey: ["runs"],
    queryFn: ({ signal }) => fetchJson("/api/runs", { signal }),
  });

  useQuery({
    queryKey: ["feedbacks"],
    queryFn: ({ signal }) => fetchJson("/api/feedbacks", { signal }),
  });

  return (
    <main className="p-6">
      <h1 className="text-2xl font-semibold">Dashboard</h1>
      <p data-testid="dashboard-welcome">Bienvenue sur le cockpit.</p>
      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
        <KpiCard title="Agents" value="42" variant="glass" />
        <KpiCard title="Runs" value="128" variant="glass" />
      </div>
    </main>
  );
}

export default function DashboardPage() {
  return <DashboardContent />;
}
