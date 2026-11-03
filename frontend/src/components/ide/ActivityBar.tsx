import React from 'react';
import {
  FolderKanban,
  Radar,
  ShieldCheck,
  BarChart3,
  BookOpen,
  Settings,
  Terminal as TerminalIcon,
  Sparkles
} from 'lucide-react';

export type ActivityBarItem =
  | 'explorer'
  | 'studio'
  | 'containment'
  | 'benchmarks'
  | 'knowledge'
  | 'settings';

interface ActivityBarProps {
  activeItem: ActivityBarItem;
  onSelectItem: (item: ActivityBarItem) => void;
  copilotOpen: boolean;
  onToggleCopilot: () => void;
  bottomDockOpen: boolean;
  onToggleBottomDock: () => void;
  apiHealthy: boolean;
  pendingApprovalsCount: number;
}

export const ActivityBar: React.FC<ActivityBarProps> = ({
  activeItem,
  onSelectItem,
  copilotOpen,
  onToggleCopilot,
  bottomDockOpen,
  onToggleBottomDock,
  apiHealthy,
  pendingApprovalsCount,
}) => {
  const items: Array<{ id: ActivityBarItem; label: string; icon: React.ReactNode; badge?: number }> = [
    { id: 'explorer', label: 'Explorer (Hunts & Scenarios)', icon: <FolderKanban className="w-5 h-5" /> },
    { id: 'studio', label: 'Threat Studio (Investigation Canvas)', icon: <Radar className="w-5 h-5" /> },
    {
      id: 'containment',
      label: 'Containment (HITL Governance)',
      icon: <ShieldCheck className="w-5 h-5" />,
      badge: pendingApprovalsCount > 0 ? pendingApprovalsCount : undefined,
    },
    { id: 'benchmarks', label: 'Benchmark Lab (5 Scenarios)', icon: <BarChart3 className="w-5 h-5" /> },
    { id: 'knowledge', label: 'Knowledge RAG & ATT&CK', icon: <BookOpen className="w-5 h-5" /> },
    { id: 'settings', label: 'Settings & Orchestration', icon: <Settings className="w-5 h-5" /> },
  ];

  return (
    <div className="w-12 bg-[#090D16] border-r border-gray-800/80 flex flex-col items-center py-2 select-none z-30 shrink-0 justify-between">
      {/* Top Activity Icons */}
      <div className="flex flex-col items-center gap-1 w-full">
        {/* Antigravity Logo / Brand Mark */}
        <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-600 to-indigo-700 flex items-center justify-center text-white font-black text-sm shadow-lg shadow-blue-900/30 mb-2 cursor-pointer hover:scale-105 transition" title="Project Sentinel — Antigravity IDE">
          <span>Δ</span>
        </div>

        {items.map((it) => {
          const isActive = activeItem === it.id;
          return (
            <button
              key={it.id}
              onClick={() => onSelectItem(it.id)}
              title={it.label}
              className={`relative w-10 h-10 flex items-center justify-center rounded-lg transition-all group ${
                isActive
                  ? 'text-white bg-blue-600/20 text-blue-400'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
              }`}
            >
              {/* Active left indicator strip */}
              {isActive && (
                <span className="absolute left-0 top-2 bottom-2 w-0.5 bg-blue-500 rounded-r" />
              )}
              {it.icon}

              {/* Badge for pending items (e.g. containment) */}
              {it.badge !== undefined && (
                <span className="absolute top-1.5 right-1.5 w-4 h-4 bg-amber-500 text-black text-[10px] font-bold rounded-full flex items-center justify-center animate-pulse">
                  {it.badge}
                </span>
              )}

              {/* Tooltip */}
              <span className="absolute left-14 bg-gray-900 text-gray-200 text-xs px-2.5 py-1 rounded shadow-xl border border-gray-700 pointer-events-none opacity-0 group-hover:opacity-100 transition whitespace-nowrap z-50">
                {it.label}
              </span>
            </button>
          );
        })}
      </div>

      {/* Bottom Auxiliary Toggles */}
      <div className="flex flex-col items-center gap-1 w-full pb-1">
        {/* Copilot Toggle */}
        <button
          onClick={onToggleCopilot}
          title={copilotOpen ? 'Close Agent Copilot (Ctrl+J)' : 'Open Agent Copilot (Ctrl+J)'}
          className={`relative w-10 h-10 flex items-center justify-center rounded-lg transition group ${
            copilotOpen
              ? 'text-purple-400 bg-purple-600/20'
              : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
          }`}
        >
          <Sparkles className="w-5 h-5" />
          <span className="absolute left-14 bg-gray-900 text-gray-200 text-xs px-2.5 py-1 rounded shadow-xl border border-gray-700 pointer-events-none opacity-0 group-hover:opacity-100 transition whitespace-nowrap z-50">
            {copilotOpen ? 'Collapse Agent Copilot' : 'Open Agent Copilot'}
          </span>
        </button>

        {/* Bottom Dock Console Toggle */}
        <button
          onClick={onToggleBottomDock}
          title={bottomDockOpen ? 'Close Telemetry Dock (`~`)' : 'Open Telemetry Dock (`~`)'}
          className={`relative w-10 h-10 flex items-center justify-center rounded-lg transition group ${
            bottomDockOpen
              ? 'text-emerald-400 bg-emerald-600/20'
              : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
          }`}
        >
          <TerminalIcon className="w-5 h-5" />
          <span className="absolute left-14 bg-gray-900 text-gray-200 text-xs px-2.5 py-1 rounded shadow-xl border border-gray-700 pointer-events-none opacity-0 group-hover:opacity-100 transition whitespace-nowrap z-50">
            {bottomDockOpen ? 'Hide Bottom Dock' : 'Show Bottom Dock'}
          </span>
        </button>

        {/* API Health Orb */}
        <div
          className="w-10 h-10 flex items-center justify-center group relative cursor-pointer"
          title={`Gateway API: ${apiHealthy ? 'Connected (localhost:8000)' : 'Offline'}`}
        >
          <span
            className={`w-2.5 h-2.5 rounded-full ring-2 ring-gray-900 ${
              apiHealthy ? 'bg-emerald-500 shadow-sm shadow-emerald-500/50' : 'bg-red-500'
            }`}
          />
          <span className="absolute left-14 bg-gray-900 text-gray-200 text-xs px-2.5 py-1 rounded shadow-xl border border-gray-700 pointer-events-none opacity-0 group-hover:opacity-100 transition whitespace-nowrap z-50">
            API: {apiHealthy ? 'Online' : 'Disconnected'}
          </span>
        </div>
      </div>
    </div>
  );
};
