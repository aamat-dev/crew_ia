import { z } from "zod";

export const vitalSchema = z.object({
  name: z.string(),
  id: z.string(),
  value: z.number(),
  delta: z.number(),
  label: z.string(),
  path: z.string(),
  userAgent: z.string().optional(),
  timestamp: z.number(),
});

export type Vital = z.infer<typeof vitalSchema>;

const WINDOW = 24 * 60 * 60 * 1000; // 24h
const store: Vital[] = [];

function cleanup() {
  const cutoff = Date.now() - WINDOW;
  while (store.length && store[0].timestamp < cutoff) {
    store.shift();
  }
}

export function addVital(vital: Vital) {
  store.push(vital);
  cleanup();
}

export function getVitals(range: number = WINDOW) {
  cleanup();
  const cutoff = Date.now() - range;
  return store.filter((v) => v.timestamp >= cutoff);
}

function quantile(values: number[], q: number) {
  if (values.length === 0) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const pos = (sorted.length - 1) * q;
  const base = Math.floor(pos);
  const rest = pos - base;
  if (sorted[base + 1] !== undefined) {
    return sorted[base] + rest * (sorted[base + 1] - sorted[base]);
  }
  return sorted[base];
}

export function aggregate(range: number = WINDOW) {
  const vitals = getVitals(range);
  const byName: Record<string, Vital[]> = {};
  const byPath: Record<string, Record<string, Vital[]>> = {};

  vitals.forEach((v) => {
    (byName[v.name] ||= []).push(v);
    (byPath[v.path] ||= {});
    (byPath[v.path][v.name] ||= []).push(v);
  });

  const totals = Object.fromEntries(
    Object.entries(byName).map(([name, arr]) => {
      const values = arr.map((v) => v.value);
      return [
        name,
        {
          count: values.length,
          mean: values.reduce((s, n) => s + n, 0) / values.length,
          p75: quantile(values, 0.75),
          p95: quantile(values, 0.95),
        },
      ];
    })
  );

  const timeline: Record<string, { timestamp: number; p50: number; p75: number; p95: number }[]> = {};
  Object.entries(byName).forEach(([name, arr]) => {
    const buckets: Record<number, number[]> = {};
    arr.forEach((v) => {
      const bucket = Math.floor(v.timestamp / 600000) * 600000; // 10m
      (buckets[bucket] ||= []).push(v.value);
    });
    timeline[name] = Object.entries(buckets)
      .sort((a, b) => Number(a[0]) - Number(b[0]))
      .map(([ts, values]) => ({
        timestamp: Number(ts),
        p50: quantile(values, 0.5),
        p75: quantile(values, 0.75),
        p95: quantile(values, 0.95),
      }));
  });

  const paths = Object.entries(byPath).map(([path, names]) => ({
    path,
    metrics: Object.fromEntries(
      Object.entries(names).map(([name, arr]) => {
        const values = arr.map((v) => v.value);
        return [name, { p75: quantile(values, 0.75), count: values.length }];
      })
    ),
  }));

  return { totals, timeline, paths };
}
