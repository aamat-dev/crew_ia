"use client";
import * as React from "react";
import { cn } from "@/lib/utils";

export type ClayButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  size?: "sm" | "md";
};

export const ClayButton = React.forwardRef<HTMLButtonElement, ClayButtonProps>(
  ({ className, size = "md", ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center rounded-xl border border-slate-200 bg-white text-slate-700 shadow-sm transition hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-focus",
        size === "sm" ? "px-3 py-1.5 text-sm" : "px-3 py-2 text-sm",
        className
      )}
      {...props}
    />
  )
);
ClayButton.displayName = "ClayButton";

export default ClayButton;

