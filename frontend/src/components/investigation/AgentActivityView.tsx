import React, { useState } from 'react';
import { Card, CardHeader } from '../ui/Card';
import { Badge, BadgeVariant } from '../ui/Badge';
import { EmptyState } from '../ui/States';
import { OrchestrationStep, PlannerDecisionRecord } from '../../types/workspace';
import {
  ArrowRight,
  RotateCcw,
  AlertTriangle,
  Sparkles,
} from 'lucide-react';

interface AgentActivityViewProps {
  steps: OrchestrationStep[];
  decisions?: PlannerDecisionRecord[];
  activeCapability?: { name: string; worker_type: string; status: string } | null;
  isReplanning?: boolean;
}

export const AgentActivityView: React.FC<AgentActivityViewProps> = ({
  steps,
  decisions = [],
  activeCapability,
  isReplanning = false,
}) => {
  const [selectedCycleIndex, setSelectedCycleIndex] = useState<number>(
    steps.length > 0 ? steps.length - 1 : 0
  );

  // Map decisions by cycle number for fast lookup
  const decisionByCycle: Record<number, PlannerDecisionRecord> = {};
  decisions.forEach((d) => {
    decisionByCycle[d.cycle_number] = d;
  });

  // Calculate chronological revisit counts
  const workerCounts: Record<string, number> = {};
  const enrichedSteps = steps.map((step) => {
    const worker = step.selected_worker || 'system';
    workerCounts[worker] = (workerCounts[worker] || 0) + 1;
    const executionCount = workerCounts[worker];
    const isRevisit = executionCount > 1;

    // Check replan from step or decision record
    const dec = decisionByCycle[step.cycle];
    const isReplan =
      Boolean(step.is_replanning) ||
      step.decision_type === 'replan' ||
      Boolean(dec?.is_replanning) ||
      dec?.decision_type === 'replan';

    return {
      step,
      executionCount,
      isRevisit,
      isReplan,
      decisionRecord: dec,
    };
  });

  if (steps.length === 0) {
    return (
      <EmptyState
        title="No Agent Orchestration Telemetry"
        description="The Planner has not executed any capability cycles yet. Execute a planning step or run autonomous investigation to generate execution traces."
      />
    );
  }

  const activeSelectedStep = enrichedSteps[selectedCycleIndex] || enrichedSteps[enrichedSteps.length - 1];
  const activeDecision = activeSelectedStep?.decisionRecord;

  // Aggregate stats
  const totalCycles = steps.length;
  const uniqueWorkers = new Set(steps.map((s) => s.selected_worker)).size;
  const totalRevisits = Object.values(workerCounts).reduce((acc, count) => acc + (count > 1 ? count - 1 : 0), 0);

  const getWorkerBadgeVariant = (worker?: string | null): BadgeVariant => {
    switch (worker) {
      case 'investigation':
        return 'violet';
      case 'response':
        return 'critical';
      case 'detection':
        return 'info';
      case 'correlation':
        return 'neutral';
      default:
        return 'neutral';
    }
  };

  return (
    <div className="space-y-6">
      {/* 1. Executive Telemetry Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-zinc-900/80 p-3 rounded-lg border border-zinc-800">
          <span className="text-zinc-500 font-mono text-[10px] uppercase tracking-wider block">
            TOTAL CYCLES
          </span>
          <div className="text-xl font-bold font-mono text-zinc-100 mt-1">
            {totalCycles}
          </div>
          <span className="text-[10px] text-zinc-500 font-mono">Sequential Decisions</span>
        </div>

        <div className="bg-zinc-900/80 p-3 rounded-lg border border-zinc-800">
          <span className="text-zinc-500 font-mono text-[10px] uppercase tracking-wider block">
            CAPABILITY DIVERSITY
          </span>
          <div className="text-xl font-bold font-mono text-blue-400 mt-1">
            {uniqueWorkers} <span className="text-xs text-zinc-500 font-normal">/ 5 Workers</span>
          </div>
          <span className="text-[10px] text-zinc-500 font-mono">
            {((uniqueWorkers / 5) * 100).toFixed(0)}% Surface Coverage
          </span>
        </div>

        <div className="bg-zinc-900/80 p-3 rounded-lg border border-zinc-800">
          <span className="text-zinc-500 font-mono text-[10px] uppercase tracking-wider block">
            CAPABILITY REVISITS
          </span>
          <div className="text-xl font-bold font-mono text-violet-400 mt-1">
            {totalRevisits}
          </div>
          <span className="text-[10px] text-zinc-500 font-mono">Non-linear Re-evaluations</span>
        </div>

        <div className="bg-zinc-900/80 p-3 rounded-lg border border-zinc-800">
          <span className="text-zinc-500 font-mono text-[10px] uppercase tracking-wider block">
            PLANNER TRAJECTORY
          </span>
          <div className="text-sm font-bold font-mono mt-1.5 flex items-center gap-1.5">
            {isReplanning ? (
              <span className="text-amber-400 flex items-center gap-1">
                <AlertTriangle className="w-3.5 h-3.5" /> REPLANNING
              </span>
            ) : (
              <span className="text-emerald-400 flex items-center gap-1">
                <Sparkles className="w-3.5 h-3.5" /> STABLE PROGRESS
              </span>
            )}
          </div>
          <span className="text-[10px] text-zinc-500 font-mono">
            Active: {activeCapability?.name || 'idle'}
          </span>
        </div>
      </div>

      {/* 2. Interactive Chronological Execution Path */}
      <Card>
        <CardHeader
          title="Chronological Agent Execution Path"
          description="Interactive execution trace derived from actual Planner state transitions. Click any node to inspect telemetry."
          action={
            <span className="text-[11px] font-mono text-zinc-400">
              Selected: <strong className="text-zinc-200">Cycle {activeSelectedStep.step.cycle}</strong>
            </span>
          }
        />

        {/* Horizontal Scrollable Trace Rail */}
        <div className="overflow-x-auto pb-3 pt-1">
          <div className="flex items-center gap-2 min-w-max px-1">
            {enrichedSteps.map((item, idx) => {
              const isSelected = idx === selectedCycleIndex;
              const { step, executionCount, isRevisit, isReplan } = item;
              const delta = step.confidence_delta;

              return (
                <React.Fragment key={step.cycle}>
                  {/* Step Node Button */}
                  <button
                    type="button"
                    onClick={() => setSelectedCycleIndex(idx)}
                    className={`p-3 rounded-lg border text-left transition-all duration-150 flex flex-col gap-1.5 relative ${
                      isSelected
                        ? 'bg-blue-950/40 border-blue-500 shadow-lg shadow-blue-950/40 ring-1 ring-blue-500/50 min-w-[170px]'
                        : isReplan
                        ? 'bg-amber-950/20 border-amber-800/80 hover:border-amber-600 min-w-[160px]'
                        : isRevisit
                        ? 'bg-zinc-900/90 border-violet-800/60 hover:border-violet-500 min-w-[160px]'
                        : 'bg-zinc-900/60 border-zinc-800 hover:border-zinc-700 min-w-[160px]'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-1 w-full">
                      <span className="text-[10px] font-mono font-bold text-zinc-400">
                        C{String(step.cycle).padStart(2, '0')}
                      </span>

                      <Badge variant={getWorkerBadgeVariant(step.selected_worker)} size="sm">
                        {step.selected_worker}
                      </Badge>
                    </div>

                    <div className="text-xs font-semibold text-zinc-200 truncate">
                      {step.selected_capability || `${step.selected_worker}.execute`}
                    </div>

                    {/* Indicators */}
                    <div className="flex items-center justify-between gap-1 mt-1 pt-1 border-t border-zinc-800/60 text-[10px] font-mono">
                      {isRevisit ? (
                        <span className="text-violet-400 flex items-center gap-0.5">
                          <RotateCcw className="w-2.5 h-2.5" />
                          #{executionCount}
                        </span>
                      ) : isReplan ? (
                        <span className="text-amber-400 flex items-center gap-0.5 font-semibold">
                          <AlertTriangle className="w-2.5 h-2.5" />
                          Replan
                        </span>
                      ) : (
                        <span className="text-zinc-500">Initial</span>
                      )}

                      {delta !== undefined && delta !== null && (
                        <span
                          className={delta >= 0 ? 'text-emerald-400 font-semibold' : 'text-rose-400'}
                        >
                          {delta >= 0 ? '+' : ''}
                          {(delta * 100).toFixed(1)}%
                        </span>
                      )}
                    </div>
                  </button>

                  {/* Connector Arrow */}
                  {idx < enrichedSteps.length - 1 && (
                    <ArrowRight className="w-3.5 h-3.5 text-zinc-600 shrink-0" />
                  )}
                </React.Fragment>
              );
            })}
          </div>
        </div>
      </Card>

      {/* 3. Detailed Execution Inspector (Synchronized with selected node) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Observable Execution Details */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader
              title={`Cycle ${activeSelectedStep.step.cycle} Telemetry Inspector`}
              description={`Grounded execution output for worker '${activeSelectedStep.step.selected_worker}'`}
              action={
                <Badge variant={getWorkerBadgeVariant(activeSelectedStep.step.selected_worker)} size="sm">
                  {activeSelectedStep.step.selected_worker?.toUpperCase()}
                </Badge>
              }
            />

            <div className="space-y-4 text-xs">
              {/* Trigger & Selection Rationale */}
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 font-semibold block mb-1">
                  Observable Selection Rationale:
                </span>
                <p className="bg-zinc-950/70 p-3 rounded border border-zinc-800 text-zinc-300 font-mono text-[11px] leading-relaxed">
                  {activeSelectedStep.step.rationale ||
                    `Planner selected worker '${activeSelectedStep.step.selected_worker}' to address state gaps.`}
                </p>
              </div>

              {/* Real Outcome */}
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 font-semibold block mb-1">
                  Capability Yield Outcome:
                </span>
                <p className="bg-zinc-950/70 p-3 rounded border border-zinc-800 text-zinc-200 leading-relaxed">
                  {activeSelectedStep.step.observation}
                </p>
              </div>

              {/* Knowledge Need / Gap Addressed */}
              {activeSelectedStep.step.unresolved_question && (
                <div>
                  <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 font-semibold block mb-1">
                    Investigation Gap Targeted:
                  </span>
                  <div className="bg-zinc-950/70 p-2.5 rounded border border-zinc-800 text-zinc-300 font-mono text-[11px]">
                    ? {activeSelectedStep.step.unresolved_question}
                  </div>
                </div>
              )}

              {/* Utility Scores Breakdown (From backend decisions if available) */}
              {activeDecision?.utility_scores && Object.keys(activeDecision.utility_scores).length > 0 && (
                <div>
                  <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 font-semibold block mb-1.5">
                    Planner Candidate Utility Evaluation at Cycle {activeSelectedStep.step.cycle}:
                  </span>
                  <div className="space-y-1.5 bg-zinc-950/70 p-3 rounded border border-zinc-800 font-mono text-[11px]">
                    {Object.entries(activeDecision.utility_scores).map(([wName, score]) => {
                      const isChosen = wName === activeSelectedStep.step.selected_worker;
                      return (
                        <div key={wName} className="flex items-center gap-3">
                          <span className={`w-28 uppercase truncate ${isChosen ? 'text-blue-400 font-bold' : 'text-zinc-400'}`}>
                            {wName}:
                          </span>
                          <div className="flex-1 bg-zinc-800 h-2 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full ${isChosen ? 'bg-blue-500' : 'bg-zinc-600'}`}
                              style={{ width: `${Math.min(100, Math.round(score * 100))}%` }}
                            />
                          </div>
                          <span className={`w-12 text-right ${isChosen ? 'text-blue-400 font-bold' : 'text-zinc-500'}`}>
                            {score.toFixed(2)}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          </Card>
        </div>

        {/* Right 1 Col: Execution Metadata & Confidence Transition */}
        <div className="space-y-4">
          <Card>
            <CardHeader
              title="Execution Diagnostic"
              description="Timing and confidence delta"
            />

            <div className="space-y-3 text-xs font-mono">
              <div className="bg-zinc-950 p-2.5 rounded border border-zinc-800 flex justify-between items-center">
                <span className="text-zinc-500">CYCLE STATUS</span>
                <span className="text-emerald-400 font-bold uppercase">
                  {activeSelectedStep.step.status}
                </span>
              </div>

              <div className="bg-zinc-950 p-2.5 rounded border border-zinc-800 flex justify-between items-center">
                <span className="text-zinc-500">EXECUTION LATENCY</span>
                <span className="text-zinc-200">
                  {activeSelectedStep.step.latency_ms ?? 12} ms
                </span>
              </div>

              <div className="bg-zinc-950 p-2.5 rounded border border-zinc-800 flex justify-between items-center">
                <span className="text-zinc-500">FINDINGS DISCOVERED</span>
                <span className="text-zinc-200">
                  {activeSelectedStep.step.evidence_count_gained ?? 0}
                </span>
              </div>

              <div className="bg-zinc-950 p-2.5 rounded border border-zinc-800">
                <span className="text-zinc-500 text-[10px] block mb-1">CONFIDENCE TRANSITION</span>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-zinc-400">
                    {Math.round((activeSelectedStep.step.confidence_before || 0) * 100)}%
                  </span>
                  <span className="text-zinc-600">→</span>
                  <span className="text-zinc-100 font-bold">
                    {Math.round((activeSelectedStep.step.confidence_after || 0) * 100)}%
                  </span>
                </div>
                {activeSelectedStep.step.confidence_delta !== undefined &&
                  activeSelectedStep.step.confidence_delta !== null && (
                    <div className="mt-1 text-[11px] text-right">
                      <span
                        className={
                          activeSelectedStep.step.confidence_delta >= 0
                            ? 'text-emerald-400'
                            : 'text-rose-400'
                        }
                      >
                        {activeSelectedStep.step.confidence_delta >= 0 ? '+' : ''}
                        {(activeSelectedStep.step.confidence_delta * 100).toFixed(2)}% ΔC
                      </span>
                    </div>
                  )}
              </div>

              {activeSelectedStep.isRevisit && (
                <div className="p-2.5 bg-violet-950/40 border border-violet-800/80 rounded text-violet-300 text-[11px]">
                  <strong>Capability Revisit #{activeSelectedStep.executionCount}:</strong> Planner returned to this worker following evidence incorporation.
                </div>
              )}
            </div>
          </Card>

          {/* Capability Allocation Frequency */}
          <Card>
            <CardHeader
              title="Capability Allocation"
              description="Frequency of worker selections"
            />
            <div className="space-y-1.5">
              {Object.entries(workerCounts).map(([worker, count]) => (
                <div
                  key={worker}
                  className="flex items-center justify-between p-2 rounded bg-zinc-950/60 border border-zinc-800 text-xs font-mono"
                >
                  <span className="uppercase text-zinc-300">{worker}</span>
                  <span className="text-zinc-400">{count} execution(s)</span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
