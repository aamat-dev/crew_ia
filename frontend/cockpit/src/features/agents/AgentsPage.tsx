"use client";

import * as React from "react";
import { HeaderBar } from "@/ui/HeaderBar";
import { MetricChartCard } from "@/ui/MetricChartCard";
import { NoticeCard } from "@/ui/NoticeCard";
import { AgentFilters } from "@/features/agents/AgentFilters";
import { AgentCard } from "@/features/agents/AgentCard";
import { Agent, AgentRole, AgentStatus } from "@/features/agents/types";

const AGENT_FIXTURES: Agent[] = [
  {
    id: "agent-1",
    name: "Ava",
    role: "Superviseur",
    status: "Actif",
    emoji: "🛰️",
    metrics: { successRate: 97, averageLatency: 1.8, runs: 34, load: 72 },
  },
  {
    id: "agent-2",
    name: "Noah",
    role: "Manager",
    status: "Actif",
    emoji: "🧠",
    metrics: { successRate: 92, averageLatency: 2.4, runs: 28, load: 64 },
  },
  {
    id: "agent-3",
    name: "Maya",
    role: "Superviseur",
    status: "Actif",
    emoji: "🧭",
    metrics: { successRate: 95, averageLatency: 2.1, runs: 31, load: 70 },
  },
  {
    id: "agent-4",
    name: "Émile",
    role: "Superviseur",
    status: "Inactif",
    emoji: "🛠️",
    metrics: { successRate: 88, averageLatency: 3.1, runs: 12, load: 24 },
  },
  {
    id: "agent-5",
    name: "Sacha",
    role: "Manager",
    status: "Actif",
    emoji: "🦾",
    metrics: { successRate: 90, averageLatency: 2.8, runs: 22, load: 58 },
  },
  {
    id: "agent-6",
    name: "Mina",
    role: "Exécutant",
    status: "Actif",
    emoji: "⚡",
    metrics: { successRate: 82, averageLatency: 1.6, runs: 48, load: 88 },
  },
  {
    id: "agent-7",
    name: "Léa",
    role: "Exécutant",
    status: "Actif",
    emoji: "🌟",
    metrics: { successRate: 85, averageLatency: 1.9, runs: 41, load: 80 },
  },
  {
    id: "agent-8",
    name: "Eliott",
    role: "Manager",
    status: "Inactif",
    emoji: "🧩",
    metrics: { successRate: 78, averageLatency: 3.4, runs: 9, load: 18 },
  },
  {
    id: "agent-9",
    name: "Jules",
    role: "Exécutant",
    status: "Actif",
    emoji: "🎯",
    metrics: { successRate: 81, averageLatency: 2.2, runs: 37, load: 66 },
  },
];

const UTILIZATION_DATA = AGENT_FIXTURES.map((agent) => ({
  name: agent.name,
  charge: agent.metrics.load,
}));

export function AgentsPage() {
  const [role, setRole] = React.useState<AgentRole | "Tous">("Tous");
  const [status, setStatus] = React.useState<AgentStatus | "Tous">("Tous");

  const filteredAgents = React.useMemo(() => {
    return AGENT_FIXTURES.filter((agent) => {
      if (role !== "Tous" && agent.role !== role) return false;
      if (status !== "Tous" && agent.status !== status) return false;
      return true;
    });
  }, [role, status]);

  return (
    <div className="space-y-6">
      <HeaderBar title="Agents" breadcrumb="Performance & disponibilité" />
      <AgentFilters role={role} onRoleChange={setRole} status={status} onStatusChange={setStatus} />
      <MetricChartCard
        title="Charge moyenne par agent"
        type="bar"
        data={UTILIZATION_DATA}
        xKey="name"
        yKey="charge"
        accent="emerald"
      />
      {filteredAgents.length === 0 ? (
        <NoticeCard type="warning" message="Aucun agent ne correspond à cette combinaison de filtres." />
      ) : (
        <section className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3" aria-label="Liste des agents">
          {filteredAgents.map((agent) => (
            <AgentCard key={agent.id} agent={agent} />
          ))}
        </section>
      )}
    </div>
  );
}

export default AgentsPage;
