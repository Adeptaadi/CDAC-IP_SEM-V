import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, SmallInteger, Numeric,
    DateTime, ForeignKey, UniqueConstraint, BigInteger, JSON, TypeDecorator
)
from sqlalchemy.orm import relationship
from app.database import Base

try:
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB as PG_JSONB, ARRAY as PG_ARRAY
except ImportError:
    PG_UUID, PG_JSONB, PG_ARRAY = None, None, None


class GUID(TypeDecorator):
    """Platform-independent GUID type. Uses PostgreSQL's UUID, otherwise String(36)."""
    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql' and PG_UUID is not None:
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return str(value) if isinstance(value, uuid.UUID) else str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        try:
            return uuid.UUID(str(value))
        except (ValueError, AttributeError):
            return value


JSONB_TYPE = JSON().with_variant(PG_JSONB, "postgresql") if PG_JSONB is not None else JSON
ARRAY_STRING = JSON().with_variant(PG_ARRAY(String), "postgresql") if PG_ARRAY is not None else JSON
ARRAY_UUID = JSON().with_variant(PG_ARRAY(PG_UUID(as_uuid=True)), "postgresql") if (PG_ARRAY is not None and PG_UUID is not None) else JSON



class Role(Base):
    __tablename__ = "roles"

    role_id = Column(SmallInteger, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)


class User(Base):
    __tablename__ = "users"

    user_id = Column(GUID, primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    display_name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    roles = relationship("Role", secondary="user_roles")


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id = Column(GUID, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(SmallInteger, ForeignKey("roles.role_id"), primary_key=True)


class Investigation(Base):
    __tablename__ = "investigations"

    investigation_id = Column(GUID, primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    status = Column(String(20), default="active", nullable=False)  # active, paused, completed, escalated, closed_no_threat
    current_confidence = Column(Numeric(5, 4), default=0.0, nullable=False)
    confidence_state = Column(String(20), default="very_low", nullable=False)
    current_goal = Column(Text, nullable=True)
    planning_cycle_count = Column(SmallInteger, default=0, nullable=False)
    triggering_event_id = Column(GUID, nullable=True)
    assigned_analyst_id = Column(GUID, ForeignKey("users.user_id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    closed_at = Column(DateTime(timezone=True), nullable=True)

    evidence = relationship("Evidence", back_populates="investigation", cascade="all, delete-orphan")
    timeline_events = relationship("TimelineEvent", back_populates="investigation", cascade="all, delete-orphan")
    hypotheses = relationship("Hypothesis", back_populates="investigation", cascade="all, delete-orphan")
    decisions = relationship("PlannerDecision", back_populates="investigation", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="investigation", cascade="all, delete-orphan")


class Evidence(Base):
    __tablename__ = "evidence"

    evidence_id = Column(GUID, primary_key=True, default=uuid.uuid4)
    investigation_id = Column(GUID, ForeignKey("investigations.investigation_id", ondelete="CASCADE"), nullable=False)
    source_type = Column(String(50), nullable=False)  # log, alert, worker_output, analyst_input
    source_ref = Column(Text, nullable=True)
    description = Column(Text, nullable=False)
    entity_refs = Column(JSONB_TYPE, nullable=True)  # {"hosts":[], "users":[], "ips":[]}
    produced_by_worker = Column(String(30), nullable=True)
    corroborated_by = Column(ARRAY_UUID, default=list)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    investigation = relationship("Investigation", back_populates="evidence")


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
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    investigation = relationship("Investigation", back_populates="hypotheses")


class HypothesisEvidence(Base):
    __tablename__ = "hypothesis_evidence"

    hypothesis_id = Column(GUID, ForeignKey("hypotheses.hypothesis_id", ondelete="CASCADE"), primary_key=True)
    evidence_id = Column(GUID, ForeignKey("evidence.evidence_id", ondelete="CASCADE"), primary_key=True)
    stance = Column(String(10), nullable=False)  # supports, contradicts
    weight = Column(Numeric(4, 3), default=1.0, nullable=False)


class PlannerDecision(Base):
    __tablename__ = "planner_decisions"
    __table_args__ = (UniqueConstraint("investigation_id", "cycle_number", name="uq_inv_cycle"),)

    decision_id = Column(GUID, primary_key=True, default=uuid.uuid4)
    investigation_id = Column(GUID, ForeignKey("investigations.investigation_id", ondelete="CASCADE"), nullable=False)
    cycle_number = Column(SmallInteger, nullable=False)
    selected_worker = Column(String(30), nullable=False)
    selection_score = Column(Numeric(6, 4), nullable=True)
    knowledge_need = Column(Text, nullable=True)
    confidence_before = Column(Numeric(5, 4), nullable=False)
    confidence_after = Column(Numeric(5, 4), nullable=False)
    explanation_summary = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    investigation = relationship("Investigation", back_populates="decisions")
    executions = relationship("WorkerExecution", back_populates="decision", cascade="all, delete-orphan")


class WorkerExecution(Base):
    __tablename__ = "worker_executions"

    execution_id = Column(GUID, primary_key=True, default=uuid.uuid4)
    decision_id = Column(GUID, ForeignKey("planner_decisions.decision_id", ondelete="CASCADE"), nullable=False)
    worker_type = Column(String(30), nullable=False)  # detection, correlation, investigation, reporting, response
    status = Column(String(15), nullable=False)  # success, partial, failed
    input_context_ref = Column(Text, nullable=True)
    raw_output = Column(JSONB_TYPE, nullable=False)
    latency_ms = Column(Integer, nullable=True)
    llm_token_usage = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    decision = relationship("PlannerDecision", back_populates="executions")


class Report(Base):
    __tablename__ = "reports"

    report_id = Column(GUID, primary_key=True, default=uuid.uuid4)
    investigation_id = Column(GUID, ForeignKey("investigations.investigation_id", ondelete="CASCADE"), nullable=False)
    executive_summary = Column(Text, nullable=False)
    technical_body = Column(Text, nullable=False)
    final_confidence = Column(Numeric(5, 4), nullable=False)
    generated_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    approved_by_user_id = Column(GUID, ForeignKey("users.user_id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    investigation = relationship("Investigation", back_populates="reports")
    recommendations = relationship("Recommendation", back_populates="report", cascade="all, delete-orphan")


class Recommendation(Base):
    __tablename__ = "recommendations"

    recommendation_id = Column(GUID, primary_key=True, default=uuid.uuid4)
    report_id = Column(GUID, ForeignKey("reports.report_id", ondelete="CASCADE"), nullable=False)
    action = Column(Text, nullable=False)
    risk_level = Column(String(10), nullable=False)  # low, medium, high, critical
    impact_summary = Column(Text, nullable=True)
    requires_approval = Column(Boolean, default=True, nullable=False)
    approval_status = Column(String(15), default="pending", nullable=False)  # pending, approved, rejected, executed
    approved_by_user_id = Column(GUID, ForeignKey("users.user_id"), nullable=True)

    report = relationship("Report", back_populates="recommendations")


class AuditLog(Base):
    __tablename__ = "audit_log"

    audit_id = Column(Integer().with_variant(BigInteger, "postgresql"), primary_key=True, autoincrement=True)
    investigation_id = Column(GUID, ForeignKey("investigations.investigation_id"), nullable=True)
    actor_type = Column(String(10), nullable=False)  # system, planner, worker, analyst
    actor_id = Column(String(100), nullable=True)
    action = Column(String(100), nullable=False)
    details = Column(JSONB_TYPE, nullable=True)
    occurred_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    doc_id = Column(GUID, primary_key=True, default=uuid.uuid4)
    chroma_vector_id = Column(String(100), unique=True, nullable=False)
    category = Column(String(30), nullable=False)  # mitre, playbook, historical, ioc, sigma, capec, intel
    title = Column(String(255), nullable=False)
    source = Column(String(255), nullable=True)
    version = Column(String(20), nullable=True)
    reliability_weight = Column(Numeric(3, 2), default=0.80, nullable=False)
    last_embedded_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
