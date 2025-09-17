"use client";

import * as React from "react";
import { AnimatePresence, motion } from "framer-motion";
import { X, RefreshCcw, Square } from "lucide-react";
import { Run } from "@/features/runs/types";
import { StatusBadge } from "@/ui/StatusBadge";
import { baseFocusRing } from "@/ui/theme";
import { cn } from "@/lib/utils";

export interface RunDrawerProps {
  run: Run | null;
  open: boolean;
  onClose: () => void;
  onRetry?: (run: Run) => void;
  onStop?: (run: Run) => void;
}

export function RunDrawer({ run, open, onClose, onRetry, onStop }: RunDrawerProps) {
  React.useEffect(() => {
    if (!open) return;
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [open, onClose]);

  return (
    <AnimatePresence>
      {open && run ? (
        <motion.div
          className="fixed inset-0 z-40 flex justify-end"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <button
            type="button"
            aria-label="Fermer le panneau"
            className="absolute inset-0 bg-black/40"
            onClick={onClose}
          />
          <motion.aside
            role="dialog"
            aria-modal="true"
            aria-label={`Détails du run ${run.title}`}
            initial={{ x: 360 }}
            animate={{ x: 0 }}
            exit={{ x: 360 }}
            transition={{ type: "spring", stiffness: 200, damping: 28 }}
            className="relative z-10 flex h-full w-full max-w-md flex-col gap-4 overflow-y-auto surface shadow-card border-l border-slate-700/60 p-6"
          >
            <div className="flex items-start justify-between">
              <div className="space-y-1">
                <h2 className="text-2xl font-semibold text-[color:var(--text)]">{run.title}</h2>
                <p className="text-sm text-secondary">{run.date}</p>
              </div>
              <button
                type="button"
                onClick={onClose}
                className={cn(
                  "h-10 w-10 rounded-full surface shadow-card grid place-content-center text-[color:var(--text)]",
                  baseFocusRing
                )}
              >
                <X className="h-5 w-5" aria-hidden />
              </button>
            </div>
            <StatusBadge status={run.status} />
            <section className="space-y-2">
              <h3 className="text-sm font-semibold text-[color:var(--text)] uppercase tracking-wide">Synthèse</h3>
              <dl className="grid grid-cols-2 gap-3 text-sm text-secondary">
                <div>
                  <dt className="font-medium text-[color:var(--text)]">Durée</dt>
                  <dd>{run.duration}</dd>
                </div>
                <div>
                  <dt className="font-medium text-[color:var(--text)]">Débit</dt>
                  <dd>{run.throughput} taches/min</dd>
                </div>
                <div>
                  <dt className="font-medium text-[color:var(--text)]">Taux succès</dt>
                  <dd>{run.successRate}%</dd>
                </div>
                <div>
                  <dt className="font-medium text-[color:var(--text)]">Agents impliqués</dt>
                  <dd>{run.agents.length}</dd>
                </div>
              </dl>
            </section>
            <section className="space-y-2">
              <h3 className="text-sm font-semibold text-[color:var(--text)] uppercase tracking-wide">Agents</h3>
              <ul className="space-y-2 text-sm text-secondary">
                {run.agents.map((agent) => (
                  <li key={agent.id} className="flex items-center justify-between">
                    <span>{agent.name}</span>
                    <span className="text-xs uppercase tracking-wide">{agent.role}</span>
                  </li>
                ))}
              </ul>
            </section>
            <section className="space-y-2">
              <h3 className="text-sm font-semibold text-[color:var(--text)] uppercase tracking-wide">Logs</h3>
              <div className="surface-muted max-h-40 overflow-y-auto rounded-2xl p-3 text-xs text-secondary">
                <ul className="space-y-2">
                  {run.logs.map((log) => (
                    <li key={log.timestamp}>
                      <span className="font-medium text-[color:var(--text)]">{log.timestamp}</span>
                      <span className="ml-2">{log.message}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </section>
            {run.errors && run.errors.length > 0 ? (
              <section className="space-y-2">
                <h3 className="text-sm font-semibold text-[color:var(--text)] uppercase tracking-wide">Erreurs</h3>
                <ul className="space-y-2 text-sm text-rose-200">
                  {run.errors.map((error, index) => (
                    <li key={index} className="surface-muted rounded-xl p-3 border border-rose-500/30">
                      {error}
                    </li>
                  ))}
                </ul>
              </section>
            ) : null}
            <div className="mt-auto flex flex-wrap gap-3 pt-4">
              <button
                type="button"
                onClick={() => run && onRetry?.(run)}
                className={cn(
                  "inline-flex items-center gap-2 rounded-full bg-[var(--accent-indigo-500)] px-4 py-2 text-sm font-medium text-white shadow-card transition hover:shadow-lg",
                  baseFocusRing
                )}
              >
                <RefreshCcw className="h-4 w-4" aria-hidden />
                Relancer
              </button>
              <button
                type="button"
                onClick={() => run && onStop?.(run)}
                className={cn(
                  "inline-flex items-center gap-2 rounded-full border border-rose-500/40 px-4 py-2 text-sm font-medium text-rose-200 transition hover:bg-rose-500/10",
                  baseFocusRing
                )}
              >
                <Square className="h-4 w-4" aria-hidden />
                Stopper
              </button>
            </div>
          </motion.aside>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}

export default RunDrawer;
