# Project Sentinel — Orchestration Design Document (ODD)

**Document Type:** Detailed System Design  
**Version:** 1.0  
**Status:** Proposed Architecture Upgrade  
**Primary Component:** Adaptive Agent Orchestration Core  
**Architecture Pattern:** Stateful, Evidence-Guided, Bounded Agentic Workflow

---

# 1. Purpose & Architectural Mandate

This document defines the detailed technical design of the **Agent Orchestration Core** for Project Sentinel.

The Orchestration Core controls the lifecycle of an autonomous cybersecurity investigation. It determines:
- What the system currently knows.
- What information is missing (evidence gaps).
- Which specialized capability should be invoked next.
- Whether the proposed action satisfies deterministic guardrails.
- How results update the central investigation state.
- When the investigation should be replanned or backtracked.
- When sufficient evidence exists to terminate.
- When human analyst review is required.

### Continuous Operating Loop
```text
READ STATE ──► UNDERSTAND SITUATION ──► IDENTIFY EVIDENCE GAP ──► SELECT CAPABILITY
                                                                          │
REPLAN / TERMINATE ◄── UPDATE STATE ◄── PROCESS RESULT ◄── EXECUTE ◄── VALIDATE
```

---

# 2. Design Goals

1. **Adaptive Execution:** Different incidents follow different capability paths; no rigid sequential pipelines.
2. **Evidence-Driven Decisions:** The Planner acts exclusively on structured investigation state rather than conversational history.
3. **Controlled Autonomy:** LLM reasoning is strictly bounded by deterministic validation (budgets, schemas, retry limits, loop detection).
4. **Fine-Grained Observability:** Every decision records state snapshot, identified gap, selected capability, rationale, execution result, and delta.
5. **Recoverability & Isolation:** Worker failures preserve the investigation state and yield control back to the orchestrator.

---

# 3. Core Architecture: The 6 Orchestration Components

```text
┌─────────────────────────────────────────────────────────┐
│                 ORCHESTRATION CORE                      │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 1. STATE INTERPRETER                           │   │
│  └──────────────────────┬──────────────────────────┘   │
│                         ↓                              │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 2. EVIDENCE GAP ANALYZER                       │   │
│  └──────────────────────┬──────────────────────────┘   │
│                         ↓                              │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 3. ACTION PLANNER                              │   │
│  └──────────────────────┬──────────────────────────┘   │
│                         ↓                              │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 4. ACTION VALIDATOR                            │   │
│  └──────────────────────┬──────────────────────────┘   │
│                         ↓                              │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 5. CAPABILITY EXECUTOR                         │   │
│  └──────────────────────┬──────────────────────────┘   │
│                         ↓                              │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 6. RESULT PROCESSOR & TERMINATION ENGINE       │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

# 4. Investigation Lifecycle State Machine

```text
CREATED ──► INITIALIZED ──► INVESTIGATING
                                 │
           ┌─────────────────────┼─────────────────────┬─────────────────────┐
           ▼                     ▼                     ▼                     ▼
      REPLANNING             ESCALATED             COMPLETED              FAILED
```

| Lifecycle Status | Operational Meaning |
| :--- | :--- |
| `CREATED` | Database record initialized; raw alert received. |
| `INITIALIZED` | Baseline telemetry loaded; trigger context normalized. |
| `INVESTIGATING` | Active orchestration loop running. |
| `REPLANNING` | Contradiction detected or hypothesis invalidated; strategy updating. |
| `ESCALATED` | Human-on-the-loop sign-off required (destructive containment or unresolved contradiction). |
| `COMPLETED` | Hypothesis confirmed, evidence sufficiency threshold met, claims validated. |
| `FAILED` | Maximum budget exhausted without convergence, or unrecoverable error. |

---

# 5. Component Detailed Specifications

## 5.1 State Interpreter (`state_interpreter.py`)
Produces a compact, structured **Orchestration Summary** for the LLM to avoid context bloating and token waste:
- **Trigger context** (initial anomaly / telemetry rule).
- **Known facts & entities** (IPs, hosts, users, hashes).
- **Active hypotheses** & current stances.
- **Execution history** (completed, failed, and retried tasks).
- **Identified contradictions** & uncertainty flags.
- **Remaining execution budget** (cycles, tool calls).

## 5.2 Evidence Gap Analyzer (`gap_analyzer.py`)
Categorizes concrete evidentiary deficiencies into structured `EvidenceGap` objects:
- `MISSING_CONTEXT` $\to$ Telemetry surrounding the alert is unknown (routes to *Correlation*).
- `MISSING_RELATIONSHIP` $\to$ Entity topology/lateral movement unclear (routes to *Graph Analysis*).
- `MISSING_TECHNICAL_KNOWLEDGE` $\to$ Obfuscated command or CVE unknown (routes to *Knowledge RAG*).
- `WEAK_HYPOTHESIS_SUPPORT` $\to$ Need corroboration from secondary source (routes to *Investigation*).
- `CONTRADICTORY_EVIDENCE` $\to$ Conflicting observations (routes to *Replanning*).
- `UNVERIFIED_CONCLUSION` $\to$ Proposed report lacks factual citations (routes to *Evidence Validation*).

## 5.3 Capability Registry (`capability_registry.py`)
Decouples the Planner from specific worker classes:
```text
CapabilityMetadata:
- name: str
- description: str
- supported_gap_types: List[str]
- input_schema: Type[BaseModel]
- output_schema: Type[BaseModel]
- estimated_cost: float
- timeout_seconds: float
- retry_policy: RetryConfig
- execution_constraints: List[str]
```
Initial MVP Registry: `CorrelationWorker`, `InvestigationWorker`, `KnowledgeWorker`, `EvidenceValidationWorker`, `ReportingWorker` (with `GraphWorker` available for multi-hop expansion).

## 5.4 Action Planner (`planner.py`)
Generates structured `ActionProposal` objects containing `capability_name`, `objective`, `rationale`, `required_inputs`, `expected_output`, and `priority`.

## 5.5 Action Validator (`action_validator.py`)
Deterministic software safety boundary:
- **Capability Check:** Does it exist and is it active?
- **Schema Check:** Do proposed arguments match Pydantic contracts?
- **Budget Check:** Steps $\le \text{MAX\_STEPS}$, worker calls within allowance.
- **Loop Check:** Is the system repeating the exact same parameters that yielded `NO_RESULT`?
- **Governance Check:** Does this require Human-in-the-Loop sign-off?

## 5.6 Result Processor & Termination Engine (`result_processor.py`, `termination.py`)
Processes `WorkerResult` (`SUCCESS`, `PARTIAL_SUCCESS`, `NO_RESULT`, `FAILED`, `TIMEOUT`).
Updates the central evidence ledger, re-evaluates logit confidence, and triggers termination:
- **Normal Stop:** Confidence $\ge 0.85$, sufficiency $\ge 0.80$, validation passed.
- **Replanning:** Contradiction detected or new parent process discovered.
- **Escalation:** Ambiguity unresolved, or high-risk containment action staged.
- **Forced Stop:** Maximum step count reached.

---

# 6. LangGraph State Machine Architecture

```text
               ┌──────────────┐
               │  INITIALIZE  │
               └──────┬───────┘
                      ↓
               ┌──────────────┐
               │  INTERPRET   │
               └──────┬───────┘
                      ↓
               ┌──────────────┐
               │ ANALYZE GAPS │
               └──────┬───────┘
                      ↓
               ┌──────────────┐
               │ PLAN ACTION  │
               └──────┬───────┘
                      ↓
               ┌──────────────┐
               │   VALIDATE   │
               └──────┬───────┘
            ┌─────────┴─────────┐
            ▼                   ▼
        [REJECTED]          [APPROVED]
            │                   │
         RE-PLAN         EXECUTE CAPABILITY
                                │
                          PROCESS RESULT
                                │
                           UPDATE STATE
                                │
                        TERMINATION CHECK
                         ┌──────┴──────┐
                         ▼             ▼
                      [STOP]      [CONTINUE]
                                       │
                                       └─► (Loop to INTERPRET)
```

---

# 7. Proposed Backend Modular Directory Structure

```text
backend/app/
├── orchestration/
│   ├── graph.py               # LangGraph state machine & conditional edges
│   ├── state_interpreter.py   # State summarizer & context compressor
│   ├── gap_analyzer.py        # Evidence gap categorizer
│   ├── planner.py             # Adaptive LLM action planner
│   ├── action_validator.py    # Deterministic guardrails & loop prevention
│   ├── executor.py            # Isolated capability runner & timeout handler
│   ├── result_processor.py    # State updater & evidence reconcile
│   ├── termination.py         # Multi-condition stop engine
│   └── capability_registry.py # Central capability catalog
├── investigation/
│   ├── state.py               # Root InvestigationState model
│   ├── evidence.py            # Evidence item contracts & stance logic
│   ├── hypotheses.py          # Hypothesis lifecycle & contradiction ledger
│   └── checkpoint.py          # State serialization & restore
├── capabilities/
│   ├── base.py                # Abstract BaseCapability interface
│   ├── correlation/           # Correlation capability
│   ├── investigation/         # Hypothesis validation capability
│   ├── knowledge/             # ATT&CK RAG retrieval capability
│   ├── validation/            # Evidence sufficiency & claim validator
│   └── reporting/             # Forensic reporter
└── observability/
    ├── tracing.py             # Decision cycle trace logger
    └── metrics.py             # Orchestration performance metrics
```

---

# 8. Measurable Orchestration Performance Indicators

| Category | Indicator | Target | Specification Meaning |
| :--- | :--- | :--- | :--- |
| **Decision Quality** | Action Validity Rate | $> 95\%$ | Proposed actions passing deterministic validation |
| | Unnecessary Action Rate | $< 10\%$ | Redundant or zero-gain capability invocations |
| | Replanning Effectiveness | $> 80\%$ | Replans successfully resolving flagged gaps |
| **Investigation Quality** | Evidence Coverage | $> 85\%$ | Ground-truth attack indicators corroborated |
| | Unsupported Claim Rate | $< 5\%$ | Assertions lacking concrete raw evidence references |
| | Correct Conclusion Rate | $> 90\%$ | Correct attack technique identified |
| **System Efficiency** | Mean Cycles to Converge | $\le 8$ cycles | Convergence latency without thrashing |
| | Failure Recovery Rate | $100\%$ | Investigations safely preserved across worker errors |
