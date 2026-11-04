import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  ShieldCheck,
  Check,
  X,
  ShieldAlert,
} from 'lucide-react';

export interface RecommendationItem {
  recommendation_id: string;
  report_id: string;
  action: string;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  impact_summary?: string;
  requires_approval: boolean;
  approval_status: 'pending' | 'approved' | 'rejected' | 'executed';
}

interface HumanReviewItem {
  review_id: string;
  investigation_id: string;
  requested_action: string;
  risk_level: string;
  status: string;
  created_at: string;
}

interface SimulationResultItem {
  action: string;
  target_identifier: string;
  status: string;
  blast_radius: string;
  service_disruption: string;
  safety_assessment: string;
  rollback_plan: string;
}

interface ContainmentPanelProps {
  recommendations: RecommendationItem[];
  apiBase: string;
  onActionComplete: () => void;
  investigationId?: string;
}

export const ContainmentPanel: React.FC<ContainmentPanelProps> = ({
  recommendations,
  apiBase,
  onActionComplete,
  investigationId,
}) => {
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [pendingReviews, setPendingReviews] = useState<HumanReviewItem[]>([]);
  const [activeSimulation, setActiveSimulation] = useState<SimulationResultItem | null>(null);
  const [simulating, setSimulating] = useState(false);

  const fetchReviews = async () => {
    try {
      const res = await axios.get(`${apiBase}/api/reviews/pending`);
      setPendingReviews(res.data);
    } catch (e) {
      // ignore
    }
  };

  useEffect(() => {
    fetchReviews();
    const interval = setInterval(fetchReviews, 3000);
    return () => clearInterval(interval);
  }, [apiBase]);

  const handleApproveReview = async (reviewId: string) => {
    setProcessingId(reviewId);
    try {
      await axios.post(`${apiBase}/api/reviews/${reviewId}/decision`, {
        decision: 'approved',
        analyst_comments: 'Analyst authorized action after blast-radius safety verification.',
      });
      fetchReviews();
      onActionComplete();
    } catch (e) {
      console.error(e);
    } finally {
      setProcessingId(null);
    }
  };

  const handleRejectReview = async (reviewId: string) => {
    setProcessingId(reviewId);
    try {
      await axios.post(`${apiBase}/api/reviews/${reviewId}/decision`, {
        decision: 'rejected',
        analyst_comments: 'Action denied by analyst.',
      });
      fetchReviews();
      onActionComplete();
    } catch (e) {
      console.error(e);
    } finally {
      setProcessingId(null);
    }
  };

  const handleSimulateAction = async (actionType: string, targetId: string) => {
    if (!investigationId) return;
    setSimulating(true);
    try {
      const res = await axios.post(`${apiBase}/api/reviews/simulate`, {
        investigation_id: investigationId,
        action_type: actionType,
        target_identifier: targetId,
      });
      setActiveSimulation(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setSimulating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* 1. Human-In-The-Loop Approval Queue (IS §11.3) */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-semibold text-gray-200 flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-amber-400" />
            Human-in-the-Loop Approval Queue (Awaiting Analyst Review)
          </h3>
          <span className="text-[10px] font-mono bg-amber-950 text-amber-400 border border-amber-800 px-2 py-0.5 rounded">
            Pending: {pendingReviews.length}
          </span>
        </div>

        {pendingReviews.length === 0 ? (
          <div className="p-4 border border-dashed border-gray-800 rounded-lg text-center text-gray-500 text-xs">
            No active human review requests. The autonomous planner is proceeding within safe operational boundaries.
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-2.5">
            {pendingReviews.map((rev) => (
              <div
                key={rev.review_id}
                className="bg-[#0f1422] border border-amber-800/60 rounded-lg p-3 flex items-center justify-between gap-3"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-red-950 text-red-400 border border-red-800 font-semibold">
                      {rev.risk_level} Risk
                    </span>
                    <span className="text-[11px] font-semibold text-gray-200">{rev.requested_action}</span>
                  </div>
                  <p className="text-[10px] text-gray-400 font-mono">
                    Investigation: {rev.investigation_id} • Requested: {new Date(rev.created_at).toLocaleTimeString()}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleApproveReview(rev.review_id)}
                    disabled={processingId === rev.review_id}
                    className="flex items-center gap-1 px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium rounded transition"
                  >
                    <Check className="w-3.5 h-3.5" />
                    Approve
                  </button>
                  <button
                    onClick={() => handleRejectReview(rev.review_id)}
                    disabled={processingId === rev.review_id}
                    className="flex items-center gap-1 px-2.5 py-1 bg-red-900/60 hover:bg-red-800 text-red-200 text-xs font-medium rounded border border-red-700 transition"
                  >
                    <X className="w-3.5 h-3.5" />
                    Reject
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 2. Response Simulation Sandbox (IS §11.4) */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-semibold text-gray-200 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-cyan-400" />
            Response Action Simulation Sandbox (Non-Destructive Blast-Radius Evaluation)
          </h3>
        </div>

        <div className="bg-[#0b101c] border border-gray-800 rounded-lg p-3 space-y-3">
          <div className="flex items-center gap-2 flex-wrap text-xs">
            <span className="text-gray-400 text-[11px]">Simulate Action:</span>
            <button
              onClick={() => handleSimulateAction('isolate_endpoint', 'WS-FINANCE-01')}
              disabled={simulating || !investigationId}
              className="px-2.5 py-1 bg-gray-800 hover:bg-gray-700 text-gray-200 rounded border border-gray-700 text-[11px] transition"
            >
              Simulate Host Isolation (WS-01)
            </button>
            <button
              onClick={() => handleSimulateAction('block_ip', '198.51.100.23')}
              disabled={simulating || !investigationId}
              className="px-2.5 py-1 bg-gray-800 hover:bg-gray-700 text-gray-200 rounded border border-gray-700 text-[11px] transition"
            >
              Simulate Perimeter IP Block (C2)
            </button>
            <button
              onClick={() => handleSimulateAction('suspend_user', 'corp\\jdoe')}
              disabled={simulating || !investigationId}
              className="px-2.5 py-1 bg-gray-800 hover:bg-gray-700 text-gray-200 rounded border border-gray-700 text-[11px] transition"
            >
              Simulate User Lock (AD)
            </button>
          </div>

          {activeSimulation && (
            <div className="p-3 bg-[#070b14] border border-cyan-800/40 rounded space-y-1.5 text-xs font-mono">
              <div className="flex items-center justify-between text-cyan-400 font-semibold">
                <span>Simulation: {activeSimulation.action}</span>
                <span className="text-[10px] px-1.5 py-0.2 bg-cyan-950 border border-cyan-800 rounded">
                  {activeSimulation.status.toUpperCase()}
                </span>
              </div>
              <p className="text-gray-300">
                <span className="text-gray-500">Blast Radius:</span> {activeSimulation.blast_radius}
              </p>
              <p className="text-gray-300">
                <span className="text-gray-500">Service Disruption:</span> {activeSimulation.service_disruption}
              </p>
              <p className="text-emerald-400">
                <span className="text-gray-500">Assessment:</span> {activeSimulation.safety_assessment}
              </p>
              <p className="text-amber-400">
                <span className="text-gray-500">Rollback Plan:</span> {activeSimulation.rollback_plan}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* 3. Report Recommendations */}
      {recommendations.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-xs font-semibold text-gray-200">Recommended Containment Playbooks from Reports</h3>
          <div className="grid grid-cols-1 gap-2">
            {recommendations.map((rec) => (
              <div
                key={rec.recommendation_id}
                className="bg-[#0b0f19] border border-gray-800/80 rounded-lg p-3 flex items-center justify-between"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-gray-900 text-gray-300 border border-gray-700">
                      {rec.risk_level}
                    </span>
                    <span className="text-xs font-semibold text-gray-200">{rec.action}</span>
                  </div>
                  {rec.impact_summary && (
                    <p className="text-[11px] text-gray-400 mt-1">{rec.impact_summary}</p>
                  )}
                </div>
                <span className="text-[11px] font-mono text-gray-400 uppercase">
                  Status: {rec.approval_status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
