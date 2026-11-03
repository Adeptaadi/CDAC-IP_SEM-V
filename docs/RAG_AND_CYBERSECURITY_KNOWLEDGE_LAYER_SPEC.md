# Project Sentinel — RAG and Cybersecurity Knowledge Layer Specification

**Document Type:** Technical Design Specification  
**Version:** 1.0  
**Status:** Architecture Baseline  
**Primary Focus:** Cybersecurity knowledge ingestion, vector retrieval, context construction, source traceability, retrieval evaluation, and safe integration with AI orchestration.  
**Related Components:** ChromaDB Vector Database, RAG Retrieval Service, `knowledge_retrieval` Capability, AI Planner, Investigation State Manager

---

# 1. Purpose

The AI Planner in Project Sentinel requires cybersecurity domain knowledge to interpret suspicious activity and make informed investigation decisions:
- What a particular attack technique represents.
- What types of telemetry may be relevant to an observed behavior.
- Which additional evidence could support or contradict a hypothesis.
- How a known attack pattern is generally characterized.

This information is not permanently embedded inside prompts or assumed to exist reliably within the language model. Instead, Project Sentinel uses a **Retrieval-Augmented Generation (RAG) knowledge layer**.

```text
CYBERSECURITY KNOWLEDGE (MITRE ATT&CK / Docs)
        │
        ▼
DOCUMENT INGESTION & VALIDATION
        │
        ▼
NORMALIZATION & CLEANING
        │
        ▼
CHUNKING + METADATA (500 tokens, 75 overlap)
        │
        ▼
EMBEDDING GENERATION (all-MiniLM-L6-v2)
        │
        ▼
VECTOR DATABASE (ChromaDB)
        │
        ▼
RETRIEVAL (Vector Search + Metadata Filtering)
        │
        ▼
RERANKING & RELEVANCE THRESHOLDING
        │
        ▼
CONTEXT PACKAGE
        │
        ▼
AI PLANNER / INVESTIGATION AGENT
```

The purpose of this layer is to provide **relevant context**, not to replace actual incident evidence.

---

# 2. Fundamental Knowledge Safety Principle

Project Sentinel enforces a strict mathematical and epistemic boundary between two types of information:

```text
                    INCIDENT
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
     TELEMETRY                 KNOWLEDGE
          │                         │
          ▼                         ▼
  WHAT HAPPENED?            WHAT MAY IT MEAN?
  (Empirical Proof)         (Contextual Theory)
          │                         │
          └────────────┬────────────┘
                       ▼
                AI INTERPRETATION
```

> **Axiomatic Rule**: Retrieved knowledge must never automatically become evidence that an attack occurred. Evidence establishes what happened; knowledge provides domain context.

---

# 3. Role of RAG in the Agent Architecture

The RAG system is exposed to the Planner strictly through the registered `knowledge_retrieval` capability. The Planner is forbidden from directly interacting with ChromaDB.

```text
AI PLANNER ──► "Need technique context" ──► KNOWLEDGE RETRIEVAL CAPABILITY ──► CHROMADB ──► VALIDATED CONTEXT PACKAGE ──► PLANNER
```

---

# 4. Knowledge Source Strategy

The MVP utilizes a small, curated knowledge base aligned with CSE-CIC-IDS2018 scenarios:
1. **MITRE ATT&CK Enterprise Techniques**: T1110 (Brute Force), T1190 (Exploit Public-Facing Application), T1071 (Application Layer C2 Protocol).
2. **Detection & Log Guidance**: Observable network indicators and flow field descriptions.
3. **Dataset Schema Documentation**: Descriptions of flow fields and labels.

---

# 5. Knowledge Document & Chunk Schemas

### 5.1 Document Metadata Schema
```json
{
  "document_id": "DOC-001",
  "title": "Attack Technique Reference",
  "source_type": "security_reference",
  "source_reference": "mitre-attack-enterprise",
  "content": "Normalized document content.",
  "knowledge_domain": "attack_technique",
  "tags": ["network", "credential_access"],
  "version": "1.0",
  "ingested_at": "2026-11-02T12:00:00Z",
  "content_hash": "sha256-hash"
}
```

### 5.2 Chunk Schema
```json
{
  "chunk_id": "CHK-001",
  "document_id": "DOC-001",
  "chunk_index": 3,
  "content": "Relevant cybersecurity knowledge content excerpt.",
  "metadata": {
    "title": "Attack Technique Reference",
    "knowledge_domain": "attack_technique",
    "source_reference": "mitre-attack-enterprise",
    "document_version": "1.0"
  }
}
```

---

# 6. Chunking & Embedding Strategy

```yaml
chunking:
  target_chunk_size: 500
  overlap: 75
  unit: tokens
  preserve_headings: true
```

### Vector Collection (`sentinel_knowledge`):
- **Embedding Model**: `all-MiniLM-L6-v2` (384 dimensions, local inference, CPU/GPU compatible).
- **Distance Metric**: Cosine similarity.

---

# 7. Retrieval Pipeline & Multi-Factor Scoring

```text
INVESTIGATION QUERY ──► QUERY EMBEDDING ──► VECTOR SEARCH (Top 20) ──► METADATA FILTERING ──► RERANKING ──► TOP 5 CONTEXT
```

### Multi-Factor Retrieval Score ($R_s$):
$$R_s = 0.50S + 0.20M + 0.20Q + 0.10F$$

Where:
- $S$ = Cosine semantic similarity (0–1)
- $M$ = Metadata match bonus (0–1)
- $Q$ = Source authority score (0–1)
- $F$ = Freshness / version recency (0–1)

---

# 8. Context Package & Citation Requirements

```json
{
  "retrieval_id": "RET-001",
  "query": "Investigation information requirement.",
  "results": [
    {
      "chunk_id": "CHK-001",
      "content": "Retrieved knowledge excerpt.",
      "retrieval_score": 0.89,
      "source": {
        "document_id": "DOC-001",
        "title": "Attack Technique Reference",
        "source_reference": "mitre-attack-enterprise"
      }
    }
  ],
  "result_count": 1
}
```

### Citation Rule:
Any AI narrative or interpretation must cite its sources:
- **Evidence References** (`EVD-xxx`): Supports claims about *what occurred*.
- **Knowledge References** (`DOC-xxx / CHK-xxx`): Supports interpretations of *what it means*.

---

# 9. Prompt Injection & Knowledge Security

Retrieved knowledge is strictly treated as **untrusted data**, never executable instructions:

```text
SYSTEM PROMPT (Immutable)
        │
        ▼
ORCHESTRATION POLICY (Hardcoded Controls)
        │
        ▼
RETRIEVED KNOWLEDGE (Escaped Data Payload)
        │
        ▼
AI PLANNER
```

Any prompt injection string embedded in documentation (e.g. *"Ignore previous instructions"*) is rendered inert because the planner prompt explicitly parses chunks as data items within strict JSON schemas.

---

# 10. Fallback Hierarchy

$$\text{Vector Search} \xrightarrow{\text{timeout}} \text{Retry} \xrightarrow{\text{failed}} \text{Simpler Reduced Query} \xrightarrow{\text{failed}} \text{Continue on Telemetry Evidence Only}$$

The system must never fabricate or invent retrieved knowledge.

---

# 11. Evaluation Metrics

$$\text{Precision@K} = \frac{\text{Relevant Retrieved Chunks}}{K}$$

$$\text{Recall@K} = \frac{\text{Relevant Retrieved Chunks}}{\text{Total Ground-Truth Relevant Chunks}}$$

$$\text{Mean Reciprocal Rank (MRR)} = \frac{1}{N} \sum_{i=1}^{N} \frac{1}{\text{rank}_i}$$

$$\text{Context Usefulness} = \frac{\text{Retrievals Used in Valid Decisions}}{\text{Total Successful Retrievals}}$$

---

# 12. Final Architecture Principle

> **Evidence establishes what happened. Knowledge provides context. The AI connects the two through controlled, evidence-driven reasoning.**
