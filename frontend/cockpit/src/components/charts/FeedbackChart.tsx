"use client";
import * as React from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface FeedbackPoint {
  date: string;
  positive: number;
  neutral: number;
  negative: number;
}

export function FeedbackChart({ data, label = "Graphique de répartition des feedbacks" }: { data: FeedbackPoint[]; label?: string }) {
  const id = React.useId();
  return (
    <div className="h-64 w-full" tabIndex={0} aria-describedby={id} role="img" aria-label={label}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
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
          <Bar dataKey="positive" stackId="a" fill="#22d3ee" radius={[8,8,0,0]} />
          <Bar dataKey="neutral" stackId="a" fill="#94a3b8" radius={[8,8,0,0]} />
          <Bar dataKey="negative" stackId="a" fill="#f87171" radius={[8,8,0,0]} />
        </BarChart>
      </ResponsiveContainer>
      <p id={id} className="sr-only">{label}</p>
    </div>
  );
}
