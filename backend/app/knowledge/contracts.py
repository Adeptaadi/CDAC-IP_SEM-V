import uuid
from typing import Literal, Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

KnowledgeCategory = Literal[
    "mitre",
    "playbook",
    "historical",
    "sigma",
    "cve",
    "capec",
    "intel",
]


class KnowledgeCitation(BaseModel):
    """Authoritative citation reference for evidence provenance and reporting (Phase 10)."""
    model_config = ConfigDict(extra="allow", from_attributes=True)

    citation_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    source_name: str
    doc_title: str
    version: str = "1.0.0"
    category: str
    content_hash: str
    snippet: str
    reliability_weight: float = Field(ge=0.0, le=1.0, default=0.85)


class KnowledgeDocumentPayload(BaseModel):
    """Input payload to ingest a structured knowledge document into RAG."""
    model_config = ConfigDict(extra="allow")

    title: str
    category: KnowledgeCategory
    source: str
    version: str = "1.0.0"
    content: str
    reliability_weight: float = Field(ge=0.0, le=1.0, default=0.85)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeIngestionResult(BaseModel):
    """Result of document ingestion and vectorization."""
    model_config = ConfigDict(extra="allow")

    doc_id: uuid.UUID
    title: str
    category: str
    content_hash: str
    chunk_count: int
    vector_ids: List[str] = Field(default_factory=list)
