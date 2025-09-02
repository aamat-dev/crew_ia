"use client";
import { Input } from "@/components/ds/Input";
import { Button } from "@/components/ds/Button";
import { Sun, Moon, Bell } from "lucide-react";
import { useTheme } from "next-themes";
import { CommandPalette } from "./CommandPalette";

export function Header() {
  const { theme, setTheme } = useTheme();
  const toggleTheme = () => setTheme(theme === "dark" ? "light" : "dark");

  return (
    <header
      className="flex items-center justify-between px-4 py-2 border-b"
      role="banner"
    >
      <Input
        aria-label="Recherche"
        placeholder="Rechercher..."
        className="w-60"
      />
      <div className="flex items-center gap-2">
        <button
          aria-label="Notifications"
          className="relative p-2 rounded-md hover:bg-primary/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-ring"
        >
          <Bell className="h-5 w-5" />
          <span className="absolute top-1 right-1 inline-flex h-2 w-2 rounded-full bg-red-500" />
        </button>
        <Button
          aria-label="Changer de thème"
          onClick={toggleTheme}
          className="p-2 h-8 w-8 flex items-center justify-center"
        >
          {theme === "dark" ? (
            <Sun className="h-4 w-4" />
          ) : (
            <Moon className="h-4 w-4" />
          )}
        </Button>
        <CommandPalette />
      </div>
    </header>
  );
}
