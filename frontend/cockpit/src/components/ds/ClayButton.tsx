"use client";
import * as React from "react";
import { cn } from "@/lib/utils";

export type ClayButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  size?: "sm" | "md";
  variant?: "outline" | "primary" | "destructive";
};

export const ClayButton = React.forwardRef<HTMLButtonElement, ClayButtonProps>(
  ({ className, size = "md", variant = "outline", ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center rounded-xl text-sm transition focus:outline-none focus-visible:ring-2 focus-visible:ring-focus transform-gpu will-change-transform disabled:opacity-60 disabled:cursor-not-allowed",
        variant === "outline" && "border border-slate-200 bg-white text-slate-700 shadow-sm hover:shadow-md",
        variant === "primary" && "border-0 text-white shadow-card hover:shadow-lg bg-gradient-to-br from-[var(--accent-brand-500)] to-[var(--accent-brand-400)]",
        variant === "destructive" && "border-0 text-white shadow-card hover:shadow-lg bg-gradient-to-br from-[var(--accent-rose-500)] to-[var(--accent-rose-400)]",
        size === "sm" ? "px-3 py-1.5 text-sm" : "px-3 py-2 text-sm",
        "hover:-translate-y-0.5 active:translate-y-0",
        className
      )}
      {...props}
    />
  )
);
ClayButton.displayName = "ClayButton";

export default ClayButton;
