"""Pydantic V2 schemas for the Unified Investigation Workspace Projection (P0).

Provides a typed, consolidated, and provenance-grounded projection contract
optimized for the Agentic Investigation Workspace frontend.
"""

from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field, ConfigDict


class AffectedEntity(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    label: str
    type: Literal["host", "ip", "user", "process", "service", "unknown"] = "unknown"
    details: Optional[Dict[str, Any]] = None


class ThreatDataProvenance(BaseModel):
    source_type: str  # "benchmark_derived_scenario" | "live_security_telemetry" | "manual"
    scenario_name: Optional[str] = None
    benchmark_basis: Optional[str] = None


class ThreatSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    investigation_id: str
    title: str
    attack_type: Optional[str] = None
    severity: Literal["critical", "high", "medium", "low"] = "medium"
    affected_entities: List[AffectedEntity] = Field(default_factory=list)
    status: str
    confidence: float
    confidence_state: Literal["very_low", "low", "medium", "high", "confirmed"]
    current_cycle: int
    max_cycles: Optional[int] = 10
    detected_at: Optional[str] = None
    data_provenance: Optional[ThreatDataProvenance] = None


class ActiveCapabilityProjection(BaseModel):
    name: str
    worker_type: str
    status: Literal["idle", "running", "completed", "failed"] = "idle"
    risk_level: Optional[str] = "low"


class PlannerWorkspaceState(BaseModel):
    current_observation: Optional[str] = None
    unresolved_questions: List[str] = Field(default_factory=list)
    current_decision: Optional[str] = None
    decision_rationale: Optional[str] = None
    rationale_source: Optional[Literal["persisted", "derived_from_execution_data"]] = None
    is_replanning: bool = False
    active_capability: Optional[ActiveCapabilityProjection] = None


class FindingProvenance(BaseModel):
    source_worker: Optional[str] = None
    planner_decision_id: Optional[str] = None
    worker_execution_id: Optional[str] = None
    agent_task_id: Optional[str] = None
    produced_at: Optional[str] = None
    provenance_status: Literal["direct", "derived", "legacy_unlinked"] = "legacy_unlinked"


class KeyFinding(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    finding_id: str
    summary: str
    source_type: str
    source_worker: Optional[str] = None
    mitre_technique_id: Optional[str] = None
    mitre_tactic: Optional[str] = None
    entity_refs: Dict[str, List[str]] = Field(default_factory=dict)
    confidence_score: Optional[float] = None
    created_at: str
    provenance: FindingProvenance


class OrchestrationStep(BaseModel):
    cycle: int
    decision_type: str
    selected_worker: Optional[str] = None
    selected_capability: Optional[str] = None
    observation: Optional[str] = None
    unresolved_question: Optional[str] = None
    rationale: Optional[str] = None
    confidence_before: Optional[float] = None
    confidence_after: Optional[float] = None
    confidence_delta: Optional[float] = None
    latency_ms: Optional[int] = None
    evidence_count_gained: Optional[int] = None
    status: Literal["success", "partial", "failed", "pending"] = "success"
    created_at: str


class SupportingFinding(BaseModel):
    finding_id: str
    summary: str
    relevance: Optional[str] = None


class SimulationProjection(BaseModel):
    blast_radius_score: Optional[float] = None
    disruption_level: Optional[str] = None
    safety_assessment: Optional[str] = None
    rollback_plan: Optional[str] = None


class RecommendationProjection(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    action: str
    rationale: Optional[str] = None
    risk_level: Optional[str] = None
    requires_approval: bool = True
    approval_status: str = "pending"
    supporting_findings: List[SupportingFinding] = Field(default_factory=list)
    provenance_status: Literal["direct", "derived", "limited"] = "limited"
    simulation: Optional[SimulationProjection] = None


class HumanReviewProjection(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    review_id: str
    recommendation_id: Optional[str] = None
    status: str
    decision: Optional[str] = None
    analyst_id: Optional[str] = None
    analyst_comments: Optional[str] = None
    requested_at: Optional[str] = None
    decided_at: Optional[str] = None
    provenance_status: Literal["direct", "legacy_unlinked"] = "legacy_unlinked"


class WorkspaceMetadata(BaseModel):
    generated_at: str
    investigation_state_version: Optional[int] = None


class InvestigationWorkspaceProjection(BaseModel):
    threat: ThreatSummary
    planner: PlannerWorkspaceState
    key_findings: List[KeyFinding] = Field(default_factory=list)
    orchestration_history: List[OrchestrationStep] = Field(default_factory=list)
    recommendation: Optional[RecommendationProjection] = None
    human_review: Optional[HumanReviewProjection] = None
    workspace_metadata: WorkspaceMetadata
