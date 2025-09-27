"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, ListCheck } from "lucide-react";
import { baseFocusRing, accentGradient } from "@/ui/theme";
import { cn } from "@/lib/utils";
import { ShortcutsCheatsheet } from "@/components/shortcuts/ShortcutsCheatsheet";

interface AppShellProps {
  children: React.ReactNode;
}

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard, accent: "brand" as const },
  { href: "/tasks/new", label: "Nouvelle tâche", icon: ListCheck, accent: "cyan" as const },
] as const;

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();
  const [cheatsheetOpen, setCheatsheetOpen] = React.useState(false);

  React.useEffect(() => {
    const isEditable = (t: EventTarget | null) => {
      const el = t as HTMLElement | null;
      if (!el) return false;
      const tag = el.tagName;
      return tag === "INPUT" || tag === "TEXTAREA" || el.isContentEditable;
    };
    const handleKeyDown = (event: KeyboardEvent) => {
      // Désactive les raccourcis globaux sur la page de création (focus prioritaire)
      if (typeof pathname === 'string' && pathname.startsWith('/tasks/new')) return;
      if (isEditable(event.target)) return;
      const key = event.key.toLowerCase();
      if (!event.metaKey && !event.ctrlKey) {
        const isQuestionMark = key === "?" || (event.shiftKey && key === "/");
        if (isQuestionMark) {
          event.preventDefault();
          setCheatsheetOpen(true);
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [pathname]);

  return (
    <div className="flex min-h-screen bg-[var(--bg)] text-[var(--text)]">
      <div className="flex flex-1 flex-col">
        <ShortcutsCheatsheet open={cheatsheetOpen} onOpenChange={setCheatsheetOpen} />
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
                  active ? cn("text-white bg-gradient-to-br", accentGradient(item.accent)) : "text-secondary bg-transparent"
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
