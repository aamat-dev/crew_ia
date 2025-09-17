"use client";

import * as React from "react";
import { Accent, accentGradient, accentHoverGlow, accentRing, baseFocusRing } from "@/ui/theme";
import { cn } from "@/lib/utils";

type SidebarAccent = Exclude<Accent, "rose">;

export type SidebarItemProps = {
  label: string;
  icon: React.ReactNode;
  accent: SidebarAccent;
  active?: boolean;
  onClick?: () => void;
};

export function SidebarItem({ label, icon, accent, active = false, onClick }: SidebarItemProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-current={active ? "page" : undefined}
      className={cn(
        "surface shadow-card w-full p-3 flex items-center gap-3 text-left text-sm transition-colors duration-150",
        "hover:bg-slate-700/40 hover:shadow-md",
        baseFocusRing,
        accentHoverGlow(accent),
        active &&
          cn(
            "ring-1 ring-offset-2 ring-offset-[var(--bg)]",
            accentRing(accent),
            "font-semibold text-[color:var(--text)]"
          )
      )}
    >
      <span
        aria-hidden
        className={cn(
          "grid h-9 w-9 place-content-center rounded-xl text-white",
          "bg-gradient-to-br",
          accentGradient(accent)
        )}
      >
        {icon}
      </span>
      <span className="hidden md:inline text-[color:var(--text)]">{label}</span>
    </button>
  );
}

export default SidebarItem;
