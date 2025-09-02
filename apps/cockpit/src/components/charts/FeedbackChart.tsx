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

export function FeedbackChart({ data }: { data: FeedbackPoint[] }) {
  const id = React.useId();
  return (
    <div className="h-64 w-full" tabIndex={0} aria-describedby={id}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="positive" stackId="a" fill="#4ade80" />
          <Bar dataKey="neutral" stackId="a" fill="#facc15" />
          <Bar dataKey="negative" stackId="a" fill="#f87171" />
        </BarChart>
      </ResponsiveContainer>
      <p id={id} className="sr-only">
        Répartition des feedbacks positifs, neutres et négatifs
      </p>
    </div>
  );
}

