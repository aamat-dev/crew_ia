"use client";
import * as React from "react";
import { Input } from "@/components/ds/Input";
import { Bell, CircleHelp, Command as CommandIcon, Menu } from "lucide-react";
import { CommandPalette } from "./CommandPalette";
import { ThemeToggle } from "./ThemeToggle";

interface HeaderProps {
  searchRef: React.RefObject<HTMLInputElement>;
  onCheatsheetOpen: () => void;
  commandPaletteOpen: boolean;
  onCommandPaletteOpenChange: (open: boolean) => void;
  onMobileMenu?: () => void;
}

export function Header({
  searchRef,
  onCheatsheetOpen,
  commandPaletteOpen,
  onCommandPaletteOpenChange,
  onMobileMenu,
}: HeaderProps) {
  React.useEffect(() => {
    const input = searchRef.current;
    if (!input) return;
    for (const attr of Array.from(input.attributes)) {
      if (attr.name.startsWith("data-dashlane-")) {
        input.removeAttribute(attr.name);
      }
    }
  }, [searchRef]);
  return (
    <header className="sticky top-0 z-10 flex h-16 md:h-20 items-center justify-between border-b border-slate-800 bg-[#1C1E26] px-4 md:px-6" role="banner">
      <div className="flex items-center gap-2 md:flex-col md:items-start">
        <button
          type="button"
          className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-slate-700 bg-[#2A2D36] text-slate-200 shadow-sm transition hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--ring))] md:hidden"
          aria-label="Ouvrir le menu"
          onClick={onMobileMenu}
        >
          <Menu className="h-5 w-5" />
        </button>
        <h1 className="text-3xl font-extrabold tracking-tight text-slate-100">Cockpit</h1>
        <p className="sr-only">Tableau de bord</p>
      </div>
      <div role="search" className="hidden flex-1 justify-center md:flex">
        <div className="hidden w-full max-w-lg items-center gap-2 rounded-2xl border border-slate-700 bg-[#2A2D36] px-3 py-2 shadow-[inset_0_2px_6px_rgba(255,255,255,0.04)] focus-within:ring-2 focus-within:ring-[hsl(var(--ring))] sm:flex">
          <span className="text-slate-400" aria-hidden>Rechercher</span>
          <Input
            ref={searchRef}
            aria-label="Recherche"
            placeholder="Rechercher..."
            className="w-full border-0 bg-transparent p-0 text-slate-100 placeholder:text-slate-400 focus-visible:ring-0"
            suppressHydrationWarning
          />
        </div>
      </div>
      <div className="ml-4 flex items-center gap-2">
        {(() => {
          const NOTIF_COUNT = 2; // mock
          return (
            <button
              aria-label={`Notifications${NOTIF_COUNT ? ` (${NOTIF_COUNT} nouvelles)` : ""}`}
              className="relative inline-flex h-10 w-10 items-center justify-center rounded-xl border border-slate-700 bg-[#2A2D36] text-slate-200 shadow-sm transition hover:bg-indigo-600/15 focus:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--ring))]"
            >
              <Bell className="h-5 w-5" />
              {NOTIF_COUNT > 0 && (
                <span
                  aria-hidden
                  className="absolute right-1 top-1 inline-flex h-2 w-2 items-center justify-center rounded-full bg-destructive"
                />
              )}
            </button>
          );
        })()}
        <button
          aria-label="Ouvrir la palette de commandes"
          onClick={() => onCommandPaletteOpenChange(true)}
          className="relative inline-flex h-10 w-10 items-center justify-center rounded-xl border border-slate-700 bg-[#2A2D36] text-slate-200 shadow-sm transition hover:bg-indigo-600/15 focus:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--ring))]"
          aria-expanded={commandPaletteOpen}
          aria-controls="command-palette"
        >
          <CommandIcon className="h-5 w-5" />
          <kbd className="pointer-events-none absolute -bottom-1 -right-1 rounded bg-muted px-1 text-[10px] text-muted-foreground">⌘K</kbd>
        </button>
        <ThemeToggle />
        <button
          aria-label="Afficher l'aide sur les raccourcis clavier"
          aria-controls="shortcuts-cheatsheet"
          onClick={onCheatsheetOpen}
          className="relative inline-flex h-10 w-10 items-center justify-center rounded-xl border border-slate-700 bg-[#2A2D36] text-slate-200 shadow-sm transition hover:bg-indigo-600/15 focus:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--ring))]"
        >
          <CircleHelp className="h-5 w-5" />
        </button>
        <CommandPalette
          open={commandPaletteOpen}
          onOpenChange={onCommandPaletteOpenChange}
        />
      </div>
    </header>
  );
}
