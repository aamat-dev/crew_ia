"use client";
import * as React from "react";
import { Input } from "@/components/ds/Input";
import { Bell, CircleHelp } from "lucide-react";
import { CommandPalette } from "./CommandPalette";
import { ThemeToggle } from "./ThemeToggle";

interface HeaderProps {
  searchRef: React.RefObject<HTMLInputElement>;
  onCheatsheetOpen: () => void;
  commandPaletteOpen: boolean;
  onCommandPaletteOpenChange: (open: boolean) => void;
}

export function Header({
  searchRef,
  onCheatsheetOpen,
  commandPaletteOpen,
  onCommandPaletteOpenChange,
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
    <header
      className="glass glass-muted sticky top-0 z-10 flex h-14 items-center justify-between border-b px-4"
      role="banner"
    >
      <div role="search" className="flex-1">
        <Input
          ref={searchRef}
          aria-label="Recherche"
          placeholder="Rechercher..."
          className="w-full max-w-sm"
          suppressHydrationWarning
        />
      </div>
      <div className="ml-4 flex items-center gap-2">
        <button
          aria-label="Notifications"
          className="relative flex h-10 w-10 items-center justify-center rounded-lg hover:bg-primary/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <Bell className="h-5 w-5" />
        </button>
        <ThemeToggle />
        <button
          aria-label="Afficher l'aide sur les raccourcis clavier"
          aria-controls="shortcuts-cheatsheet"
          onClick={onCheatsheetOpen}
          className="relative flex h-10 w-10 items-center justify-center rounded-lg hover:bg-primary/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
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
