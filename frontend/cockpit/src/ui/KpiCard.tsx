"use client";

import * as React from "react";
import { motion } from "framer-motion";
import { Accent, accentGradient, accentHoverGlow, baseFocusRing } from "@/ui/theme";
import { cn } from "@/lib/utils";

export type KpiCardProps = {
  label: string;
  value?: string | number;
  delta?: string | number;
  accent?: Accent;
  icon: React.ReactNode;
  loading?: boolean;
  noData?: boolean;
  title?: string;
  className?: string;
  unit?: string;
};

const animation = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
};

export function KpiCard({
  label,
  title,
  value,
  delta,
  accent = "indigo",
  icon,
  loading = false,
  noData = false,
  className,
  unit,
}: KpiCardProps) {
  const displayLabel = label ?? title ?? "";
  const hasValue = value !== undefined && value !== null;
  const formattedValue =
    typeof value === "number" ? value.toLocaleString("fr-FR") : value;
  const formattedDelta =
    typeof delta === "number" ? `${Math.abs(delta)}%` : delta;
  const ariaLabel = noData ? `${displayLabel} - Aucune donnée` : undefined;
  return (
    <motion.div
      variants={animation}
      initial="initial"
      animate="animate"
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
      tabIndex={0}
      role="group"
      aria-busy={loading || undefined}
      aria-label={ariaLabel}
      className={cn(
        "relative surface shadow-card overflow-hidden p-5 flex flex-col gap-4",
        "transition-transform duration-200",
        accentHoverGlow(accent),
        baseFocusRing,
        className
      )}
    >
      <span aria-hidden className={cn("absolute inset-x-0 top-0 h-1 bg-gradient-to-r", accentGradient(accent))} />
      <span aria-hidden className={cn("pointer-events-none absolute inset-0 opacity-20 bg-gradient-to-br", accentGradient(accent))} />
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-secondary">{displayLabel}</p>
        </div>
        <span
          aria-hidden
          className={cn(
            "grid h-10 w-10 place-content-center rounded-xl text-white bg-gradient-to-br",
            accentGradient(accent)
          )}
        >
          {icon}
        </span>
      </div>
      {loading ? (
        <div className="space-y-3">
          <div className="h-9 w-24 rounded-lg bg-slate-700/40 animate-pulse" role="status" aria-label="Chargement" />
          <div className="h-4 w-20 rounded bg-slate-700/40 animate-pulse" role="status" aria-label="Chargement" />
        </div>
      ) : noData ? (
        <p className="text-sm text-secondary">Aucune donnée</p>
      ) : (
        <div className="space-y-3">
          {hasValue ? (
            <div className="text-4xl font-semibold text-[color:var(--text)]">
              {formattedValue}
              {unit ? <span className="ml-1 text-base align-top text-secondary">{unit}</span> : null}
            </div>
          ) : null}
          {formattedDelta ? (
            <span className="inline-flex items-center gap-2 rounded-full bg-slate-800 px-3 py-1 text-xs font-medium text-slate-300">
              {formattedDelta}
            </span>
          ) : null}
        </div>
      )}
    </motion.div>
  );
}

export default KpiCard;
