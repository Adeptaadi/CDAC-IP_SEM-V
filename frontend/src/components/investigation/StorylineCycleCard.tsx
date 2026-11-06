import React from 'react';
import { Badge, BadgeVariant } from '../ui/Badge';
import {
  TrendingUp,
  TrendingDown,
  Clock,
  Database,
  AlertTriangle,
  RotateCcw,
  Zap,
} from 'lucide-react';
import { OrchestrationStep } from '../../types/workspace';

interface StorylineCycleCardProps {
  step: OrchestrationStep;
  executionCount: number; // 1 for initial, 2 for 2nd execution, etc.
  isRevisit: boolean;
  isReplan: boolean;
  replanReason?: string | null;
  onInspect?: () => void;
}

export const StorylineCycleCard: React.FC<StorylineCycleCardProps> = ({
  step,
  executionCount,
  isRevisit,
  isReplan,
  replanReason,
  onInspect,
}) => {
  const workerName = step.selected_worker || 'system';
  const workerBadgeVariant: BadgeVariant =
    workerName === 'investigation'
      ? 'violet'
      : workerName === 'response'
      ? 'critical'
      : workerName === 'detection'
      ? 'info'
      : workerName === 'correlation'
      ? 'neutral'
      : 'neutral';

  const delta = step.confidence_delta;
  const isPositiveDelta = delta !== undefined && delta !== null && delta > 0;
  const isNegativeDelta = delta !== undefined && delta !== null && delta < 0;

  const executionSuffix =
    executionCount === 2
      ? '2nd'
      : executionCount === 3
      ? '3rd'
      : `${executionCount}th`;

  return (
    <div
      onClick={onInspect}
      className={`relative pl-8 transition-all group ${
        onInspect ? 'cursor-pointer' : ''
      }`}
    >
      {/* Node bullet on the timeline track */}
      <div
        className={`absolute left-2.5 top-3.5 w-3.5 h-3.5 rounded-full border-2 z-10 -translate-x-1/2 transition-transform duration-150 group-hover:scale-110 ${
          isReplan
            ? 'bg-amber-950 border-amber-500'
            : isRevisit
            ? 'bg-violet-950 border-violet-400'
            : 'bg-zinc-950 border-blue-500'
        }`}
      />

      {/* Main cycle card */}
      <div
        className={`rounded-lg border p-4 transition-all duration-150 ${
          isReplan
            ? 'bg-amber-950/20 border-amber-800/80 hover:border-amber-700'
            : 'bg-zinc-900/70 border-zinc-800 hover:border-zinc-700 hover:bg-zinc-900/90'
        }`}
      >
        {/* Header: Cycle, Worker, Revisit/Replan Tags, Confidence, Duration */}
        <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-zinc-800/60 mb-3">
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs font-bold text-zinc-100 uppercase tracking-wider">
              CYCLE {String(step.cycle).padStart(2, '0')}
            </span>

            <Badge variant={workerBadgeVariant} size="sm">
              {workerName.toUpperCase()} AGENT
            </Badge>

            {isRevisit && (
              <span className="inline-flex items-center gap-1 text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-violet-950/80 text-violet-300 border border-violet-800/80">
                <RotateCcw className="w-2.5 h-2.5" />
                REVISIT · {executionSuffix.toUpperCase()} EXECUTION
              </span>
            )}

            {isReplan && (
              <span className="inline-flex items-center gap-1 text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-amber-950/90 text-amber-300 border border-amber-700">
                <AlertTriangle className="w-2.5 h-2.5 text-amber-400" />
                REPLAN EVENT
              </span>
            )}
          </div>

          {/* Metrics summary */}
          <div className="flex items-center gap-3 text-[11px] font-mono text-zinc-400">
            {step.confidence_before !== undefined &&
              step.confidence_after !== undefined && (
                <div className="flex items-center gap-1.5">
                  <span className="text-zinc-500">Confidence:</span>
                  <span className="text-zinc-300 font-semibold">
                    {Math.round((step.confidence_before || 0) * 100)}% →{' '}
                    {Math.round((step.confidence_after || 0) * 100)}%
                  </span>
                  {delta !== undefined && delta !== null && (
                    <span
                      className={`inline-flex items-center gap-0.5 px-1 rounded ${
                        isPositiveDelta
                          ? 'text-emerald-400 bg-emerald-950/40'
                          : isNegativeDelta
                          ? 'text-rose-400 bg-rose-950/40'
                          : 'text-zinc-400'
                      }`}
                    >
                      {isPositiveDelta ? (
                        <TrendingUp className="w-3 h-3" />
                      ) : isNegativeDelta ? (
                        <TrendingDown className="w-3 h-3" />
                      ) : null}
                      {delta >= 0 ? '+' : ''}
                      {(delta * 100).toFixed(1)}%
                    </span>
                  )}
                </div>
              )}

            {step.latency_ms !== undefined && step.latency_ms !== null && (
              <div className="flex items-center gap-1 text-zinc-500">
                <Clock className="w-3 h-3" />
                <span>{step.latency_ms}ms</span>
              </div>
            )}
          </div>
        </div>

        {/* Replan Distinct Alert Banner (if replan detected) */}
        {isReplan && (
          <div className="mb-3 p-2.5 rounded bg-amber-950/40 border border-amber-800/80 text-xs text-amber-200 flex items-start gap-2">
            <Zap className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
            <div>
              <strong className="font-semibold block text-[11px] uppercase tracking-wider text-amber-300">
                Planner Trajectory Shift / Contradiction Resolution
              </strong>
              <p className="mt-0.5 text-zinc-300 text-[11px]">
                {replanReason ||
                  step.rationale ||
                  'The Planner detected anomalous or contradictory evidence, pivoting capability utility to re-evaluate the attack hypothesis.'}
              </p>
            </div>
          </div>
        )}

        {/* Section 1: WHY THIS AGENT? (Observable trigger & rationale) */}
        <div className="space-y-1 mb-3">
          <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 font-semibold block">
            WHY THIS AGENT?
          </span>
          <p className="text-xs text-zinc-300 bg-zinc-950/50 p-2.5 rounded border border-zinc-800/70 font-mono text-[11px] leading-relaxed">
            {step.rationale ||
              `Autonomous planner selected '${workerName}' based on prevailing state uncertainty and capability utility.`}
          </p>
        </div>

        {/* Section 2: WHAT HAPPENED? (Observable execution outcome) */}
        <div className="space-y-1">
          <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 font-semibold block">
            WHAT HAPPENED?
          </span>
          <p className="text-xs text-zinc-200 leading-relaxed">
            {step.observation ||
              `Executed capability '${step.selected_capability || `${workerName}.execute`}' and incorporated newly observed security telemetry into investigation state.`}
          </p>
        </div>

        {/* Footer: Discovered Findings count & Action prompt */}
        <div className="flex items-center justify-between mt-3 pt-2.5 border-t border-zinc-800/40 text-[11px] font-mono text-zinc-500">
          <div className="flex items-center gap-2">
            <Database className="w-3 h-3 text-zinc-400" />
            <span>
              Evidence Gained:{' '}
              <strong className="text-zinc-200">
                {step.evidence_count_gained ?? 0} finding(s)
              </strong>
            </span>
          </div>

          <span className="text-blue-400 group-hover:underline text-[10px]">
            Inspect Cycle Telemetry →
          </span>
        </div>
      </div>
    </div>
  );
};
