"use client";
import * as React from "react";
import { cn } from "@/lib/utils";

export type RunStatus = "completed" | "running" | "queued" | "failed" | "paused" | string;

const STYLES: Record<string, string> = {
  completed: "bg-emerald-50 text-emerald-700",
  running: "bg-indigo-50 text-indigo-700",
  queued: "bg-amber-50 text-amber-700",
  failed: "bg-rose-50 text-rose-700",
  paused: "bg-slate-100 text-slate-700",
  default: "bg-slate-100 text-slate-700",
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

