from uuid import uuid4, UUID
from datetime import datetime
from typing import List, Optional, Dict, Any
from app.schemas.contracts import RetrievedChunk, RetrievedContext
from app.knowledge.store import knowledge_store
from app.knowledge.security import rag_security_filter
from app.knowledge.contracts import KnowledgeCitation
from app.knowledge.seed_data import (
    MITRE_TECHNIQUES_SEED,
    RESPONSE_PLAYBOOKS_SEED,
    HISTORICAL_CASES_SEED,
)


class RAGRetriever:
    """Retrieval-Augmented Generation engine for cybersecurity knowledge (IS §4)."""

    COLLECTION_MITRE = "mitre_attack"
    COLLECTION_PLAYBOOKS = "incident_playbooks"
    COLLECTION_HISTORICAL = "historical_cases"

    def __init__(self):
        self.store = knowledge_store

    def seed_all_knowledge(self) -> Dict[str, int]:
        """Seeds all default MITRE techniques, playbooks, and historical incidents into vector collections."""
        # 1. Seed MITRE ATT&CK
        mitre_docs = [
            f"MITRE {t['technique_id']}: {t['name']}. Tactic: {t['tactic']}. Description: {t['description']} Detection: {t['detection']} Mitigation: {t['mitigation']}"
            for t in MITRE_TECHNIQUES_SEED
        ]
        mitre_meta = [
            {
                "technique_id": t["technique_id"],
                "name": t["name"],
                "tactic": t["tactic"],
                "category": "mitre",
                "reliability_weight": t["reliability_weight"],
            }
            for t in MITRE_TECHNIQUES_SEED
        ]
        mitre_ids = [f"mitre_{t['id']}" for t in MITRE_TECHNIQUES_SEED]
        self.store.add_documents(self.COLLECTION_MITRE, mitre_docs, mitre_meta, mitre_ids)

        # 2. Seed Playbooks
        pb_docs = [
            f"Response Playbook {pb['name']}. Target Threat: {pb['target_threat']}. Description: {pb['description']}. Containment Steps: {' '.join(pb['containment_steps'])}"
            for pb in RESPONSE_PLAYBOOKS_SEED
        ]
        pb_meta = [
            {
                "name": pb["name"],
                "target_threat": pb["target_threat"],
                "category": "playbook",
                "reliability_weight": pb["reliability_weight"],
            }
            for pb in RESPONSE_PLAYBOOKS_SEED
        ]
        pb_ids = [f"pb_{pb['id']}" for pb in RESPONSE_PLAYBOOKS_SEED]
        self.store.add_documents(self.COLLECTION_PLAYBOOKS, pb_docs, pb_meta, pb_ids)

        # 3. Seed Historical Incidents
        hist_docs = [
            f"Historical Incident {h['title']}. Outcome: {h['outcome']}. Summary: {h['summary']}. Techniques: {','.join(h['mitre_techniques'])}"
            for h in HISTORICAL_CASES_SEED
        ]
        hist_meta = [
            {
                "title": h["title"],
                "outcome": h["outcome"],
                "category": "historical",
                "reliability_weight": h["reliability_weight"],
            }
            for h in HISTORICAL_CASES_SEED
        ]
        hist_ids = [f"hist_{h['id']}" for h in HISTORICAL_CASES_SEED]
        self.store.add_documents(self.COLLECTION_HISTORICAL, hist_docs, hist_meta, hist_ids)

        return {
            "mitre_count": self.store.count(self.COLLECTION_MITRE),
            "playbooks_count": self.store.count(self.COLLECTION_PLAYBOOKS),
            "historical_count": self.store.count(self.COLLECTION_HISTORICAL),
        }

    def retrieve(
        self,
        query: str,
        top_k: int = 8,
        category_filter: Optional[List[str]] = None
    ) -> RetrievedContext:
        """Retrieves and ranks relevant knowledge chunks matching query semantics (IS §4)."""
        clean_query = rag_security_filter.sanitize_content(query)
        candidates: List[Dict[str, Any]] = []

        collections_to_search = []
        if not category_filter or "mitre" in category_filter:
            collections_to_search.append(self.COLLECTION_MITRE)
        if not category_filter or "playbook" in category_filter:
            collections_to_search.append(self.COLLECTION_PLAYBOOKS)
        if not category_filter or "historical" in category_filter:
            collections_to_search.append(self.COLLECTION_HISTORICAL)

        for coll in collections_to_search:
            res = self.store.query(coll, clean_query, top_k=top_k)
            candidates.extend(res)

        # Calculate final rank score: similarity * reliability_weight
        chunks: List[RetrievedChunk] = []
        for c in candidates:
            meta = c.get("metadata", {})
            raw_sim = float(c.get("similarity", 0.5))
            rel_weight = float(meta.get("reliability_weight", 0.8))
            composite_score = raw_sim * rel_weight

            chunks.append(
                RetrievedChunk(
                    doc_id=uuid4(),
                    category=meta.get("category", "knowledge"),
                    text=c.get("document", ""),
                    similarity_score=composite_score,
                    reliability_weight=rel_weight,
                )
            )

        # Sort by composite score descending
        chunks.sort(key=lambda x: x.similarity_score, reverse=True)
        top_chunks = chunks[:top_k]

        return RetrievedContext(
            query=clean_query,
            chunks=top_chunks,
            assembled_at=datetime.utcnow()
        )

    def retrieve_citations(
        self,
        query: str,
        top_k: int = 5,
        category_filter: Optional[List[str]] = None,
    ) -> List[KnowledgeCitation]:
        """Returns structured citations with source, version, and content hash for evidence integration."""
        clean_query = rag_security_filter.sanitize_content(query)
        ctx = self.retrieve(clean_query, top_k=top_k, category_filter=category_filter)
        citations: List[KnowledgeCitation] = []

        for chunk in ctx.chunks:
            import hashlib
            chash = hashlib.sha256(chunk.text.encode("utf-8")).hexdigest()[:16]
            citations.append(
                KnowledgeCitation(
                    citation_id=uuid4(),
                    source_name=f"{chunk.category.upper()}_KNOWLEDGE_BASE",
                    doc_title=chunk.text.split(":", 1)[0] if ":" in chunk.text else chunk.category,
                    category=chunk.category,
                    version="1.0.0",
                    content_hash=chash,
                    snippet=chunk.text[:200],
                    reliability_weight=chunk.reliability_weight,
                )
            )
        return citations


rag_retriever = RAGRetriever()
