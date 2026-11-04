from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.contracts import RetrievedContext
from app.knowledge import (
    rag_retriever,
    knowledge_store,
    knowledge_ingest_service,
    KnowledgeDocumentPayload,
    KnowledgeIngestionResult,
    KnowledgeCitation,
    UntrustedSourceError,
    PromptInjectionDetectedError,
)

knowledge_router = APIRouter(prefix="/api/knowledge", tags=["RAG Knowledge Layer"])


class KnowledgeQueryRequest(BaseModel):
    query: str = Field(..., json_schema_extra={"example": "PowerShell base64 encoded command execution"})
    top_k: int = Field(default=5, ge=1, le=20)
    categories: Optional[List[str]] = Field(default=None, json_schema_extra={"example": ["mitre", "playbook"]})


class KnowledgeStatsResponse(BaseModel):
    mitre_techniques_count: int
    playbooks_count: int
    historical_cases_count: int
    total_vectors: int


@knowledge_router.post("/seed")
def seed_knowledge_base():
    """Seeds MITRE ATT&CK techniques, response playbooks, and historical incidents into ChromaDB."""
    counts = rag_retriever.seed_all_knowledge()
    return {
        "status": "success",
        "message": "Knowledge layer seeded successfully",
        "seeded_counts": counts,
    }


@knowledge_router.post("/ingest", response_model=KnowledgeIngestionResult)
def ingest_document(
    payload: KnowledgeDocumentPayload,
    db: Session = Depends(get_db),
):
    """Ingests, chunks, hashes, and indexes an approved cybersecurity document (Phase 10)."""
    try:
        return knowledge_ingest_service.ingest_document(payload, db=db)
    except UntrustedSourceError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except PromptInjectionDetectedError as e:
        raise HTTPException(status_code=400, detail=str(e))


@knowledge_router.post("/query", response_model=RetrievedContext)
def query_knowledge_base(payload: KnowledgeQueryRequest):
    """Semantic search query across cybersecurity knowledge collections."""
    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    context = rag_retriever.retrieve(
        query=payload.query,
        top_k=payload.top_k,
        category_filter=payload.categories,
    )
    return context


@knowledge_router.post("/citations", response_model=List[KnowledgeCitation])
def retrieve_citations(payload: KnowledgeQueryRequest):
    """Retrieves authoritative knowledge citations for investigation reports and hypotheses."""
    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    return rag_retriever.retrieve_citations(
        query=payload.query,
        top_k=payload.top_k,
        category_filter=payload.categories,
    )


@knowledge_router.get("/stats", response_model=KnowledgeStatsResponse)
def get_knowledge_stats():
    """Returns the vector counts stored across all knowledge collections."""
    mitre = knowledge_store.count(rag_retriever.COLLECTION_MITRE)
    playbooks = knowledge_store.count(rag_retriever.COLLECTION_PLAYBOOKS)
    hist = knowledge_store.count(rag_retriever.COLLECTION_HISTORICAL)
    return KnowledgeStatsResponse(
        mitre_techniques_count=mitre,
        playbooks_count=playbooks,
        historical_cases_count=hist,
        total_vectors=mitre + playbooks + hist,
    )
