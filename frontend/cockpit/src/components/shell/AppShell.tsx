"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Play,
  Users,
  Map,
  ListCheck,
  Settings as SettingsIcon,
} from "lucide-react";
import { SidebarItem } from "@/ui/SidebarItem";
import { baseFocusRing } from "@/ui/theme";
import { cn } from "@/lib/utils";

interface AppShellProps {
  children: React.ReactNode;
}

const NAV_ITEMS = [
  { href: "/dashboard", label: "Aperçu", icon: LayoutDashboard, accent: "indigo" as const },
  { href: "/runs", label: "Runs", icon: Play, accent: "indigo" as const },
  { href: "/agents", label: "Agents", icon: Users, accent: "emerald" as const },
  { href: "/plans", label: "Plans", icon: Map, accent: "cyan" as const },
  { href: "/tasks", label: "Tâches", icon: ListCheck, accent: "cyan" as const },
  { href: "/settings", label: "Réglages", icon: SettingsIcon, accent: "amber" as const },
];

export function AppShell({ children }: AppShellProps) {
  const router = useRouter();
  const pathname = usePathname();

  return (
    <div className="flex min-h-screen bg-[var(--bg)] text-[var(--text)]">
      <aside className="hidden h-screen w-64 flex-col gap-3 border-r border-slate-800 bg-[#1C1E26] p-4 md:flex">
        <div className="text-lg font-semibold">Cockpit</div>
        <nav aria-label="Navigation principale" className="flex flex-col gap-2">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return (
              <SidebarItem
                key={item.href}
                label={item.label}
                accent={item.accent}
                icon={<Icon className="h-5 w-5" />}
                active={active}
                onClick={() => router.push(item.href)}
              />
            );
          })}
        </nav>
      </aside>
      <div className="flex flex-1 flex-col">
        <a
          href="#main"
          className="sr-only focus-visible:not-sr-only focus-visible:fixed focus-visible:left-4 focus-visible:top-4 focus-visible:z-50 focus-visible:rounded focus-visible:bg-[var(--surface)] focus-visible:px-3 focus-visible:py-2"
        >
          Aller au contenu
        </a>
        <main id="main" className="flex-1 overflow-y-auto p-4 pb-24 md:p-6 md:pb-6">
          {children}
        </main>
        <nav
          aria-label="Navigation mobile"
          className="fixed inset-x-0 bottom-0 z-30 flex items-center justify-around border-t border-slate-800 bg-[#1C1E26] p-2 md:hidden"
        >
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-label={item.label}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "flex h-12 w-12 items-center justify-center rounded-full text-sm transition",
                  baseFocusRing,
                  active ? "bg-slate-800 text-[color:var(--text)]" : "text-secondary"
                )}
              >
                <Icon className="h-5 w-5" />
              </Link>
            );
          })}
        </nav>
      </div>
    </div>
  );
}

export default AppShell;
