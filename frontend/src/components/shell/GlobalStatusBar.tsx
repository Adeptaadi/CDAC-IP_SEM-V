import React from 'react';
import { Activity, Shield, Terminal } from 'lucide-react';

interface GlobalStatusBarProps {
  isBackendHealthy: boolean;
  activeInvestigationTitle?: string | null;
  activeCycle?: number | null;
}

export const GlobalStatusBar: React.FC<GlobalStatusBarProps> = ({
  isBackendHealthy,
  activeInvestigationTitle,
  activeCycle,
}) => {
  return (
    <footer className="h-7 bg-zinc-950 border-t border-zinc-800/80 px-3 flex items-center justify-between text-[11px] font-mono text-zinc-400 select-none shrink-0 z-30">
      <div className="flex items-center gap-3">
        {/* Backend status pill */}
        <div className="flex items-center gap-1.5">
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              isBackendHealthy ? 'bg-emerald-500' : 'bg-rose-500'
            }`}
          />
          <span className={isBackendHealthy ? 'text-zinc-300' : 'text-rose-400'}>
            {isBackendHealthy ? 'API GATEWAY LIVE' : 'GATEWAY DISCONNECTED'}
          </span>
        </div>

        <span className="text-zinc-700">|</span>

        {/* System ID */}
        <div className="flex items-center gap-1 text-zinc-500">
          <Shield className="w-3 h-3 text-blue-500/70" />
          <span>PROJECT SENTINEL v1.0.0</span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {activeInvestigationTitle && (
          <div className="flex items-center gap-1.5 text-zinc-300">
            <Activity className="w-3 h-3 text-blue-400" />
            <span className="truncate max-w-xs">{activeInvestigationTitle}</span>
            {activeCycle !== undefined && activeCycle !== null && (
              <span className="text-zinc-500">· Cycle {activeCycle}</span>
            )}
          </div>
        )}

        <span className="text-zinc-700">|</span>

        <div className="flex items-center gap-1 text-zinc-500">
          <Terminal className="w-3 h-3" />
          <span>PORT 8000</span>
        </div>
      </div>
    </footer>
  );
};
