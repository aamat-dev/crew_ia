"use client";
import { useEffect, useRef } from "react";

interface ShortcutsCheatsheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  id?: string;
}

export function ShortcutsCheatsheet({
  open,
  onOpenChange,
  id = "shortcuts-cheatsheet",
}: ShortcutsCheatsheetProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const lastFocused = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!open) return;
    lastFocused.current = document.activeElement as HTMLElement;
    const focusable = dialogRef.current?.querySelector<HTMLElement>(
      "button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])"
    );
    focusable?.focus();

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        onOpenChange(false);
      }
      if (e.key === "Tab") {
        const nodes = dialogRef.current?.querySelectorAll<HTMLElement>(
          "button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])"
        );
        if (!nodes || nodes.length === 0) return;
        const list = Array.from(nodes);
        const index = list.indexOf(document.activeElement as HTMLElement);
        if (e.shiftKey) {
          if (index === 0) {
            e.preventDefault();
            list[list.length - 1].focus();
          }
        } else if (index === list.length - 1) {
          e.preventDefault();
          list[0].focus();
        }
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      lastFocused.current?.focus();
    };
  }, [open, onOpenChange]);

  if (!open) return <div id={id} hidden />;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby={`${id}-title`}
      aria-describedby={`${id}-desc`}
      id={id}
      ref={dialogRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
    >
      <div className="w-full max-w-md rounded-md bg-background p-6 shadow-lg" id={`${id}-desc`}>
        <h2 id={`${id}-title`} className="mb-4 text-lg font-semibold">
          Raccourcis clavier
        </h2>
        <div className="space-y-2">
          <Shortcut label="Ouvrir la palette de commandes" mac="⌘ K" win="Ctrl K" />
          <Shortcut label="Aller aux runs" mac="G puis R" win="G puis R" />
          <Shortcut label="Aller aux tasks" mac="G puis T" win="G puis T" />
          <Shortcut label="Aller aux plans" mac="G puis P" win="G puis P" />
          <Shortcut label="Aller au dashboard" mac="G puis D" win="G puis D" />
          <Shortcut label="Focus sur la recherche" mac="/" win="/" />
          <Shortcut label="Ouvrir ce cheatsheet" mac="?" win="?" />
        </div>
        <div className="mt-6 text-right">
          <button
            onClick={() => onOpenChange(false)}
            className="rounded-md bg-primary px-3 py-2 text-primary-foreground focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-focus"
          >
            Fermer
          </button>
        </div>
      </div>
    </div>
  );
}

function Shortcut({
  label,
  mac,
  win,
}: {
  label: string;
  mac: string;
  win: string;
}) {
  return (
    <div className="flex items-center justify-between">
      <span>{label}</span>
      <span className="font-mono text-sm">
        {mac} / {win}
      </span>
    </div>
  );
}

export default ShortcutsCheatsheet;
