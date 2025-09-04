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

export function LatencyChart({ data }: { data: LatencyPoint[] }) {
  const id = React.useId();
  return (
    <div className="h-64 w-full" tabIndex={0} aria-describedby={id}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Area type="monotone" dataKey="p95" stroke="#f87171" fill="#fecaca" />
          <Line type="monotone" dataKey="p50" stroke="#8884d8" strokeWidth={2} />
        </AreaChart>
      </ResponsiveContainer>
      <p id={id} className="sr-only">
        Latence p50 et p95 dans le temps
      </p>
    </div>
  );
}

