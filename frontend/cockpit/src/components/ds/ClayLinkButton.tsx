"use client";
import * as React from "react";
import Link from "next/link";
import { cn } from "@/lib/utils";

export type ClayLinkButtonProps = React.ComponentProps<typeof Link> & {
  size?: "sm" | "md";
  variant?: "outline" | "primary";
  className?: string;
};

export function ClayLinkButton({ size = "md", variant = "outline", className, children, ...props }: ClayLinkButtonProps) {
  return (
    <Link
      {...props}
      className={cn(
        "inline-flex items-center rounded-xl text-sm transition focus:outline-none focus-visible:ring-2 focus-visible:ring-focus",
        variant === "outline" && "border border-slate-200 bg-white text-slate-700 shadow-sm hover:shadow-md",
        variant === "primary" && "border-transparent bg-indigo-600 text-white hover:bg-indigo-700",
        size === "sm" ? "px-3 py-1.5" : "px-3 py-2",
        className
      )}
    >
      {children}
    </Link>
  );
}

export default ClayLinkButton;

