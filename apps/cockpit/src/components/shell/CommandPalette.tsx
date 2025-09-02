"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Command } from "cmdk";
import { Command as CommandIcon } from "lucide-react";

const nav = [
  { label: "Dashboard", href: "/dashboard", shortcut: "D" },
  { label: "Tasks", href: "/tasks", shortcut: "T" },
  { label: "Plans", href: "/plans", shortcut: "P" },
  { label: "Runs", href: "/runs", shortcut: "R" },
  { label: "Settings", href: "/settings", shortcut: "S" },
];

export function CommandPalette() {
  const [open, setOpen] = React.useState(false);
  const router = useRouter();
  const inputRef = React.useRef<HTMLInputElement>(null);

  React.useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen(true);
      }
    };
    window.addEventListener("keydown", down);
    return () => window.removeEventListener("keydown", down);
  }, []);

  React.useEffect(() => {
    if (open) {
      inputRef.current?.focus();
    }
  }, [open]);

  return (
    <>
      <button
        type="button"
        aria-label="Ouvrir la palette de commandes"
        onClick={() => setOpen(true)}
        className="flex h-10 w-10 items-center justify-center rounded-lg hover:bg-primary/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      >
        <CommandIcon className="h-5 w-5" />
      </button>
      <Command.Dialog
        open={open}
        onOpenChange={setOpen}
        label="Palette de commandes"
        className="fixed inset-0 z-50 flex items-start justify-center bg-black/20 p-4 backdrop-blur-sm"
      >
        <div className="w-full max-w-md overflow-hidden rounded-lg bg-background text-foreground shadow-lg">
          <div className="flex items-center border-b px-3">
            <Command.Input
              ref={inputRef}
              placeholder="Rechercher..."
              className="flex-1 bg-transparent py-3 text-sm outline-none"
            />
          </div>
          <Command.List className="max-h-60 overflow-y-auto p-2">
            {nav.map((item) => (
              <Command.Item
                key={item.href}
                onSelect={() => {
                  router.push(item.href);
                  setOpen(false);
                }}
                className="flex cursor-pointer items-center gap-2 rounded px-2 py-1 text-sm aria-selected:bg-primary/10"
              >
                {item.label}
                <kbd className="ml-auto text-xs text-muted-foreground">⌘{item.shortcut}</kbd>
              </Command.Item>
            ))}
          </Command.List>
        </div>
      </Command.Dialog>
    </>
  );
}

export default CommandPalette;

