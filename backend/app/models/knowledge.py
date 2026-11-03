import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Numeric, DateTime, ForeignKey, Integer
)
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import GUID, JSONB_TYPE


class KnowledgeSource(Base):
    __tablename__ = "knowledge_sources"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(150), unique=True, nullable=False)
    source_type = Column(String(50), nullable=False)  # mitre_attack, playbooks, historical, threat_intel
    uri = Column(String(255), nullable=True)
    version = Column(String(50), nullable=True)
    source_metadata = Column("metadata", JSONB_TYPE, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    documents = relationship("KnowledgeDocument", back_populates="knowledge_source")


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    doc_id = Column(GUID, primary_key=True, default=uuid.uuid4)
    source_id = Column(GUID, ForeignKey("knowledge_sources.id", ondelete="SET NULL"), nullable=True)
    chroma_vector_id = Column(String(100), unique=True, nullable=False)
    category = Column(String(30), nullable=False)  # mitre, playbook, historical, ioc, sigma, capec, intel
    title = Column(String(255), nullable=False)
    source = Column(String(255), nullable=True)
    version = Column(String(20), nullable=True)
    reliability_weight = Column(Numeric(3, 2), default=0.80, nullable=False)
    last_embedded_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    knowledge_source = relationship("KnowledgeSource", back_populates="documents")
    chunks = relationship("KnowledgeChunk", back_populates="document", cascade="all, delete-orphan")


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    document_id = Column(GUID, ForeignKey("knowledge_documents.doc_id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, default=0, nullable=False)
    content = Column(Text, nullable=False)
    chroma_id = Column(String(100), nullable=True)
    chunk_metadata = Column("metadata", JSONB_TYPE, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    document = relationship("KnowledgeDocument", back_populates="chunks")
