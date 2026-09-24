import React, { useState, useEffect, useRef } from 'react';
import {
  Terminal,
  Pause,
  Play,
  Trash2,
  Sparkles,
  Maximize2,
  Minimize2
} from 'lucide-react';

export interface ThoughtLog {
  id: string;
  timestamp: string;
  category: 'PLANNER' | 'UTILITY' | 'RAG' | 'WORKER' | 'BAYESIAN' | 'CONTAINMENT' | 'SYSTEM';
  workerType?: string;
  cycleNumber?: number;
  message: string;
  details?: any;
}

interface AgentThoughtStreamProps {
  logs: ThoughtLog[];
  onClearLogs?: () => void;
  isStreaming?: boolean;
}

export const AgentThoughtStream: React.FC<AgentThoughtStreamProps> = ({
  logs,
  onClearLogs,
  isStreaming = true,
}) => {
  const [autoScroll, setAutoScroll] = useState(true);
  const [filterCategory, setFilterCategory] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [isExpanded, setIsExpanded] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  const filteredLogs = logs.filter((log) => {
    if (filterCategory !== 'ALL' && log.category !== filterCategory) return false;
    if (searchQuery && !log.message.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  const getCategoryBadge = (category: ThoughtLog['category'], workerType?: string) => {
    switch (category) {
      case 'PLANNER':
        return (
          <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-cyan-950/80 text-cyan-400 border border-cyan-800/80">
            [PLANNER]
          </span>
        );
      case 'UTILITY':
        return (
          <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-950/80 text-amber-400 border border-amber-800/80">
            [UTILITY]
          </span>
        );
      case 'RAG':
        return (
          <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-purple-950/80 text-purple-300 border border-purple-800/80">
            [RAG-KNOWLEDGE]
          </span>
        );
      case 'WORKER':
        return (
          <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-950/80 text-emerald-400 border border-emerald-800/80">
            [{workerType ? workerType.toUpperCase() : 'WORKER'}]
          </span>
        );
      case 'BAYESIAN':
        return (
          <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-950/80 text-rose-400 border border-rose-800/80">
            [BAYESIAN-DELTA]
          </span>
        );
      case 'CONTAINMENT':
        return (
          <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-red-950/80 text-red-300 border border-red-800/80 animate-pulse">
            [HITL-RESPONSE]
          </span>
        );
      default:
        return (
          <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-gray-800 text-gray-400 border border-gray-700">
            [SYSTEM]
          </span>
        );
    }
  };

  return (
    <div
      className={`bg-[#0d1117] border border-gray-800 rounded-xl flex flex-col shadow-2xl transition-all duration-300 ${
        isExpanded ? 'fixed inset-4 z-50' : 'h-[440px]'
      }`}
    >
      {/* Terminal Header */}
      <div className="px-4 py-2.5 bg-gray-950/90 border-b border-gray-800 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="flex gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500/80 inline-block" />
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500/80 inline-block" />
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/80 inline-block" />
          </div>
          <div className="flex items-center gap-1.5 text-xs font-mono font-semibold text-gray-200">
            <Terminal className="w-3.5 h-3.5 text-cyan-400" />
            <span>AGENT THOUGHT STREAM & EXECUTION LOG</span>
            {isStreaming && (
              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[9px] font-mono font-bold bg-emerald-950/80 text-emerald-400 border border-emerald-800/60 ml-2 animate-pulse">
                LIVE STREAM
              </span>
            )}
          </div>
        </div>

        {/* Console Controls */}
        <div className="flex items-center gap-2">
          <div className="relative">
            <input
              type="text"
              placeholder="Search stream..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-gray-900 border border-gray-800 text-gray-300 text-[11px] font-mono px-2 py-1 rounded w-28 focus:w-40 transition-all focus:outline-none focus:border-blue-500"
            />
          </div>

          <button
            onClick={() => setAutoScroll(!autoScroll)}
            title={autoScroll ? 'Auto-scroll Enabled' : 'Auto-scroll Paused'}
            className={`p-1 rounded text-xs transition ${
              autoScroll ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30' : 'text-gray-500 hover:text-gray-300'
            }`}
          >
            {autoScroll ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
          </button>

          {onClearLogs && (
            <button
              onClick={onClearLogs}
              title="Clear Log Stream"
              className="p-1 text-gray-500 hover:text-red-400 transition"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}

          <button
            onClick={() => setIsExpanded(!isExpanded)}
            title={isExpanded ? 'Collapse' : 'Expand'}
            className="p-1 text-gray-500 hover:text-gray-300 transition"
          >
            {isExpanded ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Filter Ribbon */}
      <div className="px-3 py-1.5 bg-gray-950/50 border-b border-gray-800/70 flex items-center gap-1.5 overflow-x-auto text-[10px] font-mono">
        {['ALL', 'PLANNER', 'UTILITY', 'RAG', 'WORKER', 'BAYESIAN', 'CONTAINMENT'].map((cat) => (
          <button
            key={cat}
            onClick={() => setFilterCategory(cat)}
            className={`px-2 py-0.5 rounded transition ${
              filterCategory === cat
                ? 'bg-blue-600 text-white font-bold'
                : 'bg-gray-900/80 text-gray-400 hover:text-gray-200 border border-gray-800'
            }`}
          >
            {cat}
          </button>
        ))}
        <span className="ml-auto text-gray-500 text-[10px] font-mono whitespace-nowrap">
          {filteredLogs.length} events
        </span>
      </div>

      {/* Log Output Stream */}
      <div
        ref={scrollRef}
        className="flex-1 p-3 overflow-y-auto font-mono text-xs space-y-2 bg-[#090d13] select-text"
      >
        {filteredLogs.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-gray-600 space-y-2 py-10">
            <Sparkles className="w-6 h-6 text-gray-700 animate-pulse" />
            <p className="text-xs">Awaiting agent thoughts & planning decisions...</p>
            <p className="text-[10px] text-gray-700">Trigger Auto-Hunt or Step to observe live cognitive execution.</p>
          </div>
        ) : (
          filteredLogs.map((log) => (
            <div
              key={log.id}
              className="p-2 rounded bg-gray-950/60 border border-gray-800/60 hover:border-gray-700/80 transition space-y-1"
            >
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-[10px] text-gray-500">{log.timestamp}</span>
                {log.cycleNumber !== undefined && (
                  <span className="px-1 py-0.2 rounded text-[9px] font-bold bg-blue-950 text-blue-400 border border-blue-900">
                    Cycle #{log.cycleNumber}
                  </span>
                )}
                {getCategoryBadge(log.category, log.workerType)}
              </div>

              <div className="text-gray-200 text-[11px] leading-relaxed pl-1 whitespace-pre-wrap">
                {log.message}
              </div>

              {/* Optional JSON / Key Metric Details Dropdown */}
              {log.details && (
                <div className="mt-1 pl-2 border-l-2 border-gray-800 text-[10px] text-gray-400 bg-black/40 p-1.5 rounded font-mono overflow-x-auto">
                  {typeof log.details === 'string' ? (
                    log.details
                  ) : (
                    <pre>{JSON.stringify(log.details, null, 2)}</pre>
                  )}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};
