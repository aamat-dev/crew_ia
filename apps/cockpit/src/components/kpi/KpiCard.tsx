"use client";
import * as React from "react";
import { motion, useReducedMotion } from "framer-motion";
import { ArrowDown, ArrowUp, LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface KpiCardProps {
  title: string;
  value: string | number;
  delta: number;
  icon: LucideIcon;
  className?: string;
}

export function KpiCard({ title, value, delta, icon: Icon, className }: KpiCardProps) {
  const reduceMotion = useReducedMotion();
  const deltaPositive = delta >= 0;
  const deltaIcon = deltaPositive ? ArrowUp : ArrowDown;
  const deltaColor = deltaPositive ? "text-green-600" : "text-red-600";

  return (
    <motion.div
      role="group"
      tabIndex={0}
      aria-label={`${title} ${value} (${deltaPositive ? "augmentation" : "diminution"} ${Math.abs(delta)}%)`}
      initial={reduceMotion ? false : { opacity: 0, scale: 0.95 }}
      animate={reduceMotion ? {} : { opacity: 1, scale: 1 }}
      whileHover={reduceMotion ? {} : { scale: 1.03 }}
      className={cn(
        "rounded-md border p-4 shadow-sm bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring",
        className
      )}
    >
      <div className="flex items-center justify-between">
        <div className="text-sm text-muted-foreground">{title}</div>
        <Icon aria-hidden className="h-4 w-4 text-muted-foreground" />
      </div>
      <div className="mt-2 text-2xl font-bold">{value}</div>
      <div className={cn("mt-1 flex items-center text-sm", deltaColor)}>
        {React.createElement(deltaIcon, { className: "mr-1 h-3 w-3", "aria-hidden": true })}
        <span>{Math.abs(delta)}%</span>
      </div>
    </motion.div>
  );
}

