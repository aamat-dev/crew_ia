"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { HeaderBar } from "@/ui/HeaderBar";
import { MetricChartCard } from "@/ui/MetricChartCard";
import { NoticeCard } from "@/ui/NoticeCard";
import { AgentFilters } from "@/features/agents/AgentFilters";
import { AgentCard } from "@/features/agents/AgentCard";
import { fetchAgents, type Agent as AgentRecord } from "@/lib/api";

type AgentStatusFilter = "Tous" | "Actif" | "Inactif";

function normalizeLabel(value: string): string {
  const cleaned = value.replace(/[_-]+/g, " ").trim();
  if (!cleaned) return "(non défini)";
  return cleaned.charAt(0).toUpperCase() + cleaned.slice(1);
}

export function AgentsPage() {
  const [role, setRole] = React.useState<string | "Tous">("Tous");
  const [status, setStatus] = React.useState<AgentStatusFilter>("Tous");

  const query = useQuery({
    queryKey: ["agents", { role, status }],
    queryFn: ({ signal }) => fetchAgents({ limit: 200, orderBy: "name", orderDir: "asc" }, { signal }),
    staleTime: 60_000,
  });

  const agents = query.data?.items ?? [];

  const availableRoles = React.useMemo(() => {
    const set = new Set<string>();
    agents.forEach((agent) => {
      if (agent.role) set.add(agent.role);
    });
    return Array.from(set).sort((a, b) => a.localeCompare(b, "fr", { sensitivity: "base" }));
  }, [agents]);

  const filteredAgents = React.useMemo(() => {
    return agents.filter((agent) => {
      if (role !== "Tous" && agent.role !== role) return false;
      if (status === "Actif" && !agent.is_active) return false;
      if (status === "Inactif" && agent.is_active) return false;
      return true;
    });
  }, [agents, role, status]);

  const chartData = React.useMemo(() => {
    const counts = new Map<string, number>();
    filteredAgents.forEach((agent) => {
      const domain = agent.domain || "(non défini)";
      counts.set(domain, (counts.get(domain) ?? 0) + 1);
    });
    return Array.from(counts.entries()).map(([domain, count]) => ({
      name: normalizeLabel(domain),
      count,
    }));
  }, [filteredAgents]);

  return (
    <div className="space-y-6">
      <HeaderBar title="Agents" breadcrumb="Performance & disponibilité" />
      <AgentFilters
        roles={availableRoles}
        role={role}
        onRoleChange={setRole}
        status={status}
        onStatusChange={setStatus}
      />

      {query.isLoading ? (
        <div className="surface shadow-card p-6" role="status" aria-live="polite">
          Chargement des agents…
        </div>
      ) : query.isError ? (
        <NoticeCard type="error" title="Erreur" message="Impossible de charger les agents depuis l'API." />
      ) : (
        <>
          <MetricChartCard
            title="Agents par domaine"
            type="bar"
            data={chartData}
            xKey="name"
            yKey="count"
            accent="emerald"
          />

          {filteredAgents.length === 0 ? (
            <NoticeCard type="warning" message="Aucun agent ne correspond à cette combinaison de filtres." />
          ) : (
            <section className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3" aria-label="Liste des agents">
              {filteredAgents.map((agent: AgentRecord) => (
                <AgentCard key={agent.id} agent={agent} />
              ))}
            </section>
          )}
        </>
      )}
    </div>
  );
}

export default AgentsPage;
