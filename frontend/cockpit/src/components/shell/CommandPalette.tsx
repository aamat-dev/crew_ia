"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Command } from "cmdk";
import { DialogTitle } from "@radix-ui/react-dialog";

const nav = [
  { label: "Dashboard", href: "/dashboard", shortcut: "D" },
  { label: "Nouvelle tâche", href: "/tasks/new", shortcut: "N" },
];

const quickActions = [
  { label: "Nouvelle tâche", href: "/tasks/new", shortcut: "↩" },
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
          <Command.Group heading="Navigation">
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
          </Command.Group>
          <Command.Separator className="my-1 border-t border-slate-800/60" />
          <Command.Group heading="Actions rapides">
            {quickActions.map((action) => (
              <Command.Item
                key={action.label}
                onSelect={() => {
                  router.push(action.href);
                  onOpenChange(false);
                }}
                className="flex cursor-pointer items-center gap-2 rounded px-2 py-1 text-sm aria-selected:bg-primary/10"
              >
                {action.label}
                <kbd className="ml-auto text-xs text-muted-foreground">{action.shortcut}</kbd>
              </Command.Item>
            ))}
          </Command.Group>
        </Command.List>
      </div>
    </Command.Dialog>
  );
}

export default CommandPalette;
