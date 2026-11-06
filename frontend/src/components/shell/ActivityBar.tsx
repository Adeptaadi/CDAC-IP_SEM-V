import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  Zap,
  ShieldAlert,
  History,
  BookOpen,
  Cpu,
  ShieldCheck,
} from 'lucide-react';

interface ActivityBarProps {
  isBackendHealthy: boolean;
}

interface NavItem {
  to: string;
  label: string;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
  { to: '/simulate', label: 'Simulate', icon: <Zap className="w-5 h-5" /> },
  { to: '/investigate', label: 'Investigate', icon: <ShieldAlert className="w-5 h-5" /> },
  { to: '/history', label: 'History', icon: <History className="w-5 h-5" /> },
  { to: '/knowledge', label: 'Knowledge', icon: <BookOpen className="w-5 h-5" /> },
  { to: '/system', label: 'System', icon: <Cpu className="w-5 h-5" /> },
];

export const ActivityBar: React.FC<ActivityBarProps> = ({ isBackendHealthy }) => {
  return (
    <aside className="w-16 bg-zinc-950 border-r border-zinc-800 flex flex-col items-center justify-between py-4 select-none shrink-0 z-30">
      {/* Top: Brand Logo */}
      <div className="flex flex-col items-center gap-6 w-full">
        <NavLink
          to="/investigate"
          className="w-10 h-10 rounded-lg bg-blue-600/10 border border-blue-500/30 flex items-center justify-center text-blue-400 hover:text-blue-300 hover:border-blue-500/60 transition-all group"
          title="Project Sentinel"
        >
          <ShieldCheck className="w-5 h-5 transition-transform group-hover:scale-110" />
        </NavLink>

        {/* Navigation Items */}
        <nav className="flex flex-col items-center gap-1.5 w-full px-2">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `w-12 h-11 rounded-md flex flex-col items-center justify-center gap-1 transition-all duration-150 relative group ${
                  isActive
                    ? 'bg-blue-600/15 text-blue-400 font-semibold'
                    : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/60'
                }`
              }
              title={item.label}
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <span className="absolute left-0 top-2 bottom-2 w-0.5 bg-blue-500 rounded-r" />
                  )}
                  {item.icon}
                  <span className="text-[9px] font-medium tracking-tight scale-90">{item.label}</span>
                </>
              )}
            </NavLink>
          ))}
        </nav>
      </div>

      {/* Bottom: Connection Indicator */}
      <div className="flex flex-col items-center gap-2">
        <NavLink
          to="/system"
          className="flex flex-col items-center gap-1 text-[10px] text-zinc-500 hover:text-zinc-300 transition-colors"
          title={isBackendHealthy ? 'Backend Connected' : 'Backend Disconnected'}
        >
          <span
            className={`w-2 h-2 rounded-full ${
              isBackendHealthy ? 'bg-emerald-500 shadow-xs shadow-emerald-500/50' : 'bg-rose-500 animate-pulse'
            }`}
          />
        </NavLink>
      </div>
    </aside>
  );
};
