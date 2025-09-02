import * as React from 'react';
import {
  ComposedChart,
  Area,
  Line,
  CartesianGrid,
  ResponsiveContainer,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from 'recharts';

interface LatencyPoint {
  date: string;
  p50: number;
  p95: number;
}

const COLORS = {
  area: '#3b82f6',
  areaFill: '#bfdbfe',
  line: '#1e3a8a',
};

export default function LatencyChart({ data }: { data: LatencyPoint[] }): JSX.Element {
  const id = React.useId();
  return (
    <div className="h-64 w-full" tabIndex={0} aria-describedby={id}>
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Area type="monotone" dataKey="p50" name="p50" stroke={COLORS.area} fill={COLORS.areaFill} />
          <Line type="monotone" dataKey="p95" name="p95" stroke={COLORS.line} />
        </ComposedChart>
      </ResponsiveContainer>
      <p id={id} className="sr-only">
        Latence p50 en zone et p95 en ligne
      </p>
    </div>
  );
}
