import React, { useState, useRef, useEffect } from 'react';
import {
  Sparkles,
  Send,
  Play,
  Zap
} from 'lucide-react';
import { ThoughtLog } from '../AgentThoughtStream';

interface AgentCopilotPaneProps {
  confidence: number;
  activeWorker: string | null;
  thoughtLogs: ThoughtLog[];
  onExecuteCycle: () => Promise<void>;
  onExecuteAuto: () => Promise<void>;
  isRunningAuto: boolean;
  isExecutingStep: boolean;
  onOpenView: (viewId: string) => void;
}

export const AgentCopilotPane: React.FC<AgentCopilotPaneProps> = ({
  confidence,
  activeWorker,
  thoughtLogs,
  onExecuteCycle,
  onExecuteAuto,
  isRunningAuto,
  isExecutingStep,
  onOpenView,
}) => {
  const [commandInput, setCommandInput] = useState('');
  const [slashMenuOpen, setSlashMenuOpen] = useState(false);
  const [selectedSlashIndex, setSelectedSlashIndex] = useState(0);
  const [commandHistory, setCommandHistory] = useState<Array<{ sender: 'user' | 'agent'; text: string; time: string }>>([
    {
      sender: 'agent',
      text: 'Antigravity Threat Hunting Copilot initialized. Type / to view autonomous commands (/hunt, /contain, /report, /plan).',
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const slashCommands = [
    { cmd: '/hunt', desc: 'Trigger 1 autonomous investigation cycle', action: onExecuteCycle },
    { cmd: '/autohunt', desc: 'Run multi-cycle autonomous loop to convergence', action: onExecuteAuto },
    { cmd: '/contain', desc: 'Inspect pending HITL containment approvals', action: () => onOpenView('containment') },
    { cmd: '/report', desc: 'View generated forensic incident report', action: () => onOpenView('reports') },
    { cmd: '/graph', desc: 'Open cross-telemetry entity graph', action: () => onOpenView('graph') },
    { cmd: '/timeline', desc: 'Open reconstructed attack timeline', action: () => onOpenView('timeline') },
    { cmd: '/math', desc: 'Inspect Bayesian logit factor contributions', action: () => onOpenView('math') },
    { cmd: '/clear', desc: 'Clear interactive copilot prompt log', action: () => setCommandHistory([]) },
  ];

  const filteredCommands = slashCommands.filter((s) =>
    s.cmd.toLowerCase().startsWith(commandInput.toLowerCase())
  );

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [commandHistory, thoughtLogs]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setCommandInput(val);
    if (val.startsWith('/')) {
      setSlashMenuOpen(true);
      setSelectedSlashIndex(0);
    } else {
      setSlashMenuOpen(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (slashMenuOpen) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedSlashIndex((prev) => (prev + 1) % filteredCommands.length);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedSlashIndex((prev) => (prev - 1 + filteredCommands.length) % filteredCommands.length);
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (filteredCommands[selectedSlashIndex]) {
          executeCommand(filteredCommands[selectedSlashIndex].cmd);
        }
      } else if (e.key === 'Escape') {
        setSlashMenuOpen(false);
      }
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (commandInput.trim()) {
        executeCommand(commandInput.trim());
      }
    }
  };

  const executeCommand = async (rawCmd: string) => {
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    setCommandHistory((prev) => [...prev, { sender: 'user', text: rawCmd, time }]);
    setCommandInput('');
    setSlashMenuOpen(false);

    const match = slashCommands.find((s) => s.cmd.toLowerCase() === rawCmd.toLowerCase());
    if (match) {
      try {
        await match.action();
        setCommandHistory((prev) => [
          ...prev,
          { sender: 'agent', text: `Command ${match.cmd} completed successfully.`, time },
        ]);
      } catch (err: any) {
        setCommandHistory((prev) => [
          ...prev,
          { sender: 'agent', text: `Error running ${match.cmd}: ${err.message}`, time },
        ]);
      }
    } else {
      // General question / reasoning fallback
      setCommandHistory((prev) => [
        ...prev,
        {
          sender: 'agent',
          text: `Investigating prompt "${rawCmd}" against live telemetry graph... (Use /hunt to trigger planning cycle)`,
          time,
        },
      ]);
    }
  };

  return (
    <div className="w-80 bg-[#0A0E18] border-l border-gray-800/80 flex flex-col h-full shrink-0 select-none text-xs">
      {/* Copilot Header */}
      <div className="h-9 px-3 border-b border-gray-800/80 flex items-center justify-between bg-[#080B14]">
        <div className="flex items-center gap-1.5 font-semibold text-purple-400">
          <Sparkles className="w-4 h-4" />
          <span>Antigravity Copilot</span>
        </div>
        <div className="flex items-center gap-1.5 font-mono text-[10px]">
          <span className="w-2 h-2 rounded-full bg-purple-500 animate-pulse" />
          <span className="text-gray-400">qwen2.5</span>
        </div>
      </div>

      {/* Agent Status Badge & Quick Controls */}
      <div className="p-3 bg-gradient-to-b from-[#0F1424] to-[#0A0E18] border-b border-gray-800/80 space-y-2">
        <div className="flex items-center justify-between text-[11px]">
          <span className="text-gray-400">Active Specialist:</span>
          <span className="font-mono text-cyan-400 font-semibold uppercase">
            {activeWorker ? `${activeWorker}_worker` : 'idle'}
          </span>
        </div>

        {/* Confidence Progress Bar */}
        <div>
          <div className="flex items-center justify-between text-[10px] mb-1">
            <span className="text-gray-400">Threat Posterior</span>
            <span className="font-mono font-bold text-white">{(confidence * 100).toFixed(1)}%</span>
          </div>
          <div className="w-full bg-gray-800 h-1.5 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-500 rounded-full ${
                confidence >= 0.75 ? 'bg-red-500' : confidence >= 0.4 ? 'bg-amber-500' : 'bg-emerald-500'
              }`}
              style={{ width: `${Math.min(100, Math.max(5, confidence * 100))}%` }}
            />
          </div>
        </div>

        {/* 1-Click Action Bar */}
        <div className="grid grid-cols-2 gap-1.5 pt-1">
          <button
            onClick={onExecuteCycle}
            disabled={isExecutingStep || isRunningAuto}
            className="flex items-center justify-center gap-1 py-1 px-2 rounded bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-medium text-[11px] transition shadow-sm"
          >
            <Play className="w-3 h-3" />
            <span>Step Cycle</span>
          </button>
          <button
            onClick={onExecuteAuto}
            disabled={isExecutingStep}
            className="flex items-center justify-center gap-1 py-1 px-2 rounded bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white font-medium text-[11px] transition shadow-sm"
          >
            <Zap className="w-3 h-3" />
            <span>{isRunningAuto ? 'Halting...' : 'Auto Hunt'}</span>
          </button>
        </div>
      </div>

      {/* Main Conversation & Thought Stream Feed */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3 custom-scrollbar">
        {/* Interaction History */}
        {commandHistory.map((item, idx) => (
          <div
            key={idx}
            className={`flex flex-col text-[11px] ${
              item.sender === 'user' ? 'items-end' : 'items-start'
            }`}
          >
            <div
              className={`p-2 rounded-lg max-w-[90%] leading-relaxed ${
                item.sender === 'user'
                  ? 'bg-blue-600 text-white font-mono text-[10px]'
                  : 'bg-gray-900 border border-gray-800 text-gray-200'
              }`}
            >
              {item.text}
            </div>
            <span className="text-[9px] text-gray-500 mt-0.5 px-1">{item.time}</span>
          </div>
        ))}

        {/* Live Thought Stream Cards */}
        {thoughtLogs.length > 0 && (
          <div className="pt-2 border-t border-gray-800/80 space-y-2">
            <span className="text-[10px] uppercase tracking-wider font-semibold text-gray-400 block">
              Autonomous Agent Decision Stream
            </span>
            {thoughtLogs.slice(-4).map((log, i) => (
              <div key={i} className="p-2 rounded bg-[#070A12] border border-gray-800/80 font-mono text-[10px] space-y-1">
                <div className="flex items-center justify-between text-blue-400">
                  <span className="font-semibold">{log.workerType || log.category}</span>
                  {log.cycleNumber !== undefined && <span className="text-gray-500">C-{log.cycleNumber}</span>}
                </div>
                <div className="text-gray-300 line-clamp-3">{log.message}</div>
                {log.details?.confidence_after !== undefined && (
                  <div className="flex items-center justify-between text-[9px] text-gray-500 pt-0.5">
                    <span>Conf: {(log.details.confidence_after * 100).toFixed(0)}%</span>
                    <span className="text-emerald-400">Δ Bayesian Gain</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Slash Command Autocomplete Dropdown */}
      {slashMenuOpen && filteredCommands.length > 0 && (
        <div className="mx-2 mb-1 bg-[#111625] border border-blue-500/50 rounded-lg shadow-2xl p-1 z-50 text-[11px] font-mono">
          <div className="px-2 py-1 text-[10px] uppercase font-semibold text-gray-400 border-b border-gray-800">
            Slash Commands
          </div>
          {filteredCommands.map((sc, i) => (
            <div
              key={sc.cmd}
              onClick={() => executeCommand(sc.cmd)}
              className={`px-2 py-1.5 rounded cursor-pointer flex items-center justify-between ${
                i === selectedSlashIndex ? 'bg-blue-600 text-white' : 'hover:bg-gray-800 text-gray-300'
              }`}
            >
              <span className="font-bold">{sc.cmd}</span>
              <span className="text-[10px] text-gray-400">{sc.desc}</span>
            </div>
          ))}
        </div>
      )}

      {/* Copilot Input Terminal */}
      <div className="p-2 border-t border-gray-800/80 bg-[#080B14]">
        <div className="relative flex items-center">
          <input
            type="text"
            placeholder="Type / for commands (/hunt, /contain)..."
            value={commandInput}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            className="w-full bg-black/60 border border-gray-700/80 rounded-lg pl-3 pr-8 py-1.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 font-mono"
          />
          <button
            onClick={() => commandInput.trim() && executeCommand(commandInput.trim())}
            className="absolute right-1.5 p-1 text-gray-400 hover:text-white rounded"
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
