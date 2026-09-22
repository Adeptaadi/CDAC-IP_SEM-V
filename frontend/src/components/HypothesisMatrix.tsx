import React from 'react';
import { Target, CheckCircle, XCircle, AlertTriangle, TrendingUp, ShieldQuestion } from 'lucide-react';

export interface HypothesisItem {
  hypothesis_id: string;
  label: string;
  status: 'active' | 'strengthened' | 'weakened' | 'rejected' | 'confirmed';
  confidence: number;
  mitre_technique_ids: string[];
}

interface HypothesisMatrixProps {
  hypotheses: HypothesisItem[];
}

export const HypothesisMatrix: React.FC<HypothesisMatrixProps> = ({ hypotheses }) => {
  if (hypotheses.length === 0) {
    return (
      <div className="h-48 border border-dashed border-gray-800 rounded-xl flex flex-col items-center justify-center text-gray-500 text-xs">
        <ShieldQuestion className="w-7 h-7 text-gray-600 mb-2" />
        <p>No hypotheses formulated yet.</p>
        <p className="text-[11px] text-gray-600 mt-1">Investigation Worker will generate and test competing threat hypotheses.</p>
      </div>
    );
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'confirmed':
        return (
          <span className="bg-emerald-950 text-emerald-300 border border-emerald-800 px-2 py-0.5 rounded text-[10px] font-mono font-semibold flex items-center gap-1">
            <CheckCircle className="w-3 h-3" /> Confirmed
          </span>
        );
      case 'strengthened':
        return (
          <span className="bg-blue-950 text-blue-300 border border-blue-800 px-2 py-0.5 rounded text-[10px] font-mono font-semibold flex items-center gap-1">
            <TrendingUp className="w-3 h-3" /> Strengthened
          </span>
        );
      case 'weakened':
        return (
          <span className="bg-amber-950 text-amber-300 border border-amber-800 px-2 py-0.5 rounded text-[10px] font-mono font-semibold flex items-center gap-1">
            <AlertTriangle className="w-3 h-3" /> Weakened
          </span>
        );
      case 'rejected':
        return (
          <span className="bg-red-950 text-red-300 border border-red-800 px-2 py-0.5 rounded text-[10px] font-mono font-semibold flex items-center gap-1">
            <XCircle className="w-3 h-3" /> Rejected
          </span>
        );
      default:
        return (
          <span className="bg-gray-800 text-gray-300 border border-gray-700 px-2 py-0.5 rounded text-[10px] font-mono uppercase">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Target className="w-4 h-4 text-purple-400" />
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-300">
            Hypothesis Verification Matrix (IS §1.3)
          </span>
        </div>
        <span className="text-[10px] bg-gray-900 border border-gray-800 px-2 py-0.5 rounded text-gray-400 font-mono">
          {hypotheses.length} Hypotheses Tracked
        </span>
      </div>

      <div className="space-y-3">
        {hypotheses.map((hyp) => (
          <div
            key={hyp.hypothesis_id}
            className="bg-[#111827] border border-gray-800 p-3.5 rounded-xl space-y-2.5 transition-all hover:border-gray-700"
          >
            <div className="flex items-start justify-between gap-2">
              <h4 className="text-xs font-semibold text-white leading-snug">{hyp.label}</h4>
              {getStatusBadge(hyp.status)}
            </div>

            {/* Confidence Progress Bar */}
            <div className="space-y-1">
              <div className="flex justify-between text-[10px] font-mono">
                <span className="text-gray-400">Calculated Confidence:</span>
                <span className="text-emerald-400 font-bold">
                  {(hyp.confidence * 100).toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-gray-900 rounded-full h-1.5 overflow-hidden border border-gray-800">
                <div
                  className="h-1.5 bg-gradient-to-r from-blue-500 to-emerald-500 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(100, Math.max(0, hyp.confidence * 100))}%` }}
                />
              </div>
            </div>

            {/* MITRE Badges */}
            {hyp.mitre_technique_ids && hyp.mitre_technique_ids.length > 0 && (
              <div className="flex flex-wrap gap-1.5 pt-1">
                {hyp.mitre_technique_ids.map((tid) => (
                  <span
                    key={tid}
                    className="bg-purple-950/70 text-purple-300 border border-purple-800/80 px-1.5 py-0.5 rounded font-mono text-[10px]"
                  >
                    {tid}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
