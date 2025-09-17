import { cn } from "@/lib/utils";

export type NoticeType = "success" | "warning" | "error";

const NOTICE_COLORS: Record<NoticeType, { dot: string; text: string; border: string }> = {
  success: {
    dot: "bg-[var(--accent-emerald-500)]",
    text: "text-emerald-200",
    border: "border border-emerald-500/30",
  },
  warning: {
    dot: "bg-[var(--accent-amber-500)]",
    text: "text-amber-200",
    border: "border border-amber-500/30",
  },
  error: {
    dot: "bg-[var(--accent-rose-500)]",
    text: "text-rose-200",
    border: "border border-rose-500/30",
  },
};

export interface NoticeCardProps {
  type: NoticeType;
  message: string;
  title?: string;
  className?: string;
}

export function NoticeCard({ type, message, title, className }: NoticeCardProps) {
  const palette = NOTICE_COLORS[type];
  return (
    <div className={cn("surface shadow-card p-3 flex items-start gap-3", palette.border, palette.text, className)}>
      <span aria-hidden className={cn("mt-1 h-2.5 w-2.5 rounded-full", palette.dot)} />
      <div className="space-y-1">
        {title ? <p className="font-semibold text-[color:var(--text)]">{title}</p> : null}
        <p className="text-sm leading-relaxed">{message}</p>
      </div>
    </div>
  );
}

export default NoticeCard;
