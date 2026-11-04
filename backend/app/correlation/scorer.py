from typing import List, Dict, Any, Set
from datetime import datetime
from app.correlation.contracts import ResolvedEntity
from app.correlation.temporal import TemporalCorrelator


class CorrelationScorer:
    """Computes composite multi-signal correlation scores based on temporal, entity, and severity signals (Phase 6).

    Formula (IS §6.4):
        C = w_t * T + w_e * E + w_s * S
    """

    def __init__(
        self,
        weight_temporal: float = 0.35,
        weight_entity: float = 0.40,
        weight_severity: float = 0.25,
    ):
        self.w_t = weight_temporal
        self.w_e = weight_entity
        self.w_s = weight_severity

    def compute_temporal_score(self, start_time: datetime, end_time: datetime, max_window_seconds: float = 3600.0) -> float:
        """T in [0, 1]: Higher if all events happened in tight succession."""
        span_seconds = abs((end_time - start_time).total_seconds())
        if span_seconds <= 1.0:
            return 1.0
        if span_seconds >= max_window_seconds:
            return 0.1
        # Linear decay mapped to [0.1, 1.0]
        return round(float(max(0.1, 1.0 - (span_seconds / max_window_seconds))), 4)

    def compute_entity_score(self, entities: List[ResolvedEntity], event_count: int) -> float:
        """E in [0, 1]: Higher if multiple distinct entity types or recurring shared entities exist."""
        if not entities or event_count == 0:
            return 0.0

        unique_types = {e.entity_type for e in entities}
        unique_ids = {e.identifier for e in entities}

        # Diversity score: 0.25 per unique type up to 4 types (host, user, ip, process)
        type_diversity = min(1.0, len(unique_types) * 0.25)

        # Entity density per event
        density = min(1.0, len(unique_ids) / max(1.0, float(event_count)))

        return round(0.6 * type_diversity + 0.4 * density, 4)

    def compute_severity_score(self, severities: List[str], confidences: List[float]) -> float:
        """S in [0, 1]: Higher if events include critical/high detections or strong confidence."""
        if not severities and not confidences:
            return 0.3

        severity_weights = {
            "critical": 1.0,
            "high": 0.8,
            "medium": 0.5,
            "low": 0.2,
        }
        max_sev = max([severity_weights.get(s.lower(), 0.3) for s in severities], default=0.3)
        avg_conf = sum(confidences) / max(1, len(confidences)) if confidences else 0.5

        return round(0.7 * max_sev + 0.3 * avg_conf, 4)

    def compute_composite_score(
        self,
        start_time: datetime,
        end_time: datetime,
        entities: List[ResolvedEntity],
        event_count: int,
        severities: List[str],
        confidences: List[float],
    ) -> float:
        """Calculates final combined correlation score C in [0.0, 1.0]."""
        T = self.compute_temporal_score(start_time, end_time)
        E = self.compute_entity_score(entities, event_count)
        S = self.compute_severity_score(severities, confidences)

        composite = (self.w_t * T) + (self.w_e * E) + (self.w_s * S)
        return round(float(min(1.0, max(0.0, composite))), 4)


correlation_scorer_instance = CorrelationScorer()
