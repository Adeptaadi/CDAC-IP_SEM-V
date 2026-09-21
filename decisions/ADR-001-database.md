# ADR-001: 3-Tier Polyglot Persistence Architecture

**Date:** 2026-09-21  
**Status:** Accepted  
**Deciders:** Project Sentinel Architecture Team  

---

## 1. Context and Problem Statement

Project Sentinel operates as an autonomous Cyber Threat Hunting platform. The system has three distinct storage requirements:
1. **Relational Investigation State:** Structured, ACID-compliant storage for investigations, timeline events, worker executions, planner decisions, reports, recommendations, and audit logs.
2. **Vector Similarity Search (RAG):** High-dimensional vector embeddings for MITRE ATT&CK techniques, incident playbooks, historical investigations, and threat intelligence.
3. **High-Throughput Streaming & Task Coordination:** In-memory queue and pub/sub system for continuous telemetry ingestion and agent task coordination.

A single monolithic database cannot efficiently serve relational transactional queries, vector similarity indexing, and high-frequency streaming simultaneously.

---

## 2. Decision

We adopt a **3-Tier Polyglot Persistence Strategy**:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. PostgreSQL 15+ (Relational Store)                        │
│    - Primary store for investigations, evidence, and audit  │
│    - UUID primary keys, JSONB for dynamic entity references │
├─────────────────────────────────────────────────────────────┤
│ 2. ChromaDB (Vector Store)                                  │
│    - Stores embeddings for MITRE ATT&CK, playbooks, IOCs    │
│    - Semantic retrieval for the RAG Knowledge Layer         │
├─────────────────────────────────────────────────────────────┤
│ 3. Redis 7 (In-Memory Cache & Stream Queue)                 │
│    - Pub/Sub streaming queue for telemetry events           │
│    - Shared task synchronization and checkpoint caching     │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Consequences

### Positive
* **Separation of Concerns:** Relational ACID integrity is preserved in Postgres without cluttering it with vector index bloat.
* **Fast Semantic Retrieval:** ChromaDB provides dedicated cosine-similarity vector search with metadata filtering for MITRE ATT&CK techniques.
* **Low Latency Streaming:** Redis handles high-frequency telemetry ingestion without locking database tables.
* **Auditability:** Relational tables record immutable audit logs with `UNIQUE (investigation_id, cycle_number)` to prevent cycle duplication.

### Negative / Trade-offs
* **Operational Overhead:** Requires orchestrating three distinct database services in `docker-compose.yml`.
* **Synchronization:** Vector IDs stored in PostgreSQL `knowledge_documents` must be kept in sync with ChromaDB vector IDs.

---

## 4. Alternatives Considered

1. **PostgreSQL with `pgvector` only:**
   * *Rejected:* Adds complexity to Postgres migrations and is less lightweight for developer onboarding than ChromaDB's zero-config local engine.
2. **MongoDB / Document Store:**
   * *Rejected:* Lacks strict relational foreign key enforcement and transactional integrity needed for audit-grade SOC investigation tracking.
