import React from 'react';
import { GitBranch, Radio, Cpu } from 'lucide-react';

interface StatusBarProps {
  scenarioName?: string;
  investigationTitle?: string;
  cycleNumber: number;
  confidence: number;
  confidenceState: string;
  activeWorker: string | null;
  apiHealthy: boolean;
  wsConnected: boolean;
  replayState: string;
}

export const StatusBar: React.FC<StatusBarProps> = ({
  scenarioName,
  investigationTitle,
  cycleNumber,
  confidence,
  confidenceState,
  activeWorker,
  apiHealthy,
  wsConnected,
  replayState,
}) => {
  return (
    <footer className="h-6 bg-[#070A12] border-t border-gray-800/80 px-3 flex items-center justify-between text-[11px] font-mono text-gray-400 select-none shrink-0 z-30">
      {/* Left Status Group */}
      <div className="flex items-center gap-3">
        {/* Project Sentinel Status Badge */}
        <div className="flex items-center gap-1.5 text-blue-400 font-semibold">
          <GitBranch className="w-3 h-3 text-gray-500" />
          <span>sentinel/main</span>
        </div>

        <span className="text-gray-700">|</span>

        {/* Replay State */}
        <div className="flex items-center gap-1.5">
          <Radio className="w-3 h-3 text-purple-400" />
          <span>Scenario: <strong className="text-gray-200">{scenarioName || 'Idle'}</strong></span>
          <span className={`text-[9px] px-1 rounded uppercase ${replayState === 'PLAYING' ? 'bg-emerald-950 text-emerald-400' : 'bg-gray-800 text-gray-400'}`}>
            {replayState}
          </span>
        </div>

        <span className="text-gray-700">|</span>

        {/* Investigation Title */}
        <div className="truncate max-w-[200px] text-gray-300">
          <span>{investigationTitle || 'No active investigation'}</span>
        </div>
      </div>

      {/* Right Status Group */}
      <div className="flex items-center gap-3">
        {/* Active Worker */}
        <div className="flex items-center gap-1.5">
          <Cpu className="w-3 h-3 text-cyan-400" />
          <span>Worker: <strong className="text-gray-200">{activeWorker || 'idle'}</strong></span>
        </div>

        <span className="text-gray-700">|</span>

        {/* Planning Cycle & Confidence */}
        <div>
          <span>C-{cycleNumber}</span>
          <span className="mx-1 text-gray-600">:</span>
          <span className={`font-semibold ${confidence >= 0.75 ? 'text-red-400' : confidence >= 0.4 ? 'text-amber-400' : 'text-emerald-400'}`}>
            {(confidence * 100).toFixed(0)}% ({confidenceState})
          </span>
        </div>

        <span className="text-gray-700">|</span>

        {/* Local LLM Sidecar */}
        <div className="flex items-center gap-1 text-purple-400">
          <span>Ollama: qwen2.5</span>
        </div>

        <span className="text-gray-700">|</span>

        {/* Gateway & WebSocket Health */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 text-[10px]" title="API Gateway Status">
            <span className={`w-1.5 h-1.5 rounded-full ${apiHealthy ? 'bg-emerald-400' : 'bg-red-500'}`} />
            <span>API: 8000</span>
          </div>

          <div className="flex items-center gap-1 text-[10px]" title="Live WebSocket Event Bus">
            <span className={`w-1.5 h-1.5 rounded-full ${wsConnected ? 'bg-emerald-400' : 'bg-gray-600'}`} />
            <span>WS</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
