from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.contracts import RetrievedContext
from app.knowledge.retriever import rag_retriever
from app.knowledge.store import knowledge_store

knowledge_router = APIRouter(prefix="/api/knowledge", tags=["RAG Knowledge Layer"])


class KnowledgeQueryRequest(BaseModel):
    query: str = Field(..., example="PowerShell base64 encoded command execution")
    top_k: int = Field(default=5, ge=1, le=20)
    categories: Optional[List[str]] = Field(default=None, example=["mitre", "playbook"])


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
        "seeded_counts": counts
    }


@knowledge_router.post("/query", response_model=RetrievedContext)
def query_knowledge_base(payload: KnowledgeQueryRequest):
    """Semantic search query across cybersecurity knowledge collections."""
    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    context = rag_retriever.retrieve(
        query=payload.query,
        top_k=payload.top_k,
        category_filter=payload.categories
    )
    return context


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
        total_vectors=mitre + playbooks + hist
    )
