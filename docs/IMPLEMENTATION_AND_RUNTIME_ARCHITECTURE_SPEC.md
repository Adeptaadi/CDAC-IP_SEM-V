# Project Sentinel — Implementation & Runtime Architecture Specification (IRAS)

**Document Type:** Technical Implementation and Runtime Architecture Specification  
**Version:** 1.0  
**Status:** Proposed Architecture Upgrade  
**Primary Focus:** Runtime Services, Component Integration, Data Flow, Asynchronous Execution, and Operational Reliability  
**Related Components:** React Frontend, FastAPI Backend, LangGraph Orchestration Runtime, PostgreSQL, Redis, ChromaDB, Ollama

---

# 1. Purpose & Runtime Tier Architecture

This document defines how Project Sentinel's adaptive multi-agent orchestration architecture executes as a resilient, production-ready software system.

```text
┌─────────────────────────────────────────────────────┐
│                  PRESENTATION LAYER                 │
│         React 18 + Vite (Antigravity IDE UI)        │
└──────────────────────────┬──────────────────────────┘
                           │ HTTPS / REST / WebSocket
                           ▼
┌─────────────────────────────────────────────────────┐
│                   APPLICATION LAYER                 │
│                   FastAPI Backend                   │
│                                                     │
│ API Routers │ Auth & RBAC │ Investigation Service   │
└──────────────────────────┬──────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│                 ORCHESTRATION LAYER                 │
│                                                     │
│ State Manager │ LangGraph Runtime │ Action Validator│
└──────────────────────────┬──────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│                  CAPABILITY LAYER                   │
│                                                     │
│ Correlation │ Investigation │ Knowledge │ Validation│
└──────────┬───────────────────┬──────────────────────┘
           │                   │
           ▼                   ▼
┌───────────────────┐  ┌──────────────────────────────┐
│ DATA SERVICES     │  │ AI / KNOWLEDGE SERVICES      │
│                   │  │                              │
│ PostgreSQL 15     │  │ Ollama (Local qwen2.5)       │
│ Redis 7           │  │ ChromaDB (BGE-M3 Embeddings) │
└───────────────────┘  └──────────────────────────────┘
```

### Invariant
> **Infrastructure and capabilities support the investigation. The Orchestration Core controls the investigation workflow.**

---

# 2. Complete Runtime Service Architecture

```text
                        ┌──────────────────┐
                        │     ANALYST      │
                        │ Browser / Client │
                        └────────┬─────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │       FRONTEND         │
                    │      React + Vite      │
                    └───────────┬────────────┘
                                │
                         REST / WebSocket
                                │
                                ▼
                    ┌────────────────────────┐
                    │        BACKEND         │
                    │        FastAPI         │
                    │                        │
                    │ API + Application      │
                    │ Service Layer          │
                    └───────────┬────────────┘
                                │
             ┌──────────────────┼───────────────────┐
             ▼                  ▼                   ▼
      ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
      │ PostgreSQL  │    │    Redis    │    │ Orchestrator│
      │ Persistent  │    │ Queue/Cache │    │  Runtime    │
      │ State       │    └─────────────┘    └──────┬──────┘
      └─────────────┘                              │
                                                   ▼
                                    ┌──────────────────────────┐
                                    │ Capability Registry      │
                                    └──────┬──────┬──────┬─────┘
                                           │      │      │
                                           ▼      ▼      ▼
                                      Correlation RAG Validation
                                           │      │      │
                                           ▼      ▼      ▼
                                      PostgreSQL ChromaDB  LLM
```

---

# 3. Component Responsibilities & Boundaries

## 3.1 Frontend (React 18 + Vite)
- Renders the Antigravity IDE UI (Activity Bar, Central Tabbed Canvas, Copilot Pane with Slash Commands, Bottom Dock).
- Requests investigations, streams execution logs, and presents human-on-the-loop containment approvals.
- **Strict Boundary:** The frontend *never* contains business orchestration logic or dictates agent execution order.

## 3.2 FastAPI Backend Application Layer
- Serves REST routes and WebSocket feeds.
- Validates requests via Pydantic V2 schemas.
- Manages authentication, RBAC, and telemetry ingestion.
- Decoupled from long-running agent loops (delegates to background runtime).

## 3.3 PostgreSQL 15 (System of Record)
- **Authoritative Source of Truth:** Incidents, normalized telemetry, evidence items, hypotheses, contradictions, execution records, audit logs, and versioned state snapshots.
- Employs optimistic locking on state updates:
  ```sql
  UPDATE investigation_state
  SET version = :new_version, snapshot_json = :new_snapshot
  WHERE investigation_id = :id AND version = :expected_version;
  ```

## 3.4 Redis 7 (Operational Coordination)
- Job queue for asynchronous background execution.
- Task locks and distributed synchronization.
- Real-time event pub/sub for WebSocket broadcasts.
- **Rule:** Redis is *never* used as a permanent store for investigation state.

## 3.5 Local LLM Sidecar (Ollama / Qwen2.5)
- Hosted locally for strict air-gapped security.
- Accessed via an isolated `LLMClient` abstraction supporting JSON structured outputs and graceful deterministic fallback.

## 3.6 ChromaDB (Vector Store)
- Stores curated MITRE ATT&CK techniques, CVE knowledge, and playbooks using BGE-M3 embeddings.
- Separated entirely from raw incident telemetry.

---

# 4. Asynchronous Background Execution Flow

Long-running investigations are decoupled from the HTTP request/response cycle:

```text
Analyst Client
      │
      ▼
POST /api/v1/investigations/{id}/start
      │
      ▼
FastAPI Route validates request & marks status="QUEUED"
      │
      ▼
Enqueues job to Redis task queue
      │
      ▼
Returns HTTP 202 Accepted { investigation_id, status: "QUEUED" }
      │
      ▼
Background Orchestration Runtime worker dequeues job
      │
      ▼
LangGraph Execution Cycle executes in background thread
      │
      ├── Streams decision events to Redis PubSub ──► WebSocket ──► UI
      │
      └── Persists immutable state snapshots to PostgreSQL
```

---

# 5. LangGraph Node Definitions

LangGraph manages stateful workflow transitions across 10 architectural nodes:

```text
1. load_state           : Fetches latest snapshot from PostgreSQL
2. check_terminal       : Evaluates max steps, timeouts, and stop rules
3. assess_investigation : Computes tripartite confidence & stance metrics
4. identify_gap         : Prioritizes unresolved information deficits
5. plan_action          : LLM planner generates candidate ActionProposal
6. validate_action      : Deterministic validator applies schema/loop checks
7. execute_capability   : Capability executor runs selected worker in isolation
8. process_result       : Reconciles WorkerResult into evidence ledger
9. persist_state        : Writes atomic state increment (Version n+1) to DB
10. finalize            : Generates forensic report or stages human escalation
```

---

# 6. Failure Recovery & Graceful Degradation Matrix

| Failed Subsystem | Impact | Automated Recovery Protocol |
| :--- | :--- | :--- |
| **Ollama / LLM** | Adaptive reasoning unavailable | Falls back to deterministic rule-based capability selector; logs degradation; continues investigation. |
| **ChromaDB / RAG** | External context unavailable | Bypasses knowledge retrieval; relies on observed empirical telemetry; flags limitation in forensic report. |
| **Worker / Capability** | Specific analysis incomplete | Catches exception in `handle_failure()`; records `FAILED` status; allows bounded retry (max 2) or alternative worker selection. |
| **Redis** | Background queue / cache offline | Degrades to direct in-process FastAPI background tasks (`BackgroundTasks`). |
| **PostgreSQL** | System of record unreachable | **Critical Halt:** Investigation immediately pauses to prevent corrupting state; triggers operator alert. |

---

# 7. Complete System Directory Structure

```text
backend/app/
├── main.py                     # FastAPI application factory & lifespan
├── config.py                   # Pydantic BaseSettings & env configs
├── api/
│   ├── v1/
│   │   ├── alerts.py           # Ingestion & alert endpoints
│   │   ├── investigations.py   # Investigation lifecycle & review
│   │   ├── telemetry.py        # Telemetry upload & scenario replayer
│   │   ├── knowledge.py        # ChromaDB index & query endpoints
│   │   └── ws.py               # WebSocket stream manager
├── core/
│   ├── database.py             # SQLAlchemy engine & sessionmaker
│   ├── redis.py                # Redis client & task queue
│   ├── logging.py              # Structured JSON logging
│   └── exceptions.py           # Custom domain exceptions
├── orchestration/
│   ├── graph.py                # LangGraph 10-node state machine
│   ├── runtime.py              # Background orchestration runner
│   ├── planner.py              # Adaptive LLM planner
│   ├── state_interpreter.py    # Context compressor & summarizer
│   ├── gap_analyzer.py         # Evidence gap categorizer
│   ├── action_validator.py     # Deterministic safety & loop guardrails
│   ├── executor.py             # Isolated worker execution runner
│   └── termination.py          # Multi-condition stop engine
├── investigation/
│   ├── state.py                # Root InvestigationState model
│   ├── state_manager.py        # Atomic merge & versioning service
│   ├── evidence.py             # Evidence items & provenance
│   ├── hypotheses.py           # Hypotheses & contradiction ledger
│   └── checkpoint.py           # Serialization & state restore
├── capabilities/
│   ├── base.py                 # BaseCapability abstract contract
│   ├── registry.py             # Central capability registry
│   ├── correlation/            # Correlation worker
│   ├── investigation/          # Hypothesis evaluation worker
│   ├── knowledge/              # RAG retrieval worker
│   ├── validation/             # Evidence sufficiency validator
│   └── reporting/              # Twin-tier report generator
├── infrastructure/
│   ├── llm/
│   │   └── client.py           # Ollama client with fallback
│   ├── vector_store/
│   │   └── chroma.py           # ChromaDB client & BGE-M3 embeddings
│   └── repositories/
│       ├── investigation_repo.py
│       └── event_repo.py
└── evaluation/
    ├── runner.py               # Standalone benchmark runner
    ├── scenarios.py            # 5-Scenario CSE-CIC-IDS2018 definitions
    ├── baselines.py            # Fixed sequential baseline runner
    └── metrics.py              # Accuracy, coverage, ECE, gap resolution
```

---

# 8. Phased Runtime Implementation Roadmap

```text
PHASE 1: Core Runtime Infrastructure (PostgreSQL + FastAPI + Docker Compose)
  │
  ▼
PHASE 2: Domain Models & Telemetry Normalization
  │
  ▼
PHASE 3: Investigation State Engine & Atomic PostgreSQL Persistence
  │
  ▼
PHASE 4: Base Capability Contracts & Central Registry
  │
  ▼
PHASE 5: Correlation Capability
  │
  ▼
PHASE 6: LangGraph 10-Node Orchestration Runtime
  │
  ▼
PHASE 7: Adaptive LLM Planner + Action Validator + Loop Prevention
  │
  ▼
PHASE 8: ChromaDB Vector Store & Knowledge RAG Integration
  │
  ▼
PHASE 9: Evidence Validation Capability & Twin-Tier Reporting
  │
  ▼
PHASE 10: Evaluation Harness & Fixed vs. Adaptive Baseline Benchmarking
  │
  ▼
PHASE 11: Antigravity IDE Frontend Integration & End-to-End Demonstration
```
