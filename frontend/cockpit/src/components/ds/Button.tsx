"use client";
import * as React from "react";
import { cn } from "@/lib/utils";

export type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement>;

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        "px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm transition-colors duration-[var(--duration-fast)] focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-focus",
        className
      )}
      {...props}
    />
  )
);
Button.displayName = "Button";
export { Button };
