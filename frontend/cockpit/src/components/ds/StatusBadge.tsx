"use client";
import * as React from "react";
import { cn } from "@/lib/utils";

export type RunStatus = "completed" | "running" | "queued" | "failed" | "paused" | string;

const STYLES: Record<string, string> = {
  completed: "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30",
  running: "bg-indigo-500/15 text-indigo-300 border border-indigo-500/30",
  queued: "bg-amber-500/15 text-amber-300 border border-amber-500/30",
  failed: "bg-rose-500/15 text-rose-300 border border-rose-500/30",
  paused: "bg-slate-500/15 text-slate-300 border border-slate-500/30",
  default: "bg-slate-500/15 text-slate-300 border border-slate-500/30",
};

const LABELS: Record<string, string> = {
  completed: "Terminé",
  running: "En cours",
  queued: "En attente",
  failed: "Échec",
  paused: "En pause",
};

interface StatusBadgeProps {
  status: RunStatus;
  label?: string;
  className?: string;
  pulseRunning?: boolean;
}

export function StatusBadge({ status, label, className, pulseRunning = true }: StatusBadgeProps) {
  const key = (status || "").toLowerCase();
  const base = STYLES[key] || STYLES.default;
  const text = label ?? LABELS[key] ?? status ?? "";
  const pulse = key === "running" && pulseRunning ? "animate-pulse" : "";
  return (
    <span className={cn("rounded px-2 py-1 text-xs", base, pulse, className)}>{text}</span>
  );
}

export default StatusBadge;
