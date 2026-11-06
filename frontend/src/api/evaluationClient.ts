import { request } from './client';
import {
  ScenarioEvaluationResult,
  AggregateEvaluationMetrics,
  EvaluationRunSummary,
} from '../types/evaluation';

export const evaluationClient = {
  /**
   * Retrieves list of past evaluation runs with high-level summaries
   * GET /api/evaluation/runs
   */
  listEvaluationRuns: (limit: number = 50): Promise<EvaluationRunSummary[]> => {
    return request<EvaluationRunSummary[]>({
      method: 'GET',
      url: '/api/evaluation/runs',
      params: { limit },
    });
  },

  /**
   * Retrieves detailed execution, planning, and reliability telemetry for a specific evaluation run
   * GET /api/evaluation/runs/{id}
   */
  getEvaluationRun: (evaluationRunId: string): Promise<ScenarioEvaluationResult> => {
    return request<ScenarioEvaluationResult>({
      method: 'GET',
      url: `/api/evaluation/runs/${evaluationRunId}`,
    });
  },

  /**
   * Computes aggregate benchmark metrics across all completed evaluation runs
   * GET /api/evaluation/summary
   */
  getAggregateSummary: (): Promise<AggregateEvaluationMetrics> => {
    return request<AggregateEvaluationMetrics>({
      method: 'GET',
      url: '/api/evaluation/summary',
    });
  },

  /**
   * Triggers evaluation on-demand for a single scenario or all scenarios
   * POST /api/evaluation/run
   */
  triggerEvaluationRun: (scenarioId?: string, maxCycles: number = 6): Promise<any> => {
    return request<any>({
      method: 'POST',
      url: '/api/evaluation/run',
      params: {
        scenario_id: scenarioId,
        max_cycles: maxCycles,
      },
    });
  },
};
