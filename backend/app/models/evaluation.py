import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Numeric, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import GUID, JSONB_TYPE


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    scenario_id = Column(String(100), nullable=False)
    name = Column(String(200), nullable=False)
    configuration = Column(JSONB_TYPE, default=dict)
    status = Column(String(30), default="pending", nullable=False)  # pending, running, completed, failed
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    results = relationship("EvaluationResult", back_populates="evaluation_run", cascade="all, delete-orphan")


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    evaluation_run_id = Column(GUID, ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False)
    metric_name = Column(String(100), nullable=False)  # accuracy, precision, recall, ece, hallucination_rate, coverage
    metric_value = Column(Numeric(10, 6), nullable=False)
    details = Column(JSONB_TYPE, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    evaluation_run = relationship("EvaluationRun", back_populates="results")
