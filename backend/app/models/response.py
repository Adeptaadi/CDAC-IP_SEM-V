import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Boolean, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import GUID, JSONB_TYPE, ARRAY_UUID


class HumanReview(Base):
    __tablename__ = "human_reviews"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    investigation_id = Column(GUID, ForeignKey("investigations.investigation_id", ondelete="CASCADE"), nullable=False)
    recommendation_id = Column(GUID, ForeignKey("recommendations.recommendation_id", ondelete="SET NULL"), nullable=True)
    requested_action = Column(Text, nullable=False)
    risk_level = Column(String(20), nullable=False)  # low, medium, high, critical
    status = Column(String(20), default="pending", nullable=False)  # pending, approved, rejected, modified
    analyst_id = Column(GUID, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    analyst_comments = Column(Text, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    investigation = relationship("Investigation", back_populates="human_reviews")
    recommendation = relationship("Recommendation", back_populates="human_reviews")
    analyst = relationship("User")


class Recommendation(Base):
    __tablename__ = "recommendations"

    recommendation_id = Column(GUID, primary_key=True, default=uuid.uuid4)
    report_id = Column(GUID, ForeignKey("reports.report_id", ondelete="CASCADE"), nullable=False)
    action = Column(Text, nullable=False)
    risk_level = Column(String(10), nullable=False)  # low, medium, high, critical
    impact_summary = Column(Text, nullable=True)
    requires_approval = Column(Boolean, default=True, nullable=False)
    approval_status = Column(String(15), default="pending", nullable=False)  # pending, approved, rejected, executed
    supporting_evidence_ids = Column(ARRAY_UUID, default=list)
    approved_by_user_id = Column(GUID, ForeignKey("users.user_id"), nullable=True)

    report = relationship("Report", back_populates="recommendations")
    simulations = relationship("ResponseSimulation", back_populates="recommendation", cascade="all, delete-orphan")
    human_reviews = relationship("HumanReview", back_populates="recommendation")


class ResponseSimulation(Base):
    __tablename__ = "response_simulations"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    investigation_id = Column(GUID, ForeignKey("investigations.investigation_id", ondelete="CASCADE"), nullable=False)
    recommendation_id = Column(GUID, ForeignKey("recommendations.recommendation_id", ondelete="SET NULL"), nullable=True)
    action = Column(String(255), nullable=False)
    target_entity_id = Column(GUID, ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    simulated_impact = Column(JSONB_TYPE, default=dict)  # {"service_disruption": "none", "estimated_blast_radius": "host"}
    status = Column(String(30), default="simulated", nullable=False)  # simulated, approved, applied, aborted
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    investigation = relationship("Investigation", back_populates="response_simulations")
    recommendation = relationship("Recommendation", back_populates="simulations")
    target_entity = relationship("Entity")
