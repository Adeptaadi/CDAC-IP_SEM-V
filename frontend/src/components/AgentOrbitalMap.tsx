import {
  Brain,
  ShieldAlert,
  Share2,
  Search,
  FileText,
  Lock,
  Zap
} from 'lucide-react';

export interface AgentOrbitalMapProps {
  activeWorker: string | null;
  activeCycle?: number;
  confidence?: number;
  workerLatencies?: Record<string, number>;
  workerUtilities?: Record<string, number>;
  onSelectWorker?: (workerKey: string) => void;
}

export const AgentOrbitalMap: React.FC<AgentOrbitalMapProps> = ({
  activeWorker,
  activeCycle = 0,
  confidence = 0.0,
  workerLatencies = {},
  workerUtilities = {},
  onSelectWorker,
}) => {
  // 5 Orbiting Workers around Planner
  const workers = [
    {
      key: 'detection',
      name: 'Detection Worker',
      shortName: 'DETECTION',
      role: 'Raw Telemetry & Sigma Triage',
      icon: ShieldAlert,
      x: 250,
      y: 60,
      color: '#38bdf8', // sky-400
      glowColor: 'rgba(56, 189, 248, 0.4)',
    },
    {
      key: 'correlation',
      name: 'Correlation Worker',
      shortName: 'CORRELATION',
      role: 'Entity Graph & Temporal Links',
      icon: Share2,
      x: 420,
      y: 160,
      color: '#a855f7', // purple-500
      glowColor: 'rgba(168, 85, 247, 0.4)',
    },
    {
      key: 'investigation',
      name: 'Investigation Worker',
      shortName: 'INVESTIGATION',
      role: 'Hypothesis Validation & RAG',
      icon: Search,
      x: 360,
      y: 330,
      color: '#ec4899', // pink-500
      glowColor: 'rgba(236, 72, 153, 0.4)',
    },
    {
      key: 'reporting',
      name: 'Reporting Worker',
      shortName: 'REPORTING',
      role: 'Twin-Tier Forensics Synthesis',
      icon: FileText,
      x: 140,
      y: 330,
      color: '#10b981', // emerald-500
      glowColor: 'rgba(16, 185, 129, 0.4)',
    },
    {
      key: 'response',
      name: 'Response Worker',
      shortName: 'RESPONSE',
      role: 'HITL Containment Strategy',
      icon: Lock,
      x: 80,
      y: 160,
      color: '#f59e0b', // amber-500
      glowColor: 'rgba(245, 158, 11, 0.4)',
    },
  ];

  const plannerX = 250;
  const plannerY = 200;

  return (
    <div className="bg-[#0b0f17] border border-gray-800 rounded-xl p-4 flex flex-col items-center relative overflow-hidden shadow-xl">
      {/* Background Orbital Rings */}
      <div className="absolute inset-0 pointer-events-none flex items-center justify-center opacity-20">
        <div className="w-[360px] h-[360px] rounded-full border border-dashed border-blue-500 animate-spin-slow" />
        <div className="absolute w-[240px] h-[240px] rounded-full border border-gray-700" />
      </div>

      {/* Header bar */}
      <div className="w-full flex items-center justify-between z-10 mb-2 border-b border-gray-800/80 pb-2">
        <div className="flex items-center gap-2">
          <Zap className="w-4 h-4 text-cyan-400 animate-pulse" />
          <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-200">
            Multi-Agent Cognitive Topology & Task Dispatch
          </h3>
        </div>
        <div className="flex items-center gap-2 text-[10px] font-mono">
          <span className="text-gray-400">
            Cycle: <strong className="text-blue-400">#{activeCycle}</strong>
          </span>
          <span className="text-gray-600">|</span>
          <span className="text-gray-400">
            Conf: <strong className="text-emerald-400">{(confidence * 100).toFixed(1)}%</strong>
          </span>
        </div>
      </div>

      {/* SVG Canvas for Links and Nodes */}
      <svg viewBox="0 0 500 400" className="w-full max-w-[500px] h-[320px] select-none">
        <defs>
          <radialGradient id="plannerGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.6" />
            <stop offset="100%" stopColor="#1e3a8a" stopOpacity="0.0" />
          </radialGradient>
          <linearGradient id="activeBeam" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#60a5fa" />
            <stop offset="100%" stopColor="#38bdf8" />
          </linearGradient>
        </defs>

        {/* Orbit Path Lines from Planner to Workers */}
        {workers.map((w) => {
          const isActive = activeWorker?.toLowerCase() === w.key;
          return (
            <g key={`link-${w.key}`}>
              {/* Static Background Guide */}
              <line
                x1={plannerX}
                y1={plannerY}
                x2={w.x}
                y2={w.y}
                stroke={isActive ? w.color : '#374151'}
                strokeWidth={isActive ? 2.5 : 1}
                strokeDasharray={isActive ? '4 2' : '2 2'}
                className={isActive ? 'animate-pulse' : ''}
              />
              {/* Animated Glowing Packet Beam when Active */}
              {isActive && (
                <circle r="4" fill="#60a5fa">
                  <animateMotion
                    dur="1.2s"
                    repeatCount="indefinite"
                    path={`M ${plannerX} ${plannerY} L ${w.x} ${w.y}`}
                  />
                </circle>
              )}
            </g>
          );
        })}

        {/* Central Planner Engine Node */}
        <g transform={`translate(${plannerX}, ${plannerY})`}>
          <circle r="44" fill="url(#plannerGlow)" className="animate-pulse" />
          <circle r="32" fill="#0f172a" stroke="#3b82f6" strokeWidth="2.5" />
          <foreignObject x="-24" y="-24" width="48" height="48" className="pointer-events-none">
            <div className="w-full h-full flex flex-col items-center justify-center text-blue-400">
              <Brain className="w-6 h-6 animate-pulse" />
            </div>
          </foreignObject>
          <text
            y="44"
            textAnchor="middle"
            className="fill-blue-300 font-mono text-[10px] font-bold tracking-wider"
          >
            PLANNER ENGINE
          </text>
        </g>

        {/* 5 Orbiting Specialist Worker Nodes */}
        {workers.map((w) => {
          const isActive = activeWorker?.toLowerCase() === w.key;
          const latency = workerLatencies[w.key];
          const utility = workerUtilities[w.key];
          const IconComp = w.icon;

          return (
            <g
              key={w.key}
              transform={`translate(${w.x}, ${w.y})`}
              className="cursor-pointer group"
              onClick={() => onSelectWorker && onSelectWorker(w.key)}
            >
              {/* Outer Glow Halo for Active Worker */}
              {isActive && (
                <circle
                  r="28"
                  fill="none"
                  stroke={w.color}
                  strokeWidth="2"
                  className="animate-ping"
                  style={{ transformOrigin: '0 0' }}
                />
              )}

              {/* Node Background */}
              <circle
                r="22"
                fill={isActive ? '#1e293b' : '#0f172a'}
                stroke={isActive ? w.color : '#475569'}
                strokeWidth={isActive ? '2.5' : '1.5'}
                className="transition-all duration-300 group-hover:stroke-white"
              />

              <foreignObject x="-14" y="-14" width="28" height="28" className="pointer-events-none">
                <div
                  className="w-full h-full flex items-center justify-center"
                  style={{ color: isActive ? w.color : '#94a3b8' }}
                >
                  <IconComp className="w-4 h-4" />
                </div>
              </foreignObject>

              {/* Worker Name Label */}
              <text
                y="32"
                textAnchor="middle"
                className={`font-mono text-[9px] font-bold tracking-tight ${
                  isActive ? 'fill-white' : 'fill-gray-400 group-hover:fill-gray-200'
                }`}
              >
                {w.shortName}
              </text>

              {/* Utility Score Badge */}
              {utility !== undefined && (
                <text
                  y="-26"
                  textAnchor="middle"
                  className="fill-amber-400 font-mono text-[8px] font-semibold"
                >
                  U: {utility.toFixed(2)}
                </text>
              )}

              {/* Active / Latency Indicator */}
              {isActive && latency !== undefined && (
                <text
                  y="42"
                  textAnchor="middle"
                  className="fill-emerald-400 font-mono text-[8px] font-semibold"
                >
                  {latency}ms
                </text>
              )}
            </g>
          );
        })}
      </svg>
    </div>
  );
};
