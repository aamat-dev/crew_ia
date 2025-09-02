import type { JSX } from 'react';
import { ArrowDown, ArrowUp, type LucideIcon } from 'lucide-react';
import { motion, useReducedMotion } from 'framer-motion';

interface KpiCardProps {
  title: string;
  value: string | number;
  delta: number;
  icon: LucideIcon;
  className?: string;
}

export function KpiCard({
  title,
  value,
  delta,
  icon: Icon,
  className = '',
}: KpiCardProps): JSX.Element {
  const reduceMotion = useReducedMotion();
  const deltaPositive = delta >= 0;
  const DeltaIcon = deltaPositive ? ArrowUp : ArrowDown;
  const deltaColor = deltaPositive ? 'text-green-600' : 'text-red-600';

  return (
    <motion.div
      role="group"
      tabIndex={0}
      aria-label={`${title} ${value} (${deltaPositive ? 'augmentation' : 'diminution'} ${Math.abs(delta)}%)`}
      initial={reduceMotion ? false : { opacity: 0, scale: 0.95 }}
      animate={reduceMotion ? {} : { opacity: 1, scale: 1 }}
      whileHover={reduceMotion ? {} : { scale: 1.03 }}
      className={`rounded-lg border border-white/20 bg-white/60 p-4 shadow-sm backdrop-blur-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-neutral-500 dark:border-slate-700 dark:bg-slate-800/60 ${className}`.trim()}
    >
      <div className="flex items-center justify-between">
        <span className="text-sm text-neutral-600 dark:text-neutral-300">{title}</span>
        <Icon aria-hidden className="h-5 w-5 text-neutral-500" />
      </div>
      <div className="mt-2 text-2xl font-semibold text-neutral-900 dark:text-neutral-100">
        {value}
      </div>
      <div className={`mt-1 flex items-center text-sm ${deltaColor}`}>
        <DeltaIcon aria-hidden className="mr-1 h-3 w-3" />
        <span>{Math.abs(delta)}%</span>
      </div>
    </motion.div>
  );
}
