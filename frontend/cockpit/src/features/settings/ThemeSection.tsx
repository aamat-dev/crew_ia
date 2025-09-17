"use client";

import * as React from "react";
import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { onToggleTheme } from "@/ui/HeaderBar";
import { baseFocusRing } from "@/ui/theme";
import { cn } from "@/lib/utils";

type ThemeValue = "light" | "dark";

export function ThemeSection() {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => setMounted(true), []);

  const current: ThemeValue = resolvedTheme === "light" ? "light" : "dark";
  const isDark = current === "dark";

  return (
    <section className="surface shadow-card p-4 space-y-3">
      <div className="space-y-1">
        <h2 className="text-lg font-semibold text-[color:var(--text)]">Thème</h2>
        <p className="text-sm text-secondary">Choisissez entre le mode clair et anthracite.</p>
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={isDark}
        onClick={() => mounted && onToggleTheme(current, setTheme as (value: ThemeValue) => void)}
        className={cn(
          "flex items-center justify-between rounded-2xl px-4 py-3 transition",
          "bg-slate-800/60 text-[color:var(--text)]",
          baseFocusRing
        )}
      >
        <span className="flex items-center gap-3 text-sm font-medium">
          {mounted && isDark ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
          {mounted && isDark ? "Mode sombre actif" : "Mode clair actif"}
        </span>
        <span
          aria-hidden
          className={cn(
            "relative h-6 w-12 rounded-full bg-slate-700",
            isDark ? "pl-6" : "pl-1"
          )}
        >
          <span className="absolute top-1 h-4 w-4 rounded-full bg-white transition-all" style={{ left: isDark ? "calc(100% - 1.5rem)" : "0.25rem" }} />
        </span>
      </button>
    </section>
  );
}

export default ThemeSection;
