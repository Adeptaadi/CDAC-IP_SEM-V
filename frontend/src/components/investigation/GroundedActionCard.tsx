import React from 'react';
import { RecommendationProjection, HumanReviewProjection } from '../../types/workspace';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import {
  AlertTriangle,
  CheckCircle2,
  XCircle,
  ShieldCheck,
  FileText,
} from 'lucide-react';

interface GroundedActionCardProps {
  recommendation: RecommendationProjection;
  humanReview?: HumanReviewProjection | null;
  onApprove: () => void;
  onReject: () => void;
  onSelectCitation: (findingId: string) => void;
}

export const GroundedActionCard: React.FC<GroundedActionCardProps> = ({
  recommendation,
  humanReview,
  onApprove,
  onReject,
  onSelectCitation,
}) => {
  const isPending = recommendation.approval_status === 'pending';
  const isApproved = recommendation.approval_status === 'approved' || humanReview?.decision === 'approve';
  const isRejected = recommendation.approval_status === 'rejected' || humanReview?.decision === 'reject';

  return (
    <div className="bg-zinc-900/90 border border-zinc-800 rounded-lg p-4 space-y-3 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        {/* Title, Action & Status */}
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-md bg-amber-950/80 border border-amber-700/80 text-amber-400 flex items-center justify-center shrink-0 mt-0.5">
            <AlertTriangle className="w-4 h-4" />
          </div>

          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[10px] font-mono uppercase tracking-wider text-amber-400 font-semibold">
                RECOMMENDED CONTAINMENT ACTION
              </span>
              <Badge
                variant={
                  isApproved
                    ? 'success'
                    : isRejected
                    ? 'critical'
                    : recommendation.risk_level === 'high'
                    ? 'high'
                    : 'warning'
                }
                size="sm"
              >
                {recommendation.approval_status.toUpperCase()}
              </Badge>
              {recommendation.risk_level && (
                <span className="text-[10px] font-mono bg-zinc-800 text-zinc-300 px-1.5 py-0.2 rounded border border-zinc-700 uppercase">
                  Risk: {recommendation.risk_level}
                </span>
              )}
            </div>

            <h3 className="text-sm font-bold text-zinc-100 mt-1">
              {recommendation.action}
            </h3>

            {recommendation.rationale && (
              <p className="text-xs text-zinc-300 mt-1 max-w-3xl leading-relaxed">
                {recommendation.rationale}
              </p>
            )}
          </div>
        </div>

        {/* Human Authorization Gate Buttons */}
        <div className="flex items-center gap-2 shrink-0">
          {isPending ? (
            <>
              <Button
                variant="primary"
                size="sm"
                icon={<CheckCircle2 className="w-3.5 h-3.5" />}
                onClick={onApprove}
              >
                Approve Containment
              </Button>
              <Button
                variant="danger"
                size="sm"
                icon={<XCircle className="w-3.5 h-3.5" />}
                onClick={onReject}
              >
                Reject Action
              </Button>
            </>
          ) : isApproved ? (
            <div className="flex items-center gap-1.5 text-xs font-mono text-emerald-400 bg-emerald-950/40 px-3 py-1.5 rounded border border-emerald-800/80">
              <ShieldCheck className="w-4 h-4" />
              <span>CONTAINMENT APPROVED & DEPLOYED</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 text-xs font-mono text-rose-400 bg-rose-950/40 px-3 py-1.5 rounded border border-rose-800/80">
              <XCircle className="w-4 h-4" />
              <span>CONTAINMENT REJECTED BY ANALYST</span>
            </div>
          )}
        </div>
      </div>

      {/* Supporting Evidence Linkage (Grounding hierarchy: Action -> Supported By -> Real Evidence) */}
      {recommendation.supporting_findings && recommendation.supporting_findings.length > 0 && (
        <div className="pt-2 border-t border-zinc-800/70 text-xs">
          <div className="flex items-center gap-2 text-[10px] font-mono text-zinc-400 uppercase tracking-wider mb-1.5">
            <FileText className="w-3 h-3 text-blue-400" />
            <span>GROUNDED SUPPORTING EVIDENCE CITATIONS ({recommendation.supporting_findings.length}):</span>
          </div>

          <div className="flex flex-wrap gap-2">
            {recommendation.supporting_findings.map((sf) => (
              <button
                key={sf.finding_id}
                type="button"
                onClick={() => onSelectCitation(sf.finding_id)}
                className="text-left p-2 rounded bg-zinc-950 border border-zinc-800 hover:border-blue-500/80 hover:bg-zinc-900 transition-colors group flex items-start gap-2 max-w-md"
              >
                <span className="font-mono text-[10px] text-blue-400 font-bold shrink-0 mt-0.5">
                  [{sf.finding_id.slice(0, 8)}]
                </span>
                <span className="text-zinc-300 text-[11px] truncate group-hover:text-blue-300">
                  {sf.summary}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Pre-Execution Simulation Projection (If available from response worker) */}
      {recommendation.simulation && (
        <div className="pt-2 border-t border-zinc-800/70 text-xs text-zinc-400 font-mono grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px]">
          {recommendation.simulation.blast_radius_score !== undefined &&
            recommendation.simulation.blast_radius_score !== null && (
              <div className="bg-zinc-950 p-2 rounded border border-zinc-800">
                <span className="text-zinc-500 block text-[10px]">BLAST RADIUS SCORE:</span>
                <span className="text-zinc-200 font-bold">
                  {recommendation.simulation.blast_radius_score} / 1.00 (
                  {recommendation.simulation.disruption_level || 'minimal disruption'})
                </span>
              </div>
            )}

          {recommendation.simulation.safety_assessment && (
            <div className="bg-zinc-950 p-2 rounded border border-zinc-800">
              <span className="text-zinc-500 block text-[10px]">SAFETY ASSESSMENT:</span>
              <span className="text-zinc-200">
                {recommendation.simulation.safety_assessment}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
