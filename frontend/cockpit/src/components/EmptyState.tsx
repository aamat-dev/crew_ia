"use client";
import Link from "next/link";

interface EmptyStateProps {
  title: string;
  description?: string;
  ctaHref?: string;
  ctaLabel?: string;
}

export function EmptyState({ title, description, ctaHref, ctaLabel }: EmptyStateProps) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="glass p-8 rounded-md border text-center space-y-2"
    >
      <p className="text-lg font-medium">{title}</p>
      {description && <p className="opacity-80">{description}</p>}
      {ctaHref && ctaLabel && (
        <div className="pt-2">
          <Link
            href={ctaHref}
            className="inline-flex items-center justify-center glass px-3 py-1 rounded-md border focus:outline-none focus-visible:ring-2 focus-visible:ring-focus"
          >
            {ctaLabel}
          </Link>
        </div>
      )}
    </div>
  );
}

export default EmptyState;
