"use client";
import * as React from "react";
import { DialogTitle } from "@radix-ui/react-dialog";
import { useToast } from "@/components/ds/Toast";
import Link from "next/link";
import { ClayButton } from "@/components/ds/ClayButton";

export type Criticity = "critical" | "major" | "minor";

export interface FeedbackItem {
  id: string;
  title: string;
  criticity: Criticity;
  createdAt: string;
  runId?: string;
  sourceAnchor?: string;
  summary?: string;
  resolved?: boolean;
}

function Badge({ criticity }: { criticity: Criticity }) {
  const classes =
    criticity === "critical"
      ? "bg-destructive text-destructive-foreground"
      : criticity === "major"
      ? "bg-warning text-warning-foreground"
      : "bg-muted text-foreground";
  const label = criticity === "critical" ? "Critique" : criticity === "major" ? "Majeur" : "Mineur";
  return (
    <span className={`inline-flex items-center rounded px-2 py-0.5 text-xs ${classes}`} aria-label={`Criticité ${label}`}>
      {label}
    </span>
  );
}

export function FeedbackPanel({
  open,
  onOpenChange,
  item,
  resolving = false,
  onResolve,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  item: FeedbackItem | null;
  resolving?: boolean;
  onResolve?: (id: string) => void;
}) {
  const dialogRef = React.useRef<HTMLDivElement>(null);
  const lastFocused = React.useRef<HTMLElement | null>(null);
  const toast = useToast();

  React.useEffect(() => {
    if (!open) return;
    lastFocused.current = document.activeElement as HTMLElement;
    const focusable = dialogRef.current?.querySelector<HTMLElement>(
      "button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])"
    );
    focusable?.focus();

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        onOpenChange(false);
      }
      if (e.key === "Tab") {
        const nodes = dialogRef.current?.querySelectorAll<HTMLElement>(
          "button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])"
        );
        if (!nodes || nodes.length === 0) return;
        const list = Array.from(nodes);
        const index = list.indexOf(document.activeElement as HTMLElement);
        if (e.shiftKey) {
          if (index === 0) {
            e.preventDefault();
            list[list.length - 1].focus();
          }
        } else if (index === list.length - 1) {
          e.preventDefault();
          list[0].focus();
        }
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      lastFocused.current?.focus();
    };
  }, [open, onOpenChange]);

  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="feedback-title"
      aria-describedby="feedback-desc"
      className="fixed inset-0 z-50 flex justify-end bg-black/40"
    >
      <div
        ref={dialogRef}
        className="h-full w-full max-w-md glass glass-card border-l p-4 overflow-y-auto"
      >
        <DialogTitle id="feedback-title" className="text-lg font-semibold">
          Détail du feedback
        </DialogTitle>
        {item ? (
          <div id="feedback-desc" className="mt-3 space-y-3">
            <div className="flex items-start justify-between gap-2">
              <div>
                <h3 className="font-medium">{item.title}</h3>
                <p className="text-sm text-muted-foreground">
                  Créé le {new Date(item.createdAt).toLocaleString()}
                </p>
              </div>
              <Badge criticity={item.criticity} />
            </div>
            {item.summary && <p className="text-sm">{item.summary}</p>}
            {item.runId && (
              <div>
                <Link
                  href={`/runs/${item.runId}${item.sourceAnchor || ""}`}
                  className="underline focus:outline-none focus-visible:ring-2 focus-visible:ring-focus rounded"
                >
                  Voir dans le run
                </Link>
              </div>
            )}
            <div className="pt-2 flex justify-end gap-2">
              <ClayButton size="sm" onClick={() => onOpenChange(false)}>Fermer</ClayButton>
              <ClayButton size="sm" variant="primary"
                onClick={() => {
                  if (item && onResolve) onResolve(item.id);
                  toast("Feedback marqué comme traité");
                }}
                disabled={resolving || item.resolved}
                aria-disabled={resolving || item.resolved}
                aria-label={item.resolved ? "Déjà traité" : "Marquer comme traité"}
              >
                {item.resolved ? "Traité" : "Marquer comme traité"}
              </ClayButton>
            </div>
          </div>
        ) : (
          <div className="mt-3" id="feedback-desc">
            <div className="h-6 w-40 animate-pulse rounded bg-muted" role="status" aria-label="Chargement..." />
            <div className="mt-2 h-4 w-64 animate-pulse rounded bg-muted" role="status" aria-label="Chargement..." />
            <div className="mt-2 h-32 w-full animate-pulse rounded bg-muted" role="status" aria-label="Chargement..." />
          </div>
        )}
      </div>
    </div>
  );
}

export default FeedbackPanel;
