import pytest
from app.knowledge.store import KnowledgeStore, EmbeddingGenerator
from app.knowledge.retriever import RAGRetriever
from app.schemas.contracts import RetrievedContext


def test_embedding_generator_dimension_and_norm():
    embedder = EmbeddingGenerator()
    vec = embedder.encode_one("PowerShell execution with base64 encoded payload")
    assert len(vec) == 384
    # Vector should be L2 normalized (approx 1.0)
    norm = sum(x * x for x in vec) ** 0.5
    assert abs(norm - 1.0) < 1e-4


def test_knowledge_store_add_and_query():
    store = KnowledgeStore()
    coll = "test_collection"
    docs = [
        "Adversaries use PowerShell to download remote malicious payloads.",
        "SQL injection allows attackers to bypass authentication and dump tables.",
        "Denial of service GoldenEye exhausts web server worker threads."
    ]
    meta = [
        {"technique": "T1059", "category": "mitre", "reliability_weight": 1.0},
        {"technique": "T1190", "category": "mitre", "reliability_weight": 1.0},
        {"technique": "T1498", "category": "mitre", "reliability_weight": 1.0}
    ]
    ids = ["doc_1", "doc_2", "doc_3"]

    store.add_documents(coll, docs, meta, ids)
    assert store.count(coll) >= 3

    results = store.query(coll, "PowerShell script command", top_k=1)
    assert len(results) == 1
    assert "PowerShell" in results[0]["document"]


def test_rag_retriever_seed_and_retrieve():
    retriever = RAGRetriever()
    counts = retriever.seed_all_knowledge()

    assert counts["mitre_count"] >= 8
    assert counts["playbooks_count"] >= 4
    assert counts["historical_count"] >= 2

    # Query specifically for credential brute force
    ctx = retriever.retrieve("brute force password guessing SSH FTP", top_k=3)
    assert isinstance(ctx, RetrievedContext)
    assert len(ctx.chunks) > 0
    assert any("T1110" in chunk.text or "Brute Force" in chunk.text for chunk in ctx.chunks)


def test_rag_retriever_category_filter():
    retriever = RAGRetriever()
    retriever.seed_all_knowledge()

    # Query only playbooks
    ctx = retriever.retrieve("isolation and firewall blocking", top_k=2, category_filter=["playbook"])
    assert len(ctx.chunks) > 0
    for chunk in ctx.chunks:
        assert chunk.category == "playbook"
