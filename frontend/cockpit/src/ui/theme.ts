export type Accent = "indigo" | "cyan" | "emerald" | "amber" | "rose";
export type Status = "completed" | "running" | "queued" | "failed" | "paused";

const accentVariable = (accent: Accent, shade: "400" | "500") => `var(--accent-${accent}-${shade})`;

export const ACCENT_COLORS: Record<Accent, { 500: string; 400: string; glow: string }> = {
  indigo: { 500: "#6366F1", 400: "#818CF8", glow: "rgba(99,102,241,0.35)" },
  cyan: { 500: "#22D3EE", 400: "#67E8F9", glow: "rgba(34,211,238,0.35)" },
  emerald: { 500: "#34D399", 400: "#6EE7B7", glow: "rgba(52,211,153,0.35)" },
  amber: { 500: "#FBBF24", 400: "#FCD34D", glow: "rgba(251,191,36,0.35)" },
  rose: { 500: "#F87171", 400: "#FDA4AF", glow: "rgba(248,113,113,0.35)" },
};

export const baseFocusRing =
  "focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-indigo-500/60 focus-visible:ring-offset-[var(--bg)]";

export const accentGradient = (accent: Accent) =>
  `bg-gradient-to-br from-[${accentVariable(accent, "500")}] to-[${accentVariable(accent, "400")}]`;

export const accentHoverGlow = (accent: Accent) => `hover-glow-${accent}`;

export const accentRing = (accent: Accent) => `ring-[color:${accentVariable(accent, "400")}]`;

export const accentText = (accent: Accent) => `text-[${accentVariable(accent, "400")}]`;

export const accentSolidBg = (accent: Accent) => `bg-[${accentVariable(accent, "500")}]`;

export const STATUS_ACCENT: Record<Status, Accent | "rose"> = {
  completed: "emerald",
  running: "indigo",
  queued: "amber",
  failed: "rose",
  paused: "cyan",
};

export const STATUS_LABEL: Record<Status, string> = {
  completed: "Terminé",
  running: "En cours",
  queued: "En file",
  failed: "Échec",
  paused: "En pause",
};

export const statusGradient = (status: Status) => accentGradient(STATUS_ACCENT[status]);
