"use client";
import * as React from "react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

interface ThroughputPoint {
  date: string;
  value: number;
}

export function ThroughputChart({ data, label = "Graphique de throughput" }: { data: ThroughputPoint[]; label?: string }) {
  const id = React.useId();
  return (
    <div className="h-64 w-full text-indigo-400" tabIndex={0} aria-describedby={id} role="img" aria-label={label}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <defs>
            <linearGradient id={`thpt-${id}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#818CF8" stopOpacity={0.35} />
              <stop offset="100%" stopColor="#818CF8" stopOpacity={0} />
            </linearGradient>
          </defs>
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
          <Area type="monotone" dataKey="value" stroke="currentColor" strokeWidth={2} fill={`url(#thpt-${id})`} />
        </AreaChart>
      </ResponsiveContainer>
      <p id={id} className="sr-only">{label}</p>
    </div>
  );
}
