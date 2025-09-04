"use client";
import { RefObject, useEffect } from "react";
import { useRouter } from "next/navigation";

interface Options {
  searchRef: RefObject<HTMLInputElement>;
  onOpenCommandPalette: () => void;
  onOpenCheatsheet: () => void;
}

function isEditable(target: EventTarget | null): boolean {
  const el = target as HTMLElement | null;
  return (
    !!el &&
    (el.tagName === "INPUT" ||
      el.tagName === "TEXTAREA" ||
      el.isContentEditable)
  );
}

export function useGlobalShortcuts({
  searchRef,
  onOpenCommandPalette,
  onOpenCheatsheet,
}: Options): void {
  const router = useRouter();

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (isEditable(e.target)) return;

      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        onOpenCommandPalette();
        return;
      }

      if (e.key === "/") {
        e.preventDefault();
        searchRef.current?.focus();
        return;
      }

      if (e.key === "?") {
        e.preventDefault();
        onOpenCheatsheet();
        return;
      }

      if (e.key.toLowerCase() === "g") {
        const next = (ev: KeyboardEvent) => {
          if (isEditable(ev.target)) return;
          const key = ev.key.toLowerCase();
          if (key === "r") router.push("/runs");
          if (key === "t") router.push("/tasks");
          if (key === "p") router.push("/plans");
          if (key === "d") router.push("/dashboard");
        };
        window.addEventListener("keydown", next, { once: true });
      }
    };

    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [router, searchRef, onOpenCommandPalette, onOpenCheatsheet]);
}

export default useGlobalShortcuts;
