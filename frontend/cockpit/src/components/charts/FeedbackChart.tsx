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
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip
            contentStyle={{
              background: '#ffffff',
              border: '1px solid #e5e7eb',
              borderRadius: 12,
              padding: '8px 12px',
            }}
            labelStyle={{ color: '#0f172a' }}
            itemStyle={{ color: '#334155' }}
          />
          <Bar dataKey="positive" stackId="a" fill="#06b6d4" />
          <Bar dataKey="neutral" stackId="a" fill="#94a3b8" />
          <Bar dataKey="negative" stackId="a" fill="#f43f5e" />
        </BarChart>
      </ResponsiveContainer>
      <p id={id} className="sr-only">{label}</p>
    </div>
  );
}
