import * as React from "react";
import { cn } from "@/lib/utils";

interface KpiCardProps {
  title: string;
  value: string;
  className?: string;
  /** Choix du rendu visuel : par défaut (carte classique) ou glass (overlay translucide) */
  variant?: "default" | "glass";
}

export function KpiCard({
  title,
  value,
  className,
  variant = "default",
}: KpiCardProps) {
  return (
    <div
      role="group"
      aria-label={`KPI ${title}`}
      className={cn(
        "rounded-lg p-4 shadow-sm",
        variant === "glass"
          ? "glass glass-card"
          : "border bg-card text-card-foreground",
        className
      )}
    >
      <div className="text-sm text-muted-foreground">{title}</div>
      <div className="text-2xl font-bold">{value}</div>
    </div>
  );
}
