import { BarChart3, Award } from 'lucide-react';

interface UtilityBreakdownViewProps {
  utilityScores?: Record<string, number>;
  selectedWorker?: string;
  cycleNumber?: number;
}

export const UtilityBreakdownView: React.FC<UtilityBreakdownViewProps> = ({
  utilityScores = {},
  selectedWorker = '',
  cycleNumber = 1,
}) => {
  const workerMeta: Record<string, { label: string; formula: string; color: string }> = {
    detection: {
      label: 'Detection Worker',
      formula: '1.0 * (untriaged / total_events)',
      color: 'bg-sky-500',
    },
    correlation: {
      label: 'Correlation Worker',
      formula: 'evidence_count * (1 - graph_density)',
      color: 'bg-purple-500',
    },
    investigation: {
      label: 'Investigation Worker',
      formula: '1.0 - max(hypotheses_confidences)',
      color: 'bg-pink-500',
    },
    reporting: {
      label: 'Reporting Worker',
      formula: '1.0 if confidence >= 0.65 & stabilized else 0',
      color: 'bg-emerald-500',
    },
    response: {
      label: 'Response Worker',
      formula: '1.0 if confirmed hypothesis exists else 0',
      color: 'bg-amber-500',
    },
  };

  const defaultKeys = ['detection', 'correlation', 'investigation', 'reporting', 'response'];
  const maxScore = Math.max(1.0, ...Object.values(utilityScores).map(Number));

  return (
    <div className="bg-[#0e131f] border border-gray-800 rounded-xl p-4 space-y-3 shadow-lg">
      <div className="flex items-center justify-between border-b border-gray-800/80 pb-2">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-amber-400" />
          <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-200">
            Worker Utility Competition (Argmax $U_w$)
          </h4>
        </div>
        <span className="text-[10px] font-mono text-gray-400">
          Cycle #{cycleNumber}
        </span>
      </div>

      <p className="text-[11px] text-gray-400 leading-snug">
        The Autonomous Planner scores each worker's utility against current investigation state gaps and dispatches the highest scoring worker.
      </p>

      {/* Horizontal Bar Chart */}
      <div className="space-y-2.5 pt-1">
        {defaultKeys.map((key) => {
          const score = utilityScores[key] ?? 0.0;
          const isWinner = selectedWorker.toLowerCase() === key.toLowerCase();
          const meta = workerMeta[key] || {
            label: key.toUpperCase(),
            formula: '',
            color: 'bg-blue-500',
          };
          const percentage = Math.min(100, Math.max(4, (score / maxScore) * 100));

          return (
            <div key={key} className="space-y-1">
              <div className="flex items-center justify-between text-xs font-mono">
                <div className="flex items-center gap-1.5">
                  {isWinner ? (
                    <Award className="w-3.5 h-3.5 text-amber-400 inline" />
                  ) : (
                    <span className="w-3.5 h-3.5 inline-block" />
                  )}
                  <span className={isWinner ? 'text-white font-bold' : 'text-gray-400'}>
                    {meta.label}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-gray-500 hidden sm:inline">
                    {meta.formula}
                  </span>
                  <span
                    className={`font-bold ${
                      isWinner ? 'text-amber-400 text-sm' : 'text-gray-400 text-xs'
                    }`}
                  >
                    {score.toFixed(3)}
                  </span>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="w-full bg-gray-950 h-2 rounded-full overflow-hidden border border-gray-800">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    isWinner ? 'bg-gradient-to-r from-amber-500 to-amber-300 shadow-md' : meta.color
                  }`}
                  style={{ width: `${percentage}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
