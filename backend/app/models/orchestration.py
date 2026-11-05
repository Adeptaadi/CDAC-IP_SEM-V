import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Boolean, SmallInteger, Numeric,
    DateTime, ForeignKey, UniqueConstraint, Integer
)
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import GUID, JSONB_TYPE


class Capability(Base):
    __tablename__ = "capabilities"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    capability_type = Column(String(50), nullable=False)  # detection, correlation, investigation, reporting, response
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    versions = relationship("CapabilityVersion", back_populates="capability", cascade="all, delete-orphan")
    agent_tasks = relationship("AgentTask", back_populates="capability")


class CapabilityVersion(Base):
    __tablename__ = "capability_versions"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    capability_id = Column(GUID, ForeignKey("capabilities.id", ondelete="CASCADE"), nullable=False)
    version = Column(String(50), nullable=False)
    input_schema = Column(JSONB_TYPE, nullable=False)
    output_schema = Column(JSONB_TYPE, nullable=False)
    configuration = Column(JSONB_TYPE, default=dict)
    is_current = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    capability = relationship("Capability", back_populates="versions")


class PlannerRun(Base):
    __tablename__ = "planner_runs"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    investigation_id = Column(GUID, ForeignKey("investigations.investigation_id", ondelete="CASCADE"), nullable=False)
    run_number = Column(Integer, nullable=False)
    cycle_number = Column(SmallInteger, nullable=False)
    reasoning = Column(Text, nullable=True)
    status = Column(String(30), default="completed", nullable=False)  # running, completed, replanned, aborted
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    decisions = relationship("PlannerDecision", back_populates="planner_run")


class PlannerDecision(Base):
    __tablename__ = "planner_decisions"
    __table_args__ = (UniqueConstraint("investigation_id", "cycle_number", name="uq_inv_cycle"),)

    decision_id = Column(GUID, primary_key=True, default=uuid.uuid4)
    investigation_id = Column(GUID, ForeignKey("investigations.investigation_id", ondelete="CASCADE"), nullable=False)
    planner_run_id = Column(GUID, ForeignKey("planner_runs.id", ondelete="SET NULL"), nullable=True)
    cycle_number = Column(SmallInteger, nullable=False)
    selected_worker = Column(String(30), nullable=False)
    selection_score = Column(Numeric(6, 4), nullable=True)
    knowledge_need = Column(Text, nullable=True)
    confidence_before = Column(Numeric(5, 4), nullable=False)
    confidence_after = Column(Numeric(5, 4), nullable=False)
    explanation_summary = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    investigation = relationship("Investigation", back_populates="decisions")
    planner_run = relationship("PlannerRun", back_populates="decisions")
    executions = relationship("WorkerExecution", back_populates="decision", cascade="all, delete-orphan")
    evidence = relationship("Evidence", back_populates="planner_decision")


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
    evidence = relationship("Evidence", back_populates="worker_execution")


class AgentTask(Base):
    __tablename__ = "agent_tasks"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    investigation_id = Column(GUID, ForeignKey("investigations.investigation_id", ondelete="CASCADE"), nullable=False)
    capability_id = Column(GUID, ForeignKey("capabilities.id", ondelete="SET NULL"), nullable=True)
    worker_type = Column(String(50), nullable=False)
    status = Column(String(30), default="pending", nullable=False)  # pending, running, completed, failed, cancelled
    objective = Column(Text, nullable=False)
    input_payload = Column(JSONB_TYPE, default=dict)
    output_payload = Column(JSONB_TYPE, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    investigation = relationship("Investigation", back_populates="agent_tasks")
    capability = relationship("Capability", back_populates="agent_tasks")
    attempts = relationship("TaskAttempt", back_populates="task", cascade="all, delete-orphan")
    evidence = relationship("Evidence", back_populates="agent_task")


class TaskDependency(Base):
    __tablename__ = "task_dependencies"

    task_id = Column(GUID, ForeignKey("agent_tasks.id", ondelete="CASCADE"), primary_key=True)
    depends_on_task_id = Column(GUID, ForeignKey("agent_tasks.id", ondelete="CASCADE"), primary_key=True)


class TaskAttempt(Base):
    __tablename__ = "task_attempts"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    task_id = Column(GUID, ForeignKey("agent_tasks.id", ondelete="CASCADE"), nullable=False)
    attempt_number = Column(Integer, default=1, nullable=False)
    status = Column(String(30), nullable=False)  # success, error, timeout
    latency_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    task = relationship("AgentTask", back_populates="attempts")


class OrchestrationCheckpoint(Base):
    __tablename__ = "orchestration_checkpoints"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    investigation_id = Column(GUID, ForeignKey("investigations.investigation_id", ondelete="CASCADE"), nullable=False)
    checkpoint_key = Column(String(100), nullable=False)
    state_payload = Column(JSONB_TYPE, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
