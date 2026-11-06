import math
from typing import Dict, List, Optional, Any
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
            "contradiction": 0.20,
        }

    def compute_factors(
        self,
        worker_result: WorkerResult,
        evidence_count_this_cycle: int = 1,
        novel_evidence_count: Optional[int] = None,
        duplicate_evidence_count: int = 0,
        distinct_sources: int = 1,
        total_evidence: int = 1,
        corroborated: bool = False,
        edges_added: int = 0,
        nodes_in_graph: int = 1,
        knowledge_similarities: Optional[List[float]] = None,
        source_reliability: float = 0.8,
        has_novel_knowledge: bool = False,
        worker_confidences: Optional[List[float]] = None,
        historical_sim_score: float = 0.0,
        unresolved_contradictions_count: int = 0,
    ) -> Dict[str, float]:
        """Calculates individual factor deltas (δ_i) without artificial drift (B0.3 & B2.5)."""
        effective_novel_count = novel_evidence_count if novel_evidence_count is not None else evidence_count_this_cycle

        # 1. Detection Quality
        if worker_result.worker_type == "detection":
            raw_detection = worker_result.confidence_signal
            delta_detection = (raw_detection * 1.0) - 0.5  # baseline 0.5
        else:
            delta_detection = 0.0

        # 2. Evidence Quality
        if effective_novel_count <= 0:
            delta_evidence = 0.0
        else:
            source_diversity = min(1.0, distinct_sources / 2.0)
            corroboration_bonus = 1.2 if corroborated else 1.0
            delta_evidence = (
                min(1.0, effective_novel_count / 2.0)
                * source_diversity
                * corroboration_bonus
            )

        # 3. Correlation Quality
        if edges_added <= 0 or worker_result.worker_type not in ["correlation", "investigation"]:
            delta_correlation = 0.0
        else:
            delta_correlation = edges_added / max(1.0, float(nodes_in_graph))

        # 4. Knowledge Match
        if not has_novel_knowledge:
            delta_knowledge = 0.0
        else:
            sims = knowledge_similarities or [0.5]
            delta_knowledge = (sum(sims) / len(sims)) * source_reliability

        # 5. Worker Agreement
        confs = worker_confidences or []
        if len(confs) > 1:
            mean_c = sum(confs) / len(confs)
            std_c = math.sqrt(sum((x - mean_c) ** 2 for x in confs) / len(confs))
            delta_agreement = 0.5 - (std_c / 0.5)
        else:
            delta_agreement = 0.0

        # 6. Historical Similarity
        delta_historical = max(-1.0, min(1.0, historical_sim_score))

        # 7. Contradiction Penalty (Phase B2 §5.2)
        if unresolved_contradictions_count <= 0:
            delta_contradiction = 0.0
        else:
            ratio = min(1.0, unresolved_contradictions_count / max(1.0, float(total_evidence)))
            delta_contradiction = -0.60 * max(0.4, ratio)

        return {
            "detection": delta_detection,
            "evidence": delta_evidence,
            "correlation": delta_correlation,
            "knowledge": delta_knowledge,
            "agreement": delta_agreement,
            "historical": delta_historical,
            "contradiction": delta_contradiction,
        }

    def compute_factor_trace(
        self,
        factors: Dict[str, float],
        inputs: Optional[Dict[str, Any]] = None,
        sources: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """Returns structured factor-level confidence trace for every planner cycle."""
        inp = inputs or {}
        src = sources or {}
        trace = []
        for k in ["detection", "evidence", "correlation", "knowledge", "agreement", "historical", "contradiction"]:
            raw_d = float(factors.get(k, 0.0))
            w = float(self.weights.get(k, 0.0))
            contrib = round(w * raw_d, 4)
            trace.append({
                "factor_name": k,
                "input_value": inp.get(k, raw_d),
                "raw_delta": round(raw_d, 4),
                "weight": round(w, 3),
                "contribution": contrib,
                "source": src.get(k, "system_computation"),
            })
        return trace

    def compute_delta(self, factors: Dict[str, float]) -> float:
        """Compute the weighted delta sum Σ w_i · δ_i."""
        return sum(self.weights.get(k, 0.0) * factors.get(k, 0.0) for k in self.weights)

    def compute_factor_contributions(self, factors: Dict[str, float]) -> Dict[str, Dict[str, float]]:
        """Returns individual weighted factor contributions for visual observability."""
        return {
            k: {
                "raw_delta": round(float(factors.get(k, 0.0)), 4),
                "weight": round(float(self.weights.get(k, 0.0)), 3),
                "weighted_contribution": round(float(self.weights.get(k, 0.0) * factors.get(k, 0.0)), 4),
            }
            for k in self.weights
        }

    def update(
        self,
        current_confidence: float,
        delta: float,
        unresolved_contradictions_count: int = 0
    ) -> float:
        """Apply bounded logit-space update: sigmoid(logit(C) + delta), capped under unresolved contradiction."""
        current_logit = logit(current_confidence)
        new_logit = current_logit + delta
        new_conf = sigmoid(new_logit)
        if unresolved_contradictions_count > 0:
            # Unresolved contradictions strictly cap confidence at 0.60
            new_conf = min(0.60, new_conf)
        return new_conf

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
