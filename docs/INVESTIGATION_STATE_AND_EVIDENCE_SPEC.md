# Project Sentinel — Investigation State & Evidence Specification (ISES)

**Document Type:** Detailed System and Data Design  
**Version:** 1.0  
**Status:** Proposed Architecture Upgrade  
**Primary Focus:** Investigation State, Evidence, Hypotheses, Confidence, and Memory  
**Related Components:** Orchestration Core, Specialized Capabilities, PostgreSQL, RAG, Observability

---

# 1. Purpose & Information Model

This document defines how Project Sentinel represents, stores, updates, and reasons about an active cybersecurity investigation.

The **Investigation State** is the central shared information model of the platform. All agents, planners, and capabilities interact through this structured state rather than conversational chat histories:

```text
Security Signal
      │
      ▼
┌──────────────────────┐
│ INVESTIGATION STATE  │
│                      │
│ Events               │
│ Entities             │
│ Evidence             │
│ Hypotheses           │
│ Uncertainty          │
│ Decisions            │
│ Execution History    │
└──────────┬───────────┘
           │
     ┌─────┴─────┐
     ▼           ▼
Orchestrator   Capabilities
     │           │
     └─────┬─────┘
           ▼
    Updated State
```

The core question the state answers at any time:
> **What do we know, how do we know it, what remains uncertain, and what should happen next?**

---

# 2. Design Principles

1. **Explicit Structured State:** Crucial facts live in typed schemas, not in unstructured conversational context.
2. **End-to-End Evidence Traceability:** Every finding references its source telemetry, worker, collection timestamp, and integrity hashes.
3. **Strict Separation of Facts and Context:**
   $$\text{Observed Events} \neq \text{Derived Findings} \neq \text{Hypotheses} \neq \text{Retrieved Knowledge} \neq \text{Final Conclusions}$$
4. **Controlled Updates:** Workers never overwrite global state; they submit `StateUpdate` deltas validated by the State Manager.
5. **Durable Persistence:** Investigations survive process restarts and worker crashes via PostgreSQL checkpoints.
6. **Immutable State Versioning:** Every state mutation produces an incremented version ($V_1 \to V_2 \to \dots \to V_n$).
7. **Tri-Tier Memory Scoping:**
   - **Canonical Memory:** Complete, durable PostgreSQL database record.
   - **Operational Memory:** Active runtime parameters, task bus, and locks.
   - **Reasoning Memory:** Compact, token-efficient state summary sent to the LLM Planner.

---

# 3. Canonical Investigation State Schema

```text
InvestigationState
├── Identity (investigation_id, incident_id, status, created_at, updated_at, current_state_version)
├── Trigger Context (trigger_type, source, alert_reference, initial_confidence, initial_events)
├── Event Context (events: List[SecurityEvent], raw_references, ingestion_provenance)
├── Entity Context (entities: Dict[str, Entity], canonical_names, aliases, resolutions)
├── Evidence Repository (evidence: List[EvidenceItem] - observed, derived, analytical)
├── Hypothesis Repository (hypotheses: List[Hypothesis], stances, active_status)
├── Evidence Gaps (gaps: List[EvidenceGap], priority, candidate_capabilities)
├── Execution History (executions: List[ExecutionRecord], worker_latencies, failures)
├── Confidence & Sufficiency (detection_confidence, evidence_sufficiency, investigation_confidence)
├── Control Boundaries (max_steps, current_steps, max_retries, deadline, budget)
├── Decision History (decisions: List[DecisionRecord], rationale, validation_verdict)
└── State Metadata (provenance, checksums)
```

---

# 4. Evidence Classification & Data Contracts

## 4.1 Five Distinct Evidence Classes
| Class | Origin | Role | Example |
| :--- | :--- | :--- | :--- |
| **Observed Evidence** | Direct normalized telemetry | Hard empirical facts | 14 failed logins followed by 1 success |
| **Derived Evidence** | Deterministic calculations | Mathematical / temporal aggregations | All 14 failures occurred within a 7-minute window |
| **Analytical Findings** | Specialized worker outputs | Inferred domain correlations | Correlation worker identified outbound TCP to C2 IP |
| **Retrieved Context** | RAG knowledge base | External background framing | ATT&CK T1059.001 procedure description |
| **Analyst Evidence** | Human-in-the-loop intervention | Authoritative human ground-truth | SOC Analyst confirmed host is an off-network workstation |

## 4.2 `EvidenceItem` Schema
```python
class EvidenceItem(BaseModel):
    evidence_id: UUID
    evidence_type: Literal["observed", "derived", "analytical", "retrieved_context", "analyst"]
    statement: str
    source_type: str
    source_reference: str
    related_entities: Dict[str, List[str]] # {"hosts": [...], "ips": [...]}
    related_event_ids: List[UUID]
    provenance: Dict[str, Any]
    confidence: float
    collected_at: datetime
    limitations: Optional[str] = None # Explicitly documents analytical caveats
```

---

# 5. Hypothesis Lifecycle & Contradiction Ledger

## 5.1 Hypothesis Lifecycle State Machine
```text
PROPOSED ──► ACTIVE ──┬──► SUPPORTED ───┐
                      │                 ├──► REASSESSED ──┬──► VALIDATED
                      └──► CONTRADICTED ┘                 └──► REJECTED
```

## 5.2 Contradiction Management (`ContradictionItem`)
The system strictly forbids discarding conflicting observations. Contradictions persist as first-class objects until resolved:
```python
class ContradictionItem(BaseModel):
    contradiction_id: UUID
    related_hypothesis_id: UUID
    evidence_reference_ids: List[UUID]
    description: str
    severity: Literal["low", "medium", "high", "critical"]
    resolution_status: Literal["unresolved", "investigating", "resolved", "accepted_ambiguity"]
    resolution_notes: Optional[str] = None
```

---

# 6. Tripartite Confidence & Sufficiency Model

```text
┌────────────────────────────────────────────────────────────────────────┐
│ 1. Detection Confidence (Signal Level)                                 │
│    Model probability from ML flow classifiers or Sigma rule weights.   │
├────────────────────────────────────────────────────────────────────────┤
│ 2. Evidence Sufficiency (Investigation Completeness)                   │
│    Ratio of required hypothesis criteria verified by concrete facts.   │
│    Sufficiency = (Observed Criteria - Unresolved Contradictions) / Req │
├────────────────────────────────────────────────────────────────────────┤
│ 3. Investigation Confidence (Overall Posterior)                        │
│    Bayesian posterior: F(Evidence Quality, Diversity, Stance, Checks). │
└────────────────────────────────────────────────────────────────────────┘
```
**Rule:** An investigation **cannot finalize** merely because numerical detection confidence is high; evidence sufficiency must independently pass thresholds ($\ge 0.80$).

---

# 7. Controlled State Update & Merge Protocol

Workers return lightweight `StateUpdate` payloads. The State Manager executes atomic merges:

```text
Worker Output ──► StateUpdate Object
                         │
                         ▼
               Schema & Type Validation
                         │
                         ▼
             Provenance & Reference Checks
                         │
                         ▼
             Contradiction & Conflict Detection
                         │
                         ▼
                Atomic DB Transaction
                         │
                         ▼
            New State Version (V_n+1 Created)
```

### Mandatory Merge Rules
1. **Never Overwrite Evidence:** Existing evidence cannot be silently modified or deleted.
2. **Preserve Contradictions:** Conflicting statements coexist explicitly.
3. **Reference Integrity:** All `related_event_ids` and `related_entities` must point to valid identifiers.
4. **Deduplication:** Repeated events are linked into the provenance chain rather than replicated.

---

# 8. PostgreSQL Schema Mapping

```sql
-- Core Investigation Entity
CREATE TABLE investigations (
    investigation_id UUID PRIMARY KEY,
    incident_id VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL,
    current_version INT NOT NULL DEFAULT 1,
    detection_confidence DOUBLE PRECISION NOT NULL,
    evidence_sufficiency DOUBLE PRECISION NOT NULL,
    investigation_confidence DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Immutable State Snapshots / Versions
CREATE TABLE investigation_versions (
    version_id UUID PRIMARY KEY,
    investigation_id UUID REFERENCES investigations(investigation_id),
    version_number INT NOT NULL,
    snapshot_json JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Normalised Security Events
CREATE TABLE security_events (
    event_id UUID PRIMARY KEY,
    investigation_id UUID REFERENCES investigations(investigation_id),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    source VARCHAR(64) NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    host VARCHAR(128),
    user_name VARCHAR(128),
    src_ip INET,
    dest_ip INET,
    process_name VARCHAR(256),
    raw_payload JSONB
);

-- Traceable Evidence Ledger
CREATE TABLE evidence_items (
    evidence_id UUID PRIMARY KEY,
    investigation_id UUID REFERENCES investigations(investigation_id),
    evidence_type VARCHAR(32) NOT NULL,
    statement TEXT NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    limitations TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Hypotheses and Contradictions
CREATE TABLE hypotheses (
    hypothesis_id UUID PRIMARY KEY,
    investigation_id UUID REFERENCES investigations(investigation_id),
    statement TEXT NOT NULL,
    status VARCHAR(32) NOT NULL,
    confidence DOUBLE PRECISION NOT NULL
);

CREATE TABLE contradictions (
    contradiction_id UUID PRIMARY KEY,
    investigation_id UUID REFERENCES investigations(investigation_id),
    hypothesis_id UUID REFERENCES hypotheses(hypothesis_id),
    description TEXT NOT NULL,
    severity VARCHAR(16) NOT NULL,
    resolution_status VARCHAR(32) NOT NULL
);
```

---

# 9. Investigation State Quality Metrics

| Metric | Target | Evaluation Meaning |
| :--- | :--- | :--- |
| **Provenance Completeness** | $100\%$ | Every evidence item possesses traceable source and timestamp |
| **Reference Integrity** | $100\%$ | Zero orphaned event or entity identifiers in findings |
| **Contradiction Visibility** | $100\%$ | Conflicting evidence triggers an explicit ledger record |
| **State Compression Ratio** | $> 80\%$ | Reduction from raw canonical bytes to LLM reasoning summary |
