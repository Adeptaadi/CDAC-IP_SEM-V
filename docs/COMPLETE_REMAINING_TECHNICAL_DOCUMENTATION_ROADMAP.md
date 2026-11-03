# Project Sentinel — Complete Remaining Technical Documentation Roadmap

**Document Type:** Architecture and Implementation Documentation Plan  
**Version:** 1.0  
**Status:** Proposed Master Documentation Plan  
**Purpose:** Define all remaining technical documentation required to make Project Sentinel architecturally complete, implementation-ready, testable, and academically demonstrable.  
**Related Components:** All Subsystems (Data, Detection, Correlation, Capabilities, AI Planner, UI, Evaluation, Operations)

---

# 1. Document Purpose

Project Sentinel is being designed as an **AI-assisted cybersecurity investigation platform centered on intelligent agent orchestration**.

The architecture already establishes the major foundations:

```text
                    PROJECT SENTINEL
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
     DATA LAYER       AI INTELLIGENCE    ORCHESTRATION
          │                │                │
          └────────────────┼────────────────┘
                           │
                           ▼
                    INVESTIGATION
```

The remaining documentation defines how these architectural layers operate as a complete system, answering:
- What does the system do?
- Who uses it?
- What data enters the system?
- How is the data processed?
- How is an attack detected?
- How does an investigation begin?
- How does the AI Planner make decisions?
- What tools can the Planner use?
- How is evidence correlated?
- How is confidence calculated?
- When does the investigation stop?
- What happens when a component fails?
- How does a human analyst interact with the system?
- How is the system evaluated?
- How can the project prove that its architecture is better than a baseline?

---

# 2. Complete Documentation Architecture

```text
PROJECT DOCUMENTATION
│
├── 1. PRODUCT & REQUIREMENTS
│   ├── PRD
│   └── System Scope
│
├── 2. CORE ARCHITECTURE
│   ├── TDD
│   ├── System Architecture
│   ├── Agent Orchestration
│   ├── Data Architecture
│   └── AI / RAG Strategy
│
├── 3. INVESTIGATION INTELLIGENCE
│   ├── Detection Engine
│   ├── Correlation Engine
│   ├── Capability Implementation
│   └── Investigation Lifecycle
│
├── 4. DATA & EVALUATION
│   ├── Dataset Specification
│   ├── Attack Scenarios
│   └── Evaluation & Benchmarking
│
├── 5. SYSTEM IMPLEMENTATION
│   ├── Backend & API
│   ├── Frontend & Analyst Experience
│   ├── Security & Reliability
│   └── Deployment
│
└── 6. QUALITY & OPERATIONS
    ├── Testing Strategy
    └── Observability & Audit
```

---

# 3. Document 1 — Detection, Correlation & Investigation Engine Specification

### Priority: CRITICAL (Next Immediate Specification)

The agent orchestration architecture defines **how the system decides what to do next**. This document defines **what information the agents investigate and how evidence is generated**.

```text
RAW TELEMETRY ──► NORMALIZATION ──► DETECTION ──► ALERT ──► INITIAL INVESTIGATION ──► CORRELATION ──► EVIDENCE ──► AI ORCHESTRATION ──► FINAL OUTCOME
```

### Key Requirements:
- **Detection Architecture**: Deterministic detection rules, thresholds, event sequence detection, and false-positive suppression. LLMs must *never* perform basic deterministic detection.
- **Alert Model**: Alert UUID, rule ID, triggering events, severity, timestamp, status, and queue lifecycle.
- **Entity Extraction**: Canonical pivot entities (User, Host, IP, Process, File, Session) for cross-event linkage.
- **Correlation Engine**: Temporal correlation, entity clustering, network flow linkage, and process tree reconstruction.
- **Timeline Construction**: Chronological ordering, event grouping, deduplication, and windowing.
- **Evidence Scoring**: Deterministic multi-factor scoring (Source Reliability, Relevance, Corroboration, Recency).
- **Investigation Lifecycle & Termination**: Explicit state transitions (`CREATED` $\to$ `INITIALIZED` $\to$ `INVESTIGATING` $\to$ `RESOLVED` / `ESCALATED` / `INCONCLUSIVE`).

---

# 4. Document 2 — Capability & Tool Implementation Specification

### Priority: CRITICAL

The Planner orchestrates **capabilities**, not uncontrolled autonomous agents. Each capability exposes a strict schema contract.

```text
                    AI PLANNER
                        │
                        ▼
                CAPABILITY REGISTRY
                        │
       ┌────────────────┼─────────────────┐
       ▼                ▼                 ▼
 EVENT QUERY       CORRELATION        KNOWLEDGE
       │                │                 │
       └────────────────┼─────────────────┘
                        ▼
                  VALIDATION
```

### Required Capabilities:
1. **Event Query Capability**: Query normalized telemetry with filters, time ranges, and pagination.
2. **Correlation Capability**: Multi-dimensional entity and temporal relationship extraction.
3. **Timeline Capability**: Ordered timeline generation and event aggregation.
4. **Knowledge Retrieval Capability**: Semantic RAG search over MITRE ATT&CK chunks.
5. **Evidence Validation Capability**: Verifies claims against empirical event evidence.
6. **Reporting Capability**: Generates structured reports separating facts, hypotheses, and uncertainty.

---

# 5. Document 3 — Dataset & Attack Scenario Specification

### Priority: CRITICAL

Establishes the experimental foundation grounded in CSE-CIC-IDS2018:
- Source schema mapping to `NormalizedEvent`.
- 3 to 5 realistic attack scenarios (Infiltration, Brute Force, Web SQLi, Botnet C2, DoS).
- Exact file filters, record offsets, replay sequences, and ground-truth fact manifests.

---

# 6. Document 4 — Evaluation & Benchmarking Specification

### Priority: CRITICAL

Measures the value proposition of the architecture against a fixed sequential baseline:
- **Detection Metrics**: Precision, Recall, F1 Score.
- **Orchestration Metrics**: Valid Action Rate, Action Utility Rate, Redundant Action Rate, Step Efficiency.
- **Grounding Metrics**: $\text{Grounded Claim Rate} = \frac{\text{Supported Claims}}{\text{Total Claims}}$.
- **RAG Metrics**: Precision@K, Context Coverage.
- **Runtime Performance**: P95 latency, capability execution time, LLM inference latency.

---

# 7. Document 5 — Security, Reliability & Failure Recovery Specification

### Priority: CRITICAL

Operational resiliency across failure domains:
- LLM timeouts, backoff retries, and deterministic fallback planning.
- Concurrency conflicts and optimistic state locking (`OptimisticLockError`).
- Bounded autonomy, analyst role-based access control (Admin vs. SOC Analyst), and cryptographic audit ledgers.

---

# 8. Document 6 — Backend & API Service Specification

### Priority: HIGH

FastAPI REST & WebSocket interface contracts:
- Alert endpoints (`/alerts`).
- Investigation lifecycle endpoints (`/investigations`).
- Evidence querying (`/investigations/{id}/evidence`).
- Human analyst oversight & review (`/investigations/{id}/review`, `/escalate`).

---

# 9. Document 7 — Frontend & Analyst Interaction Specification

### Priority: HIGH

Antigravity IDE interface design for SOC analysts:
- Investigation Dashboard, Timeline & Graph views, Hypothesis Matrix.
- Action decision inspector (displaying Gaps $\to$ Action $\to$ Rationale).
- Human-in-the-Loop review controls (Approve, Override, Escalate).

---

# 10. Document 8 — Testing & Quality Assurance Specification

### Priority: HIGH

Multi-tiered testing framework:
- Unit tests (normalization, detection rules, state transitions, logit math).
- Capability contract verification tests.
- Orchestration policy & budget boundary tests.
- Scenario-based end-to-end integration tests.

---

# 11. Document 9 — Deployment & Infrastructure Specification

### Priority: HIGH

Air-gapped and containerized deployment blueprint:
- Docker Compose topology (Backend, Frontend, PostgreSQL 15, Redis 7, ChromaDB, local Ollama).
- Health checks, volume mounts, startup dependency graphs, and environment configurations.

---

# 12. Document 10 — Observability & Audit Specification

### Priority: VALUABLE

End-to-end investigation trace observability:
- Traceable execution logs for every planner cycle.
- Auditable cryptographic hash chaining for evidence and decisions.
- Real-time latency and error tracking metrics.

---

# 13. Recommended Documentation & Delivery Sequence

```text
PHASE 1 — CORE INVESTIGATION INTELLIGENCE
1. Detection, Correlation & Investigation Engine Specification
2. Capability & Tool Implementation Specification
3. Dataset & Attack Scenario Specification

PHASE 2 — PROVING THE ARCHITECTURE
4. Evaluation & Benchmarking Specification
5. Security, Reliability & Failure Recovery Specification

PHASE 3 — SYSTEM IMPLEMENTATION
6. Backend & API Service Specification
7. Frontend & Analyst Interaction Specification
8. Testing & Quality Assurance Specification

PHASE 4 — DEPLOYMENT & OPERATIONS
9. Deployment & Infrastructure Specification
10. Observability & Audit Specification
```

---

# 14. Master Operational Relationship

```text
                         DATASET
                            │
                            ▼
                       INGESTION
                            │
                            ▼
                      NORMALIZATION
                            │
                            ▼
                        DETECTION
                            │
                            ▼
                          ALERT
                            │
                            ▼
                    INVESTIGATION STATE
                            │
                            ▼
                      AI PLANNER
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
         EVENT QUERY    CORRELATION      RAG
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                     VALIDATED EVIDENCE
                            │
                            ▼
                    UPDATED STATE
                            │
                      ┌─────┴─────┐
                      ▼           ▼
                  REPLAN       TERMINATE
                      │           │
                      └─────┬─────┘
                            ▼
                      FINAL RESULT
                            │
                            ▼
                      ANALYST REVIEW
```

---

# 15. Next Immediate Priority

The immediate next document to ingest and formalize:

> ### **Detailed Detection, Correlation & Investigation Engine Specification**

This provides the concrete operational bridge connecting raw telemetry data to alerts, correlated entities, and empirical evidence evaluated by the AI Orchestration Core.
