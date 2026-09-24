import React from 'react';
import { Activity, ShieldCheck, Database, GitCommit, Users, History, TrendingUp } from 'lucide-react';

interface FactorItem {
  raw_delta: number;
  weight: number;
  weighted_contribution: number;
}

interface FactorDecompositionViewProps {
  factorContributions?: Record<string, FactorItem>;
  confidenceBefore?: number;
  confidenceAfter?: number;
  confidenceDelta?: number;
  cycleNumber?: number;
}

export const FactorDecompositionView: React.FC<FactorDecompositionViewProps> = ({
  factorContributions = {},
  confidenceBefore = 0.0,
  confidenceAfter = 0.0,
  confidenceDelta = 0.0,
  cycleNumber = 1,
}) => {
  const factorMeta: Record<
    string,
    { label: string; icon: any; color: string; desc: string }
  > = {
    detection: {
      label: 'Detection Quality',
      icon: ShieldCheck,
      color: 'text-sky-400',
      desc: 'Detector confidence signal × severity multiplier',
    },
    evidence: {
      label: 'Evidence Corroboration',
      icon: Database,
      color: 'text-indigo-400',
      desc: 'Source diversity ratio & multi-source fact corroboration',
    },
    correlation: {
      label: 'Correlation Quality',
      icon: GitCommit,
      color: 'text-purple-400',
      desc: 'Entity graph density gain: edges / max(1, nodes)',
    },
    knowledge: {
      label: 'Knowledge Match (RAG)',
      icon: Activity,
      color: 'text-pink-400',
      desc: 'ChromaDB cosine similarity × source reliability (MITRE=1.0)',
    },
    agreement: {
      label: 'Worker Agreement',
      icon: Users,
      color: 'text-emerald-400',
      desc: 'Inverse variance across independent worker estimates',
    },
    historical: {
      label: 'Historical Similarity',
      icon: History,
      color: 'text-amber-400',
      desc: 'Cosine similarity against nearest episodic memory cases',
    },
  };

  const defaultKeys = ['detection', 'evidence', 'correlation', 'knowledge', 'agreement', 'historical'];

  return (
    <div className="bg-[#0e131f] border border-gray-800 rounded-xl p-4 space-y-3 shadow-lg">
      <div className="flex items-center justify-between border-b border-gray-800/80 pb-2">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-emerald-400" />
          <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-200">
            6-Factor Bayesian Confidence Decomposition (Logit Update)
          </h4>
        </div>
        <div className="flex items-center gap-2 font-mono text-[11px]">
          <span className="text-[10px] text-gray-500 font-mono">Cycle #{cycleNumber}</span>
          <span className="text-gray-400">
            {(confidenceBefore * 100).toFixed(1)}% →{' '}
            <strong className="text-emerald-400">{(confidenceAfter * 100).toFixed(1)}%</strong>
          </span>
          <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-950 text-emerald-400 border border-emerald-800/60">
            Δ {confidenceDelta >= 0 ? `+${confidenceDelta.toFixed(3)}` : confidenceDelta.toFixed(3)}
          </span>
        </div>
      </div>

      <p className="text-[11px] text-gray-400 leading-snug">
        Updates are computed in log-odds space: <code className="text-gray-300 font-mono">logit(C_t) = logit(C_t-1) + Σ (w_i · δ_i)</code> to guarantee bounded values in (0,1).
      </p>

      {/* Grid of 6 Factors */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
        {defaultKeys.map((key) => {
          const item = factorContributions[key] || {
            raw_delta: 0.0,
            weight: 0.15,
            weighted_contribution: 0.0,
          };
          const meta = factorMeta[key] || {
            label: key.toUpperCase(),
            icon: Activity,
            color: 'text-blue-400',
            desc: '',
          };
          const IconComp = meta.icon;
          const isPositive = item.weighted_contribution > 0;

          return (
            <div
              key={key}
              className="p-2.5 rounded-lg bg-gray-950/70 border border-gray-800/80 flex flex-col justify-between space-y-1 hover:border-gray-700 transition"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <IconComp className={`w-3.5 h-3.5 ${meta.color}`} />
                  <span className="text-[11px] font-semibold text-gray-200">{meta.label}</span>
                </div>
                <span
                  className={`font-mono text-xs font-bold ${
                    isPositive ? 'text-emerald-400' : 'text-gray-400'
                  }`}
                >
                  {isPositive ? `+${item.weighted_contribution.toFixed(4)}` : item.weighted_contribution.toFixed(4)}
                </span>
              </div>

              <p className="text-[10px] text-gray-500 line-clamp-1">{meta.desc}</p>

              <div className="flex items-center justify-between text-[9px] font-mono text-gray-400 pt-0.5 border-t border-gray-900">
                <span>Raw δ: <strong className="text-gray-300">{item.raw_delta.toFixed(3)}</strong></span>
                <span>Weight w: <strong className="text-gray-300">{item.weight.toFixed(2)}</strong></span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
