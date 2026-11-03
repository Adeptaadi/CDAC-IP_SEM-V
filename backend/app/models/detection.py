import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import GUID, JSONB_TYPE, ARRAY_STRING


class DetectionRule(Base):
    __tablename__ = "detection_rules"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    rule_key = Column(String(150), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    rule_type = Column(String(50), nullable=False)  # sigma, regex, heuristic, threshold
    severity = Column(String(30), nullable=False)    # low, medium, high, critical
    mitre_tactics = Column(ARRAY_STRING, default=list)
    mitre_techniques = Column(ARRAY_STRING, default=list)
    confidence = Column(Numeric(5, 4), default=0.80, nullable=False)
    rule_logic = Column(JSONB_TYPE, nullable=False)
    version = Column(String(50), default="1.0.0", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    findings = relationship("DetectionFinding", back_populates="rule")


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    model_name = Column(String(150), nullable=False)
    version = Column(String(50), nullable=False)
    model_type = Column(String(50), nullable=False)  # anomaly_detection, random_forest, xgboost, autoencoder
    artifact_uri = Column(Text, nullable=False)
    parameters = Column(JSONB_TYPE, default=dict)
    metrics = Column(JSONB_TYPE, default=dict)
    is_active = Column(Boolean, default=True, nullable=False)
    trained_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    findings = relationship("DetectionFinding", back_populates="model_version")


class DetectionFinding(Base):
    __tablename__ = "detection_findings"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    security_event_id = Column(GUID, ForeignKey("security_events.id", ondelete="CASCADE"), nullable=False)
    rule_id = Column(GUID, ForeignKey("detection_rules.id", ondelete="SET NULL"), nullable=True)
    model_version_id = Column(GUID, ForeignKey("model_versions.id", ondelete="SET NULL"), nullable=True)
    finding_type = Column(String(50), nullable=False)  # rule_match, anomaly_score, ml_classification
    confidence = Column(Numeric(5, 4), nullable=False)
    severity = Column(String(30), nullable=False)
    details = Column(JSONB_TYPE, default=dict)
    detected_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    security_event = relationship("SecurityEvent", back_populates="detection_findings")
    rule = relationship("DetectionRule", back_populates="findings")
    model_version = relationship("ModelVersion", back_populates="findings")
