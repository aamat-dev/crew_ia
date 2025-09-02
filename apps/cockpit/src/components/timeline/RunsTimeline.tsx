"use client";
import * as React from "react";
import { useVirtualizer } from "@tanstack/react-virtual";
import { Pause, Play, RotateCw, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { useToast } from "@/components/ds/Toast";
import { Button } from "@/components/ds/Button";

export type Run = {
  id: string;
  title: string;
  status: "queued" | "running" | "completed" | "failed" | "paused";
  startedAt?: string;
  endedAt?: string;
};

interface RunsTimelineProps {
  runs: Run[];
  onPause: (id: string) => void;
  onResume: (id: string) => void;
  onCancel: (id: string) => void;
  onRetry: (id: string) => void;
}

type PendingAction =
  | { id: string; action: "pause" | "resume" | "cancel" | "retry" }
  | null;

const statusLabels: Record<Run["status"], string> = {
  queued: "En attente",
  running: "En cours",
  completed: "Terminé",
  failed: "Échec",
  paused: "En pause",
};

const statusClasses: Record<Run["status"], string> = {
  queued: "bg-blue-100 text-blue-800",
  running: "bg-green-100 text-green-800",
  completed: "bg-gray-100 text-gray-800",
  failed: "bg-red-100 text-red-800",
  paused: "bg-yellow-100 text-yellow-800",
};

export function RunsTimeline({
  runs,
  onPause,
  onResume,
  onCancel,
  onRetry,
}: RunsTimelineProps) {
  const parentRef = React.useRef<HTMLDivElement>(null);
  const rowVirtualizer = useVirtualizer({
    count: runs.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 96,
    overscan: 5,
  });
  const toast = useToast();
  const [confirm, setConfirm] = React.useState<PendingAction>(null);

  const handleConfirm = () => {
    if (!confirm) return;
    const { id, action } = confirm;
    if (action === "pause") onPause(id);
    if (action === "resume") onResume(id);
    if (action === "cancel") onCancel(id);
    if (action === "retry") onRetry(id);
    toast(`Action ${action} déclenchée pour ${id}`);
    setConfirm(null);
  };

  React.useEffect(() => {
    const esc = (e: KeyboardEvent) => {
      if (e.key === "Escape") setConfirm(null);
    };
    window.addEventListener("keydown", esc);
    return () => window.removeEventListener("keydown", esc);
  }, []);

  const formatDate = (iso?: string) =>
    iso ? new Date(iso).toLocaleString() : "N/A";

  return (
    <>
      <div
        ref={parentRef}
        className="h-96 overflow-auto"
        role="list"
        aria-label="Historique des exécutions"
      >
        <div
          style={{
            height: `${rowVirtualizer.getTotalSize()}px`,
            position: "relative",
          }}
        >
          {rowVirtualizer.getVirtualItems().map((virtualRow) => {
            const run = runs[virtualRow.index];
            const actions: Array<{
              action: NonNullable<PendingAction>["action"];
              icon: React.ComponentType<{ className?: string }>;
              label: string;
            }> = [];
            if (run.status === "running") {
              actions.push({ action: "pause", icon: Pause, label: "Mettre en pause" });
              actions.push({ action: "cancel", icon: X, label: "Annuler" });
            } else if (run.status === "queued") {
              actions.push({ action: "cancel", icon: X, label: "Annuler" });
            } else if (run.status === "paused") {
              actions.push({ action: "resume", icon: Play, label: "Reprendre" });
              actions.push({ action: "cancel", icon: X, label: "Annuler" });
            } else if (run.status === "failed" || run.status === "completed") {
              actions.push({ action: "retry", icon: RotateCw, label: "Relancer" });
            }

            return (
              <div
                key={run.id}
                data-index={virtualRow.index}
                ref={rowVirtualizer.measureElement}
                style={{
                  position: "absolute",
                  top: 0,
                  left: 0,
                  width: "100%",
                  transform: `translateY(${virtualRow.start}px)`,
                }}
                className="border-b p-4 focus-within:ring-2 focus-within:ring-ring"
                role="listitem"
                tabIndex={0}
              >
                <div className="flex items-center justify-between gap-4">
                  <div className="flex flex-col gap-1">
                    <span className="font-medium">{run.title}</span>
                    <span className="text-sm text-muted-foreground">
                      Début : {formatDate(run.startedAt)} – Fin : {formatDate(run.endedAt)}
                    </span>
                  </div>
                  <span
                    className={cn(
                      "rounded px-2 py-1 text-xs",
                      statusClasses[run.status]
                    )}
                  >
                    {statusLabels[run.status]}
                  </span>
                </div>
                {run.status === "running" && (
                  <div className="mt-2 h-2 w-full overflow-hidden rounded bg-muted">
                    <div className="h-full w-full animate-pulse bg-primary" />
                  </div>
                )}
                {actions.length > 0 && (
                  <div className="mt-3 flex gap-2">
                    {actions.map(({ action, icon: Icon, label }) => (
                      <button
                        key={action}
                        onClick={() => setConfirm({ id: run.id, action })}
                        className="rounded-md border p-1 hover:bg-muted focus:outline-none focus:ring-2 focus:ring-ring"
                        aria-label={label}
                      >
                        <Icon className="h-4 w-4" />
                      </button>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
      {confirm && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="confirm-title"
          className="fixed inset-0 flex items-center justify-center bg-black/50"
        >
          <div className="w-full max-w-sm rounded bg-background p-4 shadow">
            <h2 id="confirm-title" className="text-lg font-semibold">
              Confirmer l&apos;action
            </h2>
            <p className="mt-2">
              Voulez-vous
              {" "}
              {confirm.action === "pause"
                ? "mettre en pause"
                : confirm.action === "resume"
                ? "reprendre"
                : confirm.action === "cancel"
                ? "annuler"
                : "relancer"}
              {" "}l&apos;exécution {confirm.id} ?
            </p>
            <div className="mt-4 flex justify-end gap-2">
              <Button onClick={() => setConfirm(null)}>Annuler</Button>
              <Button
                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                onClick={handleConfirm}
              >
                Confirmer
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
