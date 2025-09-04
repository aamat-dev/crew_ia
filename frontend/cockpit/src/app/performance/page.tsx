"use client";

import { useEffect, useRef, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

interface Totals {
  [name: string]: { count: number; mean: number; p75: number; p95: number };
}
interface TimelinePoint {
  timestamp: number;
  p50: number;
  p75: number;
  p95: number;
}
interface Timeline {
  [name: string]: TimelinePoint[];
}
interface PathMetric {
  p75: number;
  count: number;
}
interface PathData {
  path: string;
  metrics: Record<string, PathMetric>;
}
interface ApiData {
  totals: Totals;
  timeline: Timeline;
  paths: PathData[];
}

export default function PerformancePage() {
  const [data, setData] = useState<ApiData | null>(null);
  const [prev, setPrev] = useState<ApiData | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const toastRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    async function load() {
      const res = await fetch("/api/vitals");
      const json = await res.json();
      setData(json);
      const resPrev = await fetch(
        "/api/vitals?range=" + 2 * 24 * 60 * 60 * 1000
      );
      const jsonPrev = await resPrev.json();
      setPrev(jsonPrev);

      const t = json.totals;
      if (t?.LCP?.p75 > 2500) setToast("LCP supérieur à 2.5s");
      else if ((t?.INP?.p75 ?? t?.FID?.p75 ?? 0) > 200)
        setToast("INP supérieur à 200ms");
      else if (t?.CLS?.p75 > 0.1) setToast("CLS supérieur à 0.1");
    }
    load();
  }, []);

  useEffect(() => {
    if (toastRef.current) {
      toastRef.current.focus();
    }
  }, [toast]);

  if (!data) return <p>Chargement…</p>;

  const alerts: string[] = [];
  if (data.totals.LCP?.p75 > 2500) alerts.push("LCP");
  if ((data.totals.INP?.p75 ?? data.totals.FID?.p75 ?? 0) > 200)
    alerts.push("INP");
  if (data.totals.CLS?.p75 > 0.1) alerts.push("CLS");

  const trend = (metric: string) => {
    if (!prev) return 0;
    const curr = data.totals[metric]?.p75 ?? 0;
    const prevVal = prev.totals[metric]?.p75 ?? 0;
    return curr - prevVal;
  };

  return (
    <div className="space-y-8 p-4">
      {alerts.length > 0 && (
        <div className="bg-yellow-100 p-2 rounded" role="alert">
          {alerts.join(", ")} dépassent les seuils Core Web Vitals
        </div>
      )}

      {toast && (
        <div
          ref={toastRef}
          tabIndex={0}
          role="status"
          className="fixed top-4 right-4 bg-gray-800 text-white p-2 rounded shadow"
        >
          {toast}
        </div>
      )}

      <section
        className="grid gap-4 md:grid-cols-3"
        aria-label="Indicateurs clés des Web Vitals"
      >
        {["LCP", "INP", "CLS"].map((m) => {
          const value = data.totals[m]?.p75 ?? 0;
          return (
            <div key={m} className="border p-4 rounded" tabIndex={0}>
              <h2 className="text-lg font-semibold">{m}</h2>
              <p>{value.toFixed(2)}</p>
              <p className="text-sm text-gray-500">
                Δ {trend(m).toFixed(2)}
              </p>
            </div>
          );
        })}
      </section>

      <section className="space-y-6" aria-label="Graphiques des Web Vitals">
        {Object.entries(data.timeline).map(([name, points]) => (
          <div key={name} className="h-64" tabIndex={0}>
            <h3 className="font-medium">{name}</h3>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={points} aria-hidden="true">
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={(n) => new Date(n).toLocaleTimeString()}
                />
                <YAxis />
                <Tooltip labelFormatter={(n) => new Date(n).toLocaleString()} />
                <Legend />
                <Line type="monotone" dataKey="p50" stroke="#8884d8" />
                <Line type="monotone" dataKey="p75" stroke="#82ca9d" />
                <Line type="monotone" dataKey="p95" stroke="#ffc658" />
              </LineChart>
            </ResponsiveContainer>
            <span className="sr-only">Graphique de {name}</span>
          </div>
        ))}
      </section>

      <section aria-label="Performances par page">
        <table className="w-full text-left border" role="table">
          <thead>
            <tr>
              <th className="p-2 border">Page</th>
              <th className="p-2 border">LCP p75</th>
              <th className="p-2 border">INP/FID p75</th>
              <th className="p-2 border">CLS p75</th>
              <th className="p-2 border">Échantillons</th>
            </tr>
          </thead>
          <tbody>
            {data.paths.map((p) => (
              <tr key={p.path} tabIndex={0}>
                <td className="p-2 border">{p.path}</td>
                <td className="p-2 border">
                  {p.metrics.LCP ? p.metrics.LCP.p75.toFixed(2) : "-"}
                </td>
                <td className="p-2 border">
                  {p.metrics.INP
                    ? p.metrics.INP.p75.toFixed(2)
                    : p.metrics.FID
                    ? p.metrics.FID.p75.toFixed(2)
                    : "-"}
                </td>
                <td className="p-2 border">
                  {p.metrics.CLS ? p.metrics.CLS.p75.toFixed(2) : "-"}
                </td>
                <td className="p-2 border">
                  {p.metrics.LCP ? p.metrics.LCP.count : 0}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
