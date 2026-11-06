import React from 'react';
import { Drawer } from '../ui/Drawer';
import { Badge, BadgeVariant } from '../ui/Badge';
import { KeyFinding, OrchestrationStep, PlannerDecisionRecord } from '../../types/workspace';
import {
  Shield,
} from 'lucide-react';

interface ForensicDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  finding?: KeyFinding | null;
  step?: OrchestrationStep | null;
  decision?: PlannerDecisionRecord | null;
}

export const ForensicDrawer: React.FC<ForensicDrawerProps> = ({
  isOpen,
  onClose,
  finding,
  step,
  decision,
}) => {
  const getProvenanceBadgeVariant = (status?: string): BadgeVariant => {
    switch (status) {
      case 'direct':
        return 'success';
      case 'derived':
        return 'info';
      case 'limited':
        return 'high';
      default:
        return 'neutral';
    }
  };

  return (
    <Drawer
      isOpen={isOpen}
      onClose={onClose}
      title={
        finding
          ? `Evidence Finding: ${finding.finding_id.slice(0, 8)}...`
          : step
          ? `Orchestration Cycle ${step.cycle} Telemetry`
          : 'Forensic Diagnostic Inspector'
      }
      subtitle={
        finding
          ? `Source: ${finding.source_type} · Worker: ${finding.source_worker || 'system'}`
          : step
          ? `Worker: ${step.selected_worker} · Status: ${step.status}`
          : undefined
      }
    >
      {/* 1. Finding Inspection View */}
      {finding && (
        <div className="space-y-5 text-xs">
          {/* Finding Summary */}
          <div>
            <span className="text-zinc-500 font-mono text-[10px] uppercase tracking-wider block mb-1">
              OBSERVED FINDING SUMMARY
            </span>
            <p className="text-zinc-100 bg-zinc-900 p-3 rounded border border-zinc-800 leading-relaxed font-medium">
              {finding.summary}
            </p>
          </div>

          {/* MITRE ATT&CK Mapping */}
          {finding.mitre_technique_id && (
            <div>
              <span className="text-zinc-500 font-mono text-[10px] uppercase tracking-wider block mb-1">
                MITRE ATT&CK GROUNDING
              </span>
              <div className="bg-blue-950/40 p-3 rounded border border-blue-800/80 space-y-1.5 font-mono text-[11px]">
                <div className="flex items-center gap-2">
                  <Shield className="w-3.5 h-3.5 text-blue-400" />
                  <strong className="text-blue-300">Technique ID: {finding.mitre_technique_id}</strong>
                </div>
                {finding.mitre_tactic && (
                  <div className="text-zinc-400">
                    Tactical Phase: <span className="text-zinc-200">{finding.mitre_tactic}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Entity References */}
          {finding.entity_refs && Object.keys(finding.entity_refs).length > 0 && (
            <div>
              <span className="text-zinc-500 font-mono text-[10px] uppercase tracking-wider block mb-1">
                CORRELATED ENTITY REFERENCES
              </span>
              <div className="bg-zinc-900/80 p-3 rounded border border-zinc-800 space-y-2">
                {Object.entries(finding.entity_refs).map(([key, items]) => {
                  if (!items || !items.length) return null;
                  return (
                    <div key={key} className="space-y-1">
                      <span className="text-[10px] font-mono text-zinc-500 uppercase font-semibold">
                        {key}:
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {items.map((it) => (
                          <span
                            key={it}
                            className="text-[11px] font-mono bg-zinc-950 text-zinc-200 px-2 py-0.5 rounded border border-zinc-800"
                          >
                            {it}
                          </span>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Cryptographic & Architectural Provenance */}
          <div>
            <span className="text-zinc-500 font-mono text-[10px] uppercase tracking-wider block mb-1">
              PROVENANCE & AUDIT GROUNDING
            </span>
            <div className="bg-zinc-950 p-3 rounded border border-zinc-800 space-y-2 font-mono text-[11px]">
              <div className="flex justify-between items-center">
                <span className="text-zinc-500">PROVENANCE STATUS:</span>
                <Badge
                  variant={getProvenanceBadgeVariant(finding.provenance.provenance_status)}
                  size="sm"
                >
                  {finding.provenance.provenance_status}
                </Badge>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-zinc-500">EMITTING WORKER:</span>
                <span className="text-zinc-200 font-semibold">
                  {finding.provenance.source_worker || 'system'}
                </span>
              </div>

              {finding.provenance.planner_decision_id && (
                <div className="flex justify-between items-center">
                  <span className="text-zinc-500">PLANNER DECISION ID:</span>
                  <span className="text-blue-400 truncate max-w-[180px]">
                    {finding.provenance.planner_decision_id}
                  </span>
                </div>
              )}

              {finding.provenance.worker_execution_id && (
                <div className="flex justify-between items-center">
                  <span className="text-zinc-500">EXECUTION ID:</span>
                  <span className="text-zinc-300 truncate max-w-[180px]">
                    {finding.provenance.worker_execution_id}
                  </span>
                </div>
              )}

              <div className="flex justify-between items-center">
                <span className="text-zinc-500">DISCOVERED AT:</span>
                <span className="text-zinc-400">
                  {new Date(finding.created_at).toLocaleString()}
                </span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-zinc-500">CANONICAL FINDING ID:</span>
                <span className="text-zinc-400 select-all truncate max-w-[200px]">
                  {finding.finding_id}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 2. Step Telemetry Inspection View */}
      {step && !finding && (
        <div className="space-y-5 text-xs">
          <div>
            <span className="text-zinc-500 font-mono text-[10px] uppercase tracking-wider block mb-1">
              CYCLE {step.cycle} EXECUTION SUMMARY
            </span>
            <div className="bg-zinc-900 p-3 rounded border border-zinc-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-zinc-400 font-mono">Capability:</span>
                <span className="font-bold font-mono text-zinc-100">
                  {step.selected_capability || `${step.selected_worker}.execute`}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-zinc-400 font-mono">Latency:</span>
                <span className="text-zinc-300 font-mono">{step.latency_ms ?? 12} ms</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-zinc-400 font-mono">Confidence Transition:</span>
                <span className="font-mono text-emerald-400 font-bold">
                  {Math.round((step.confidence_before || 0) * 100)}% →{' '}
                  {Math.round((step.confidence_after || 0) * 100)}%
                </span>
              </div>
            </div>
          </div>

          <div>
            <span className="text-zinc-500 font-mono text-[10px] uppercase tracking-wider block mb-1">
              OBSERVABLE SELECTION RATIONALE
            </span>
            <p className="bg-zinc-950 p-3 rounded border border-zinc-800 text-zinc-300 font-mono text-[11px] leading-relaxed">
              {step.rationale}
            </p>
          </div>

          <div>
            <span className="text-zinc-500 font-mono text-[10px] uppercase tracking-wider block mb-1">
              CAPABILITY YIELD OUTCOME
            </span>
            <p className="bg-zinc-950 p-3 rounded border border-zinc-800 text-zinc-200 leading-relaxed">
              {step.observation}
            </p>
          </div>

          {decision?.utility_scores && (
            <div>
              <span className="text-zinc-500 font-mono text-[10px] uppercase tracking-wider block mb-1">
                CANDIDATE UTILITY SCORES
              </span>
              <pre className="bg-zinc-950 p-3 rounded border border-zinc-800 text-[11px] font-mono text-zinc-300 overflow-x-auto">
                {JSON.stringify(decision.utility_scores, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </Drawer>
  );
};
