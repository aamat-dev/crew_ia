"use client";
import * as React from "react";
import { ResponsiveContainer, Tooltip, CartesianGrid, XAxis, YAxis, AreaChart, Area, BarChart, Bar } from "recharts";
import { cn } from "@/lib/utils";

type Accent = 'indigo'|'cyan'|'emerald'|'amber';

interface MetricChartCardProps<T extends object> {
  title: string;
  type: 'area'|'bar';
  data: T[];
  xKey: keyof T & string;
  yKey: keyof T & string;
  accent?: Accent;
  className?: string;
}

const strokeFor = (a: Accent) => ({
  indigo: '#818CF8',
  cyan: '#22D3EE',
  emerald: '#34D399',
  amber: '#FBBF24',
}[a]);

export function MetricChartCard<T extends object>({ title, type, data, xKey, yKey, accent = 'indigo', className }: MetricChartCardProps<T>) {
  const id = React.useId();
  const stroke = strokeFor(accent);
  return (
    <section className={cn("clay-card p-4", className)} aria-label={title}>
      <h3 className="text-sm font-medium mb-2 text-slate-200">{title}</h3>
      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          {type === 'area' ? (
            <AreaChart data={data as Array<Record<string, unknown>>}>
              <defs>
                <linearGradient id={`grad-${accent}-${id}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={stroke} stopOpacity={0.35} />
                  <stop offset="100%" stopColor={stroke} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeOpacity={0.15} stroke="#94A3B8" />
              <XAxis dataKey={xKey} tick={{ fill: '#94A3B8' }} tickLine={false} axisLine={{ stroke: '#475569' }} />
              <YAxis tick={{ fill: '#94A3B8' }} tickLine={false} axisLine={{ stroke: '#475569' }} />
              <Tooltip
                contentStyle={{ background: '#2A2D36', border: '1px solid #475569', borderRadius: 12, padding: '8px 12px', color: '#F1F5F9' }}
                labelStyle={{ color: '#F1F5F9' }}
                itemStyle={{ color: '#CBD5E1' }}
              />
              <Area type="monotone" dataKey={yKey} stroke={stroke} strokeWidth={2} fill={`url(#grad-${accent}-${id})`} />
            </AreaChart>
          ) : (
            <BarChart data={data as Array<Record<string, unknown>>}>
              <CartesianGrid strokeOpacity={0.15} stroke="#94A3B8" />
              <XAxis dataKey={xKey} tick={{ fill: '#94A3B8' }} tickLine={false} axisLine={{ stroke: '#475569' }} />
              <YAxis tick={{ fill: '#94A3B8' }} tickLine={false} axisLine={{ stroke: '#475569' }} />
              <Tooltip
                contentStyle={{ background: '#2A2D36', border: '1px solid #475569', borderRadius: 12, padding: '8px 12px', color: '#F1F5F9' }}
                labelStyle={{ color: '#F1F5F9' }}
                itemStyle={{ color: '#CBD5E1' }}
              />
              <Bar dataKey={yKey} fill={stroke} radius={[6,6,0,0]} />
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
    </section>
  );
}

export default MetricChartCard;
