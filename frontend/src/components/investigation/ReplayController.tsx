import React from 'react';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import {
  Play,
  Pause,
  ChevronLeft,
  ChevronRight,
  LogOut,
} from 'lucide-react';
import { OrchestrationStep } from '../../types/workspace';

interface ReplayControllerProps {
  currentCycle: number;
  totalCycles: number;
  steps: OrchestrationStep[];
  isPlaying: boolean;
  replaySpeed: number; // in milliseconds (e.g. 1500, 800, 400)
  onPrevious: () => void;
  onNext: () => void;
  onTogglePlay: () => void;
  onSelectCycle: (cycle: number) => void;
  onChangeSpeed: (speed: number) => void;
  onExitReplay: () => void;
}

export const ReplayController: React.FC<ReplayControllerProps> = ({
  currentCycle,
  totalCycles,
  steps,
  isPlaying,
  replaySpeed,
  onPrevious,
  onNext,
  onTogglePlay,
  onSelectCycle,
  onChangeSpeed,
  onExitReplay,
}) => {
  // Current step details
  const activeStep = currentCycle > 0 ? steps[currentCycle - 1] : null;

  return (
    <div className="bg-zinc-950/95 border-b border-amber-600/40 p-3 shadow-xl backdrop-blur-sm sticky top-0 z-30 select-none">
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-3">
        {/* Left: Replay Status Pill & Mode Badge */}
        <div className="flex items-center gap-3">
          <Badge variant="high" size="sm">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse mr-1" />
            READ-ONLY REPLAY MODE
          </Badge>

          <div className="text-xs font-mono text-zinc-300 flex items-center gap-2">
            <span>
              {currentCycle === 0 ? (
                <strong className="text-amber-300">Initial Telemetry (Cycle 0)</strong>
              ) : (
                <>
                  <strong className="text-zinc-100">Cycle {currentCycle}</strong> of {totalCycles}
                </>
              )}
            </span>

            {activeStep?.selected_worker && (
              <>
                <span className="text-zinc-600">·</span>
                <span className="text-blue-400 font-semibold uppercase">
                  {activeStep.selected_worker}
                </span>
              </>
            )}

            {activeStep?.confidence_after !== undefined && activeStep?.confidence_after !== null && (
              <>
                <span className="text-zinc-600">·</span>
                <span className="text-emerald-400">
                  {Math.round(activeStep.confidence_after * 100)}% Conf
                </span>
              </>
            )}
          </div>
        </div>

        {/* Center: Playback Controls (Previous, Play/Pause, Next, Speed) */}
        <div className="flex items-center gap-2">
          {/* Previous Step Button */}
          <Button
            variant="secondary"
            size="sm"
            onClick={onPrevious}
            disabled={currentCycle <= 0 || isPlaying}
            title="Step back to previous cycle"
            icon={<ChevronLeft className="w-4 h-4" />}
          >
            Prev
          </Button>

          {/* Play / Pause Toggle Button */}
          <Button
            variant={isPlaying ? 'danger' : 'primary'}
            size="sm"
            onClick={onTogglePlay}
            title={isPlaying ? 'Pause playback' : 'Play chronological replay'}
            icon={
              isPlaying ? (
                <Pause className="w-4 h-4 fill-current" />
              ) : (
                <Play className="w-4 h-4 fill-current" />
              )
            }
          >
            {isPlaying ? 'Pause' : 'Play'}
          </Button>

          {/* Next Step Button */}
          <Button
            variant="secondary"
            size="sm"
            onClick={onNext}
            disabled={currentCycle >= totalCycles || isPlaying}
            title="Advance to next cycle"
            icon={<ChevronRight className="w-4 h-4" />}
          >
            Next
          </Button>

          {/* Playback Speed Multipliers */}
          <div className="flex items-center gap-1 bg-zinc-900 border border-zinc-800 rounded p-0.5 ml-1">
            {[
              { label: '1x', speed: 1500 },
              { label: '2x', speed: 800 },
              { label: '4x', speed: 400 },
            ].map(({ label, speed }) => (
              <button
                key={label}
                type="button"
                onClick={() => onChangeSpeed(speed)}
                className={`px-1.5 py-0.5 text-[10px] font-mono rounded transition-colors ${
                  replaySpeed === speed
                    ? 'bg-blue-600 text-white font-bold'
                    : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* Right: Exit Replay / Return to Live Mode */}
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            icon={<LogOut className="w-3.5 h-3.5" />}
            onClick={onExitReplay}
            title="Exit replay and return to live investigation workspace"
          >
            Exit Replay
          </Button>
        </div>
      </div>

      {/* Interactive Timeline Scrubber Rail */}
      <div className="max-w-6xl mx-auto mt-2 pt-2 border-t border-zinc-800/80">
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
          {/* Cycle 0 Button */}
          <button
            type="button"
            onClick={() => onSelectCycle(0)}
            title="Initial Baseline Ingest"
            className={`px-2 py-1 rounded text-[10px] font-mono transition-all shrink-0 ${
              currentCycle === 0
                ? 'bg-amber-500 text-black font-bold ring-2 ring-amber-400/50'
                : 'bg-zinc-900 text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200 border border-zinc-800'
            }`}
          >
            C0: Init
          </button>

          {/* Steps 1..N */}
          {steps.map((st) => {
            const isCurrent = currentCycle === st.cycle;
            const isPast = currentCycle >= st.cycle;

            return (
              <button
                key={st.cycle}
                type="button"
                onClick={() => onSelectCycle(st.cycle)}
                title={`Cycle ${st.cycle}: ${st.selected_worker || 'system'} (${
                  st.observation?.slice(0, 40) || ''
                }...)`}
                className={`px-2 py-1 rounded text-[10px] font-mono transition-all flex items-center gap-1 shrink-0 ${
                  isCurrent
                    ? 'bg-blue-600 text-white font-bold ring-2 ring-blue-400/50'
                    : isPast
                    ? 'bg-zinc-800 text-zinc-200 border border-zinc-700 hover:bg-zinc-750'
                    : 'bg-zinc-950 text-zinc-600 border border-zinc-900 hover:text-zinc-400'
                }`}
              >
                <span>C{st.cycle}</span>
                {st.selected_worker && (
                  <span className="text-[9px] uppercase opacity-80">
                    {st.selected_worker.slice(0, 3)}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};
