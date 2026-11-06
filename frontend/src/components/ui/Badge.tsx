import React from 'react';

export type BadgeVariant =
  | 'critical'
  | 'high'
  | 'medium'
  | 'low'
  | 'success'
  | 'warning'
  | 'info'
  | 'neutral'
  | 'violet';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  size?: 'sm' | 'md';
  className?: string;
  dot?: boolean;
}

const variantStyles: Record<BadgeVariant, string> = {
  critical: 'bg-rose-950/60 text-rose-300 border-rose-800/80',
  high: 'bg-amber-950/60 text-amber-300 border-amber-800/80',
  medium: 'bg-yellow-950/40 text-yellow-300 border-yellow-800/60',
  low: 'bg-blue-950/40 text-blue-300 border-blue-800/60',
  success: 'bg-emerald-950/60 text-emerald-300 border-emerald-800/80',
  warning: 'bg-amber-950/60 text-amber-300 border-amber-800/80',
  info: 'bg-cyan-950/60 text-cyan-300 border-cyan-800/80',
  neutral: 'bg-zinc-900 text-zinc-400 border-zinc-800',
  violet: 'bg-violet-950/60 text-violet-300 border-violet-800/80',
};

const dotColors: Record<BadgeVariant, string> = {
  critical: 'bg-rose-500',
  high: 'bg-amber-500',
  medium: 'bg-yellow-500',
  low: 'bg-blue-500',
  success: 'bg-emerald-500',
  warning: 'bg-amber-500',
  info: 'bg-cyan-500',
  neutral: 'bg-zinc-500',
  violet: 'bg-violet-500',
};

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  size = 'md',
  className = '',
  dot = false,
}) => {
  const sizeClasses = size === 'sm' ? 'text-[10px] px-1.5 py-0.5' : 'text-xs px-2 py-0.5';

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-medium border rounded font-mono uppercase tracking-wider ${sizeClasses} ${variantStyles[variant]} ${className}`}
    >
      {dot && <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${dotColors[variant]}`} />}
      {children}
    </span>
  );
};
