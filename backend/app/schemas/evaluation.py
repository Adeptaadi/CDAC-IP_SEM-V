"""Pydantic V2 schemas for System Validation, Agent Evaluation & Performance Observability (P1).

Provides typed, auditable contracts for scenario evaluation results, agent execution reliability,
planner adaptivity metrics, and aggregate benchmark summaries.
"""

from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field, ConfigDict


class PlannerTraceStep(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cycle: int
    selected_worker: str
    selected_capability: str
    utility_score: Optional[float] = None
    observation: Optional[str] = None
    unresolved_question: Optional[str] = None
    confidence_before: float
    confidence_after: float
    confidence_delta: float
    latency_ms: Optional[int] = None
    evidence_gained: int = 0
    decision_type: str = "continue_investigation"


class WorkerEvaluationMetric(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    worker_type: str
    capability_name: str
    total_executions: int
    successful_executions: int
    failed_executions: int
    partial_executions: int
    success_rate_percent: float
    sample_size_repr: str  # e.g. "100.0% (3/3 executions)"
    average_latency_ms: float
    total_evidence_produced: int
    evidence_yield_per_execution: Optional[float] = None


class ScenarioInfo(BaseModel):
    scenario_id: str
    name: str
    source_type: str = "benchmark_derived_scenario"
    benchmark_basis: Optional[str] = "CSE-CIC-IDS2018 Profile"
    attack_type: Optional[str] = None
    description: Optional[str] = None


class TimingMetrics(BaseModel):
    started_at: str
    completed_at: Optional[str] = None
    total_duration_ms: Optional[float] = None


class InvestigationEvaluationMetrics(BaseModel):
    investigation_id: Optional[str] = None
    initial_confidence: Optional[float] = None
    final_confidence: Optional[float] = None
    confidence_delta: Optional[float] = None
    planning_cycles: int
    termination_reason: Optional[str] = None
    final_status: str


class PlannerEvaluationMetrics(BaseModel):
    total_selections: int
    unique_capabilities: int
    capability_diversity: Optional[float] = None  # unique / total
    replanning_events: int
    capability_revisits: int
    revisit_sequences: List[str] = Field(default_factory=list)
    confidence_progression: List[Dict[str, Any]] = Field(default_factory=list)
    execution_trace: List[PlannerTraceStep] = Field(default_factory=list)


class AgentExecutionMetrics(BaseModel):
    total_executions: int
    successful_executions: int
    failed_executions: int
    partial_executions: int
    execution_success_rate: float
    worker_metrics: List[WorkerEvaluationMetric] = Field(default_factory=list)


class EvidenceEvaluationMetrics(BaseModel):
    total_items: int
    direct_provenance_items: int
    derived_provenance_items: int
    legacy_unlinked_items: int
    evidence_per_successful_execution: Optional[float] = None


class RecommendationEvaluationMetrics(BaseModel):
    generated: bool
    action: Optional[str] = None
    risk_level: Optional[str] = None
    requires_human_review: Optional[bool] = None
    review_completed: Optional[bool] = None
    review_status: Optional[str] = None


class BenchmarkAccuracyScores(BaseModel):
    accuracy: float
    evidence_coverage: float
    hallucination_rate: float
    expected_calibration_error: float


class ScenarioEvaluationResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    evaluation_run_id: str
    scenario: ScenarioInfo
    status: Literal["completed", "failed", "partial"]
    timing: TimingMetrics
    investigation: InvestigationEvaluationMetrics
    planner: PlannerEvaluationMetrics
    agents: AgentExecutionMetrics
    evidence: EvidenceEvaluationMetrics
    recommendation: RecommendationEvaluationMetrics
    benchmark_scores: BenchmarkAccuracyScores


class AggregateEvaluationMetrics(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_evaluation_runs: int
    completed_runs: int
    failed_runs: int
    unique_scenarios_evaluated: int
    scenarios_evaluated_list: List[str] = Field(default_factory=list)
    average_planning_cycles: Optional[float] = None
    average_investigation_duration_ms: Optional[float] = None
    average_confidence_delta: Optional[float] = None
    average_evidence_per_investigation: Optional[float] = None
    total_replanning_events: int
    total_capability_revisits: int
    overall_agent_success_rate: float
    overall_agent_success_sample: str  # e.g. "100.0% (15/15 executions)"
    most_frequently_selected_capability: Optional[str] = None
    most_frequently_revisited_capability: Optional[str] = None
    highest_evidence_yield_capability: Optional[str] = None
    sample_size_population_statement: str
    generated_at: str


class EvaluationRunSummary(BaseModel):
    evaluation_run_id: str
    scenario_id: str
    scenario_name: str
    status: str
    started_at: str
    completed_at: Optional[str] = None
    duration_ms: Optional[float] = None
    planning_cycles: int
    final_confidence: float
    accuracy: float
    evidence_coverage: float
