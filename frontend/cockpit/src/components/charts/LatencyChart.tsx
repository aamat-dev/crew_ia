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
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Area type="monotone" dataKey="p95" stroke="#f43f5e" fill="#fecdd3" />
          <Line type="monotone" dataKey="p50" stroke="#4f46e5" strokeWidth={2} />
        </AreaChart>
      </ResponsiveContainer>
      <p id={id} className="sr-only">{label}</p>
    </div>
  );
}
