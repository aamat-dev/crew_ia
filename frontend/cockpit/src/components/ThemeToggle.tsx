"use client";
import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const toggle = () => setTheme(theme === "dark" ? "light" : "dark");
  return (
    <button
      aria-label="Changer de thème"
      onClick={toggle}
      className="flex h-10 w-10 items-center justify-center rounded-lg hover:bg-primary/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-focus"
    >
      {theme === "dark" ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
    </button>
  );
}

export default ThemeToggle;
