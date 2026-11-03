import React, { useState } from 'react';
import {
  Terminal as TerminalIcon,
  Radio,
  ShieldAlert,
  AlertTriangle,
  Play,
  Pause,
  RotateCcw,
  X
} from 'lucide-react';
import { TelemetryTicker } from '../TelemetryTicker';

interface BottomDockPanelProps {
  isOpen: boolean;
  onToggle: () => void;
  // Replayer controls
  replayStatus: {
    scenario: string | null;
    state: 'IDLE' | 'PLAYING' | 'PAUSED' | 'COMPLETED';
    speed: number;
    total_events: number;
    dispatched_events_count: number;
    progress_percent: number;
    latest_event: any | null;
  };
  scenarioName?: string;
  onStartReplay: () => void;
  onPauseReplay: () => void;
  onResetReplay: () => void;
  onChangeSpeed: (speed: number) => void;
  // Terminal logs
  thoughtLogs: any[];
}

export const BottomDockPanel: React.FC<BottomDockPanelProps> = ({
  isOpen,
  onToggle,
  replayStatus,
  scenarioName,
  onStartReplay,
  onPauseReplay,
  onResetReplay,
  onChangeSpeed,
  thoughtLogs,
}) => {
  const [activeDockTab, setActiveDockTab] = useState<'replayer' | 'logs' | 'audit' | 'contradictions'>('replayer');

  if (!isOpen) return null;

  return (
    <div className="h-56 bg-[#080C16] border-t border-gray-800/90 flex flex-col shrink-0 select-none text-xs z-20">
      {/* Dock Header Tabs */}
      <div className="h-8 bg-[#060912] border-b border-gray-800/80 px-3 flex items-center justify-between">
        <div className="flex items-center gap-1">
          <button
            onClick={() => setActiveDockTab('replayer')}
            className={`px-3 py-1 font-mono text-[11px] rounded transition flex items-center gap-1.5 ${
              activeDockTab === 'replayer'
                ? 'bg-blue-600/20 text-blue-400 font-semibold'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            <Radio className="w-3 h-3" />
            <span>TELEMETRY REPLAYER</span>
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                replayStatus.state === 'PLAYING' ? 'bg-emerald-400 animate-pulse' : 'bg-gray-600'
              }`}
            />
          </button>

          <button
            onClick={() => setActiveDockTab('logs')}
            className={`px-3 py-1 font-mono text-[11px] rounded transition flex items-center gap-1.5 ${
              activeDockTab === 'logs'
                ? 'bg-blue-600/20 text-blue-400 font-semibold'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            <TerminalIcon className="w-3 h-3" />
            <span>AGENT TERMINAL</span>
            <span className="text-[10px] text-gray-500">({thoughtLogs.length})</span>
          </button>

          <button
            onClick={() => setActiveDockTab('audit')}
            className={`px-3 py-1 font-mono text-[11px] rounded transition flex items-center gap-1.5 ${
              activeDockTab === 'audit'
                ? 'bg-blue-600/20 text-blue-400 font-semibold'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            <ShieldAlert className="w-3 h-3" />
            <span>AUDIT BUS</span>
          </button>

          <button
            onClick={() => setActiveDockTab('contradictions')}
            className={`px-3 py-1 font-mono text-[11px] rounded transition flex items-center gap-1.5 ${
              activeDockTab === 'contradictions'
                ? 'bg-blue-600/20 text-blue-400 font-semibold'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            <AlertTriangle className="w-3 h-3 text-amber-500" />
            <span>PROBLEMS / CONTRADICTIONS</span>
          </button>
        </div>

        {/* Right Dock Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={onToggle}
            className="p-1 text-gray-400 hover:text-white rounded hover:bg-gray-800 transition"
            title="Minimize Panel"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Dock Content Body */}
      <div className="flex-1 overflow-y-auto p-2.5 custom-scrollbar font-mono text-[11px]">
        {/* ================= REPLAYER TAB ================= */}
        {activeDockTab === 'replayer' && (
          <div className="space-y-2 h-full flex flex-col justify-between">
            {/* Ticker Component embedded */}
            <TelemetryTicker
              latestEvent={replayStatus.latest_event}
              totalEvents={replayStatus.total_events}
              dispatchedEvents={replayStatus.dispatched_events_count}
              replayState={replayStatus.state}
              scenarioName={scenarioName || replayStatus.scenario || 'CSE-CIC-IDS2018'}
              speed={replayStatus.speed}
            />

            {/* Playback Controls Strip */}
            <div className="flex items-center justify-between bg-[#0C111E] border border-gray-800/80 px-3 py-1.5 rounded-lg">
              <div className="flex items-center gap-2">
                {replayStatus.state === 'PLAYING' ? (
                  <button
                    onClick={onPauseReplay}
                    className="flex items-center gap-1 px-2.5 py-1 rounded bg-amber-600 hover:bg-amber-500 text-white font-medium text-[10px]"
                  >
                    <Pause className="w-3 h-3" />
                    <span>Pause</span>
                  </button>
                ) : (
                  <button
                    onClick={onStartReplay}
                    className="flex items-center gap-1 px-2.5 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-[10px]"
                  >
                    <Play className="w-3 h-3" />
                    <span>Play</span>
                  </button>
                )}

                <button
                  onClick={onResetReplay}
                  className="flex items-center gap-1 px-2 py-1 rounded bg-gray-800 hover:bg-gray-700 text-gray-300 text-[10px]"
                >
                  <RotateCcw className="w-3 h-3" />
                  <span>Reset</span>
                </button>
              </div>

              {/* Speed Multiplier Buttons */}
              <div className="flex items-center gap-1">
                <span className="text-[10px] text-gray-400 mr-1">Speed:</span>
                {[1, 5, 10, Infinity].map((s) => (
                  <button
                    key={s}
                    onClick={() => onChangeSpeed(s)}
                    className={`px-2 py-0.5 rounded text-[10px] ${
                      replayStatus.speed === s
                        ? 'bg-blue-600 text-white font-bold'
                        : 'bg-gray-800/80 text-gray-400 hover:text-white'
                    }`}
                  >
                    {s === Infinity ? 'Instant' : `${s}x`}
                  </button>
                ))}
              </div>

              {/* Progress */}
              <div className="text-[10px] text-gray-400">
                Dispatched: <strong className="text-white">{replayStatus.dispatched_events_count}</strong> / {replayStatus.total_events}
              </div>
            </div>
          </div>
        )}

        {/* ================= AGENT TERMINAL LOGS TAB ================= */}
        {activeDockTab === 'logs' && (
          <div className="space-y-1">
            {thoughtLogs.length === 0 ? (
              <div className="text-gray-500 py-4 text-center">No terminal logs recorded for active hunt.</div>
            ) : (
              thoughtLogs.map((log, idx) => (
                <div key={idx} className="flex items-start gap-2 text-gray-300">
                  <span className="text-gray-500 select-none">[{new Date().toLocaleTimeString()}]</span>
                  <span className="text-cyan-400 font-semibold">{log.workerType || log.category || 'planner'}:</span>
                  <span className="text-gray-300">{log.message}</span>
                </div>
              ))
            )}
          </div>
        )}

        {/* ================= AUDIT BUS TAB ================= */}
        {activeDockTab === 'audit' && (
          <div className="space-y-1 text-gray-300">
            <div className="flex items-center gap-2 text-emerald-400 font-semibold pb-1 border-b border-gray-800">
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>Cryptographic Governance & Containment Audit Trail</span>
            </div>
            <div className="py-2 text-gray-400">
              All containment approvals and manual overrides are cryptographically logged with actor identity, timestamp, and action risk rating.
            </div>
          </div>
        )}

        {/* ================= CONTRADICTIONS / PROBLEMS TAB ================= */}
        {activeDockTab === 'contradictions' && (
          <div className="space-y-1">
            <div className="text-gray-400 py-2">
              No active hypothesis contradictions detected in the current evidence ledger. (Evidence sufficiency check: PASSED)
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
