"use client";
import * as React from "react";
import { useRouter } from "next/navigation";
import { Command } from "cmdk";

const nav = [
  { label: "Dashboard", href: "/" },
  { label: "Tasks", href: "/tasks" },
  { label: "Plans", href: "/plans" },
  { label: "Runs", href: "/runs" },
  { label: "Settings", href: "/settings" },
];

interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CommandPalette({
  open,
  onOpenChange,
}: CommandPaletteProps) {
  const router = useRouter();

  return (
    <Command.Dialog open={open} onOpenChange={onOpenChange} label="Commandes">
      <Command.Input placeholder="Rechercher..." />
      <Command.List>
        {nav.map((item) => (
          <Command.Item
            key={item.href}
            onSelect={() => {
              router.push(item.href);
              onOpenChange(false);
            }}
          >
            {item.label}
          </Command.Item>
        ))}
      </Command.List>
    </Command.Dialog>
  );
}

export default CommandPalette;
