"use client";

import * as React from "react";
import { Bell, Search, UserRound, Sun, Moon } from "lucide-react";
import { useTheme } from "next-themes";
import { baseFocusRing } from "@/ui/theme";
import { cn } from "@/lib/utils";

export const THEME_STORAGE_KEY = "cockpit-theme";

type ThemeValue = "light" | "dark";

export function onToggleTheme(current: ThemeValue, setTheme: (value: ThemeValue) => void) {
  const next: ThemeValue = current === "dark" ? "light" : "dark";
  setTheme(next);
  if (typeof window !== "undefined") {
    window.localStorage.setItem(THEME_STORAGE_KEY, next);
  }
  return next;
}

export interface HeaderBarProps {
  title: string;
  breadcrumb?: string;
  searchValue?: string;
  onSearchChange?: (value: string) => void;
  searchPlaceholder?: string;
  actions?: React.ReactNode;
  showSearch?: boolean;
}

export function HeaderBar({
  title,
  breadcrumb,
  searchValue,
  onSearchChange,
  searchPlaceholder = "Rechercher...",
  actions,
  showSearch = false,
}: HeaderBarProps) {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);
  const [internalSearch, setInternalSearch] = React.useState(searchValue ?? "");
  const notificationCount = 2;

  React.useEffect(() => setMounted(true), []);
  React.useEffect(() => {
    if (typeof searchValue === "string") {
      setInternalSearch(searchValue);
    }
  }, [searchValue]);

  const handleSearch = (value: string) => {
    setInternalSearch(value);
    onSearchChange?.(value);
  };

  const currentTheme: ThemeValue = (resolvedTheme === "light" ? "light" : "dark");

  return (
    <header className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
      <div className="space-y-1">
        <h1 className="text-3xl font-semibold text-[color:var(--text)]">{title}</h1>
        {breadcrumb ? (
          <p className="text-sm text-secondary">{breadcrumb}</p>
        ) : null}
      </div>
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-end md:gap-4 flex-1">
        {showSearch ? (
          <label className="flex-1 md:max-w-md" aria-label="Recherche">
            <div className="surface shadow-card flex items-center gap-2 px-3 py-2 text-sm text-secondary">
              <Search className="h-4 w-4" aria-hidden />
              <input
                type="search"
                value={internalSearch}
                onChange={(event) => handleSearch(event.target.value)}
                placeholder={searchPlaceholder}
                className={cn(
                  "w-full bg-transparent text-[color:var(--text)] placeholder:text-secondary",
                  "border-0 outline-none focus:ring-0"
                )}
              />
            </div>
          </label>
        ) : null}
        <div className="flex items-center gap-2">
          <button
            type="button"
            aria-label="Afficher les notifications"
            className={cn(
              "relative h-10 w-10 rounded-full surface shadow-card grid place-content-center text-[color:var(--text)]",
              baseFocusRing
            )}
          >
            <Bell className="h-5 w-5" aria-hidden />
            {notificationCount > 0 ? (
              <span aria-hidden className="absolute top-2 right-2 h-2 w-2 rounded-full bg-[var(--accent-rose-500)]" />
            ) : null}
          </button>
          <button
            type="button"
            aria-label="Basculer le thème"
            onClick={() => {
              if (!mounted) return;
              onToggleTheme(currentTheme, setTheme as (value: ThemeValue) => void);
            }}
            className={cn(
              "h-10 w-10 rounded-full surface shadow-card grid place-content-center text-[color:var(--text)]",
              baseFocusRing
            )}
          >
            {mounted && resolvedTheme === "light" ? (
              <Moon className="h-5 w-5" aria-hidden />
            ) : (
              <Sun className="h-5 w-5" aria-hidden />
            )}
          </button>
          <button
            type="button"
            aria-label="Profil utilisateur"
            className={cn(
              "h-10 w-10 rounded-full surface shadow-card grid place-content-center text-[color:var(--text)]",
              baseFocusRing
            )}
          >
            <UserRound className="h-5 w-5" aria-hidden />
          </button>
          {actions}
        </div>
      </div>
    </header>
  );
}

export default HeaderBar;
