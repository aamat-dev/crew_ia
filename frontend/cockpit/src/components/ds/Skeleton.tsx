"use client";
import { cn } from "@/lib/utils";
import * as React from "react";

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      role="status"
      aria-label="Chargement..."
      className={cn("animate-pulse rounded-md bg-muted", className)}
    />
  );
}

