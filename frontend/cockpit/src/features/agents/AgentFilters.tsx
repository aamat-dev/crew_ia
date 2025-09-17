"use client";

import * as React from "react";
import { AgentRole, AgentStatus } from "@/features/agents/types";
import { baseFocusRing } from "@/ui/theme";
import { cn } from "@/lib/utils";

export interface AgentFiltersProps {
  role: AgentRole | "Tous";
  onRoleChange: (role: AgentRole | "Tous") => void;
  status: AgentStatus | "Tous";
  onStatusChange: (status: AgentStatus | "Tous") => void;
}

const ROLES: Array<AgentRole | "Tous"> = ["Tous", "Superviseur", "Manager", "Exécutant"];
const STATUSES: Array<AgentStatus | "Tous"> = ["Tous", "Actif", "Inactif"];

export function AgentFilters({ role, onRoleChange, status, onStatusChange }: AgentFiltersProps) {
  return (
    <div className="surface shadow-card p-4 flex flex-wrap items-center gap-3">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs uppercase tracking-wide text-secondary">Rôle</span>
        {ROLES.map((item) => (
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
            {item}
          </button>
        ))}
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs uppercase tracking-wide text-secondary">Statut</span>
        {STATUSES.map((item) => (
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
