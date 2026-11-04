import uuid
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.correlation import IncidentCandidate
from app.correlation.contracts import ResolvedEntity, EntityRelationPayload, CorrelatedGroup
from app.correlation.entity_resolver import EntityResolver, entity_resolver_instance
from app.correlation.temporal import TemporalCorrelator, temporal_correlator_instance
from app.correlation.graph import CorrelationGraphEngine, graph_engine_instance
from app.correlation.scorer import CorrelationScorer, correlation_scorer_instance


class CorrelationEngine:
    """End-to-end Correlation Engine orchestrating entity resolution, temporal clustering, graph linking, scoring, and incident candidate generation (Phase 6)."""

    def __init__(
        self,
        resolver: Optional[EntityResolver] = None,
        temporal: Optional[TemporalCorrelator] = None,
        graph_engine: Optional[CorrelationGraphEngine] = None,
        scorer: Optional[CorrelationScorer] = None,
        min_candidate_score: float = 0.55,
    ):
        self.resolver = resolver or entity_resolver_instance
        self.temporal = temporal or temporal_correlator_instance
        self.graph_engine = graph_engine or graph_engine_instance
        self.scorer = scorer or correlation_scorer_instance
        self.min_candidate_score = min_candidate_score

    def correlate(
        self,
        events: List[Dict[str, Any]],
        db: Optional[Session] = None,
    ) -> List[IncidentCandidate]:
        """Runs the complete correlation pipeline over a batch of security events and creates IncidentCandidates."""
        if not events:
            return []

        # 1. Temporal partitioning into sliding-window clusters
        clusters = self.temporal.group_by_sliding_window(events)
        candidates: List[IncidentCandidate] = []

        for cluster in clusters:
            # 2. Extract and resolve all entities in the cluster
            all_resolved: List[ResolvedEntity] = []
            all_relationships: List[EntityRelationPayload] = []
            severities: List[str] = []
            confidences: List[float] = []
            event_ids: List[uuid.UUID] = []
            tactics: Set[str] = set()
            techniques: Set[str] = set()

            for ev in cluster:
                # Event ID
                ev_id_raw = ev.get("id") or ev.get("event_id")
                if ev_id_raw:
                    try:
                        event_ids.append(uuid.UUID(str(ev_id_raw)))
                    except ValueError:
                        pass

                # Resolved entities
                ents = self.resolver.extract_and_resolve_from_event(ev, db=db)
                all_resolved.extend(ents)

                # Relationships
                rels = self.graph_engine.build_relationships_for_event(ev, ents, db=db)
                all_relationships.extend(rels)

                # Severity & Confidence
                if ev.get("severity"):
                    severities.append(str(ev["severity"]))
                if ev.get("confidence") is not None:
                    try:
                        confidences.append(float(ev["confidence"]))
                    except ValueError:
                        pass

                # MITRE mappings
                for t in ev.get("mitre_tactics") or []:
                    tactics.add(t)
                for t in ev.get("mitre_techniques") or []:
                    techniques.add(t)

            # Deduplicate entities
            unique_entities = list({e.id: e for e in all_resolved}.values())

            # 3. Time boundaries
            times = [self.temporal.parse_event_time(ev) for ev in cluster]
            start_time = min(times)
            end_time = max(times)

            # 4. Correlation scoring (C = wt*T + we*E + ws*S)
            score = self.scorer.compute_composite_score(
                start_time=start_time,
                end_time=end_time,
                entities=unique_entities,
                event_count=len(cluster),
                severities=severities,
                confidences=confidences,
            )

            # 5. Graph metrics
            graph_metrics = self.graph_engine.compute_graph_metrics(unique_entities, all_relationships)

            # 6. Candidate evaluation
            has_high_sev = any(s.lower() in ["high", "critical"] for s in severities)
            if score >= self.min_candidate_score or (has_high_sev and len(cluster) >= 1):
                # Determine title and primary severity
                primary_sev = "critical" if any(s.lower() == "critical" for s in severities) else (
                    "high" if any(s.lower() == "high" for s in severities) else "medium"
                )

                # Build descriptive title
                entity_summary = ", ".join([f"{e.entity_type.upper()}:{e.identifier}" for e in unique_entities[:3]])
                title = f"Correlated Incident: Multi-Event Activity on {entity_summary or 'Target Environment'}"
                description = (
                    f"Correlated {len(cluster)} security events across {len(unique_entities)} entities "
                    f"with correlation score {score:.2f} (Density: {graph_metrics['graph_density']:.2f})."
                )

                candidate_id = uuid.uuid4()
                metadata = {
                    "correlation_score": score,
                    "event_count": len(cluster),
                    "event_ids": [str(eid) for eid in event_ids],
                    "entity_identifiers": [e.identifier for e in unique_entities],
                    "graph_metrics": graph_metrics,
                    "mitre_tactics": list(tactics),
                    "mitre_techniques": list(techniques),
                    "time_window_start": start_time.isoformat(),
                    "time_window_end": end_time.isoformat(),
                }

                candidate = IncidentCandidate(
                    id=candidate_id,
                    title=title,
                    description=description,
                    severity=primary_sev,
                    confidence=score,
                    candidate_metadata=metadata,
                    status="open",
                    created_at=datetime.utcnow(),
                )

                if db is not None:
                    db.add(candidate)
                    try:
                        db.commit()
                        db.refresh(candidate)
                    except Exception:
                        db.rollback()

                candidates.append(candidate)

        return candidates


correlation_engine_instance = CorrelationEngine()
