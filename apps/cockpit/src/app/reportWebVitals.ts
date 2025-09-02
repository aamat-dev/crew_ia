export function reportWebVitals(metric: any) {
  if (process.env.NODE_ENV !== "production") {
    return;
  }

  const body = {
    name: metric.name,
    id: metric.id,
    value: metric.value,
    delta: metric.delta,
    label: metric.label,
    path: window.location.pathname,
    userAgent: navigator.userAgent,
    timestamp: Date.now(),
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
  } catch (err) {
    // Erreurs ignorées
  }
}
