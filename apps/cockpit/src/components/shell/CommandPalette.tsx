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

export function CommandPalette() {
  const [open, setOpen] = React.useState(false);
  const router = useRouter();

  React.useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((o) => !o);
      }
      if (e.key.toLowerCase() === "g") {
        const next = (ev: KeyboardEvent) => {
          if (ev.key.toLowerCase() === "r") router.push("/runs");
          if (ev.key.toLowerCase() === "t") router.push("/tasks");
        };
        window.addEventListener("keydown", next, { once: true });
      }
    };
    window.addEventListener("keydown", down);
    return () => window.removeEventListener("keydown", down);
  }, [router]);

  return (
    <Command.Dialog open={open} onOpenChange={setOpen} label="Commandes">
      <Command.Input placeholder="Rechercher..." />
      <Command.List>
        {nav.map((item) => (
          <Command.Item
            key={item.href}
            onSelect={() => {
              router.push(item.href);
              setOpen(false);
            }}
          >
            {item.label}
          </Command.Item>
        ))}
      </Command.List>
    </Command.Dialog>
  );
}
