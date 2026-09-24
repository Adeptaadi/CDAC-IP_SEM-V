from typing import Dict, Tuple, List, Optional
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
        graph_density: float = 0.0,
        hypotheses_confidences: Optional[List[float]] = None,
        has_confirmed_hypothesis: bool = False,
        cycles_since_confidence_gain: int = 0,
        has_unresolved_contradictions: bool = False,
        analyst_requested_stop: bool = False,
    ):
        self.investigation_id = investigation_id
        self.confidence = confidence
        self.cycle_number = cycle_number
        self.untriaged_event_count = untriaged_event_count
        self.total_event_count = total_event_count
        self.evidence_count = evidence_count
        self.graph_density = graph_density
        self.hypotheses_confidences = hypotheses_confidences or []
        self.has_confirmed_hypothesis = has_confirmed_hypothesis
        self.cycles_since_confidence_gain = cycles_since_confidence_gain
        self.has_unresolved_contradictions = has_unresolved_contradictions
        self.analyst_requested_stop = analyst_requested_stop
        self.termination_reason: Optional[str] = None
        self.requires_analyst_review: bool = False


def select_worker(state: InvestigationStateSnapshot) -> Tuple[str, float, Dict[str, float]]:
    """Scores each of the 5 worker types against current investigation gaps (IS §3.2)."""
    scores: Dict[str, float] = {}

    # Detection: high value when raw signals haven't been triaged
    if state.untriaged_event_count > 0:
        scores["detection"] = 1.0 * (state.untriaged_event_count / max(1, state.total_event_count))
    else:
        scores["detection"] = 0.0

    # Correlation: high value when evidence exists but entity graph is sparse
    if state.evidence_count >= 2:
        scores["correlation"] = float(state.evidence_count) * (1.0 - min(1.0, state.graph_density))
    else:
        scores["correlation"] = 0.0

    # Investigation: high value when hypotheses are weak / contradicted / missing
    if state.hypotheses_confidences:
        scores["investigation"] = 1.0 - max(state.hypotheses_confidences, default=0.0)
    else:
        scores["investigation"] = 0.8  # no hypothesis yet -> strongly favor this worker

    # Reporting: becomes viable once confidence is moderate-to-high and stabilized
    if state.confidence >= 0.65 and state.cycles_since_confidence_gain >= 1:
        scores["reporting"] = 1.0
    else:
        scores["reporting"] = 0.0

    # Response: only viable once a hypothesis is confirmed
    if state.has_confirmed_hypothesis:
        scores["response"] = 1.0
    else:
        scores["response"] = 0.0

    # Clean rounding for presentation
    rounded_scores = {k: round(float(v), 4) for k, v in scores.items()}
    best_worker = max(scores, key=scores.get)
    return best_worker, float(scores[best_worker]), rounded_scores


def should_terminate(state: InvestigationStateSnapshot) -> bool:
    """Checks termination conditions matching IS §3.3."""
    if state.analyst_requested_stop:
        state.termination_reason = "analyst_requested_stop"
        return True

    if state.cycle_number >= settings.MAX_PLANNING_CYCLES:
        state.termination_reason = "max_cycles_reached"
        return True

    if (
        state.confidence >= settings.CONFIDENCE_AUTO_COMPLETE_THRESHOLD
        and state.cycle_number >= 3
        and not state.has_unresolved_contradictions
    ):
        state.termination_reason = "confidence_threshold_met"
        return True

    if state.cycles_since_confidence_gain >= settings.STAGNATION_CYCLE_LIMIT:
        state.termination_reason = "stagnation"
        state.requires_analyst_review = True
        return True

    return False
