"use client";
import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  ListCheck,
  Map,
  Play,
  Settings as SettingsIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Header } from "./Header";
import { ShortcutsCheatsheet } from "@/components/shortcuts/ShortcutsCheatsheet";
import { useGlobalShortcuts } from "@/hooks/useGlobalShortcuts";

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();
  const [commandPaletteOpen, setCommandPaletteOpen] = React.useState(false);
  const [cheatsheetOpen, setCheatsheetOpen] = React.useState(false);
  const searchRef = React.useRef<HTMLInputElement>(null);

  useGlobalShortcuts({
    searchRef,
    onOpenCommandPalette: () => setCommandPaletteOpen(true),
    onOpenCheatsheet: () => setCheatsheetOpen(true),
  });

  const navItems = [
    { href: "/dashboard", label: "Aperçu", icon: LayoutDashboard, tone: "indigo" },
    { href: "/runs", label: "Runs", icon: Play, tone: "indigo" },
    { href: "/plans", label: "Plans", icon: Map, tone: "cyan" },
    { href: "/tasks", label: "Tâches", icon: ListCheck, tone: "emerald" },
    { href: "/settings", label: "Réglages", icon: SettingsIcon, tone: "amber" },
  ] as const;

  return (
      <div className="flex min-h-screen bg-[#F9FAFB] text-foreground">
        <aside className="sticky top-0 flex h-screen w-56 flex-col border-r border-slate-200 bg-white p-4 shadow">
          <nav className="mt-2 flex flex-col gap-2" role="navigation" aria-label="Navigation principale">
            {navItems.map(({ href, label, icon: Icon, tone }) => (
              <Link
                key={href}
                href={href}
                aria-label={label}
                aria-current={pathname === href ? "page" : undefined}
                className={cn(
                  "flex items-center gap-3 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm transition-all hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-focus",
                  pathname === href ? "shadow-md" : "shadow-sm"
                )}
              >
                <span
                  className={cn(
                    "inline-flex h-8 w-8 items-center justify-center rounded-full text-white",
                    tone === "indigo" && "bg-indigo-600",
                    tone === "cyan" && "bg-cyan-500",
                    tone === "emerald" && "bg-emerald-500",
                    tone === "amber" && "bg-amber-500"
                  )}
                >
                  <Icon className="h-4 w-4" />
                </span>
                <span className="text-slate-900">{label}</span>
              </Link>
            ))}
          </nav>
        </aside>
        <div className="flex flex-1 flex-col">
          <Header
            searchRef={searchRef}
            onCheatsheetOpen={() => setCheatsheetOpen(true)}
            commandPaletteOpen={commandPaletteOpen}
            onCommandPaletteOpenChange={setCommandPaletteOpen}
          />
          <main className="flex-1 overflow-y-auto p-4" role="main">
            {children}
          </main>
        </div>
        <ShortcutsCheatsheet
          open={cheatsheetOpen}
          onOpenChange={setCheatsheetOpen}
        />
      </div>
  );
}

export default AppShell;
