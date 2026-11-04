import hashlib
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.knowledge import KnowledgeSource, KnowledgeDocument, KnowledgeChunk
from app.knowledge.contracts import KnowledgeDocumentPayload, KnowledgeIngestionResult
from app.knowledge.security import rag_security_filter
from app.knowledge.store import knowledge_store, KnowledgeStore


class KnowledgeIngestionService:
    """Handles structured document parsing, chunking, SHA-256 hashing, and dual DB/vector storage (Phase 10)."""

    def __init__(self, store: Optional[KnowledgeStore] = None):
        self.store = store or knowledge_store
        self.security = rag_security_filter

    @staticmethod
    def compute_sha256(text: str) -> str:
        """Generates SHA-256 content hash for document versioning and tamper verification."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def chunk_text(self, text: str, max_chars: int = 600, overlap: int = 60) -> List[str]:
        """Performs structure-aware paragraph and sliding-window chunking."""
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks: List[str] = []

        current_chunk = ""
        for p in paragraphs:
            if len(current_chunk) + len(p) <= max_chars:
                current_chunk = f"{current_chunk}\n\n{p}".strip()
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                if len(p) > max_chars:
                    # Break long paragraph
                    start = 0
                    while start < len(p):
                        end = min(start + max_chars, len(p))
                        chunks.append(p[start:end])
                        start += max_chars - overlap
                    current_chunk = ""
                else:
                    current_chunk = p

        if current_chunk:
            chunks.append(current_chunk)

        return chunks or [text]

    def ingest_document(
        self,
        payload: KnowledgeDocumentPayload,
        db: Optional[Session] = None,
    ) -> KnowledgeIngestionResult:
        """Ingests a verified knowledge document into relational database and vector collections."""
        # 1. Security Validation
        self.security.validate_source(payload.source)
        clean_content = self.security.sanitize_content(payload.content)

        # 2. Hashing and Chunking
        doc_hash = self.compute_sha256(clean_content)
        chunks = self.chunk_text(clean_content)

        doc_id = uuid.uuid4()
        vector_ids: List[str] = []
        now = datetime.utcnow()

        # 3. Target Collection
        category = payload.category.lower()
        if category in ["mitre", "technique"]:
            coll_name = "mitre_attack"
        elif category in ["playbook", "response"]:
            coll_name = "incident_playbooks"
        else:
            coll_name = "historical_cases"

        # 4. Prepare Vector Store Payload
        chunk_docs: List[str] = []
        chunk_metas: List[Dict[str, Any]] = []

        for idx, chunk_text in enumerate(chunks):
            v_id = f"{category}_{doc_id}_{idx}"
            vector_ids.append(v_id)
            chunk_docs.append(f"{payload.title}: {chunk_text}")
            chunk_metas.append({
                "doc_id": str(doc_id),
                "title": payload.title,
                "category": category,
                "source": payload.source,
                "version": payload.version,
                "content_hash": doc_hash,
                "reliability_weight": payload.reliability_weight,
                "chunk_index": idx,
            })

        # Add to ChromaDB vector store
        self.store.add_documents(coll_name, chunk_docs, chunk_metas, vector_ids)

        # 5. Persist Relational Metadata in DB if session provided
        if db is not None:
            # Upsert KnowledgeSource
            src = db.query(KnowledgeSource).filter(KnowledgeSource.name == payload.source).first()
            if not src:
                src = KnowledgeSource(
                    id=uuid.uuid4(),
                    name=payload.source,
                    source_type=category,
                    version=payload.version,
                    created_at=now,
                )
                db.add(src)
                db.flush()

            # Create KnowledgeDocument
            k_doc = KnowledgeDocument(
                doc_id=doc_id,
                source_id=src.id,
                chroma_vector_id=vector_ids[0] if vector_ids else str(doc_id),
                category=category,
                title=payload.title,
                source=payload.source,
                version=payload.version,
                reliability_weight=payload.reliability_weight,
                last_embedded_at=now,
            )
            db.add(k_doc)
            db.flush()

            # Create KnowledgeChunks
            for idx, (chunk_text, v_id) in enumerate(zip(chunks, vector_ids)):
                k_chunk = KnowledgeChunk(
                    id=uuid.uuid4(),
                    document_id=doc_id,
                    chunk_index=idx,
                    content=chunk_text,
                    chroma_id=v_id,
                    chunk_metadata={"content_hash": doc_hash},
                    created_at=now,
                )
                db.add(k_chunk)

            try:
                db.commit()
            except Exception:
                db.rollback()

        return KnowledgeIngestionResult(
            doc_id=doc_id,
            title=payload.title,
            category=category,
            content_hash=doc_hash,
            chunk_count=len(chunks),
            vector_ids=vector_ids,
        )


knowledge_ingest_service = KnowledgeIngestionService()
