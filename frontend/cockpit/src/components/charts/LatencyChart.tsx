"use client";
import * as React from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface LatencyPoint {
  date: string;
  p50: number;
  p95: number;
}

export function LatencyChart({ data, label = "Graphique de latence" }: { data: LatencyPoint[]; label?: string }) {
  const id = React.useId();
  return (
    <div className="h-64 w-full" tabIndex={0} aria-describedby={id} role="img" aria-label={label}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <CartesianGrid strokeOpacity={0.15} stroke="#94A3B8" />
          <XAxis dataKey="date" tick={{ fill: '#94A3B8' }} tickLine={false} axisLine={{ stroke: '#475569' }} />
          <YAxis tick={{ fill: '#94A3B8' }} tickLine={false} axisLine={{ stroke: '#475569' }} />
          <Tooltip
            contentStyle={{
              background: 'rgba(28,30,38,0.95)',
              border: '1px solid rgba(148,163,184,0.25)',
              borderRadius: 12,
              padding: '8px 12px',
              color: '#F1F5F9',
            }}
            labelStyle={{ color: '#F1F5F9' }}
            itemStyle={{ color: '#CBD5E1' }}
          />
          <Area type="monotone" dataKey="p95" stroke="#f87171" fill="#fecdd3" />
          <Line type="monotone" dataKey="p50" stroke="#818cf8" strokeWidth={2} />
        </AreaChart>
      </ResponsiveContainer>
      <p id={id} className="sr-only">{label}</p>
    </div>
  );
}
