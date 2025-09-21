"use client";

import * as React from "react";
import { baseFocusRing } from "@/ui/theme";
import { cn } from "@/lib/utils";

export type AgentStatusFilter = "Tous" | "Actif" | "Inactif";

export interface AgentFiltersProps {
  roles: string[];
  role: string | "Tous";
  onRoleChange: (role: string | "Tous") => void;
  status: AgentStatusFilter;
  onStatusChange: (status: AgentStatusFilter) => void;
}

const STATUS_OPTIONS: AgentStatusFilter[] = ["Tous", "Actif", "Inactif"];

function formatLabel(value: string): string {
  const cleaned = value.replace(/[_-]+/g, " ").trim();
  if (!cleaned) return "(non défini)";
  return cleaned.charAt(0).toUpperCase() + cleaned.slice(1);
}

export function AgentFilters({ roles, role, onRoleChange, status, onStatusChange }: AgentFiltersProps) {
  const roleOptions = React.useMemo<(string | "Tous")[]>(() => ["Tous", ...roles], [roles]);

  return (
    <div className="surface shadow-card p-4 flex flex-wrap items-center gap-3">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs uppercase tracking-wide text-secondary">Rôle</span>
        {roleOptions.map((item) => (
          <button
            key={item}
            type="button"
            onClick={() => onRoleChange(item)}
            className={cn(
              "rounded-full px-3 py-1 text-xs font-medium uppercase tracking-wide transition",
              baseFocusRing,
              role === item ? "bg-[var(--accent-indigo-500)] text-white shadow-card" : "border border-slate-700 text-secondary"
            )}
          >
            {item === "Tous" ? "Tous" : formatLabel(item)}
          </button>
        ))}
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs uppercase tracking-wide text-secondary">Statut</span>
        {STATUS_OPTIONS.map((item) => (
          <button
            key={item}
            type="button"
            onClick={() => onStatusChange(item)}
            className={cn(
              "rounded-full px-3 py-1 text-xs font-medium uppercase tracking-wide transition",
              baseFocusRing,
              status === item ? "bg-[var(--accent-emerald-500)] text-white shadow-card" : "border border-slate-700 text-secondary"
            )}
          >
            {item}
          </button>
        ))}
      </div>
    </div>
  );
}

export default AgentFilters;
