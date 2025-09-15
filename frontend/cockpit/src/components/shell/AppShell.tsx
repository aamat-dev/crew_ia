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
  const [mobileNavOpen, setMobileNavOpen] = React.useState(false);
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
        <aside className="sticky top-0 hidden h-screen w-16 flex-col border-r border-slate-200 bg-white p-2 shadow md:flex md:w-44 lg:w-56 lg:p-4">
          <nav className="mt-2 flex flex-col gap-2" role="navigation" aria-label="Navigation principale">
            {navItems.map(({ href, label, icon: Icon, tone }) => (
              <Link
                key={href}
                href={href}
                aria-label={label}
                aria-current={pathname === href ? "page" : undefined}
                className={cn(
                  "flex items-center gap-3 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm transition-all hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-focus md:justify-start justify-center",
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
                <span className="hidden text-slate-900 md:inline">{label}</span>
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
            onMobileMenu={() => setMobileNavOpen(true)}
          />
          <main className="flex-1 overflow-y-auto p-4 pb-24 md:p-6 md:pb-6" role="main">
            {children}
          </main>
          {mobileNavOpen && (
            <div
              role="dialog"
              aria-modal="true"
              aria-label="Navigation"
              className="fixed inset-0 z-50 flex md:hidden"
              onClick={() => setMobileNavOpen(false)}
            >
              <div className="w-3/4 max-w-xs h-full border-r border-slate-200 bg-white p-4 shadow" onClick={(e) => e.stopPropagation()}>
                <nav className="mt-2 flex flex-col gap-2" aria-label="Navigation mobile">
                  {navItems.map(({ href, label, icon: Icon, tone }) => (
                    <Link
                      key={href}
                      href={href}
                      onClick={() => setMobileNavOpen(false)}
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
              </div>
              <div className="flex-1 bg-black/30" />
            </div>
          )}
          {/* Navigation mobile fixe (icônes uniquement) */}
          <nav className="fixed inset-x-0 bottom-0 z-10 border-t border-slate-200 bg-white shadow md:hidden" aria-label="Navigation mobile">
            <ul className="flex items-center justify-around p-2 pb-[env(safe-area-inset-bottom)]">
              {navItems.map(({ href, label, icon: Icon, tone }) => (
                <li key={href}>
                  <Link
                    href={href}
                    aria-label={label}
                    aria-current={pathname === href ? "page" : undefined}
                    className={cn(
                      "flex h-10 w-10 items-center justify-center rounded-full focus:outline-none focus-visible:ring-2 focus-visible:ring-focus",
                      pathname === href ? "bg-slate-100" : undefined
                    )}
                  >
                    <Icon className={cn("h-5 w-5", tone === "indigo" && "text-indigo-600", tone === "cyan" && "text-cyan-500", tone === "emerald" && "text-emerald-500", tone === "amber" && "text-amber-500")} />
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </div>
        <ShortcutsCheatsheet
          open={cheatsheetOpen}
          onOpenChange={setCheatsheetOpen}
        />
      </div>
  );
}

export default AppShell;
