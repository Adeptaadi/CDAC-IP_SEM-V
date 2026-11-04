import uuid
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.orchestration import Capability, CapabilityVersion
from app.orchestration.contracts import CapabilityDefinition


class CapabilityRegistry:
    """Catalog of registered worker capabilities ensuring typed discovery and configuration (Phase 8)."""

    def __init__(self):
        self._registry: Dict[str, CapabilityDefinition] = {}
        self._init_default_capabilities()

    def register(self, cap: CapabilityDefinition) -> None:
        """Registers a capability definition in-memory."""
        self._registry[cap.name] = cap

    def get(self, name: str) -> Optional[CapabilityDefinition]:
        """Retrieves a capability by unique name."""
        return self._registry.get(name)

    def list_capabilities(self, capability_type: Optional[str] = None) -> List[CapabilityDefinition]:
        """Lists all registered capabilities, optionally filtered by type."""
        all_caps = list(self._registry.values())
        if capability_type:
            return [c for c in all_caps if c.capability_type == capability_type]
        return all_caps

    def _init_default_capabilities(self):
        """Initializes standard baseline capabilities specified in Section 8.1."""
        defaults = [
            CapabilityDefinition(
                name="detection.analyze_events",
                version="1.0.0",
                description="Executes hybrid rule-based and ML anomaly detection over raw or normalized events.",
                capability_type="detection",
                worker_type="detection",
                risk_level="low",
                timeout_seconds=30,
                max_retries=2,
                requires_human_approval=False,
                input_schema={"type": "object", "properties": {"events": {"type": "array"}}},
                output_schema={"type": "object", "properties": {"findings": {"type": "array"}}},
            ),
            CapabilityDefinition(
                name="correlation.analyze_entities",
                version="1.0.0",
                description="Resolves entities across telemetry and builds an entity graph with cross-source edges.",
                capability_type="correlation",
                worker_type="correlation",
                risk_level="low",
                timeout_seconds=45,
                max_retries=2,
                requires_human_approval=False,
                input_schema={"type": "object", "properties": {"events": {"type": "array"}}},
                output_schema={"type": "object", "properties": {"graph_metrics": {"type": "object"}}},
            ),
            CapabilityDefinition(
                name="correlation.analyze_temporal_patterns",
                version="1.0.0",
                description="Performs sliding-window clustering and chronological sequence alignment on telemetry.",
                capability_type="correlation",
                worker_type="correlation",
                risk_level="low",
                timeout_seconds=30,
                max_retries=2,
                requires_human_approval=False,
                input_schema={"type": "object", "properties": {"events": {"type": "array"}}},
                output_schema={"type": "object", "properties": {"clusters": {"type": "array"}}},
            ),
            CapabilityDefinition(
                name="investigation.collect_evidence",
                version="1.0.0",
                description="Gathers corroborating telemetry, extracts indicators, and updates threat hypotheses.",
                capability_type="investigation",
                worker_type="investigation",
                risk_level="low",
                timeout_seconds=60,
                max_retries=2,
                requires_human_approval=False,
                input_schema={"type": "object", "properties": {"objective": {"type": "string"}}},
                output_schema={"type": "object", "properties": {"hypotheses": {"type": "array"}}},
            ),
            CapabilityDefinition(
                name="knowledge.retrieve_context",
                version="1.0.0",
                description="Queries the RAG knowledge store for relevant MITRE ATT&CK techniques and remediation playbooks.",
                capability_type="knowledge",
                worker_type="investigation",
                risk_level="low",
                timeout_seconds=20,
                max_retries=3,
                requires_human_approval=False,
                input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
                output_schema={"type": "object", "properties": {"knowledge_items": {"type": "array"}}},
            ),
            CapabilityDefinition(
                name="reporting.generate_report",
                version="1.0.0",
                description="Synthesizes investigation timeline, findings, evidence, and remediation guidance into formal reports.",
                capability_type="reporting",
                worker_type="reporting",
                risk_level="low",
                timeout_seconds=60,
                max_retries=1,
                requires_human_approval=False,
                input_schema={"type": "object", "properties": {"investigation_id": {"type": "string"}}},
                output_schema={"type": "object", "properties": {"report_text": {"type": "string"}}},
            ),
            CapabilityDefinition(
                name="response.simulate_action",
                version="1.0.0",
                description="Simulates containment and remediation actions (e.g. host isolation) under mandatory human approval.",
                capability_type="response",
                worker_type="response",
                risk_level="high",
                timeout_seconds=30,
                max_retries=0,
                requires_human_approval=True,  # Critical human-in-the-loop requirement
                input_schema={"type": "object", "properties": {"action_type": {"type": "string"}}},
                output_schema={"type": "object", "properties": {"simulation_plan": {"type": "object"}}},
            ),
        ]

        for d in defaults:
            self.register(d)

    def sync_to_db(self, db: Session) -> None:
        """Synchronizes in-memory capabilities and versions to relational database tables."""
        for cap_def in self._registry.values():
            existing = db.query(Capability).filter(Capability.name == cap_def.name).first()
            if not existing:
                cap_id = uuid.uuid4()
                db_cap = Capability(
                    id=cap_id,
                    name=cap_def.name,
                    description=cap_def.description,
                    capability_type=cap_def.capability_type,
                    is_active=True,
                    created_at=datetime.utcnow(),
                )
                db.add(db_cap)
                db.flush()

                db_ver = CapabilityVersion(
                    id=uuid.uuid4(),
                    capability_id=cap_id,
                    version=cap_def.version,
                    input_schema=cap_def.input_schema,
                    output_schema=cap_def.output_schema,
                    configuration={
                        "risk_level": cap_def.risk_level,
                        "timeout_seconds": cap_def.timeout_seconds,
                        "max_retries": cap_def.max_retries,
                        "requires_human_approval": cap_def.requires_human_approval,
                    },
                    is_current=True,
                    created_at=datetime.utcnow(),
                )
                db.add(db_ver)
            else:
                existing.description = cap_def.description
                existing.capability_type = cap_def.capability_type

        try:
            db.commit()
        except Exception:
            db.rollback()


capability_registry_instance = CapabilityRegistry()
