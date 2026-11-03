import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Numeric, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import GUID, JSONB_TYPE


class Entity(Base):
    __tablename__ = "entities"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    entity_type = Column(String(50), nullable=False)  # host, user, ip, process, domain, file_hash
    identifier = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=True)
    entity_metadata = Column("metadata", JSONB_TYPE, default=dict)
    first_seen_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    last_seen_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_entity_type_identifier", "entity_type", "identifier", unique=True),
    )


class EntityRelationship(Base):
    __tablename__ = "entity_relationships"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    source_entity_id = Column(GUID, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    target_entity_id = Column(GUID, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    relationship_type = Column(String(50), nullable=False)  # communicates_with, authenticated_as, executed, resolved_to
    confidence = Column(Numeric(5, 4), default=1.0, nullable=False)
    evidence_event_id = Column(GUID, ForeignKey("security_events.id", ondelete="SET NULL"), nullable=True)
    valid_from = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    valid_to = Column(DateTime(timezone=True), nullable=True)

    source_entity = relationship("Entity", foreign_keys=[source_entity_id])
    target_entity = relationship("Entity", foreign_keys=[target_entity_id])


class IncidentCandidate(Base):
    __tablename__ = "incident_candidates"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String(30), nullable=False)  # low, medium, high, critical
    confidence = Column(Numeric(5, 4), default=0.50, nullable=False)
    candidate_metadata = Column("metadata", JSONB_TYPE, default=dict)
    status = Column(String(30), default="open", nullable=False)  # open, triaged, promoted, dismissed
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    investigations = relationship("Investigation", back_populates="incident_candidate")
