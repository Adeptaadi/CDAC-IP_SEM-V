# Project Sentinel — Capability & Agent Interface Specification (CAIS)

**Document Type:** Technical Interface and Component Specification  
**Version:** 1.0  
**Status:** Proposed Architecture Upgrade  
**Primary Focus:** Specialized Agent Capabilities and Their Integration with the Orchestration Core  
**Architecture Pattern:** Registry-Based, Schema-Controlled Capability Architecture

---

# 1. Purpose & Core Architectural Boundary

This document defines the formal interfaces, data contracts, execution lifecycles, and failure protocols for all specialized capabilities within Project Sentinel.

### The Defining Principle
> **Capabilities perform specialized work. The Orchestrator controls the investigation.**

Individual capabilities (Correlation, Investigation, Knowledge RAG, Evidence Validation, Reporting) never alter the global investigation state directly, never trigger other workers peer-to-peer, and never dictate the final investigation verdict. They execute bounded tasks and return typed results to the Orchestration Core.

```text
                    ┌────────────────────────────┐
                    │     ORCHESTRATION CORE     │
                    │ Controls investigation and │
                    │ selects next capabilities  │
                    └──────────────┬─────────────┘
                                   │
                                   ▼
                    ┌────────────────────────────┐
                    │    CAPABILITY REGISTRY     │
                    │ Available capabilities,    │
                    │ metadata & cost profiles   │
                    └──────────────┬─────────────┘
                                   │
        ┌──────────────┬───────────┼───────────┬──────────────┐
        ▼              ▼           ▼           ▼              ▼
   Correlation    Investigation  Knowledge  Validation    Reporting
    Capability     Capability    Capability Capability   Capability
        │              │           │           │              │
        └──────────────┴───────────┴───────────┴──────────────┘
                                   │
                                   ▼
                       Structured Worker Results
                                   │
                                   ▼
                         Investigation State
```

---

# 2. Agent vs. Capability

| Concept | Internal Scope | External Contract with Orchestrator |
| :--- | :--- | :--- |
| **Agent** | May possess internal loops, LLM chains, semantic search tools, or heuristics. | Opaque black box to the orchestrator. |
| **Capability** | Controlled, stateless interface registered in the central system. | Invoked via `CapabilityRequest` $\to$ Returns `CapabilityResult`. |

---

# 3. Base Capability Contract

All specialized workers implement the abstract interface:

```python
class BaseCapability(ABC):
    @abstractmethod
    def metadata(self) -> CapabilityMetadata:
        """Returns capabilities, cost profile, supported gap types, and timeouts."""
        pass

    @abstractmethod
    def validate_input(self, request: CapabilityRequest) -> bool:
        """Validates payload against Pydantic schema before execution starts."""
        pass

    @abstractmethod
    def execute(self, request: CapabilityRequest) -> CapabilityResult:
        """Executes specialized domain analysis in an isolated sandbox/thread."""
        pass

    @abstractmethod
    def handle_failure(self, error: Exception) -> CapabilityResult:
        """Generates structured failure result with recovery recommendations."""
        pass
```

---

# 4. Standard Data Contracts

## 4.1 Capability Metadata (`CapabilityMetadata`)
```python
class CapabilityMetadata(BaseModel):
    name: str
    version: str
    description: str
    supported_objectives: List[str]
    supported_gap_types: List[str] # e.g., ["missing_context", "unverified_conclusion"]
    input_schema: str              # Pydantic schema name
    output_schema: str             # Pydantic schema name
    timeout_seconds: float
    retry_limit: int
    estimated_cost: float          # In abstract compute/token units
    dependencies: List[str]        # e.g., ["chromadb", "sqlite", "catboost"]
    enabled: bool = True
```

## 4.2 Capability Request (`CapabilityRequest`)
```python
class CapabilityRequest(BaseModel):
    request_id: UUID
    investigation_id: UUID
    state_version: int
    objective: str
    evidence_gap_reference: Optional[UUID]
    input_data: Dict[str, Any]
    evidence_references: List[UUID]
    execution_constraints: Dict[str, Any] # max_events, time_range, max_tokens
    correlation_id: str
```

## 4.3 Standard Capability Result (`CapabilityResult`)
```python
class CapabilityResult(BaseModel):
    request_id: UUID
    capability_name: str
    status: Literal["SUCCESS", "PARTIAL_SUCCESS", "NO_RESULT", "FAILED", "TIMEOUT"]
    findings: List[Finding]
    evidence_updates: List[EvidenceItem]
    entity_updates: List[Entity]
    hypothesis_updates: List[Dict[str, Any]]
    new_evidence_gaps: List[EvidenceGap]
    contradictions: List[ContradictionItem]
    limitations: Optional[str]
    recommendations: List[str]
    execution_metadata: Dict[str, Any] # latency_ms, model_used, tokens
```

*Note on `NO_RESULT`:* A capability finding zero related events is a valid empirical outcome (`status="NO_RESULT"`), **not** an execution failure.

---

# 5. Core Capabilities Specifications

## 5.1 Correlation Capability (`capabilities/correlation/`)
- **Objective:** Discover events linked by shared source/dest IPs, user accounts, processes, and time windows.
- **Input:** Seed event IDs, entity filters, time range ($\pm \Delta t$).
- **Output:** Linked event IDs, graph edge candidates, timeline additions, and limitations.

## 5.2 Investigation Capability (`capabilities/investigation/`)
- **Objective:** Test candidate attack hypotheses against available evidence.
- **Input:** Target hypothesis statement, relevant evidence IDs, contextual constraints.
- **Output:** Categorized findings (*Supporting Evidence*, *Contradictory Evidence*, *Remaining Gaps*).

## 5.3 Knowledge Retrieval Capability (`capabilities/knowledge/`)
- **Objective:** Surface relevant ATT&CK techniques, detection guidance, and mitigation playbooks from ChromaDB/BGE-M3.
- **Input:** Investigation context, query text, entity filters.
- **Output:** Grounded context chunks with similarity scores.
- **Strict Invariant:** Every retrieved item is stamped `evidence_type="retrieved_context"`. It is never treated as observed incident evidence.

## 5.4 Evidence Validation Capability (`capabilities/validation/`)
- **Objective:** Verify whether a proposed report claim is strictly backed by raw events.
- **Input:** Proposed claim statement, cited evidence IDs, active timeline.
- **Output:** Status (`VALIDATED`, `PARTIALLY_SUPPORTED`, `UNSUPPORTED`, `CONTRADICTED`, `INSUFFICIENT_EVIDENCE`).

## 5.5 Reporting Capability (`capabilities/reporting/`)
- **Objective:** Synthesize validated facts into executive briefings and forensic timelines.
- **Requirement:** Every factual statement must cite corresponding `evidence_id`s.

---

# 6. Failure, Timeout, & Retry Protocol

```text
Execution Starts ──► [Worker Crashes / Times Out]
                              │
                              ▼
                handle_failure() Catches Exception
                              │
                              ▼
                Formulates Structured Result:
                - status: FAILED / TIMEOUT
                - failure_type: INPUT_ERROR / MODEL_ERROR / TIMEOUT
                - retryable: bool
                - partial_results: List
                - recovery_recommendation: str
                              │
                              ▼
                State Manager Records Failure
                              │
                              ▼
        ┌─────────────────────┴─────────────────────┐
        ▼                                           ▼
[Retryable & Retries < Limit]             [Exhausted / Fatal]
        │                                           │
  Re-enqueue Action                          Re-plan / Escalate
```

### Standard Timeouts
- Correlation: 30s
- Knowledge RAG: 30s
- Investigation: 60s
- Evidence Validation: 45s
- Reporting: 60s

---

# 7. Capability Registry & Discovery (`registry.py`)

The `CapabilityRegistry` enables dynamic capability discovery:
1. **Startup Registration:** Capabilities auto-register with typed metadata.
2. **Gap Compatibility Filtering:** Given an `EvidenceGap` category (`MISSING_CONTEXT`, `MISSING_TECHNICAL_KNOWLEDGE`), the registry returns only capable and enabled workers.
3. **Decoupled Extension:** Adding a new capability (e.g. `GraphAnalysisWorker` or `CatBoostTriageWorker`) requires zero changes to the Orchestrator code—simply declare supported gap types and register.

---

# 8. Component File Organization

```text
backend/app/capabilities/
├── base.py                   # BaseCapability abstract class & contracts
├── registry.py               # CapabilityRegistry & discovery methods
├── schemas.py                # CapabilityRequest, CapabilityResult, Metadata
├── correlation/
│   ├── capability.py         # Correlation worker implementation
│   └── service.py            # Event linking & temporal window logic
├── investigation/
│   ├── capability.py         # Hypothesis evaluation worker
│   └── reasoning.py          # Evidence-hypothesis stance evaluator
├── knowledge/
│   ├── capability.py         # Knowledge RAG retrieval worker
│   └── vector_store.py       # ChromaDB / BGE-M3 integration
├── validation/
│   ├── capability.py         # Claim validation worker
│   └── validator.py          # Strict evidence citation checker
└── reporting/
    ├── capability.py         # Twin-tier report generator
    └── generator.py          # Forensic template renderer
```

---

# 9. Capability Evaluation Dimensions

Each capability is benchmarked independently:
- **Correlation:** Recall of ground-truth attack events, false relationship rate, execution latency.
- **Investigation:** Correct stance identification (supports vs. contradicts), contradiction detection recall.
- **Knowledge RAG:** Recall@K of MITRE techniques, citation accuracy.
- **Evidence Validation:** Precision in catching unsupported claims and hallucinations.
