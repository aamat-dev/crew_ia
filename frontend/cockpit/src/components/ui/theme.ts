export type Accent = 'indigo' | 'cyan' | 'emerald' | 'amber' | 'rose';

export const ACCENT_GRADIENT = (accent: Accent) =>
  (
    accent === 'indigo' ? 'from-indigo-500 to-indigo-400' :
    accent === 'cyan' ? 'from-cyan-500 to-cyan-400' :
    accent === 'emerald' ? 'from-emerald-500 to-emerald-400' :
    accent === 'amber' ? 'from-amber-500 to-amber-400' :
    'from-rose-500 to-rose-400'
  );

export const ACCENT_RING = (accent: Accent) =>
  (
    accent === 'indigo' ? 'ring-[hsl(var(--indigo-500))]' :
    accent === 'cyan' ? 'ring-[hsl(var(--cyan-500))]' :
    accent === 'emerald' ? 'ring-[hsl(var(--emerald-500))]' :
    accent === 'amber' ? 'ring-[hsl(var(--amber-500))]' :
    'ring-[hsl(var(--rose-500))]'
  );

export const ACCENT_GLOW = (accent: Accent) =>
  (
    accent === 'indigo' ? 'shadow-glow-indigo' :
    accent === 'cyan' ? 'shadow-glow-cyan' :
    accent === 'emerald' ? 'shadow-glow-emerald' :
    accent === 'amber' ? 'shadow-glow-amber' :
    'shadow-glow-rose'
  );

export const CARD_BASE = 'bg-[#2A2D36] border border-slate-700 rounded-2xl';
export const CARD_SHADOW = 'shadow-card';
export const CARD_HOVER = (accent: Accent) => `hover:${ACCENT_GLOW(accent)}`;
export const FOCUS_RING = 'focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-[hsl(var(--ring))] focus-visible:ring-offset-[#1C1E26]';

