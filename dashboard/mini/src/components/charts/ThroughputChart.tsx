import * as React from 'react';
import {
  LineChart,
  Line,
  CartesianGrid,
  ResponsiveContainer,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from 'recharts';

interface DataPoint {
  date: string;
  value: number;
}

const COLOR = '#3b82f6';

export default function ThroughputChart({ data }: { data: DataPoint[] }): JSX.Element {
  const id = React.useId();
  return (
    <div className="h-64 w-full" tabIndex={0} aria-describedby={id}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="value" stroke={COLOR} name="Throughput" />
        </LineChart>
      </ResponsiveContainer>
      <p id={id} className="sr-only">
        Évolution du throughput dans le temps
      </p>
    </div>
  );
}
