import uuid
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.correlation import EntityRelationship
from app.correlation.contracts import ResolvedEntity, EntityRelationPayload
from app.correlation.entity_resolver import EntityResolver, entity_resolver_instance


class CorrelationGraphEngine:
    """Builds and queries the multi-entity relationship graph across telemetry (Phase 6)."""

    def __init__(self, resolver: Optional[EntityResolver] = None):
        self.resolver = resolver or entity_resolver_instance

    def build_relationships_for_event(
        self,
        event: Dict[str, Any],
        resolved_entities: List[ResolvedEntity],
        db: Optional[Session] = None,
    ) -> List[EntityRelationPayload]:
        """Extracts directed relationships among entities co-occurring in a security event."""
        relationships: List[EntityRelationPayload] = []
        event_id_raw = event.get("id") or event.get("event_id")
        event_id: Optional[uuid.UUID] = None
        if event_id_raw:
            try:
                event_id = uuid.UUID(str(event_id_raw))
            except ValueError:
                event_id = None

        now = datetime.utcnow()

        # Categorize resolved entities by type
        hosts = [e for e in resolved_entities if e.entity_type == "host"]
        users = [e for e in resolved_entities if e.entity_type == "user"]
        ips = [e for e in resolved_entities if e.entity_type == "ip"]
        procs = [e for e in resolved_entities if e.entity_type == "process"]

        # 1. Host <-> User (authenticated_as)
        for h in hosts:
            for u in users:
                rel = EntityRelationPayload(
                    id=uuid.uuid4(),
                    source_entity_id=h.id,
                    target_entity_id=u.id,
                    relationship_type="authenticated_as",
                    confidence=0.95,
                    evidence_event_id=event_id,
                    valid_from=now,
                )
                relationships.append(rel)

        # 2. Host <-> Process (executed)
        for h in hosts:
            for p in procs:
                rel = EntityRelationPayload(
                    id=uuid.uuid4(),
                    source_entity_id=h.id,
                    target_entity_id=p.id,
                    relationship_type="executed",
                    confidence=0.98,
                    evidence_event_id=event_id,
                    valid_from=now,
                )
                relationships.append(rel)

        # 3. Host <-> IP (communicates_with)
        for h in hosts:
            for ip in ips:
                rel = EntityRelationPayload(
                    id=uuid.uuid4(),
                    source_entity_id=h.id,
                    target_entity_id=ip.id,
                    relationship_type="communicates_with",
                    confidence=0.90,
                    evidence_event_id=event_id,
                    valid_from=now,
                )
                relationships.append(rel)

        # 4. IP <-> IP (network_flow)
        src_ip_val = self.resolver.normalize_ip(event.get("src_ip") or event.get("source_ip"))
        dest_ip_val = self.resolver.normalize_ip(event.get("dest_ip") or event.get("destination_ip"))
        if src_ip_val and dest_ip_val and src_ip_val != dest_ip_val:
            src_ent = next((e for e in ips if e.identifier == src_ip_val), None)
            dest_ent = next((e for e in ips if e.identifier == dest_ip_val), None)
            if src_ent and dest_ent:
                rel = EntityRelationPayload(
                    id=uuid.uuid4(),
                    source_entity_id=src_ent.id,
                    target_entity_id=dest_ent.id,
                    relationship_type="network_flow",
                    confidence=0.99,
                    evidence_event_id=event_id,
                    valid_from=now,
                )
                relationships.append(rel)

        # Persist to database if db session provided
        if db is not None:
            for rel_payload in relationships:
                db_rel = EntityRelationship(
                    id=rel_payload.id,
                    source_entity_id=rel_payload.source_entity_id,
                    target_entity_id=rel_payload.target_entity_id,
                    relationship_type=rel_payload.relationship_type,
                    confidence=rel_payload.confidence,
                    evidence_event_id=rel_payload.evidence_event_id,
                    valid_from=rel_payload.valid_from,
                )
                db.add(db_rel)
            try:
                db.commit()
            except Exception:
                db.rollback()

        return relationships

    def compute_graph_metrics(
        self,
        nodes: List[ResolvedEntity],
        relationships: List[EntityRelationPayload],
    ) -> Dict[str, Any]:
        """Calculates graph structure density, node counts, and degree distributions."""
        num_nodes = len({n.id for n in nodes})
        num_edges = len(relationships)
        density = num_edges / max(1.0, float(num_nodes))

        # Adjacency
        degrees: Dict[uuid.UUID, int] = {}
        for r in relationships:
            degrees[r.source_entity_id] = degrees.get(r.source_entity_id, 0) + 1
            degrees[r.target_entity_id] = degrees.get(r.target_entity_id, 0) + 1

        top_degree = max(degrees.values()) if degrees else 0

        return {
            "node_count": num_nodes,
            "edge_count": num_edges,
            "graph_density": round(float(density), 4),
            "max_degree": top_degree,
        }


graph_engine_instance = CorrelationGraphEngine()
