from typing import Dict, Tuple, List, Optional, Any
from app.config import settings


class InvestigationStateSnapshot:
    """Lightweight representation of the investigation state used for planning decisions."""
    def __init__(
        self,
        investigation_id: str,
        confidence: float = 0.0,
        cycle_number: int = 0,
        untriaged_event_count: int = 0,
        total_event_count: int = 0,
        evidence_count: int = 0,
        novel_evidence_count: int = 0,
        duplicate_evidence_count: int = 0,
        graph_density: float = 0.0,
        hypotheses_confidences: Optional[List[float]] = None,
        has_confirmed_hypothesis: bool = False,
        has_formulated_response: bool = False,
        cycles_since_confidence_gain: int = 0,
        cycles_since_meaningful_progress: int = 0,
        has_unresolved_contradictions: bool = False,
        analyst_requested_stop: bool = False,
        requires_analyst_review: bool = False,
        last_worker: Optional[str] = None,
        consecutive_worker_count: int = 0,
        worker_history: Optional[List[str]] = None,
        is_replanning: bool = False,
        replan_reason: Optional[str] = None,
        selected_worker_details: Optional[Dict[str, Any]] = None,
    ):
        self.investigation_id = investigation_id
        self.confidence = confidence
        self.cycle_number = cycle_number
        self.untriaged_event_count = untriaged_event_count
        self.total_event_count = total_event_count
        self.evidence_count = evidence_count
        self.novel_evidence_count = novel_evidence_count
        self.duplicate_evidence_count = duplicate_evidence_count
        self.graph_density = graph_density
        self.hypotheses_confidences = hypotheses_confidences or []
        self.has_confirmed_hypothesis = has_confirmed_hypothesis
        self.has_formulated_response = has_formulated_response
        self.cycles_since_confidence_gain = max(cycles_since_confidence_gain, cycles_since_meaningful_progress)
        self.cycles_since_meaningful_progress = max(cycles_since_meaningful_progress, cycles_since_confidence_gain)
        self.has_unresolved_contradictions = has_unresolved_contradictions
        self.analyst_requested_stop = analyst_requested_stop
        self.termination_reason: Optional[str] = None
        self.termination_classification: Optional[str] = None
        self.requires_analyst_review = requires_analyst_review
        self.last_worker = last_worker
        self.consecutive_worker_count = consecutive_worker_count
        self.worker_history = worker_history or []
        self.is_replanning = is_replanning
        self.replan_reason = replan_reason
        self.selected_worker_details = selected_worker_details or {}


def select_worker(
    state: InvestigationStateSnapshot,
    return_details: bool = False
) -> Any:
    """Scores worker capabilities against investigation state, applying execution history & repeat penalties (B0.5, B0.6)."""
    raw_scores: Dict[str, float] = {}

    # 1. Detection: high value when raw signals haven't been triaged
    if state.untriaged_event_count > 0:
        raw_scores["detection"] = 1.0 * (state.untriaged_event_count / max(1, state.total_event_count))
    elif state.cycle_number <= 1 and state.evidence_count < 8:
        raw_scores["detection"] = 0.40  # Viable for early secondary indicator collection
    else:
        raw_scores["detection"] = 0.05

    # 2. Correlation: high value when evidence exists but entity graph is sparse
    if state.evidence_count >= 2:
        density_factor = max(0.0, 1.0 - min(1.0, state.graph_density))
        raw_scores["correlation"] = float(state.evidence_count) * density_factor
    else:
        raw_scores["correlation"] = 0.0

    # 3. Investigation: high value when hypotheses are weak / contradicted / missing
    if state.has_unresolved_contradictions:
        raw_scores["investigation"] = 0.90
    elif state.hypotheses_confidences:
        raw_scores["investigation"] = 1.0 - max(state.hypotheses_confidences, default=0.0)
    else:
        raw_scores["investigation"] = 0.80  # No hypothesis yet -> favor hypothesis formulation

    # 4. Reporting: becomes viable once confidence is moderate-to-high (suppressed if contradictions exist)
    if state.confidence >= 0.65 and not state.has_unresolved_contradictions:
        raw_scores["reporting"] = 0.70 + min(0.30, state.confidence - 0.65)
    else:
        raw_scores["reporting"] = 0.0

    # 5. Response: safety-bounded once containment is already formulated
    if state.has_confirmed_hypothesis and not state.has_formulated_response:
        raw_scores["response"] = 0.95  # Formulate initial containment actions
    elif state.has_confirmed_hypothesis and state.has_formulated_response:
        raw_scores["response"] = 0.05  # Already formulated; near-zero remaining utility
    else:
        raw_scores["response"] = 0.0

    # History Awareness & Repeat Penalties (B0.5)
    history_adjustments: Dict[str, float] = {}
    adjusted_scores: Dict[str, float] = {}

    for w, base_s in raw_scores.items():
        adj = 1.0
        if state.is_replanning and state.last_worker == w:
            # Replan explicitly excludes the stagnated/failing worker
            adj = 0.0
        elif state.last_worker == w:
            # Exponential decay on repeated consecutive invocations (0.25^k)
            k = max(1, state.consecutive_worker_count)
            adj = round(0.25 ** k, 4)
        
        history_adjustments[w] = adj
        adjusted_scores[w] = round(base_s * adj, 4)

    # Determine highest utility capability
    best_worker = max(adjusted_scores, key=adjusted_scores.get)
    best_score = float(adjusted_scores[best_worker])

    # If all adjusted scores drop to 0.0 (e.g. edge cases), pick highest raw score
    if best_score <= 0.0:
        candidates = [w for w in raw_scores if w != state.last_worker]
        if candidates:
            best_worker = max(candidates, key=raw_scores.get)
            best_score = float(raw_scores[best_worker])
        else:
            best_worker = max(raw_scores, key=raw_scores.get)
            best_score = float(raw_scores[best_worker])

    rationale = (
        f"Selected '{best_worker}' (Score: {best_score:.4f}, Raw: {raw_scores.get(best_worker, 0.0):.4f}, "
        f"RepeatPenalty: {history_adjustments.get(best_worker, 1.0)})."
    )
    if state.is_replanning:
        rationale = f"[REPLAN] Pivoted from '{state.last_worker}' to '{best_worker}'. " + rationale

    state.selected_worker_details = {
        "raw_scores": {k: round(v, 4) for k, v in raw_scores.items()},
        "history_adjustments": history_adjustments,
        "adjusted_scores": adjusted_scores,
        "selection_rationale": rationale,
    }

    if return_details:
        return best_worker, best_score, adjusted_scores, history_adjustments, rationale
    return best_worker, best_score, adjusted_scores


def should_terminate(state: InvestigationStateSnapshot) -> bool:
    """Checks termination conditions matching IS §3.3 with clear safety-bound labeling (B0.8)."""
    if state.analyst_requested_stop:
        state.termination_reason = "analyst_requested_stop"
        state.termination_classification = "analyst_intervention"
        return True

    if state.requires_analyst_review:
        state.termination_reason = "stagnation"
        state.termination_classification = "stagnation_escalation"
        return True

    if state.cycle_number >= settings.MAX_PLANNING_CYCLES:
        state.termination_reason = "max_cycles_reached"
        state.termination_classification = "safety_bound"
        return True

    if (
        state.confidence >= settings.CONFIDENCE_AUTO_COMPLETE_THRESHOLD
        and state.cycle_number >= 3
        and not state.has_unresolved_contradictions
    ):
        state.termination_reason = "confidence_threshold_met"
        state.termination_classification = "uncalibrated_heuristic"
        return True

    stagnation_cycles = max(
        getattr(state, "cycles_since_meaningful_progress", 0),
        getattr(state, "cycles_since_confidence_gain", 0)
    )
    if stagnation_cycles >= settings.STAGNATION_CYCLE_LIMIT:
        state.termination_reason = "stagnation"
        state.termination_classification = "stagnation_escalation"
        state.requires_analyst_review = True
        return True

    return False
