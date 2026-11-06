/**
 * P1 Evaluation & Performance Observability Types
 * Directly maps to backend schemas in app.schemas.evaluation
 */

export interface BenchmarkAccuracyScores {
  accuracy: number;
  evidence_coverage: number;
  hallucination_rate: number;
  expected_calibration_error: number;
}

export interface WorkerExecutionTelemetry {
  worker_type: string;
  capability_name: string;
  total_executions: number;
  successful_executions: number;
  failed_executions: number;
  success_rate: number;
  total_latency_ms: number;
  average_latency_ms: number;
  total_evidence_produced: number;
  average_evidence_yield: number;
  sample_size_repr: string;
}

export interface InvestigationEvaluationMetrics {
  investigation_id: string;
  planning_cycles: number;
  initial_confidence: number;
  final_confidence: number;
  confidence_delta: number;
  termination_reason: string;
  total_evidence_collected: number;
  duration_ms: number;
}

export interface PlannerTraceStep {
  cycle: number;
  selected_worker: string;
  capability_name?: string | null;
  confidence_before: number;
  confidence_after: number;
  confidence_delta: number;
  latency_ms: number;
  evidence_count_gained: number;
  status: string;
  explanation_summary?: string | null;
  is_replanning: boolean;
  revisit_count: number;
  candidate_utilities?: Record<string, number> | null;
}

export interface ScenarioEvaluationResult {
  evaluation_run_id: string;
  scenario_id: string;
  scenario_name: string;
  attack_category: string;
  source_profile: string;
  dataset_source: string;
  executed_at: string;
  investigation_metrics: InvestigationEvaluationMetrics;
  agent_metrics: {
    total_worker_executions: number;
    worker_success_rate: number;
    worker_metrics: Record<string, WorkerExecutionTelemetry>;
  };
  planner_metrics: {
    capability_diversity: number;
    unique_capabilities_used: number;
    replanning_events: number;
    capability_revisits: number;
    trace_steps: PlannerTraceStep[];
  };
  benchmark_scores: BenchmarkAccuracyScores;
}

export interface EvaluationRunSummary {
  evaluation_run_id: string;
  scenario_id: string;
  scenario_name: string;
  status: string;
  started_at: string;
  completed_at?: string | null;
  planning_cycles: number;
  confidence_delta: number;
  worker_success_rate: number;
  evidence_count: number;
  accuracy: number;
  coverage: number;
}

export interface AggregateEvaluationMetrics {
  total_evaluation_runs: number;
  scenarios_evaluated: string[];
  average_planning_cycles: number;
  average_investigation_duration_ms: number;
  average_confidence_delta: number;
  average_evidence_per_run: number;
  total_replanning_events: number;
  total_capability_revisits: number;
  overall_worker_success_rate: number;
  most_selected_capability?: string | null;
  most_revisited_capability?: string | null;
  highest_evidence_yield_worker?: string | null;
  transparency_statement: string;
}
