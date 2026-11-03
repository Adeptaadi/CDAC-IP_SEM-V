import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, SmallInteger, Numeric, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import GUID, JSONB_TYPE


class Investigation(Base):
    __tablename__ = "investigations"

    investigation_id = Column(GUID, primary_key=True, default=uuid.uuid4)
    incident_candidate_id = Column(GUID, ForeignKey("incident_candidates.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    status = Column(String(30), default="active", nullable=False)  # active, paused, completed, escalated, closed_no_threat
    current_confidence = Column(Numeric(5, 4), default=0.0, nullable=False)
    confidence_state = Column(String(20), default="very_low", nullable=False)
    current_goal = Column(Text, nullable=True)
    planning_cycle_count = Column(SmallInteger, default=0, nullable=False)
    state_version = Column(Integer, default=1, nullable=False)  # Optimistic concurrency lock
    triggering_event_id = Column(GUID, nullable=True)
    assigned_analyst_id = Column(GUID, ForeignKey("users.user_id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    closed_at = Column(DateTime(timezone=True), nullable=True)

    incident_candidate = relationship("IncidentCandidate", back_populates="investigations")
    evidence = relationship("Evidence", back_populates="investigation", cascade="all, delete-orphan")
    timeline_events = relationship("TimelineEvent", back_populates="investigation", cascade="all, delete-orphan")
    hypotheses = relationship("Hypothesis", back_populates="investigation", cascade="all, delete-orphan")
    decisions = relationship("PlannerDecision", back_populates="investigation", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="investigation", cascade="all, delete-orphan")
    state_versions = relationship("InvestigationStateVersion", back_populates="investigation", cascade="all, delete-orphan")
    investigation_events = relationship("InvestigationEvent", back_populates="investigation", cascade="all, delete-orphan")
    agent_tasks = relationship("AgentTask", back_populates="investigation", cascade="all, delete-orphan")
    human_reviews = relationship("HumanReview", back_populates="investigation", cascade="all, delete-orphan")
    response_simulations = relationship("ResponseSimulation", back_populates="investigation", cascade="all, delete-orphan")


class InvestigationStateVersion(Base):
    __tablename__ = "investigation_state_versions"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    investigation_id = Column(GUID, ForeignKey("investigations.investigation_id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False)
    state_snapshot = Column(JSONB_TYPE, nullable=False)
    confidence = Column(Numeric(5, 4), nullable=False)
    cycle_number = Column(SmallInteger, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    investigation = relationship("Investigation", back_populates="state_versions")


class InvestigationEvent(Base):
    __tablename__ = "investigation_events"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    investigation_id = Column(GUID, ForeignKey("investigations.investigation_id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(50), nullable=False)  # task_started, task_completed, hypothesis_updated, replanned
    summary = Column(Text, nullable=False)
    details = Column(JSONB_TYPE, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    investigation = relationship("Investigation", back_populates="investigation_events")
