"use client";
import * as React from "react";
import { cn } from "@/lib/utils";

type DivCardProps = React.HTMLAttributes<HTMLDivElement> & { as?: "div" };
type LiCardProps = React.LiHTMLAttributes<HTMLLIElement> & { as: "li" };
type ClayCardProps = DivCardProps | LiCardProps;

export function ClayCard({ as = "div", className, ...props }: ClayCardProps) {
  if (as === "li") {
    const liProps = props as React.LiHTMLAttributes<HTMLLIElement>;
    return <li className={cn("clay-card", className)} {...liProps} />;
  }

  const divProps = props as React.HTMLAttributes<HTMLDivElement>;
  return <div className={cn("clay-card", className)} {...divProps} />;
}

export default ClayCard;
