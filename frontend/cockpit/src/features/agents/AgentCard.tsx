import type { Agent } from "@/lib/api";
import { StatusBadge } from "@/ui/StatusBadge";
import { accentGradient } from "@/ui/theme";
import { cn } from "@/lib/utils";

export interface AgentCardProps {
  agent: Agent;
}

function toAccent(role: string): "indigo" | "cyan" | "emerald" {
  const normalized = role.toLowerCase();
  if (normalized.includes("manager")) return "cyan";
  if (normalized.includes("exec")) return "emerald";
  if (normalized.includes("executor")) return "emerald";
  return "indigo";
}

function formatValue(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return "N/A";
  if (typeof value === "number") return value.toString();
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : "N/A";
}

function formatLabel(value: string): string {
  const cleaned = value.replace(/[_-]+/g, " ").trim();
  if (!cleaned) return "(non défini)";
  return cleaned.charAt(0).toUpperCase() + cleaned.slice(1);
}

function formatDate(value?: string | null): string {
  if (!value) return "N/A";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

export function AgentCard({ agent }: AgentCardProps) {
  const status = agent.is_active ? "completed" : "failed";
  const accent = toAccent(agent.role || "");
  const initials = agent.name ? agent.name.charAt(0).toUpperCase() : "?";

  return (
    <article className="surface shadow-card p-4 space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <span
            aria-hidden
            className={cn(
              "grid h-12 w-12 place-content-center rounded-2xl text-xl font-semibold text-white",
              "bg-gradient-to-br",
              accentGradient(accent)
            )}
          >
            {initials}
          </span>
          <div>
            <h3 className="text-lg font-semibold text-[color:var(--text)]">{agent.name}</h3>
            <p className="text-sm text-secondary">{formatLabel(agent.role)}</p>
          </div>
        </div>
        <StatusBadge status={status} />
      </div>
      <div className="grid grid-cols-2 gap-3 text-sm">
        <Metric label="Domaine" value={formatLabel(agent.domain || "")} />
        <Metric label="Modèle par défaut" value={formatValue(agent.default_model)} />
        <Metric label="Version" value={formatValue(agent.version)} />
        <Metric label="Mis à jour" value={formatDate(agent.updated_at)} />
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
