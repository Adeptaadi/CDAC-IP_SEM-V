/**
 * P0 Unified Investigation Workspace Projection Types
 * Directly maps to backend schemas in app.schemas.workspace_projection
 */

export type SeverityLevel = 'critical' | 'high' | 'medium' | 'low';
export type ConfidenceState = 'very_low' | 'low' | 'medium' | 'high' | 'confirmed';
export type WorkerStatus = 'idle' | 'running' | 'completed' | 'failed';
export type StepStatus = 'success' | 'partial' | 'failed' | 'pending';
export type ProvenanceStatus = 'direct' | 'derived' | 'limited' | 'legacy_unlinked';

export interface AffectedEntity {
  id: string;
  label: string;
  type: 'host' | 'ip' | 'user' | 'process' | 'service' | 'unknown';
  details?: Record<string, any> | null;
}

export interface ThreatDataProvenance {
  source_type: string;
  scenario_name?: string | null;
  benchmark_basis?: string | null;
}

export interface ThreatSummary {
  investigation_id: string;
  title: string;
  attack_type?: string | null;
  severity: SeverityLevel;
  affected_entities: AffectedEntity[];
  status: string;
  confidence: number;
  confidence_state: ConfidenceState;
  current_cycle: number;
  max_cycles?: number | null;
  detected_at?: string | null;
  data_provenance?: ThreatDataProvenance | null;
}

export interface ActiveCapabilityProjection {
  name: string;
  worker_type: string;
  status: WorkerStatus;
  risk_level?: string | null;
}

export interface PlannerWorkspaceState {
  current_observation?: string | null;
  unresolved_questions: string[];
  current_decision?: string | null;
  decision_rationale?: string | null;
  rationale_source?: 'persisted' | 'derived_from_execution_data' | null;
  is_replanning: boolean;
  active_capability?: ActiveCapabilityProjection | null;
}

export interface FindingProvenance {
  source_worker?: string | null;
  planner_decision_id?: string | null;
  worker_execution_id?: string | null;
  agent_task_id?: string | null;
  produced_at?: string | null;
  provenance_status: ProvenanceStatus;
}

export interface KeyFinding {
  finding_id: string;
  summary: string;
  source_type: string;
  source_worker?: string | null;
  mitre_technique_id?: string | null;
  mitre_tactic?: string | null;
  entity_refs: Record<string, string[]>;
  confidence_score?: number | null;
  created_at: string;
  provenance: FindingProvenance;
}

export interface OrchestrationStep {
  cycle: number;
  decision_type: string;
  selected_worker?: string | null;
  selected_capability?: string | null;
  observation?: string | null;
  unresolved_question?: string | null;
  rationale?: string | null;
  confidence_before?: number | null;
  confidence_after?: number | null;
  confidence_delta?: number | null;
  latency_ms?: number | null;
  evidence_count_gained?: number | null;
  status: StepStatus;
  created_at: string;
  candidate_utilities?: Record<string, number> | null;
  is_replanning?: boolean;
  replan_reason?: string | null;
}

export interface SupportingFinding {
  finding_id: string;
  summary: string;
  relevance?: string | null;
}

export interface SimulationProjection {
  blast_radius_score?: number | null;
  disruption_level?: string | null;
  safety_assessment?: string | null;
  rollback_plan?: string | null;
}

export interface RecommendationProjection {
  id: string;
  action: string;
  rationale?: string | null;
  risk_level?: string | null;
  requires_approval: boolean;
  approval_status: 'pending' | 'approved' | 'rejected' | 'modified';
  supporting_findings: SupportingFinding[];
  provenance_status: ProvenanceStatus;
  simulation?: SimulationProjection | null;
}

export interface HumanReviewProjection {
  review_id: string;
  recommendation_id?: string | null;
  status: string;
  decision?: string | null;
  analyst_id?: string | null;
  analyst_comments?: string | null;
  requested_at?: string | null;
  decided_at?: string | null;
  provenance_status: ProvenanceStatus;
}

export interface WorkspaceMetadata {
  generated_at: string;
  investigation_state_version?: number | null;
}

export interface InvestigationWorkspaceProjection {
  threat: ThreatSummary;
  planner: PlannerWorkspaceState;
  key_findings: KeyFinding[];
  orchestration_history: OrchestrationStep[];
  recommendation?: RecommendationProjection | null;
  human_review?: HumanReviewProjection | null;
  workspace_metadata: WorkspaceMetadata;
}

export interface InvestigationSummary {
  investigation_id: string;
  title: string;
  status: string;
  confidence: number;
  current_confidence?: number;
  confidence_state: ConfidenceState;
  state_version?: number;
  planning_cycle_count: number;
  created_at: string;
  updated_at?: string | null;
}

export interface InvestigationStateSnapshot {
  version_number: number;
  confidence: number;
  cycle_number: number;
  state_snapshot: Record<string, any>;
  created_at: string;
}

export interface ConfidenceFactorTraceItem {
  factor_name: string;
  input_value: any;
  raw_delta: number;
  weight: number;
  contribution: number;
  source: string;
}

export interface PlannerDecisionRecord {
  decision_id: string;
  cycle_number: number;
  decision_type: string;
  is_replanning: boolean;
  replan_reason?: string | null;
  selected_worker: string;
  selection_score?: number | null;
  utility_scores?: Record<string, number>;
  history_adjustments?: Record<string, number>;
  factor_contributions?: Record<string, any>;
  confidence_factor_trace?: ConfidenceFactorTraceItem[];
  rag_citations?: string[];
  confidence_delta?: number | null;
  novel_evidence_count?: number | null;
  duplicate_evidence_count?: number | null;
  latency_ms?: number | null;
  knowledge_need: string;
  confidence_before: number;
  confidence_after: number;
  explanation_summary: string;
  created_at: string;
}
