export type AgentRole = "Superviseur" | "Manager" | "Exécutant";
export type AgentStatus = "Actif" | "Inactif";

export interface AgentMetrics {
  successRate: number;
  averageLatency: number;
  runs: number;
  load: number;
}

export interface Agent {
  id: string;
  name: string;
  role: AgentRole;
  status: AgentStatus;
  emoji: string;
  metrics: AgentMetrics;
}
