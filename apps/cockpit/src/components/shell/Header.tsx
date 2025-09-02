"use client";
import { Input } from "@/components/ds/Input";
import { Bell } from "lucide-react";
import { CommandPalette } from "./CommandPalette";
import { ThemeToggle } from "./ThemeToggle";

export function Header() {
  return (
    <header
      className="glass glass-muted sticky top-0 z-10 flex h-14 items-center justify-between border-b px-4"
      role="banner"
    >
      <div role="search" className="flex-1">
        <Input
          aria-label="Recherche"
          placeholder="Rechercher..."
          className="w-full max-w-sm"
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
        <CommandPalette />
      </div>
    </header>
  );
}
