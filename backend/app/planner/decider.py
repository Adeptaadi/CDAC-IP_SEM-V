import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.planner.contracts import PlannerDecisionPayload, PlannerDecisionType
from app.planner.selection import InvestigationStateSnapshot, select_worker, should_terminate
from app.orchestration import CapabilityRegistry, capability_registry_instance


class DecisionValidationError(Exception):
    """Raised when a planner decision fails structural or security constraints."""
    pass


class DynamicPlanner:
    """Non-linear autonomous planner formulating capability decisions from evolving investigation state (Phase 9)."""

    def __init__(self, registry: Optional[CapabilityRegistry] = None):
        self.registry = registry or capability_registry_instance

    def formulate_decision(
        self,
        investigation_id: uuid.UUID,
        state: InvestigationStateSnapshot,
        unresolved_questions: Optional[List[str]] = None,
        last_error: Optional[str] = None,
    ) -> PlannerDecisionPayload:
        """Evaluates investigation conditions and produces a validated PlannerDecisionPayload."""
        questions = unresolved_questions or []
        now = datetime.utcnow()

        # 1. Termination & Review Check
        if should_terminate(state):
            if state.termination_reason == "confidence_threshold_met":
                return PlannerDecisionPayload(
                    decision_id=uuid.uuid4(),
                    investigation_id=investigation_id,
                    cycle_number=state.cycle_number,
                    decision_type="complete_investigation",
                    selected_capability="reporting.generate_report",
                    selected_worker="reporting",
                    selection_score=1.0,
                    confidence_before=state.confidence,
                    target_confidence=state.confidence,
                    reasoning=f"Confidence threshold satisfied ({state.confidence:.2f} >= 0.85). Finalizing report.",
                    created_at=now,
                )
            elif state.termination_reason in ["stagnation", "analyst_requested_stop"] or state.requires_analyst_review:
                return PlannerDecisionPayload(
                    decision_id=uuid.uuid4(),
                    investigation_id=investigation_id,
                    cycle_number=state.cycle_number,
                    decision_type="request_human_review",
                    selected_capability=None,
                    selected_worker="investigation",
                    selection_score=0.0,
                    confidence_before=state.confidence,
                    reasoning=f"Investigation reached review criteria: {state.termination_reason or 'Analyst intervention requested'}.",
                    created_at=now,
                )
            elif state.termination_reason == "max_cycles_reached":
                return PlannerDecisionPayload(
                    decision_id=uuid.uuid4(),
                    investigation_id=investigation_id,
                    cycle_number=state.cycle_number,
                    decision_type="escalate",
                    selected_capability=None,
                    selected_worker="investigation",
                    selection_score=0.0,
                    confidence_before=state.confidence,
                    reasoning="Max planning cycles exhausted without conclusive threshold. Escalating to Senior SOC Lead.",
                    created_at=now,
                )

        # 2. Re-plan Check (if previous worker failed or unresolved contradiction emerged)
        if last_error or state.has_unresolved_contradictions:
            # Shift focus to hypothesis testing or evidence collection
            return PlannerDecisionPayload(
                decision_id=uuid.uuid4(),
                investigation_id=investigation_id,
                cycle_number=state.cycle_number,
                decision_type="replan",
                selected_capability="investigation.collect_evidence",
                selected_worker="investigation",
                selection_score=0.85,
                confidence_before=state.confidence,
                reasoning=f"Replanning required to resolve ambiguity: {last_error or 'Hypothesis contradiction detected'}.",
                unresolved_questions=questions + ["Resolve contradictory evidence on primary hypothesis"],
                created_at=now,
            )

        # 3. Dynamic Worker Selection via Utility Function (IS §3.2)
        worker_type, utility_score, utility_scores = select_worker(state)

        # Map selected worker to corresponding capability
        if worker_type == "detection":
            cap_name = "detection.analyze_events"
        elif worker_type == "correlation":
            # If graph is already partially dense, do temporal correlation; otherwise analyze entities
            cap_name = "correlation.analyze_temporal_patterns" if state.graph_density > 0.4 else "correlation.analyze_entities"
        elif worker_type == "investigation":
            # If questions exist, retrieve context; otherwise collect evidence
            cap_name = "knowledge.retrieve_context" if questions else "investigation.collect_evidence"
        elif worker_type == "reporting":
            cap_name = "reporting.generate_report"
        elif worker_type == "response":
            cap_name = "response.simulate_action"
        else:
            cap_name = "investigation.collect_evidence"

        # Check capability human review requirement
        cap_def = self.registry.get(cap_name)
        if cap_def and cap_def.requires_human_approval and not state.has_confirmed_hypothesis:
            return PlannerDecisionPayload(
                decision_id=uuid.uuid4(),
                investigation_id=investigation_id,
                cycle_number=state.cycle_number,
                decision_type="request_human_review",
                selected_capability=cap_name,
                selected_worker=worker_type,
                selection_score=utility_score,
                confidence_before=state.confidence,
                reasoning=f"High-risk capability '{cap_name}' selected; pausing for analyst review.",
                created_at=now,
            )

        decision = PlannerDecisionPayload(
            decision_id=uuid.uuid4(),
            investigation_id=investigation_id,
            cycle_number=state.cycle_number,
            decision_type="continue_investigation",
            selected_capability=cap_name,
            selected_worker=worker_type,
            selection_score=round(utility_score, 4),
            confidence_before=state.confidence,
            target_confidence=min(0.95, state.confidence + 0.15),
            reasoning=f"Planner prioritized worker '{worker_type}' with utility {utility_score:.2f} (Scores: {utility_scores}).",
            unresolved_questions=questions,
            created_at=now,
        )

        self.validate_decision(decision)
        return decision

    def validate_decision(self, decision: PlannerDecisionPayload) -> None:
        """Validates decision consistency against registry, schema, and security policies (IS §9.3)."""
        valid_types = {
            "continue_investigation",
            "replan",
            "request_human_review",
            "complete_investigation",
            "escalate",
            "blocked",
        }
        if decision.decision_type not in valid_types:
            raise DecisionValidationError(f"Invalid decision type '{decision.decision_type}'")

        if decision.selected_capability:
            cap = self.registry.get(decision.selected_capability)
            if not cap:
                raise DecisionValidationError(f"Selected capability '{decision.selected_capability}' is not registered.")


dynamic_planner_instance = DynamicPlanner()
