"use client";
import * as React from "react";
import { motion, useReducedMotion } from "framer-motion";
import { ArrowDown, ArrowUp, LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface KpiCardProps {
  title: string;
  value?: string | number;
  /** Variation en pourcentage (facultatif) */
  delta?: number;
  /** Icône illustrant le KPI (facultatif) */
  icon?: LucideIcon;
  className?: string;
  /** Choix du rendu visuel : par défaut ou glass */
  variant?: "default" | "glass";
  /** Affiche un état de chargement squelettique */
  loading?: boolean;
  /** Affiche un état "aucune donnée" */
  noData?: boolean;
  /** Indication additionnelle (affichée comme title) */
  hint?: string;
  /** Suffixe d'unité pour la valeur (ex: %) */
  unit?: string;
}

export function KpiCard({
  title,
  value,
  delta,
  icon: Icon,
  className,
  variant = "default",
  loading = false,
  noData = false,
  hint,
  unit,
}: KpiCardProps) {
  const reduceMotion = useReducedMotion();
  const deltaPositive = (delta ?? 0) >= 0;
  const DeltaIcon = deltaPositive ? ArrowUp : ArrowDown;
  const deltaColor = deltaPositive ? "text-green-600" : "text-red-600";

  return (
    <motion.div
      role="group"
      tabIndex={0}
      title={hint}
      aria-busy={loading || undefined}
      aria-label={(() => {
        if (loading) return `${title} (chargement)`;
        if (noData) return `${title} (aucune donnée)`;
        if (value === undefined || value === null) return `${title} (indisponible)`;
        const v = unit ? `${value}${unit}` : `${value}`;
        return delta !== undefined
          ? `${title} ${v} (${deltaPositive ? "augmentation" : "diminution"} ${Math.abs(delta)}%)`
          : `${title} ${v}`;
      })()}
      initial={reduceMotion ? false : { opacity: 0, scale: 0.98 }}
      animate={reduceMotion ? {} : { opacity: 1, scale: 1 }}
      whileHover={reduceMotion ? {} : { scale: 1.05 }}
      transition={{ duration: 0.2 }}
      className={cn(
        "rounded-2xl p-4 text-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-focus",
        variant === "glass"
          ? "glass glass-card"
          : "clay-card",
        className
      )}
    >
      <div className="flex items-center justify-between">
        <div className="text-sm text-slate-500">{title}</div>
        {Icon && <Icon aria-hidden className="h-4 w-4 text-slate-500" />}
      </div>
      {loading ? (
        <div className="mt-2">
          <div className="h-7 w-24 animate-pulse rounded bg-muted" role="status" aria-label="Chargement..." />
          <div className="mt-2 h-3 w-16 animate-pulse rounded bg-muted" role="status" aria-label="Chargement..." />
        </div>
      ) : noData ? (
        <div className="mt-2 text-sm text-muted-foreground">Aucune donnée</div>
      ) : (
        <>
          <div className="mt-2 text-2xl font-bold">
            {unit ? (
              <span>
                {value}
                <span className="ml-1 text-base align-text-top opacity-80">{unit}</span>
              </span>
            ) : (
              value
            )}
          </div>
          {delta !== undefined && (
            <div className={cn("mt-1 flex items-center text-sm", deltaColor)}>
              <DeltaIcon className="mr-1 h-3 w-3" aria-hidden />
              <span>{Math.abs(delta)}%</span>
            </div>
          )}
        </>
      )}
    </motion.div>
  );
}
