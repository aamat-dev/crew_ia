"use client";
import * as React from "react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { ACCENT_GRADIENT, ACCENT_RING, ACCENT_GLOW, FOCUS_RING } from "@/components/ui/theme";

export type SidebarAccent = 'indigo'|'cyan'|'emerald'|'amber';

interface SidebarItemProps {
  href: string;
  label: string;
  icon: React.ReactNode;
  accent: SidebarAccent;
  active?: boolean;
}

export function SidebarItem({ href, label, icon, accent, active }: SidebarItemProps) {
  return (
    <Link
      href={href}
      aria-current={active ? "page" : undefined}
      className={cn(
        "flex items-center gap-3 p-3 rounded-2xl bg-[#2A2D36] border border-slate-700 transition md:justify-start justify-center hover:bg-slate-700/40",
        FOCUS_RING,
        active && cn("ring-1", ACCENT_RING(accent), ACCENT_GLOW(accent)),
        `hover:${ACCENT_GLOW(accent)}`
      )}
    >
      <span className={cn("grid h-9 w-9 place-content-center rounded-xl text-white bg-gradient-to-br", ACCENT_GRADIENT(accent))}>
        {icon}
      </span>
      <span className="hidden text-slate-100 md:inline">{label}</span>
    </Link>
  );
}

export default SidebarItem;
