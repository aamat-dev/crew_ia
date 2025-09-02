import * as React from "react";
import { cn } from "@/lib/utils";

interface KpiCardProps {
  title: string;
  value: string;
  className?: string;
  variant?: "default" | "glass";
}

export function KpiCard({ title, value, className, variant = "default" }: KpiCardProps) {
  return (
    <div
      role="group"
      aria-label={`KPI ${title}`}
      className={cn(
        "rounded-md p-4 text-foreground",
        variant === "glass"
          ? "glass glass-card"
          : "border bg-background shadow-sm",
        className
      )}
    >
      <div className="text-sm text-muted-foreground">{title}</div>
      <div className="text-2xl font-bold">{value}</div>
    </div>
  );
}
