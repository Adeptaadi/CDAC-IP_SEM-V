# Project Sentinel — Detailed Data Architecture & Investigation State Specification (DAISS)

**Document Type:** Data and State Architecture Specification  
**Version:** 1.0  
**Status:** Proposed Architecture Upgrade  
**Primary Focus:** Data models, telemetry normalization, investigation state, evidence lineage, persistence, caching, vector knowledge storage, and data lifecycle  
**Related Components:** Ingestion Engine, Normalization Pipeline, State Manager, PostgreSQL, ChromaDB, Redis, Action Validator

---

# 1. Purpose

Project Sentinel depends on a controlled flow of information. The agent orchestration layer can only make reliable decisions when the information it receives is:
- Structured
- Validated
- Traceable
- Versioned
- Consistently represented

This document defines the architecture through which data moves from raw telemetry into an evidence-based investigation.

The fundamental data flow is:

```text
RAW DATA
   │
   ▼
INGESTION
   │
   ▼
NORMALIZATION
   │
   ▼
DETECTION / ALERT
   │
   ▼
INVESTIGATION STATE
   │
   ├──────────────┐
   ▼              ▼
EVIDENCE      KNOWLEDGE CONTEXT
   │              │
   └──────┬───────┘
          ▼
     ORCHESTRATION
          │
          ▼
   FINAL OUTCOME
```

---

# 2. Data Architecture Principles

## 2.1 Canonical Representation
Raw datasets may contain different field names and formats. The rest of the application should not depend directly on those formats:

```text
Dataset A ──┐
            │
Dataset B ──┼──► NORMALIZATION ───► CANONICAL EVENT
            │
Dataset C ──┘
```

The canonical event model (`NormalizedEvent`) becomes the common language of Project Sentinel.

## 2.2 Separation of Data Types
Different information should not be stored as if it were the same thing:
- **Telemetry**: What was observed?
- **Evidence**: What supports an investigation finding?
- **Knowledge**: What provides external domain context?
- **Decisions**: Why did the system take an action?

These categories have different lifecycles and storage requirements.

## 2.3 Traceability
Every claim must remain linked through an unbroken chain of custody:

```text
FINAL CLAIM ──► VALIDATED FINDING ──► EVIDENCE ITEM ──► NORMALIZED EVENT ──► SOURCE RECORD
```

---

# 3. Data Layers

| Layer | Purpose | Primary Store |
|---|---|---|
| **Raw Data** | Original dataset records (PCAP, CSV, Sysmon) | File System / Cold Storage |
| **Normalized Data** | Canonical telemetry events | PostgreSQL (`events`) |
| **Investigation Data** | Alerts, evidence, hypotheses, decisions | PostgreSQL (Relational Truth) |
| **Operational Data** | Cache, task queues, temporary lock data | Redis 7 |
| **Knowledge Data** | MITRE ATT&CK chunks & semantic embeddings | ChromaDB |

---

# 4. Raw Telemetry Layer

Raw telemetry is preserved unchanged to maintain forensic integrity:

```text
RAW RECORD ──┬──► Preserved Reference
             │
             ▼
   NORMALIZATION PROCESS
             │
             ▼
      NORMALIZED EVENT
```

The normalized event stores a strict pointer back to the raw record.

---

# 5. NormalizedEvent Model

`NormalizedEvent` is the canonical schema:

```text
NormalizedEvent
│
├── event_id
├── source_id
├── source_type
│
├── timestamp
├── ingestion_timestamp
│
├── event_type
├── category
│
├── actor
├── target
│
├── host
├── network
│
├── process
├── attributes
│
├── labels
└── source_reference
```

Missing fields remain explicitly `None` rather than being fabricated.

---

# 6. Event Identity & Lineage

Every normalized event has a deterministic UUID (`event_id`) and a `source_reference`:

```text
source_reference
│
├── dataset
├── file
├── record_identifier
└── original_location
```

---

# 7. Dual Timestamp Model

```text
occurred_at   (Event Time: when activity took place in the telemetry)
ingested_at   (Ingestion Time: when Sentinel received or processed the event)
```

This prevents temporal distortion during historical benchmark replays.

---

# 8. Event Classification

Standardized event categories:
- `AUTHENTICATION`
- `PROCESS`
- `NETWORK`
- `FILE`
- `SYSTEM`
- `OTHER`

---

# 9. Entity Representation

Entities connect events across dimensional pivots:

```text
Entity
│
├── entity_id
├── entity_type (User, Host, IP, Process, File, Session)
├── value
└── attributes
```

---

# 10. Extensible Attributes

Non-universal or source-specific telemetry is isolated in an `attributes` JSON dictionary to prevent schema bloat while supporting multi-source telemetry.

---

# 11. Normalization Pipeline

```text
RAW DATA ──► LOAD ──► PARSE ──► MAP SOURCE FIELDS ──► VALIDATE ──► GENERATE NORMALIZED EVENT ──► STORE
```

Each stage has isolated responsibility and error handling.

---

# 12. Normalization Validation

Records failing schema, timestamp, or identifier validation trigger a validation error without halting processing of remaining batch records:

```text
INVALID RECORD ──► VALIDATION ERROR ──► RECORD IN ERROR LOG ──► CONTINUE PROCESSING OTHER RECORDS
```

---

# 13. Alert Model

An alert represents an event or condition warranting investigation:

```text
Alert
│
├── alert_id
├── created_at
│
├── severity (CRITICAL, HIGH, MEDIUM, LOW, INFORMATIONAL)
├── status
│
├── trigger
├── related_event_ids
│
├── initial_summary
└── metadata
```

An alert triggers an investigation; it is not a final finding.

---

# 14. Alert Lifecycle

```text
CREATED ──► QUEUED ──► INVESTIGATING ──┬──► ESCALATED
                                       ├──► RESOLVED
                                       └──► INCONCLUSIVE
```

---

# 15. Investigation Model

The top-level container for all investigation data:

```text
Investigation
│
├── investigation_id
├── alert_id
│
├── status (CREATED, QUEUED, RUNNING, WAITING_REVIEW, FINALIZED, FAILED)
├── created_at
├── updated_at
│
├── current_state_version
├── confidence
└── final_outcome
```

---

# 16. Investigation State

The operational state seen by the Planner:

```text
InvestigationState
│
├── identity
├── status
│
├── alert_context
│
├── evidence
├── hypotheses
├── evidence_gaps
│
├── action_history
│
├── confidence
├── budget
│
└── metadata
```

---

# 17. State as the Source of Operational Truth

Capabilities do not own state. The Planner does not own state. **The State Manager is the single authority of investigation state.**

```text
PLANNER ──► READ STATE COPY ──► DECISION ──► RESULT ──► VALIDATION ──► STATE UPDATE ──► NEW STATE VERSION
```

---

# 18. State Versioning & Optimistic Concurrency

Every update increments `state_version` (Version 1 $\to$ Version 2 $\to \dots$).

```text
Current Version: 5
Capability Result expects: 5
        │
   ┌────┴────┐
   ▼         ▼
MATCH     MISMATCH
   │         │
UPDATE    REJECT (OptimisticLockError)
```

---

# 19. Evidence Model & Taxonomy

Structured empirical artifact:

```text
Evidence
│
├── evidence_id
├── investigation_id
│
├── evidence_type (TELEMETRY, CORRELATION, KNOWLEDGE_CONTEXT, VALIDATION, ANALYST)
├── description
│
├── source_event_ids
├── source_capability
│
├── collected_at
├── confidence
└── metadata
```

$$\text{Knowledge Context (RAG)} \neq \text{Observed Telemetry}$$

---

# 20. Evidence Lineage

```text
Raw Event ──► Normalized Event ──► Correlation Finding ──► Validated Evidence ──► Investigation Claim
```

Derived artifacts reference UUIDs of ancestral events to minimize data redundancy.

---

# 21. Hypothesis Model

```text
Hypothesis
│
├── hypothesis_id
├── description
│
├── status (ACTIVE, SUPPORTED, REJECTED, UNRESOLVED)
├── supporting_evidence
├── conflicting_evidence
│
├── confidence
└── last_updated
```

---

# 22. Evidence Gap Model

```text
EvidenceGap
│
├── gap_id
├── description
├── priority (HIGH, MEDIUM, LOW)
│
├── related_hypothesis
├── suggested_capabilities
│
├── status (OPEN, IN_PROGRESS, RESOLVED, ABANDONED)
└── created_at
```

---

# 23. Action & Decision History

- **`ActionRecord`**: Capability invoked, parameters passed, execution timing, status, failure reasons.
- **`DecisionRecord`**: Planner reasoning trace, state version evaluated, gaps identified, candidate action scores, and rationale.

---

# 24. PostgreSQL Relational Persistence

```text
POSTGRESQL
│
├── events
├── alerts
├── investigations
│
├── evidence
├── hypotheses
├── evidence_gaps
│
├── actions
├── decisions
│
└── audit_logs
```

---

# 25. ChromaDB Knowledge Architecture

```text
Knowledge Documents (MITRE ATT&CK / Docs)
        │
        ▼
Document Processing (Chunking + Metadata)
        │
        ▼
Embedding Generation (Local all-MiniLM-L6-v2)
        │
        ▼
ChromaDB Vector Store
```

ChromaDB answers semantic context questions; it is never the authoritative investigation truth store.

---

# 26. Redis Operational Architecture

Redis is strictly scoped for ephemeral data:
- Worker task queue coordination
- Rate limiting and distributed locks
- Short-lived capability query cache

---

# 27. Five Fundamental Data Integrity Rules

1. **Rule 1**: Evidence must reference a valid source event or declare itself as derived.
2. **Rule 2**: Every state mutation must match the expected current `state_version`.
3. **Rule 3**: Every decision record must cite the exact `state_version` on which it evaluated.
4. **Rule 4**: Every final conclusion must trace back to concrete empirical evidence.
5. **Rule 5**: External knowledge context must never be stored as or equated to observed telemetry.

---

# 28. Data Architecture Responsibility Matrix

| Component | Reads | Writes | Authoritative For |
|---|---|---|---|
| **Ingestion** | Raw data | Normalized events | Source transformation |
| **Detection** | Events | Alerts | Alert generation |
| **Planner** | State | Decisions | Next-action reasoning |
| **Capabilities** | State context | Results | Specialized analytical tasks |
| **State Manager** | Results | Investigation state | Current investigation truth |
| **PostgreSQL** | Structured data | Persistent records | Durable investigation records |
| **ChromaDB** | Knowledge documents | Vector index | Semantic retrieval |
| **Redis** | Temporary data | Cache / task state | Operational queue data |

---

# 29. Recommended Implementation Sequence

```text
1. NormalizedEvent
        ↓
2. Dataset Adapter
        ↓
3. Event Validation
        ↓
4. Alert Model
        ↓
5. Investigation Model
        ↓
6. Evidence Model
        ↓
7. State Manager
        ↓
8. Action / Decision History
        ↓
9. PostgreSQL Persistence
        ↓
10. Knowledge Index (ChromaDB)
```

---

# 30. Central Architectural Principle

> **The Planner should reason over a structured representation of the investigation, not over an uncontrolled collection of raw logs and chat messages.**
