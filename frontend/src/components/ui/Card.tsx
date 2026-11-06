import React from 'react';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
  hoverEffect?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  hoverEffect = false,
  ...props
}) => {
  return (
    <div
      className={`bg-zinc-900/80 border border-zinc-800 rounded-lg p-4 text-zinc-200 transition-all duration-200 ${
        hoverEffect ? 'hover:border-zinc-700 hover:bg-zinc-900 shadow-sm' : ''
      } ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

export const CardHeader: React.FC<{
  title: React.ReactNode;
  description?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}> = ({ title, description, action, className = '' }) => {
  return (
    <div className={`flex items-start justify-between gap-3 mb-3 border-b border-zinc-800/80 pb-3 ${className}`}>
      <div>
        <h3 className="text-sm font-semibold text-zinc-100 flex items-center gap-2">{title}</h3>
        {description && <p className="text-xs text-zinc-400 mt-0.5">{description}</p>}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
};
