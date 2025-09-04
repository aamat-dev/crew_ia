"use client";
import * as React from "react";
import { cn } from "@/lib/utils";

export type InputProps = React.InputHTMLAttributes<HTMLInputElement>;

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        "px-3 py-2 border rounded-md bg-background text-foreground transition-colors duration-[var(--duration-fast)] focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-focus",
        className
      )}
      {...props}
    />
  )
);
Input.displayName = "Input";
export { Input };
