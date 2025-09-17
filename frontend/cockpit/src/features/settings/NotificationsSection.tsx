"use client";

import * as React from "react";
import { baseFocusRing } from "@/ui/theme";
import { cn } from "@/lib/utils";

export function NotificationsSection() {
  const [toast, setToast] = React.useState(true);
  const [email, setEmail] = React.useState(false);
  const [quota, setQuota] = React.useState(80);

  return (
    <section className="surface shadow-card p-4 space-y-4">
      <div className="space-y-1">
        <h2 className="text-lg font-semibold text-[color:var(--text)]">Notifications</h2>
        <p className="text-sm text-secondary">Configurez les canaux d’alerte et seuils critiques.</p>
      </div>
      <div className="space-y-3">
        <ToggleRow
          label="Toasts dans l’interface"
          description="Affiche des alertes temps réel lors des actions critiques."
          enabled={toast}
          onToggle={() => setToast((value) => !value)}
        />
        <ToggleRow
          label="Alertes email"
          description="Recevoir un résumé des incidents chaque matin."
          enabled={email}
          onToggle={() => setEmail((value) => !value)}
        />
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-[color:var(--text)]">Seuil quotas API</p>
              <p className="text-xs text-secondary">Déclenche une alerte lorsque le quota dépasse ce pourcentage.</p>
            </div>
            <span className="text-sm font-semibold text-[color:var(--text)]">{quota}%</span>
          </div>
          <input
            type="range"
            min={40}
            max={100}
            value={quota}
            onChange={(event) => setQuota(Number(event.target.value))}
            className="w-full"
          />
        </div>
      </div>
    </section>
  );
}

interface ToggleRowProps {
  label: string;
  description: string;
  enabled: boolean;
  onToggle: () => void;
}

function ToggleRow({ label, description, enabled, onToggle }: ToggleRowProps) {
  return (
    <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
      <div>
        <p className="text-sm font-medium text-[color:var(--text)]">{label}</p>
        <p className="text-xs text-secondary">{description}</p>
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={enabled}
        onClick={onToggle}
        className={cn(
          "relative flex h-8 w-16 items-center rounded-full border border-slate-700 bg-slate-800",
          baseFocusRing
        )}
      >
        <span className="absolute inset-y-1 w-6 rounded-full bg-white transition-all" style={{ left: enabled ? "calc(100% - 2.75rem)" : "0.5rem" }} />
        <span className="sr-only">{enabled ? "Activé" : "Désactivé"}</span>
      </button>
    </div>
  );
}

export default NotificationsSection;
