import { Agent } from "@/features/agents/types";
import { StatusBadge } from "@/ui/StatusBadge";
import { accentGradient, baseFocusRing } from "@/ui/theme";
import { cn } from "@/lib/utils";

export interface AgentCardProps {
  agent: Agent;
}

export function AgentCard({ agent }: AgentCardProps) {
  const status = agent.status === "Actif" ? "completed" : "failed";
  const accent = agent.role === "Superviseur" ? "indigo" : agent.role === "Manager" ? "cyan" : "emerald";

  return (
    <article className="surface shadow-card p-4 space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <span
            aria-hidden
            className={cn(
              "grid h-12 w-12 place-content-center rounded-2xl text-2xl",
              "bg-gradient-to-br",
              accentGradient(accent)
            )}
          >
            {agent.emoji}
          </span>
          <div>
            <h3 className="text-lg font-semibold text-[color:var(--text)]">{agent.name}</h3>
            <p className="text-sm text-secondary">{agent.role}</p>
          </div>
        </div>
        <StatusBadge status={status} />
      </div>
      <div className="grid grid-cols-2 gap-3 text-sm">
        <Metric label="Taux succès" value={`${agent.metrics.successRate}%`} />
        <Metric label="Latence moyenne" value={`${agent.metrics.averageLatency}s`} />
        <Metric label="Runs 7j" value={agent.metrics.runs.toString()} />
        <Metric label="Charge" value={`${agent.metrics.load}%`} />
      </div>
      <div className="flex gap-2">
        <button
          type="button"
          className={cn(
            "rounded-full border border-slate-700 px-3 py-1 text-xs font-medium uppercase tracking-wide text-secondary",
            baseFocusRing
          )}
        >
          Profil
        </button>
        <button
          type="button"
          className={cn(
            "rounded-full bg-[var(--accent-cyan-500)] px-3 py-1 text-xs font-medium uppercase tracking-wide text-white shadow-card",
            baseFocusRing
          )}
        >
          Assigner
        </button>
      </div>
    </article>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="space-y-1">
      <p className="text-xs uppercase tracking-wide text-secondary">{label}</p>
      <p className="text-base font-semibold text-[color:var(--text)]">{value}</p>
    </div>
  );
}

export default AgentCard;
