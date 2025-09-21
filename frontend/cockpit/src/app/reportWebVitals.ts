import type { NextWebVitalsMetric } from "next/app";

type MetricWithDelta = NextWebVitalsMetric & { delta: number };

const hasDelta = (metric: NextWebVitalsMetric): metric is MetricWithDelta => {
  return typeof (metric as { delta?: unknown }).delta === "number";
};

export function reportWebVitals(metric: NextWebVitalsMetric) {
  if (process.env.NODE_ENV !== "production") {
    return;
  }

  const delta = hasDelta(metric) ? metric.delta : undefined;

  const body = {
    name: metric.name,
    id: metric.id,
    value: metric.value,
    label: metric.label,
    path: window.location.pathname,
    userAgent: navigator.userAgent,
    timestamp: Date.now(),
    ...(delta !== undefined ? { delta } : {}),
  };

  const url = "/api/vitals";
  try {
    if (navigator.sendBeacon) {
      navigator.sendBeacon(url, JSON.stringify(body));
    } else {
      fetch(url, {
        method: "POST",
        body: JSON.stringify(body),
        keepalive: true,
        headers: { "Content-Type": "application/json" },
      });
    }
  } catch {
    // Erreurs ignorées
  }
}
