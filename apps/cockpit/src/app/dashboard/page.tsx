"use client";


import { useQuery } from "@tanstack/react-query";
import { fetchJson } from "@/lib/http";

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
    </main>
  );
}

export default function DashboardPage() {
  return <DashboardContent />;
}
