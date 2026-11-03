import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import GUID, JSONB_TYPE


class SecurityEvent(Base):
    __tablename__ = "security_events"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    replay_session_id = Column(GUID, ForeignKey("replay_sessions.id", ondelete="SET NULL"), nullable=True)
    dataset_file_id = Column(GUID, ForeignKey("dataset_files.id", ondelete="SET NULL"), nullable=True)
    source_record_id = Column(Text, nullable=True)
    event_type = Column(String(100), nullable=False)
    event_timestamp = Column(DateTime(timezone=True), nullable=False)
    ingestion_timestamp = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    source_ip = Column(String(45), nullable=True)  # supports IPv4 and IPv6
    destination_ip = Column(String(45), nullable=True)
    source_port = Column(Integer, nullable=True)
    destination_port = Column(Integer, nullable=True)
    protocol = Column(String(30), nullable=True)
    source_identifier = Column(String(255), nullable=True)
    normalized_data = Column(JSONB_TYPE, nullable=False)
    normalization_version = Column(String(50), default="1.0.0", nullable=False)
    content_hash = Column(String(128), nullable=True)

    __table_args__ = (
        Index("ix_sec_evt_timestamp", "event_timestamp"),
        Index("ix_sec_evt_src_ip", "source_ip"),
        Index("ix_sec_evt_dst_ip", "destination_ip"),
        Index("ix_sec_evt_src_ip_ts", "source_ip", "event_timestamp"),
        Index("ix_sec_evt_dst_ip_ts", "destination_ip", "event_timestamp"),
    )

    replay_session = relationship("ReplaySession", back_populates="security_events")
    detection_findings = relationship("DetectionFinding", back_populates="security_event")
