import os
import math
from typing import List, Dict, Any, Optional
from uuid import uuid4, UUID
from app.config import settings

CHROMA_PERSIST_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../chroma_data")
)


class EmbeddingGenerator:
    """Generates dense vector embeddings using SentenceTransformers or deterministic fallback."""
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self._dimension = 384

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except Exception:
                self._model = "fallback"
        return self._model

    def encode(self, texts: List[str]) -> List[List[float]]:
        model = self._get_model()
        if model != "fallback":
            embeddings = model.encode(texts, convert_to_numpy=True)
            return embeddings.tolist()
        else:
            # Deterministic hash-based 384-dim pseudo-embedding fallback for lightweight tests
            return [self._fallback_vector(t) for t in texts]

    def encode_one(self, text: str) -> List[float]:
        return self.encode([text])[0]

    def _fallback_vector(self, text: str) -> List[float]:
        import hashlib
        words = text.lower().split()
        vec = [0.0] * self._dimension
        for word in words:
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            for i in range(16):
                idx = (h >> (i * 8)) % self._dimension
                vec[idx] += 1.0

        # L2 normalize
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        else:
            vec[0] = 1.0
        return vec


class KnowledgeStore:
    """Manages vector collections in ChromaDB with persistent storage."""
    def __init__(self, persist_directory: Optional[str] = None):
        self.persist_dir = persist_directory or CHROMA_PERSIST_DIR
        os.makedirs(self.persist_dir, exist_ok=True)
        self.embedder = EmbeddingGenerator()
        self._client = None
        self._memory_docs: Dict[str, List[Dict[str, Any]]] = {}

    def _get_client(self):
        if self._client is None:
            try:
                import chromadb
                from chromadb.config import Settings as ChromaSettings
                self._client = chromadb.PersistentClient(
                    path=self.persist_dir,
                    settings=ChromaSettings(anonymized_telemetry=False)
                )
            except Exception:
                self._client = "in_memory_fallback"
        return self._client

    def get_or_create_collection(self, name: str):
        client = self._get_client()
        if client != "in_memory_fallback":
            return client.get_or_create_collection(name=name)
        else:
            if name not in self._memory_docs:
                self._memory_docs[name] = []
            return name

    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ):
        embeddings = self.embedder.encode(documents)
        client = self._get_client()

        if client != "in_memory_fallback":
            coll = client.get_or_create_collection(name=collection_name)
            coll.upsert(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )
        else:
            if collection_name not in self._memory_docs:
                self._memory_docs[collection_name] = []
            for doc, emb, meta, doc_id in zip(documents, embeddings, metadatas, ids):
                # replace if id exists
                self._memory_docs[collection_name] = [
                    d for d in self._memory_docs[collection_name] if d["id"] != doc_id
                ]
                self._memory_docs[collection_name].append({
                    "id": doc_id,
                    "document": doc,
                    "embedding": emb,
                    "metadata": meta
                })

    def query(
        self,
        collection_name: str,
        query_text: str,
        top_k: int = 5,
        category_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        query_embedding = self.embedder.encode_one(query_text)
        client = self._get_client()

        if client != "in_memory_fallback":
            try:
                coll = client.get_or_create_collection(name=collection_name)
                where_clause = {"category": category_filter} if category_filter else None
                results = coll.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    where=where_clause
                )
                output = []
                if results and results.get("ids") and len(results["ids"][0]) > 0:
                    for i in range(len(results["ids"][0])):
                        doc_id = results["ids"][0][i]
                        doc = results["documents"][0][i]
                        meta = results["metadatas"][0][i]
                        distance = results["distances"][0][i] if "distances" in results and results["distances"] else 0.5
                        # Cosine similarity approximation from distance
                        similarity = max(0.0, min(1.0, 1.0 - (distance / 2.0)))
                        output.append({
                            "id": doc_id,
                            "document": doc,
                            "metadata": meta,
                            "similarity": similarity
                        })
                return output
            except Exception:
                pass

        # In-memory cosine search fallback
        docs = self._memory_docs.get(collection_name, [])
        if category_filter:
            docs = [d for d in docs if d["metadata"].get("category") == category_filter]

        scored = []
        for d in docs:
            sim = self._cosine_similarity(query_embedding, d["embedding"])
            scored.append({
                "id": d["id"],
                "document": d["document"],
                "metadata": d["metadata"],
                "similarity": sim
            })

        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return scored[:top_k]

    def count(self, collection_name: str) -> int:
        client = self._get_client()
        if client != "in_memory_fallback":
            try:
                coll = client.get_or_create_collection(name=collection_name)
                return coll.count()
            except Exception:
                return len(self._memory_docs.get(collection_name, []))
        return len(self._memory_docs.get(collection_name, []))

    @staticmethod
    def _cosine_similarity(v1: List[float], v2: List[float]) -> float:
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a, b in zip(v1, v2)))
        norm2 = math.sqrt(sum(b * b for a, b in zip(v1, v2)))
        if norm1 > 0 and norm2 > 0:
            return max(0.0, min(1.0, dot / (norm1 * norm2)))
        return 0.0


knowledge_store = KnowledgeStore()
