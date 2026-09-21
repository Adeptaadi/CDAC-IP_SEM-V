import math
from typing import Dict, List, Optional
from app.config import settings
from app.schemas.contracts import WorkerResult


def logit(p: float, epsilon: float = 1e-5) -> float:
    """Safely compute logit (log-odds) for p in (0, 1)."""
    p_clamped = max(epsilon, min(1.0 - epsilon, p))
    return math.log(p_clamped / (1.0 - p_clamped))


def sigmoid(x: float) -> float:
    """Compute logistic sigmoid for real x."""
    return 1.0 / (1.0 + math.exp(-x))


class ConfidenceEngine:
    def __init__(self, custom_weights: Optional[Dict[str, float]] = None):
        self.weights = custom_weights or {
            "detection": settings.WEIGHT_DETECTION,
            "evidence": settings.WEIGHT_EVIDENCE,
            "correlation": settings.WEIGHT_CORRELATION,
            "knowledge": settings.WEIGHT_KNOWLEDGE,
            "agreement": settings.WEIGHT_AGREEMENT,
            "historical": settings.WEIGHT_HISTORICAL,
        }

    def compute_factors(
        self,
        worker_result: WorkerResult,
        evidence_count_this_cycle: int = 1,
        distinct_sources: int = 1,
        total_evidence: int = 1,
        corroborated: bool = False,
        edges_added: int = 0,
        nodes_in_graph: int = 1,
        knowledge_similarities: Optional[List[float]] = None,
        source_reliability: float = 0.8,
        worker_confidences: Optional[List[float]] = None,
        historical_sim_score: float = 0.0,
    ) -> Dict[str, float]:
        """Calculates individual factor deltas (δ_i) matching IS §1.3."""
        # 1. Detection Quality
        raw_detection = worker_result.confidence_signal
        delta_detection = (raw_detection * 1.0) - 0.5  # assuming medium multiplier (1.0) and baseline 0.5

        # 2. Evidence Quality
        source_diversity = min(1.0, distinct_sources / max(1, total_evidence))
        corroboration_bonus = 1.2 if corroborated else 1.0
        delta_evidence = (
            min(1.0, evidence_count_this_cycle / 5.0)
            * source_diversity
            * corroboration_bonus
        )

        # 3. Correlation Quality
        delta_correlation = edges_added / max(1.0, float(nodes_in_graph))

        # 4. Knowledge Match
        sims = knowledge_similarities or [0.5]
        delta_knowledge = (sum(sims) / len(sims)) * source_reliability

        # 5. Worker Agreement
        confs = worker_confidences or [worker_result.confidence_signal]
        if len(confs) > 1:
            mean_c = sum(confs) / len(confs)
            std_c = math.sqrt(sum((x - mean_c) ** 2 for x in confs) / len(confs))
            delta_agreement = 1.0 - (std_c / 0.5)
        else:
            delta_agreement = 0.5

        # 6. Historical Similarity
        delta_historical = max(-1.0, min(1.0, historical_sim_score))

        return {
            "detection": delta_detection,
            "evidence": delta_evidence,
            "correlation": delta_correlation,
            "knowledge": delta_knowledge,
            "agreement": delta_agreement,
            "historical": delta_historical,
        }

    def compute_delta(self, factors: Dict[str, float]) -> float:
        """Compute the weighted delta sum Σ w_i · δ_i."""
        return sum(self.weights.get(k, 0.0) * factors.get(k, 0.0) for k in self.weights)

    def update(self, current_confidence: float, delta: float) -> float:
        """Apply bounded logit-space update: sigmoid(logit(C) + delta)."""
        current_logit = logit(current_confidence)
        new_logit = current_logit + delta
        return sigmoid(new_logit)

    def classify_state(self, confidence: float) -> str:
        """Classify confidence into IS §1.5 bands."""
        if confidence < 0.20:
            return "very_low"
        elif confidence < 0.40:
            return "low"
        elif confidence < 0.65:
            return "moderate"
        elif confidence < 0.85:
            return "high"
        else:
            return "very_high"
