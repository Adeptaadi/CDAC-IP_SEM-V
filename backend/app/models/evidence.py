import uuid
import hashlib
import json
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column, String, Text, Integer, Numeric, DateTime, ForeignKey, Boolean
)
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import GUID, JSONB_TYPE, ARRAY_STRING, ARRAY_UUID


def compute_evidence_fingerprint(description: str, entity_refs: Optional[Dict[str, Any]] = None) -> str:
    """Computes a deterministic SHA-256 fingerprint for semantic deduplication of evidence."""
    clean_desc = (description or "").strip().lower()
    norm_entities = {}
    if entity_refs and isinstance(entity_refs, dict):
        for k in sorted(entity_refs.keys()):
            val = entity_refs[k]
            if isinstance(val, list):
                norm_entities[k] = sorted(str(x).strip().lower() for x in val if x)
            elif val:
                norm_entities[k] = str(val).strip().lower()
    raw = f"{clean_desc}::{json.dumps(norm_entities, sort_keys=True)}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class Evidence(Base):
    __tablename__ = "evidence"

    evidence_id = Column(GUID, primary_key=True, default=uuid.uuid4)
    investigation_id = Column(GUID, ForeignKey("investigations.investigation_id", ondelete="CASCADE"), nullable=False)
    source_type = Column(String(50), nullable=False)  # log, alert, worker_output, analyst_input
    source_ref = Column(Text, nullable=True)
    description = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=True, index=True)
    is_duplicate = Column(Boolean, default=False, nullable=False)
    is_novel = Column(Boolean, default=True, nullable=False)
    observation_count = Column(Integer, default=1, nullable=False)
    entity_refs = Column(JSONB_TYPE, nullable=True)  # {"hosts":[], "users":[], "ips":[]}
    produced_by_worker = Column(String(30), nullable=True)
    planner_decision_id = Column(GUID, ForeignKey("planner_decisions.decision_id", ondelete="SET NULL"), nullable=True)
    worker_execution_id = Column(GUID, ForeignKey("worker_executions.execution_id", ondelete="SET NULL"), nullable=True)
    agent_task_id = Column(GUID, ForeignKey("agent_tasks.id", ondelete="SET NULL"), nullable=True)
    corroborated_by = Column(ARRAY_UUID, default=list)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    investigation = relationship("Investigation", back_populates="evidence")
    planner_decision = relationship("PlannerDecision", back_populates="evidence")
    worker_execution = relationship("WorkerExecution", back_populates="evidence")
    agent_task = relationship("AgentTask", back_populates="evidence")


class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    event_id = Column(GUID, primary_key=True, default=uuid.uuid4)
    investigation_id = Column(GUID, ForeignKey("investigations.investigation_id", ondelete="CASCADE"), nullable=False)
    evidence_id = Column(GUID, ForeignKey("evidence.evidence_id"), nullable=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    event_summary = Column(Text, nullable=False)
    mitre_technique_id = Column(String(20), nullable=True)
    sequence_position = Column(Integer, nullable=True)

    investigation = relationship("Investigation", back_populates="timeline_events")


class Hypothesis(Base):
    __tablename__ = "hypotheses"

    hypothesis_id = Column(GUID, primary_key=True, default=uuid.uuid4)
    investigation_id = Column(GUID, ForeignKey("investigations.investigation_id", ondelete="CASCADE"), nullable=False)
    label = Column(String(255), nullable=False)
    status = Column(String(20), default="active", nullable=False)  # active, strengthened, weakened, rejected, confirmed
    confidence = Column(Numeric(5, 4), nullable=False)
    mitre_technique_ids = Column(ARRAY_STRING, default=list)
    generation_source = Column(String(50), default="RULE_DERIVED", nullable=True)  # RULE_DERIVED, RAG_ASSISTED, LLM_ASSISTED
    provenance_summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    investigation = relationship("Investigation", back_populates="hypotheses")


class HypothesisEvidence(Base):
    __tablename__ = "hypothesis_evidence"

    hypothesis_id = Column(GUID, ForeignKey("hypotheses.hypothesis_id", ondelete="CASCADE"), primary_key=True)
    evidence_id = Column(GUID, ForeignKey("evidence.evidence_id", ondelete="CASCADE"), primary_key=True)
    stance = Column(String(10), nullable=False)  # supports, contradicts
    weight = Column(Numeric(4, 3), default=1.0, nullable=False)
