# Project Sentinel — Agent-Centric Architecture Implementation Plan

## 1. Implementation Objective

### Primary Goal
Build a **reliable, adaptive, evidence-driven orchestration engine** capable of dynamically coordinating specialized cybersecurity capabilities during an investigation.

The core execution model:

```text
Security Signal
      │
      ▼
Investigation State
      │
      ▼
┌─────────────────────────────┐
│   ORCHESTRATOR / PLANNER    │
│                             │
│  1. Understand state        │
│  2. Identify knowledge gaps │
│  3. Select next capability  │
│  4. Validate execution      │
│  5. Re-plan or terminate    │
└──────────────┬──────────────┘
               │
               ▼
       Execute Capability
               │
               ▼
       Structured Result
               │
               ▼
       Update Evidence
               │
               └──────────► Re-plan
```

### Core Implementation Principle
> **No major subsystem should be added unless it improves the quality, reliability, or efficiency of orchestration decisions.**

---

## 2. Implementation Strategy

The system is built in **progressive layers**, beginning with a deterministic orchestration baseline:

```text
PHASE 1: Foundation and Contracts
  │
  ▼
PHASE 2: Investigation State Engine
  │
  ▼
PHASE 3: Baseline Orchestrator (Deterministic / Rule-based)
  │
  ▼
PHASE 4: Specialized Capabilities (Correlation, Investigation, RAG, Validation, Reporting)
  │
  ▼
PHASE 5: Adaptive LLM Planning (Gap Analysis, Dynamic Routing)
  │
  ▼
PHASE 6: Evidence Validation and Recovery (Action Validator, Budgets, Guardrails)
  │
  ▼
PHASE 7: Advanced Decision Intelligence (Hybrid ML Detection, Temporal Graph, Advanced RAG)
  │
  ▼
PHASE 8: Evaluation and Benchmarking (Baseline vs. Adaptive Experimentation)
```

**Rule:** Do not start by connecting multiple free-form AI agents. First, establish the state model, capability contracts, execution controls, and a measurable baseline.

---

## 3. Phase 1 — Orchestration Foundation & Contracts

### 3.1 Investigation State Schema
The `InvestigationState` is the **central, versioned source of context**:

```text
InvestigationState
│
├── investigation_id: UUID
├── status: str
├── trigger: SecuritySignal
│
├── events: List[TelemetryEvent]
├── entities: Dict[str, List[str]]
├── timeline: List[TimelineEvent]
│
├── evidence: List[EvidenceItem]
├── hypotheses: List[HypothesisItem]
├── contradictions: List[ContradictionItem]
│
├── completed_tasks: List[TaskRecord]
├── pending_tasks: List[TaskRecord]
├── failed_tasks: List[TaskRecord]
│
├── detection_confidence: float
├── evidence_sufficiency: float
├── investigation_confidence: float
│
├── execution_budget: BudgetState
├── retry_state: Dict[str, int]
│
└── audit_log: List[AuditEntry]
```

### 3.2 Capability Contracts
Every worker/specialist implements a standardized interface:

```text
Capability
│
├── metadata (name, description, supported_tasks, cost_profile)
├── input_schema (Pydantic contract)
├── execute(input) -> WorkerResult
└── output_schema (Pydantic contract)
```

#### Standard WorkerResult Contract
```text
WorkerResult
│
├── status: "success" | "failure" | "needs_more_info"
├── findings: List[Finding]
├── evidence_ids: List[str]
├── confidence: float
├── uncertainty: float
├── contradictions: List[str]
├── limitations: List[str]
├── new_information: bool
└── execution_metadata: Dict[str, Any]
```

**Critical Invariant:** Workers must **never directly modify the overall investigation conclusion**. They return factual evidence and findings to the orchestrator, which reconciles the state.

---

## 4. Phase 2 — Investigation State Engine

```text
                    ┌───────────────────┐
                    │ InvestigationState│
                    └─────────┬─────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
       Evidence Manager  Hypothesis Manager  Task Manager
              │               │               │
              └───────────────┼───────────────┘
                              ▼
                       State Checkpoint
```

### Module Layout
```text
backend/app/investigation/
├── state.py         # Root InvestigationState model & versioning
├── evidence.py      # Evidence Manager (corroboration, stance)
├── hypotheses.py    # Hypothesis lifecycle & contradiction ledger
├── tasks.py         # Task queue, retry tracking, budget enforcement
├── timeline.py      # Chronological alignment & sequence
├── confidence.py    # Independent scoring (detection != sufficiency != posterior)
└── checkpoint.py    # State persistence, freeze, and resume
```

---

## 5. Phase 3 — Baseline Orchestrator (Deterministic)

Before integrating LLM reasoning, implement a **fixed, deterministic orchestration baseline**:

```text
Alert Ingestion
  │
  ▼
Correlation Capability
  │
  ▼
Investigation Capability
  │
  ▼
Knowledge Retrieval (RAG)
  │
  ▼
Evidence Validation Capability
  │
  ▼
Finalize / Containment
```

### Purpose of the Baseline
Provides a scientific ground truth to evaluate against:
- **Baseline:** Fixed / rule-based capability pipeline.
- **Proposed:** Adaptive evidence-driven LLM orchestration.
- **Evaluation Question:** Does adaptive orchestration reduce unnecessary tool calls, resolve ambiguity faster, and yield higher evidence coverage than the fixed pipeline?

---

## 6. Phase 4 — Specialized Capabilities

| Capability | Core Objective | Inputs | Outputs |
| :--- | :--- | :--- | :--- |
| **1. Correlation** | Discover related telemetry across hosts and network | Event IDs, time window, entities | Related events, entity links, timeline additions |
| **2. Investigation** | Test active hypotheses against available evidence | Hypothesis, evidence subset, constraints | Supporting/contradicting evidence, residual uncertainty |
| **3. Knowledge Retrieval** | Surface relevant ATT&CK techniques, CVEs, playbooks | Investigation context, target technique/entity | Grounded knowledge chunks, authoritative citations |
| **4. Evidence Validation** | Verify whether proposed claims are backed by raw facts | Proposed claim, evidence ledger, timeline | Validation verdict, unbacked claims, contradiction alerts |
| **5. Reporting** | Produce twin-tier incident briefs (executive + technical) | Validated state, timeline, audit trail | Formatted forensic report with strict evidence ID citations |

---

## 7. Phase 5 — Adaptive Agentic Planning

```text
                 ┌────────────────────┐
                 │ READ CURRENT STATE │
                 └─────────┬──────────┘
                           ▼
                 ┌────────────────────┐
                 │ GAP ANALYSIS       │
                 │ What is unknown?   │
                 └─────────┬──────────┘
                           ▼
                 ┌────────────────────┐
                 │ GENERATE OPTIONS   │
                 │ Which capability   │
                 │ can reduce doubt?  │
                 └─────────┬──────────┘
                           ▼
                 ┌────────────────────┐
                 │ SELECT ACTION      │
                 └─────────┬──────────┘
                           ▼
                    Execute Worker
                           │
                           ▼
                    Update State
                           │
                           └──────► Re-plan
```

### 4 Explicit Planner Operations
1. **State Interpretation:** Parse current entities, timeline coverage, and unresolved contradictions.
2. **Evidence Gap Analysis:** Identify specific missing links (e.g., "Parent process unknown", "C2 destination unverified").
3. **Action Selection:** Choose the most cost-effective capability to resolve the gap.
4. **Termination Decision:** Stop when confidence/sufficiency thresholds are met, execution budget is exhausted, or analyst intervention is required.

---

## 8. Phase 6 — Orchestration Safety & Action Validation Layer

The LLM Planner is **never** granted unrestricted execution authority.

```text
                 LLM Planner
                      │
                      ▼
              Proposed Action
                      │
                      ▼
        ┌────────────────────────┐
        │ ACTION VALIDATOR       │
        │                        │
        │ • Valid capability?    │
        │ • Input available?     │
        │ • Budget remaining?    │
        │ • Retry limit passed?  │
        │ • Human sign-off req?  │
        └────────────┬───────────┘
                     │
              ┌──────┴──────┐
              ▼             ▼
           [Valid]       [Invalid]
              │             │
              ▼             ▼
           Execute       Re-plan (with error context)
```

### Separation of Responsibilities
| System Function | Controlling Mechanism |
| :--- | :--- |
| Ambiguous reasoning & hypothesis formation | Local LLM (qwen2.5 / Qwen3) |
| Knowledge gap identification | Hybrid (LLM + Rule checks) |
| Capability parameter validation | Deterministic Pydantic contracts |
| Task budget & loop limits | Deterministic state counters |
| Safety & destructive containment boundaries | Deterministic Human-in-the-Loop (HITL) |
| Final evidence citation checks | Deterministic validator |

---

## 9. Phase 7 — Supporting Intelligence

### 9.1 Hybrid Detection as an Intelligent Signal Provider
```text
DetectionResult
├── predicted_category: str
├── suspicion_score: float
├── model_confidence: float
├── rule_matches: List[str]
├── important_features: Dict[str, float] (SHAP)
└── event_ids: List[str]
```
- **Tri-hybrid Stack:** CatBoost/XGBoost tabular classifier + Isolation Forest anomaly detection + Sigma deterministic rules.
- **Role:** High-throughput triage ($< 1\text{ ms}$ per flow) that feeds prioritized alerts into the orchestrator.

### 9.2 Graph-Based Correlation (NetworkX)
- Discovers multi-hop attack paths (Patient Zero $\to$ Privilege Escalation $\to$ Lateral Movement $\to$ Egress).
- Invoked **on-demand** by the orchestrator when cross-entity clustering is required.

### 9.3 Grounded Hybrid RAG
- **Strict Invariant:** `Observed Event Evidence != Retrieved Knowledge`.
- Hybrid retrieval (BGE-M3 dense embeddings + BM25 keyword search) filtered by platform and technique.
- Every claim in the generated report must cite verified `evidence_id`s.

---

## 10. Phase 8 & 9 — Observability & Evaluation Benchmark

### Execution Tracing
Store immutable traces for every investigation cycle:
`Investigation ID` $\to$ `Cycle #` $\to$ `State Snapshot` $\to$ `Identified Gap` $\to$ `Selected Capability` $\to$ `Worker Execution Latency` $\to$ `Evidence Delta` $\to$ `Posterior Update`.

### 3-Track Benchmark Comparison
Evaluate **Baseline (Deterministic Pipeline)** vs. **Proposed (Adaptive Orchestrator)** across:
1. **Decision Quality:** Appropriate action rate, unnecessary tool call rate, replanning effectiveness.
2. **Investigation Quality:** Evidence coverage ($>85\%$), hallucination/unsupported claim rate ($<5\%$), posterior calibration error (ECE).
3. **Efficiency:** Total worker invocations, time-to-converge, token cost.
4. **Generalization:** (Track 1: Known scenarios, Track 2: Unseen attack variants, Track 3: Benign-heavy high-noise replay).

---

## 11. Target Backend Directory Structure

```text
backend/app/
├── api/
│   ├── routes/
│   └── schemas/
├── orchestration/
│   ├── graph.py                 # LangGraph / state machine coordinator
│   ├── planner.py               # Adaptive LLM planner
│   ├── gap_analysis.py          # Evidence gap identifier
│   ├── action_selector.py       # Capability routing logic
│   ├── action_validator.py      # Deterministic guardrails & budget checks
│   ├── termination.py           # Stop conditions & convergence checks
│   └── capability_registry.py   # Registry of available worker capabilities
├── investigation/
│   ├── state.py                 # Core InvestigationState model
│   ├── evidence.py              # Evidence ledger & corroboration
│   ├── hypotheses.py            # Hypotheses & contradiction matrix
│   ├── confidence.py            # Multi-metric confidence engine
│   └── checkpoint.py            # State freezing & restoration
├── capabilities/
│   ├── correlation/             # Temporal & entity correlation
│   ├── investigation/           # Hypothesis testing
│   ├── knowledge/               # Grounded RAG & MITRE ATT&CK
│   ├── validation/              # Evidence sufficiency validator
│   ├── detection/               # Triage & signal ingestion
│   └── reporting/               # Twin-tier forensic reporting
├── intelligence/
│   ├── models/                  # CatBoost / XGBoost flow classifiers
│   ├── rules/                   # Sigma & heuristic rules
│   ├── anomaly/                 # Isolation Forest detector
│   └── fusion/                  # Score calibration & feature importance
├── persistence/
│   ├── repositories/
│   └── database.py
├── observability/
│   ├── tracing.py               # Cycle decision tracing
│   ├── metrics.py               # Runtime metrics
│   └── audit.py                 # Cryptographic containment log
└── evaluation/
    ├── scenarios.py             # CSE-CIC-IDS2018 scenario definitions
    ├── runner.py                # Standalone benchmark harness
    ├── metrics.py               # Scientific evaluation metrics
    └── baselines.py             # Fixed-workflow comparison baseline
```

---

## 12. Phased Development Milestones

- **Milestone 1 — Orchestration Foundation & Contracts:** Implement `InvestigationState`, Pydantic capability contracts, and checkpoint persistence. Testable without an LLM.
- **Milestone 2 — Baseline Workflow & Comparative Harness:** Build the deterministic sequential pipeline and evaluate on the 5 CSE-CIC-IDS2018 scenarios to record ground-truth baseline metrics.
- **Milestone 3 — Adaptive Orchestrator & Action Validator:** Implement gap analysis, the LLM Planner, and deterministic safety/budget validators. Demonstrate dynamic routing paths across different attack scenarios.
- **Milestone 4 — Advanced Intelligence (Detection + Graph + Hybrid RAG):** Add CatBoost triage, NetworkX temporal pathfinding, and BGE-M3/BM25 hybrid knowledge retrieval with mandatory citations.
- **Milestone 5 — Comprehensive Evaluation & Trace Observability:** Run the 3-track benchmark suite comparing Adaptive vs. Baseline, and surface decision traces in the Antigravity IDE UI.
