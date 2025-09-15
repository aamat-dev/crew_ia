"use client";
import * as React from "react";
import { cn } from "@/lib/utils";

type DivProps = React.HTMLAttributes<HTMLDivElement> & { as?: keyof JSX.IntrinsicElements };

export function ClayCard({ className, as: Tag = "div", ...props }: DivProps) {
  return <Tag className={cn("clay-card", className)} {...props} />;
}

export default ClayCard;

