import * as React from "react";
import { cn } from "@/lib/utils";

interface KpiCardProps {
  title: string;
  value: string;
  className?: string;
}

export function KpiCard({ title, value, className }: KpiCardProps) {
  return (
    <div
      role="group"
      aria-label={`KPI ${title}`}
      className={cn(
        "rounded-lg border p-4 shadow-sm bg-card text-card-foreground",
        className
      )}
    >
      <div className="text-sm text-muted-foreground">{title}</div>
      <div className="text-2xl font-bold">{value}</div>
    </div>
  );
}
