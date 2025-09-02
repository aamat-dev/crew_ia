import * as React from 'react';
import {
  BarChart,
  Bar,
  CartesianGrid,
  ResponsiveContainer,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from 'recharts';

interface FeedbackPoint {
  date: string;
  positive: number;
  neutral: number;
  negative: number;
}

const COLORS = {
  positive: '#4ade80',
  neutral: '#facc15',
  negative: '#f87171',
};

export default function FeedbackChart({ data }: { data: FeedbackPoint[] }): JSX.Element {
  const id = React.useId();
  return (
    <div className="h-64 w-full" tabIndex={0} aria-describedby={id}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey="positive" stackId="a" fill={COLORS.positive} name="Positif" />
          <Bar dataKey="neutral" stackId="a" fill={COLORS.neutral} name="Neutre" />
          <Bar dataKey="negative" stackId="a" fill={COLORS.negative} name="Négatif" />
        </BarChart>
      </ResponsiveContainer>
      <p id={id} className="sr-only">
        Répartition des feedbacks positifs, neutres et négatifs
      </p>
    </div>
  );
}
