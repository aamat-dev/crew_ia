"use client";
import * as React from "react";
import { motion, useReducedMotion } from "framer-motion";
import { ArrowDown, ArrowUp, LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface KpiCardProps {
  /** Nouveau: étiquette du KPI. 'title' reste supporté pour compat. */
  label?: string;
  /** Compat: ancien nom */
  title?: string;
  value?: string | number;
  /** Variation en pourcentage (facultatif) */
  delta?: number;
  /** Icône illustrant le KPI (facultatif) */
  icon?: LucideIcon;
  /** Accent de couleur */
  accent?: "indigo" | "cyan" | "emerald" | "amber" | "rose";
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
  label,
  title,
  value,
  delta,
  icon: Icon,
  accent = "indigo",
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
  const deltaColor = deltaPositive ? "text-emerald-400" : "text-rose-400";
  const name = label ?? title ?? "";

  return (
    <motion.div
      role="group"
      tabIndex={0}
      title={hint}
      aria-busy={loading || undefined}
      aria-label={(() => {
        if (loading) return `${name} (chargement)`;
        if (noData) return `${name} (aucune donnée)`;
        if (value === undefined || value === null) return `${name} (indisponible)`;
        const v = unit ? `${value}${unit}` : `${value}`;
        return delta !== undefined
          ? `${name} ${v} (${deltaPositive ? "augmentation" : "diminution"} ${Math.abs(delta)}%)`
          : `${name} ${v}`;
      })()}
      initial={reduceMotion ? false : { opacity: 0, scale: 0.98 }}
      animate={reduceMotion ? {} : { opacity: 1, scale: 1 }}
      whileHover={reduceMotion ? {} : { scale: 1.05 }}
      transition={{ duration: 0.15 }}
      className={cn(
        "relative overflow-hidden rounded-2xl p-4 text-slate-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--ring))]",
        variant === "glass"
          ? "glass glass-card"
          : "clay-card",
        className
      )}
    >
      {/* Bandeau supérieur 1px dégradé */}
      <div
        aria-hidden
        className={cn(
          "pointer-events-none absolute left-0 top-0 h-1 w-full bg-gradient-to-r",
          accent === "indigo" && "from-indigo-500 to-indigo-400",
          accent === "cyan" && "from-cyan-500 to-cyan-400",
          accent === "emerald" && "from-emerald-500 to-emerald-400",
          accent === "amber" && "from-amber-500 to-amber-400",
          accent === "rose" && "from-rose-500 to-rose-400"
        )}
      />
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="text-sm text-slate-300">{name}</div>
        </div>
        {Icon && (
          <span
            className={cn(
              "grid place-content-center rounded-xl p-2 text-white bg-gradient-to-br",
              "h-9 w-9",
              accent === "indigo" && "from-indigo-500 to-indigo-400",
              accent === "cyan" && "from-cyan-500 to-cyan-400",
              accent === "emerald" && "from-emerald-500 to-emerald-400",
              accent === "amber" && "from-amber-500 to-amber-400",
              accent === "rose" && "from-rose-500 to-rose-400"
            )}
          >
            <Icon aria-hidden className="h-4 w-4" />
          </span>
        )}
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
          <div className="mt-2 text-3xl font-bold text-slate-50">
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
            <div className={cn("mt-1 flex items-center text-xs", deltaColor)}>
              <DeltaIcon className="mr-1 h-3 w-3" aria-hidden />
              <span>{Math.abs(delta)}%</span>
            </div>
          )}
        </>
      )}
    </motion.div>
  );
}
