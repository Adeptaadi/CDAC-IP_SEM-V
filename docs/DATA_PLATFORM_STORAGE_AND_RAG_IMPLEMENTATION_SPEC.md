# Project Sentinel — Data Platform, Storage & RAG Implementation Specification (DPSRIS)

**Document Type:** Technical Design and Implementation Specification  
**Version:** 1.0  
**Status:** Architecture Baseline  
**Primary Focus:** Data architecture, PostgreSQL, Redis, vector storage, RAG pipelines, data lineage, provenance, retention, and investigation memory.  
**Related Components:** PostgreSQL 15 Database, Redis 7 Cache/Queue, ChromaDB Vector Store, Ingestion Engine, State Manager, AI Planner

---

# 1. Purpose

The AI orchestration layer cannot operate reliably without a structured and traceable data foundation.

Project Sentinel processes several fundamentally different types of data:
1. **Raw telemetry** — original security events from datasets or future sources.
2. **Normalized telemetry** — events converted into the project's canonical schema.
3. **Operational data** — alerts, investigations, actions, and audit records.
4. **Investigation evidence** — traceable empirical information supporting findings.
5. **Knowledge data** — cybersecurity documentation used through RAG.
6. **Temporary execution data** — caches, task state, and short-lived coordination data.

These data types must not all be stored in the same system:

```text
                    PROJECT SENTINEL DATA PLATFORM

 RAW DATASET
     │
     ▼
┌─────────────────┐
│ INGESTION LAYER │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ NORMALIZED      │
│ EVENT STORE     │──────────────► PostgreSQL
└────────┬────────┘
         │
         ├──────────────────► Detection & Correlation
         │
         ▼
┌─────────────────┐
│ INVESTIGATION   │──────────────► PostgreSQL
│ DATA            │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ AGENT CONTEXT   │──────────────► Redis / PostgreSQL
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ KNOWLEDGE RAG   │──────────────► ChromaDB
└─────────────────┘
```

---

# 2. Data Storage Principles

1. **Source Data Is Preserved**: Normalized events maintain an unbroken `raw_reference` to original source records.
2. **Structured and Semantic Data Remain Separate**: PostgreSQL stores structured operational truth; ChromaDB stores embeddings and semantic knowledge chunks. ChromaDB is never the system of record.
3. **Redis Is Not the Source of Truth**: Redis is strictly operational (ephemeral cache, distributed locking, worker coordination). All investigation truth resides in PostgreSQL.
4. **All Important Data Has Provenance**: Every major finding must answer where the information originated (raw event, capability result, knowledge chunk, or derived analysis).
5. **AI-Generated Text Is Not Automatically Evidence**:
   $$\text{Source Evidence } \neq \text{ AI Interpretation}$$
   LLM narrative must cite evidence UUIDs, not replace them.

---

# 3. Complete Data Flow

```text
┌───────────────┐
│ RAW DATASET   │
└───────┬───────┘
        ▼
┌───────────────┐
│ DATA INGESTION│
└───────┬───────┘
        ▼
┌───────────────┐
│ NORMALIZATION │
└───────┬───────┘
        ▼
┌───────────────┐
│ EVENT STORAGE │
└───────┬───────┘
        ├──────────────► DETECTION
        │                    │
        │                    ▼
        │                 ALERT
        │                    │
        ▼                    ▼
   CORRELATION        INVESTIGATION
                             │
                             ▼
                       AGENT ORCHESTRATION
                        │             │
                        ▼             ▼
                   POSTGRESQL      CHROMADB
                   Investigation    Knowledge
                     Evidence         RAG
                        │             │
                        └──────┬──────┘
                               ▼
                         FINAL REPORT
```

---

# 4. PostgreSQL Architecture (System of Record)

PostgreSQL is the authoritative persistent store for:
- Telemetry Metadata & Canonical Events
- Normalized Entities & Entity Relationships
- Detection Rules & Results
- Alerts & Investigation State
- Scored Evidence & Hypotheses
- Action & Decision Audit Logs
- Final Investigation Reports

### Logical Schema Separation:
```text
DATABASE: sentinel
│
├── telemetry       (events, entities, event_entities, raw_sources)
├── detection       (detection_rules, detection_results, alerts)
├── investigation   (investigations, actions, evidence, hypotheses, state_transitions)
├── audit           (audit_logs)
└── reporting       (reports)
```

---

# 5. Core Relational Schemas

### 5.1 Events Table (`telemetry.events`)
| Column | Type | Constraints | Purpose |
|---|---|---|---|
| `event_id` | UUID | PRIMARY KEY | Internal unique event identifier |
| `source_event_id` | Text | NOT NULL | Identifier in original source dataset |
| `source_id` | UUID | REFERENCES `raw_sources` | Pointer to source dataset file |
| `event_type` | Text | NOT NULL | Canonical type (`network_connection`, `auth`, `process`) |
| `occurred_at` | Timestamp with TZ | NOT NULL | Telemetry timestamp |
| `ingested_at` | Timestamp with TZ | NOT NULL | Ingestion timestamp |
| `entities` | JSONB | NOT NULL | Embedded entity dictionary |
| `attributes` | JSONB | NULL | Source-specific extensible attributes |
| `raw_reference` | Text | NOT NULL | Lineage pointer (`raw://dataset/file-01/record-1024`) |
| `schema_version` | Text | NOT NULL | Event contract version |

### 5.2 Event Indexing Strategy
```sql
CREATE INDEX idx_events_occurred_at ON telemetry.events (occurred_at);
CREATE INDEX idx_events_event_type ON telemetry.events (event_type);
CREATE INDEX idx_events_source_id ON telemetry.events (source_id);
CREATE INDEX idx_events_entities_gin ON telemetry.events USING GIN (entities);
```

### 5.3 Normalized Entities & Pivot Relationships
```text
telemetry.entities (entity_id, entity_type, normalized_value, first_seen, last_seen, attributes)
telemetry.event_entities (event_id, entity_id, relationship_type)
```

---

# 6. Investigation State Hybrid Persistence

The system uses a **hybrid relational + snapshot model**:

```text
STRUCTURED RELATIONAL TABLES + STATE SNAPSHOT
```

1. **Relational Tables**: Provides referential integrity, historical querying, and auditability.
2. **State Snapshots (`state_snapshot` in `investigations`)**: Stores current state JSON for instantaneous crash recovery and atomic optimistic lock checks ($\text{ExpectedVersion} = \text{CurrentVersion}$).

```json
{
  "investigation_id": "INV-001",
  "state_version": 5,
  "snapshot": {
    "facts": [],
    "hypotheses": [],
    "evidence_gaps": []
  }
}
```

---

# 7. Evidence & Audit Logging

- **`investigation.evidence`**: Stores empirical evidence items linked to ancestral `source_event_ids`, calculated evidence score ($E_s$), directness, and corroboration score.
- **`audit.audit_logs`**: Strictly append-only cryptographic ledger recording `component`, `event_type`, `input_state_version`, `output_reference`, and UTC timestamp. Existing rows cannot be modified or deleted.

---

# 8. Redis Operational Layer

Redis 7 is strictly scoped for ephemeral operational acceleration:
- **Short-Lived Query Cache**: Key format `sentinel:query:{sha256_hash}` (TTL: 300s).
- **Capability Result Cache**: Key format `sentinel:capability:{request_id}` (TTL: 600s).
- **Worker Distributed Locks**: Key format `sentinel:lock:inv:{investigation_id}` (TTL: 30s).
- **Rate Limiting & Queue State**: Active Celery/Arq task queue tracking.

---

# 9. ChromaDB Vector Knowledge Architecture (RAG)

ChromaDB provides external domain context (e.g. MITRE ATT&CK techniques, detection rules, threat actor profiles). It is never used to store raw incident events.

```text
KNOWLEDGE SOURCES (MITRE ATT&CK / Docs)
       │
       ▼
TEXT EXTRACTION & CLEANING
       │
       ▼
CHUNKING (400–800 tokens, 50–100 token overlap)
       │
       ▼
EMBEDDINGS (all-MiniLM-L6-v2)
       │
       ▼
CHROMADB COLLECTION (`security_knowledge`)
       │
       ▼
COSINE VECTOR SEARCH (Top-K) ──► METADATA FILTER ──► RERANKER ──► CONTEXT PACKAGE
```

### Chunk Metadata Schema:
```json
{
  "chunk_id": "CHUNK-001",
  "document_id": "DOC-001",
  "title": "Security Knowledge",
  "section": "Relevant Technique",
  "source_reference": "knowledge-source-reference",
  "chunk_index": 4,
  "content_hash": "hash-value",
  "ingestion_version": "1.0"
}
```

### Mandatory Provenance Distinction:
$$\text{Incident Evidence } \implies \text{Proves observed telemetry in target environment}$$
$$\text{Knowledge Context } \implies \text{Explains what observed behavior may indicate}$$

---

# 10. Tri-Partitioned Investigation Memory Scoping

```text
                    INVESTIGATION MEMORY
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
      WORKING            HISTORY           EVIDENCE
      CONTEXT            MEMORY            MEMORY
   (Redis/Memory)      (PostgreSQL)      (PostgreSQL)
          │                 │                 │
          ▼                 ▼                 ▼
     AI Planner         Lifecycle &       Verifiable
    Active Gaps         Audit Trail         Proofs
```

- **Working Context**: Active objective, confirmed facts, top evidence gaps, remaining budget.
- **History Memory**: Action logs, previous state versions, rejected hypotheses.
- **Evidence Memory**: Verifiable telemetry items and source references.

---

# 11. End-to-End Data Lineage

```text
RAW TELEMETRY RECORD
   │ (File / Offset)
   ▼
NORMALIZED EVENT (evt_uuid)
   │ (Evaluated by Rule)
   ▼
DETECTION RESULT (det_uuid)
   │ (Severity Scored)
   ▼
ALERT (alt_uuid)
   │ (Triggers)
   ▼
INVESTIGATION (inv_uuid)
   │ (Correlated & Validated)
   ▼
EVIDENCE (evd_uuid)
   │ (Hypothesis Tested)
   ▼
FINDING
   │ (Synthesized)
   ▼
FINAL REPORT
```

---

# 12. Dataset Replay & Reproducibility

The data platform supports deterministic evaluation replay:
1. **Batch Mode**: Ingests preprocessed CSV/JSONL records at line offsets.
2. **Simulated Stream Mode**: Replays records respecting historical inter-event time deltas ($\Delta t$).
3. **Reproducibility Guarantee**: Given identical dataset files and `engine.yaml` configuration, the system produces identical state transitions, evidence graphs, and termination outcomes.

---

# 13. Technology Stack Summary

| Technology | Role |
|---|---|
| **PostgreSQL 15** | System of record, relational investigation truth, audit logs |
| **Redis 7** | Cache, distributed locking, background worker coordination |
| **ChromaDB** | Semantic MITRE ATT&CK vector knowledge retrieval |
| **FastAPI** | REST & WebSocket API gateway |
| **SQLAlchemy 2.0** | Async ORM and database connection pooling |
| **Alembic** | Relational schema migrations |
| **all-MiniLM-L6-v2** | Local air-gapped sentence transformer embeddings |

---

# 14. Final Storage Principle

> **Structured operational truth belongs in the system of record. Semantic knowledge belongs in the retrieval layer. Temporary execution state belongs in the cache. AI-generated interpretation must always remain traceable to the underlying data.**
