import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Numeric, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import GUID, JSONB_TYPE


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    version = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    source = Column(String(255), nullable=True)
    dataset_type = Column(String(50), nullable=False)  # network_flow, system_log, pcap, mixed
    checksum = Column(String(128), nullable=True)
    dataset_metadata = Column("metadata", JSONB_TYPE, default=dict)
    registered_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    files = relationship("DatasetFile", back_populates="dataset", cascade="all, delete-orphan")
    replay_sessions = relationship("ReplaySession", back_populates="dataset", cascade="all, delete-orphan")


class DatasetFile(Base):
    __tablename__ = "dataset_files"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    dataset_id = Column(GUID, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    storage_uri = Column(Text, nullable=False)
    file_format = Column(String(30), nullable=False)  # csv, jsonl, pcap, evtx
    file_size_bytes = Column(BigInteger, nullable=True)
    checksum = Column(String(128), nullable=True)
    record_count = Column(BigInteger, nullable=True)
    schema_metadata = Column(JSONB_TYPE, default=dict)
    validation_status = Column(String(30), default="valid", nullable=False)  # pending, valid, invalid
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    dataset = relationship("Dataset", back_populates="files")
    ground_truth_labels = relationship("GroundTruthLabel", back_populates="dataset_file", cascade="all, delete-orphan")


class ReplaySession(Base):
    __tablename__ = "replay_sessions"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    dataset_id = Column(GUID, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(30), default="pending", nullable=False)  # pending, running, paused, completed, failed, cancelled
    replay_speed = Column(Numeric(10, 3), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    records_read = Column(BigInteger, default=0, nullable=False)
    records_accepted = Column(BigInteger, default=0, nullable=False)
    records_rejected = Column(BigInteger, default=0, nullable=False)
    configuration = Column(JSONB_TYPE, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    dataset = relationship("Dataset", back_populates="replay_sessions")
    security_events = relationship("SecurityEvent", back_populates="replay_session")


class GroundTruthLabel(Base):
    """Isolated evaluation-only ground truth labels to prevent training/inference leakage."""
    __tablename__ = "ground_truth_labels"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    dataset_file_id = Column(GUID, ForeignKey("dataset_files.id", ondelete="CASCADE"), nullable=False)
    source_record_id = Column(Text, nullable=False)
    label = Column(String(100), nullable=False)
    label_metadata = Column(JSONB_TYPE, default=dict)
    evaluation_split = Column(String(30), nullable=True)  # train, test, val, benchmark
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    dataset_file = relationship("DatasetFile", back_populates="ground_truth_labels")
