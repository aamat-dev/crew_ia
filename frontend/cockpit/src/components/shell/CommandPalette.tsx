"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Command } from "cmdk";
import { DialogTitle } from "@radix-ui/react-dialog";

const nav = [
  { label: "Dashboard", href: "/dashboard", shortcut: "D" },
  { label: "Tasks", href: "/tasks", shortcut: "T" },
  { label: "Plans", href: "/plans", shortcut: "P" },
  { label: "Runs", href: "/runs", shortcut: "R" },
  { label: "Settings", href: "/settings", shortcut: "S" },
];

interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  const router = useRouter();
  const inputRef = React.useRef<HTMLInputElement>(null);

  React.useEffect(() => {
    if (open) inputRef.current?.focus();
  }, [open]);

  React.useEffect(() => {
    const input = inputRef.current;
    if (!input) return;
    Array.from(input.attributes).forEach((attr) => {
      if (attr.name.startsWith("data-dashlane")) {
        input.removeAttribute(attr.name);
      }
    });
  }, []);

  return (
    <Command.Dialog
      open={open}
      onOpenChange={onOpenChange}
      label="Palette de commandes"
      className="fixed inset-0 z-50 flex items-start justify-center bg-black/20 p-4 backdrop-blur-sm"
      id="command-palette"
    >
      <DialogTitle className="sr-only">Palette de commandes</DialogTitle>
      <div className="w-full max-w-md overflow-hidden rounded-lg bg-background text-foreground shadow-lg">
        <div className="flex items-center border-b px-3">
          <Command.Input
            ref={inputRef}
            placeholder="Rechercher..."
            role="textbox"
            className="flex-1 bg-transparent py-3 text-sm outline-none"
            suppressHydrationWarning
          />
        </div>
        <Command.List className="max-h-60 overflow-y-auto p-2">
          {nav.map((item) => (
            <Command.Item
              key={item.href}
              onSelect={() => {
                router.push(item.href);
                onOpenChange(false);
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
  );
}

export default CommandPalette;
