"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import { X } from "lucide-react";
import { fetchRun, normalizeRunStatus, type RunDetail } from "@/lib/api";
import { StatusBadge } from "@/ui/StatusBadge";
import { baseFocusRing } from "@/ui/theme";
import { cn } from "@/lib/utils";
import type { Status } from "@/ui/theme";

export interface RunDrawerFallback {
  id: string;
  title: string;
  status: Status;
  startedAt?: string | null;
  endedAt?: string | null;
}

export interface RunDrawerProps {
  runId: string | null;
  fallback?: RunDrawerFallback | null;
  open: boolean;
  onClose: () => void;
}

function formatDateTime(value?: string | null): string {
  if (!value) return "Non renseigné";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

function formatDuration(ms?: number | null): string {
  if (!ms || Number.isNaN(ms)) return "—";
  const seconds = Math.round(ms / 1000);
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  const remaining = seconds % 60;
  return remaining ? `${minutes}m ${remaining}s` : `${minutes}m`;
}

export function RunDrawer({ runId, fallback, open, onClose }: RunDrawerProps) {
  React.useEffect(() => {
    if (!open) return;
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [open, onClose]);

  const query = useQuery({
    queryKey: ["run", runId],
    queryFn: ({ signal }) => fetchRun(runId!, { signal }),
    enabled: open && Boolean(runId),
    staleTime: 30_000,
  });

  const data = query.data as RunDetail | undefined;
  const status: Status = data
    ? normalizeRunStatus(data.status)
    : fallback
    ? fallback.status
    : "queued";

  const title = data?.title || fallback?.title || fallback?.id || runId || "Run";
  const startedAt = data?.started_at ?? fallback?.startedAt;
  const endedAt = data?.ended_at ?? fallback?.endedAt;
  const durationMs = data?.summary?.duration_ms;
  const nodesCompleted = data?.summary?.nodes_completed ?? 0;
  const nodesFailed = data?.summary?.nodes_failed ?? 0;
  const nodesTotal = data?.summary?.nodes_total ?? 0;
  const artifactsTotal = data?.summary?.artifacts_total ?? 0;
  const eventsTotal = data?.summary?.events_total ?? 0;

  return (
    <AnimatePresence>
      {open && runId ? (
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
            aria-label={`Détails du run ${title}`}
            initial={{ x: 360 }}
            animate={{ x: 0 }}
            exit={{ x: 360 }}
            transition={{ type: "spring", stiffness: 200, damping: 28 }}
            className="relative z-10 flex h-full w-full max-w-md flex-col gap-4 overflow-y-auto surface shadow-card border-l border-slate-700/60 p-6"
          >
            <div className="flex items-start justify-between">
              <div className="space-y-1">
                <h2 className="text-2xl font-semibold text-[color:var(--text)]">{title}</h2>
                <p className="text-sm text-secondary">ID&nbsp;: {runId}</p>
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

            <StatusBadge status={status} />

            <section className="space-y-2">
              <h3 className="text-sm font-semibold text-[color:var(--text)] uppercase tracking-wide">Horodatage</h3>
              <dl className="grid grid-cols-1 gap-2 text-sm text-secondary">
                <div>
                  <dt className="font-medium text-[color:var(--text)]">Démarré</dt>
                  <dd>{formatDateTime(startedAt)}</dd>
                </div>
                <div>
                  <dt className="font-medium text-[color:var(--text)]">Terminé</dt>
                  <dd>{formatDateTime(endedAt)}</dd>
                </div>
                <div>
                  <dt className="font-medium text-[color:var(--text)]">Durée</dt>
                  <dd>{formatDuration(durationMs ?? undefined)}</dd>
                </div>
              </dl>
            </section>

            <section className="space-y-2">
              <h3 className="text-sm font-semibold text-[color:var(--text)] uppercase tracking-wide">Synthèse</h3>
              {query.isFetching && !data ? (
                <p className="text-sm text-secondary">Chargement…</p>
              ) : data?.summary ? (
                <dl className="grid grid-cols-2 gap-3 text-sm text-secondary">
                  <div>
                    <dt className="font-medium text-[color:var(--text)]">Nœuds total</dt>
                    <dd>{nodesTotal}</dd>
                  </div>
                  <div>
                    <dt className="font-medium text-[color:var(--text)]">Terminés</dt>
                    <dd>{nodesCompleted}</dd>
                  </div>
                  <div>
                    <dt className="font-medium text-[color:var(--text)]">Échecs</dt>
                    <dd>{nodesFailed}</dd>
                  </div>
                  <div>
                    <dt className="font-medium text-[color:var(--text)]">Artifacts</dt>
                    <dd>{artifactsTotal}</dd>
                  </div>
                  <div>
                    <dt className="font-medium text-[color:var(--text)]">Événements</dt>
                    <dd>{eventsTotal}</dd>
                  </div>
                </dl>
              ) : (
                <p className="text-sm text-secondary">Aucun résumé disponible pour ce run.</p>
              )}
            </section>

            <section className="space-y-2">
              <h3 className="text-sm font-semibold text-[color:var(--text)] uppercase tracking-wide">Actions</h3>
              <p className="text-sm text-secondary">
                Consultez la page détaillée pour suivre les événements et artifacts générés par le run.
              </p>
              <a
                href={`/runs/${runId}`}
                className={cn(
                  "inline-flex w-fit items-center gap-2 rounded-full bg-[var(--accent-indigo-500)] px-4 py-2 text-sm font-medium text-white shadow-card transition hover:shadow-lg",
                  baseFocusRing
                )}
              >
                Ouvrir la fiche du run
              </a>
            </section>

            {query.isError ? (
              <p className="text-sm text-rose-200">
                Erreur lors du chargement des détails. Retentez plus tard.
              </p>
            ) : null}
          </motion.aside>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}

export default RunDrawer;
