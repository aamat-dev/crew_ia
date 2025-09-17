"use client";

import * as React from "react";
import { baseFocusRing } from "@/ui/theme";
import { cn } from "@/lib/utils";

interface ApiKeyItem {
  id: string;
  label: string;
  value: string;
}

function generateKey() {
  return Array.from({ length: 4 })
    .map(() => Math.random().toString(36).slice(2, 6).toUpperCase())
    .join("-");
}

export function ApiKeysSection() {
  const [keys, setKeys] = React.useState<ApiKeyItem[]>([
    { id: "primary", label: "Clé principale", value: "PK-4H9D-92LM-1TZQ" },
    { id: "backup", label: "Clé secours", value: "BK-0ZQF-6NPA-3LWX" },
  ]);
  const [visible, setVisible] = React.useState<Record<string, boolean>>({});

  const toggleVisibility = (id: string) => {
    setVisible((state) => ({ ...state, [id]: !state[id] }));
  };

  const regenerate = (id: string) => {
    setKeys((state) =>
      state.map((key) =>
        key.id === id ? { ...key, value: `${key.value.slice(0, 2)}-${generateKey()}` } : key
      )
    );
  };

  return (
    <section className="surface shadow-card p-4 space-y-4">
      <div className="space-y-1">
        <h2 className="text-lg font-semibold text-[color:var(--text)]">API Keys</h2>
        <p className="text-sm text-secondary">Générez et partagez vos clés de manière sécurisée.</p>
      </div>
      <div className="space-y-3">
        {keys.map((key) => {
          const isVisible = visible[key.id];
          return (
            <div key={key.id} className="space-y-2">
              <label className="text-xs uppercase tracking-wide text-secondary" htmlFor={`key-${key.id}`}>
                {key.label}
              </label>
              <div className="flex flex-col gap-2 md:flex-row md:items-center">
                <input
                  id={`key-${key.id}`}
                  type={isVisible ? "text" : "password"}
                  value={key.value}
                  readOnly
                  className="flex-1 rounded-xl border border-slate-700 bg-transparent px-3 py-2 text-sm text-[color:var(--text)]"
                />
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => toggleVisibility(key.id)}
                    className={cn(
                      "rounded-full border border-slate-700 px-3 py-1 text-xs font-medium uppercase tracking-wide text-secondary",
                      baseFocusRing
                    )}
                  >
                    {isVisible ? "Masquer" : "Afficher"}
                  </button>
                  <button
                    type="button"
                    onClick={() => regenerate(key.id)}
                    className={cn(
                      "rounded-full bg-[var(--accent-amber-500)] px-3 py-1 text-xs font-medium uppercase tracking-wide text-white shadow-card",
                      baseFocusRing
                    )}
                  >
                    Regénérer
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

export default ApiKeysSection;
