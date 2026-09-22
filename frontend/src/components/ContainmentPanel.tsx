import React, { useState } from 'react';
import axios from 'axios';
import { ShieldCheck, Check, X, ShieldAlert, CheckCircle2, XCircle } from 'lucide-react';

export interface RecommendationItem {
  recommendation_id: string;
  report_id: string;
  action: string;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  impact_summary?: string;
  requires_approval: boolean;
  approval_status: 'pending' | 'approved' | 'rejected' | 'executed';
}

interface ContainmentPanelProps {
  recommendations: RecommendationItem[];
  apiBase: string;
  onActionComplete: () => void;
}

export const ContainmentPanel: React.FC<ContainmentPanelProps> = ({
  recommendations,
  apiBase,
  onActionComplete,
}) => {
  const [processingId, setProcessingId] = useState<string | null>(null);

  if (recommendations.length === 0) {
    return (
      <div className="h-40 border border-dashed border-gray-800 rounded-xl flex flex-col items-center justify-center text-gray-500 text-xs">
        <ShieldCheck className="w-7 h-7 text-gray-600 mb-2" />
        <p>No active containment actions pending.</p>
        <p className="text-[11px] text-gray-600 mt-1">Response Worker generates containment playbooks upon confirmed threats.</p>
      </div>
    );
  }

  const handleApprove = async (id: string) => {
    setProcessingId(id);
    try {
      await axios.post(`${apiBase}/api/planner/recommendations/${id}/approve`);
      onActionComplete();
    } catch (e) {
      console.error(e);
    } finally {
      setProcessingId(null);
    }
  };

  const handleReject = async (id: string) => {
    setProcessingId(id);
    try {
      await axios.post(`${apiBase}/api/planner/recommendations/${id}/reject`);
      onActionComplete();
    } catch (e) {
      console.error(e);
    } finally {
      setProcessingId(null);
    }
  };

  const getRiskBadge = (risk: string) => {
    switch (risk) {
      case 'critical':
        return 'bg-red-950 text-red-300 border-red-800';
      case 'high':
        return 'bg-amber-950 text-amber-300 border-amber-800';
      case 'medium':
        return 'bg-blue-950 text-blue-300 border-blue-800';
      default:
        return 'bg-gray-800 text-gray-300 border-gray-700';
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-amber-400" />
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-300">
            Containment & Response (Human-in-the-Loop)
          </span>
        </div>
        <span className="text-[10px] bg-amber-950/70 border border-amber-800 text-amber-300 px-2 py-0.5 rounded font-mono">
          Mandatory Approval Enforced
        </span>
      </div>

      <div className="space-y-3">
        {recommendations.map((rec) => (
          <div
            key={rec.recommendation_id}
            className="bg-[#111827] border border-gray-800 p-4 rounded-xl space-y-3"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="space-y-1">
                <span
                  className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border uppercase ${getRiskBadge(
                    rec.risk_level
                  )}`}
                >
                  {rec.risk_level} Risk
                </span>
                <h4 className="text-sm font-semibold text-white mt-1.5">{rec.action}</h4>
              </div>

              <div>
                {rec.approval_status === 'approved' && (
                  <span className="bg-emerald-950 text-emerald-300 border border-emerald-800 px-2.5 py-1 rounded text-xs font-mono flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Approved
                  </span>
                )}
                {rec.approval_status === 'rejected' && (
                  <span className="bg-red-950 text-red-300 border border-red-800 px-2.5 py-1 rounded text-xs font-mono flex items-center gap-1">
                    <XCircle className="w-3.5 h-3.5" /> Rejected
                  </span>
                )}
                {rec.approval_status === 'pending' && (
                  <span className="bg-amber-950 text-amber-300 border border-amber-800 px-2.5 py-1 rounded text-xs font-mono animate-pulse">
                    Pending Review
                  </span>
                )}
              </div>
            </div>

            {rec.impact_summary && (
              <p className="text-xs text-gray-300 bg-gray-900/60 p-2.5 rounded-lg border border-gray-800/80">
                <strong className="text-gray-400">Impact Analysis:</strong> {rec.impact_summary}
              </p>
            )}

            {rec.approval_status === 'pending' && (
              <div className="flex items-center justify-end gap-2 pt-1 border-t border-gray-800/60">
                <button
                  onClick={() => handleReject(rec.recommendation_id)}
                  disabled={processingId === rec.recommendation_id}
                  className="bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs px-3 py-1.5 rounded-lg border border-gray-700 flex items-center gap-1 transition"
                >
                  <X className="w-3.5 h-3.5 text-red-400" />
                  <span>Reject</span>
                </button>
                <button
                  onClick={() => handleApprove(rec.recommendation_id)}
                  disabled={processingId === rec.recommendation_id}
                  className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold px-4 py-1.5 rounded-lg flex items-center gap-1 transition shadow-lg shadow-emerald-950"
                >
                  <Check className="w-3.5 h-3.5" />
                  <span>{processingId === rec.recommendation_id ? 'Authorizing...' : 'Authorize Action'}</span>
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
