"use client";

import * as React from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  CartesianGrid,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Accent, ACCENT_COLORS } from "@/ui/theme";
import { cn } from "@/lib/utils";

export interface MetricChartProps<T extends Record<string, unknown>> {
  title: string;
  type: "area" | "bar";
  data: T[];
  xKey: keyof T;
  yKey: keyof T;
  accent?: Accent;
  className?: string;
}

const tooltipStyle: React.CSSProperties = {
  background: "#2A2D36",
  border: "1px solid #475569",
  borderRadius: 12,
  color: "#F1F5F9",
};

export function MetricChartCard<T extends Record<string, unknown>>({
  title,
  type,
  data,
  xKey,
  yKey,
  accent = "indigo",
  className,
}: MetricChartProps<T>) {
  const gradientId = React.useId();
  const accentColors = ACCENT_COLORS[accent];

  return (
    <section className={cn("surface shadow-card p-4 space-y-4", className)}>
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-[color:var(--text)]">{title}</h2>
      </div>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          {type === "area" ? (
            <AreaChart data={data} margin={{ top: 10, right: 16, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id={`${gradientId}-fill`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={accentColors[500]} stopOpacity={0.8} />
                  <stop offset="95%" stopColor={accentColors[500]} stopOpacity={0.05} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="#475569" strokeOpacity={0.15} vertical={false} />
              <XAxis
                dataKey={xKey as string}
                stroke="#94A3B8"
                tick={{ fill: "#94A3B8", fontSize: 12 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                stroke="#94A3B8"
                tick={{ fill: "#94A3B8", fontSize: 12 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                cursor={{ strokeDasharray: "3 3", stroke: accentColors[500] }}
                contentStyle={tooltipStyle}
                labelStyle={{ color: "#F1F5F9" }}
              />
              <Area
                type="monotone"
                dataKey={yKey as string}
                stroke={accentColors[500]}
                strokeWidth={3}
                fill={`url(#${gradientId}-fill)`}
                fillOpacity={1}
              />
            </AreaChart>
          ) : (
            <BarChart data={data} margin={{ top: 10, right: 16, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id={`${gradientId}-bar`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={accentColors[500]} stopOpacity={0.9} />
                  <stop offset="100%" stopColor={accentColors[400]} stopOpacity={0.6} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="#475569" strokeOpacity={0.15} vertical={false} />
              <XAxis
                dataKey={xKey as string}
                stroke="#94A3B8"
                tick={{ fill: "#94A3B8", fontSize: 12 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                stroke="#94A3B8"
                tick={{ fill: "#94A3B8", fontSize: 12 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                cursor={{ fill: "rgba(148, 163, 184, 0.12)" }}
                contentStyle={tooltipStyle}
                labelStyle={{ color: "#F1F5F9" }}
              />
              <Bar dataKey={yKey as string} fill={`url(#${gradientId}-bar)`} radius={[6, 6, 0, 0]} />
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
    </section>
  );
}

export default MetricChartCard;
