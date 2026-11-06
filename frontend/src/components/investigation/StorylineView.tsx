import React from 'react';
import { Card, CardHeader } from '../ui/Card';
import { EmptyState } from '../ui/States';
import { StorylineCycleCard } from './StorylineCycleCard';
import {
  OrchestrationStep,
  ThreatSummary,
  PlannerWorkspaceState,
  KeyFinding,
} from '../../types/workspace';
import { ShieldCheck, HelpCircle, AlertOctagon, RotateCw } from 'lucide-react';
import { Button } from '../ui/Button';

interface StorylineViewProps {
  steps: OrchestrationStep[];
  threat: ThreatSummary;
  planner: PlannerWorkspaceState;
  keyFindings: KeyFinding[];
  onInspectStep: (step: OrchestrationStep) => void;
  onStepPlanner?: () => void;
  isExecutingStep?: boolean;
}

export const StorylineView: React.FC<StorylineViewProps> = ({
  steps,
  threat,
  planner,
  keyFindings,
  onInspectStep,
  onStepPlanner,
  isExecutingStep,
}) => {
  // Pre-calculate running occurrence count for each step to support honest revisit markers
  const workerCountsSoFar: Record<string, number> = {};
  const enrichedSteps = steps.map((step) => {
    const worker = step.selected_worker || 'system';
    workerCountsSoFar[worker] = (workerCountsSoFar[worker] || 0) + 1;
    const executionCount = workerCountsSoFar[worker];
    const isRevisit = executionCount > 1;
    const isReplan =
      Boolean(step.is_replanning) ||
      step.decision_type === 'replan' ||
      Boolean(step.replan_reason) ||
      (planner.is_replanning && step.cycle === steps.length);

    return {
      step,
      executionCount,
      isRevisit,
      isReplan,
      replanReason: step.replan_reason || null,
    };
  });

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Left 2 Cols: Chronological Cycle Feed */}
      <div className="lg:col-span-2 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider flex items-center gap-2">
            <span>Chronological Investigation Storyline</span>
            <span className="font-mono text-[10px] text-zinc-500 bg-zinc-900 px-2 py-0.5 rounded border border-zinc-800">
              {steps.length} Decision Cycle(s)
            </span>
          </h2>

          {onStepPlanner && (
            <Button
              variant="secondary"
              size="sm"
              icon={<RotateCw className="w-3.5 h-3.5" />}
              isLoading={isExecutingStep}
              onClick={onStepPlanner}
              disabled={threat.status === 'completed' || threat.status === 'closed'}
            >
              Step Planner
            </Button>
          )}
        </div>

        {steps.length === 0 ? (
          <EmptyState
            title="No Planning Cycles Executed Yet"
            description="The investigation has established initial state. Click 'Step Planner' or 'Run Autonomous' to begin autonomous investigation."
            action={
              onStepPlanner ? (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={onStepPlanner}
                  isLoading={isExecutingStep}
                >
                  Execute First Planning Cycle
                </Button>
              ) : undefined
            }
          />
        ) : (
          <div className="space-y-4 relative before:absolute before:inset-0 before:left-4 before:w-0.5 before:bg-zinc-800">
            {enrichedSteps.map(({ step, executionCount, isRevisit, isReplan, replanReason }) => (
              <StorylineCycleCard
                key={`${step.cycle}-${step.selected_worker}-${executionCount}`}
                step={step}
                executionCount={executionCount}
                isRevisit={isRevisit}
                isReplan={isReplan}
                replanReason={replanReason}
                onInspect={() => onInspectStep(step)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Right 1 Col: Tri-Part State Box (Linear/Operational Cognitive Summary) */}
      <div className="space-y-4">
        <Card>
          <CardHeader
            title="Investigation State Breakdown"
            description="Observable cognitive ledger of confirmed facts vs. active gaps"
          />

          <div className="space-y-4 text-xs">
            {/* 1. WHAT WE KNOW */}
            <div>
              <div className="flex items-center gap-1.5 text-emerald-400 font-mono text-[10px] font-semibold uppercase tracking-wider mb-1.5">
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>[WHAT WE KNOW] (Verified Facts)</span>
              </div>
              <div className="space-y-1.5 bg-zinc-950/70 p-3 rounded border border-zinc-800/80 font-mono text-[11px]">
                {threat.affected_entities.length > 0 ? (
                  threat.affected_entities.map((e) => (
                    <div key={e.id} className="text-zinc-300 flex items-start gap-1.5">
                      <span className="text-emerald-500 font-bold">•</span>
                      <span>
                        <strong className="text-zinc-200">{e.type.toUpperCase()}:</strong> {e.label}
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="text-zinc-500">• Telemetry entities being triaged</div>
                )}

                {keyFindings.slice(0, 3).map((f) => (
                  <div key={f.finding_id} className="text-zinc-400 flex items-start gap-1.5 truncate">
                    <span className="text-blue-500 font-bold">•</span>
                    <span className="truncate">{f.summary}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* 2. WHAT WE SUSPECT */}
            <div>
              <div className="flex items-center gap-1.5 text-amber-400 font-mono text-[10px] font-semibold uppercase tracking-wider mb-1.5">
                <AlertOctagon className="w-3.5 h-3.5" />
                <span>[WHAT WE SUSPECT] (Current Hypothesis)</span>
              </div>
              <div className="bg-zinc-950/70 p-3 rounded border border-zinc-800/80 text-zinc-200 text-xs leading-relaxed">
                {planner.current_observation ||
                  'Evaluating telemetry baseline against candidate MITRE ATT&CK techniques.'}
              </div>
            </div>

            {/* 3. WHAT REMAINS UNRESOLVED */}
            <div>
              <div className="flex items-center gap-1.5 text-rose-400 font-mono text-[10px] font-semibold uppercase tracking-wider mb-1.5">
                <HelpCircle className="w-3.5 h-3.5" />
                <span>[WHAT REMAINS UNRESOLVED] (Gaps)</span>
              </div>
              <div className="space-y-1.5 bg-zinc-950/70 p-3 rounded border border-zinc-800/80 text-xs">
                {planner.unresolved_questions && planner.unresolved_questions.length > 0 ? (
                  planner.unresolved_questions.map((q, idx) => (
                    <div key={idx} className="flex items-start gap-1.5 text-zinc-300">
                      <span className="text-rose-400 font-mono">?</span>
                      <span>{q}</span>
                    </div>
                  ))
                ) : (
                  <div className="text-zinc-500 font-mono text-[11px]">
                    • Forensic certainty reached; no unresolved gaps for current state.
                  </div>
                )}
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};
