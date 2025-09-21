import { STATUS_LABEL, Status } from "@/ui/theme";
import { cn } from "@/lib/utils";

const STATUS_STYLES: Record<Status, string> = {
  completed: "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30",
  running: "bg-indigo-500/15 text-indigo-300 border border-indigo-500/30 animate-pulse",
  queued: "bg-amber-500/15 text-amber-300 border border-amber-500/30",
  failed: "bg-rose-500/15 text-rose-300 border border-rose-500/30",
  paused: "bg-cyan-500/15 text-cyan-300 border border-cyan-500/30",
};

export interface StatusBadgeProps {
  status: Status;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide",
        STATUS_STYLES[status],
        className
      )}
    >
      <span className="inline-block h-2 w-2 rounded-full bg-current" aria-hidden />
      {STATUS_LABEL[status]}
    </span>
  );
}

export default StatusBadge;
