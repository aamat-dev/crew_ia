"use client";
import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  ListCheck,
  Map,
  Play,
  Settings as SettingsIcon,
} from "lucide-react";
import { ToastProvider } from "@/components/ds/Toast";
import { cn } from "@/lib/utils";
import { Header } from "./Header";

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();

  const navItems = [
    { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { href: "/tasks", label: "Tasks", icon: ListCheck },
    { href: "/plans", label: "Plans", icon: Map },
    { href: "/runs", label: "Runs", icon: Play },
    { href: "/settings", label: "Settings", icon: SettingsIcon },
  ];

  return (
    <ToastProvider>
      <div className="flex min-h-screen bg-background text-foreground">
        <aside
          className="sticky top-0 flex h-screen w-16 flex-col items-center border-r bg-background/60 p-2 backdrop-blur-md shadow-lg rounded-r-xl"
        >
          <nav
            className="mt-4 flex flex-col items-center gap-2"
            role="navigation"
            aria-label="Navigation principale"
          >
            {navItems.map(({ href, label, icon: Icon }) => (
              <Link
                key={href}
                href={href}
                aria-label={label}
                aria-current={pathname === href ? "page" : undefined}
                className={cn(
                  "flex h-10 w-10 items-center justify-center rounded-lg transition-colors hover:bg-primary/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                  pathname === href && "bg-primary/10"
                )}
              >
                <Icon className="h-5 w-5" />
              </Link>
            ))}
          </nav>
        </aside>
        <div className="flex flex-1 flex-col">
          <Header />
          <main className="flex-1 overflow-y-auto p-4" role="main">
            {children}
          </main>
        </div>
      </div>
    </ToastProvider>
  );
}

export default AppShell;
