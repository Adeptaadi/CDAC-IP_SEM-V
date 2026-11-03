# Project Sentinel — Detailed Data, State & Interface Specification (DSIS)

**Document Type:** Technical Data and Interface Specification  
**Version:** 1.0  
**Status:** Proposed Architecture Upgrade  
**Primary Focus:** Data Contracts, Investigation State, Evidence Models, Capability Interfaces, API Models, Persistence, and Data Lifecycle  
**Related Components:** Ingestion Layer, State Manager, Action Validator, Capability Registry, PostgreSQL, Frontend

---

# 1. Purpose & Core Contract Principle

This document defines the formal data contracts, database mappings, validation layers, and entity lifecycles governing inter-component communication in Project Sentinel.

### Core Architectural Axiom
> **Components communicate through structured, validated data contracts rather than unstructured messages or direct internal dependencies.**

```text
Incident Evidence != Knowledge Context != AI Interpretation
```

---

# 2. Comprehensive Entity Architecture

```text
                    ┌──────────────────────┐
                    │   RAW TELEMETRY      │ (CSE-CIC-IDS2018 / Sysmon)
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ NORMALIZED EVENTS    │ (NormalizedEvent Schema)
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ ALERTS               │ (Alert Schema)
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ INVESTIGATION STATE  │ (State Version n)
                    └───────┬───────┬──────┘
                            │       │
                ┌───────────┘       └───────────┐
                ▼                               ▼
        ┌───────────────┐               ┌───────────────┐
        │ EVIDENCE      │               │ HYPOTHESES    │
        └───────────────┘               └───────────────┘
                │                               │
                └───────────────┬───────────────┘
                                ▼
                      ┌──────────────────┐
                      │ DECISION HISTORY │
                      └────────┬─────────┘
                               ▼
                      ┌──────────────────┐
                      │ FINAL OUTCOME    │
                      └──────────────────┘
```

---

# 3. Core Data Contracts (Pydantic V2 Models)

## 3.1 Normalized Telemetry (`NormalizedEvent`)
Preserves telemetry integrity across diverse datasets while standardizing host, process, and network keys:

```python
class NormalizedEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime
    source_type: Literal["network_flow", "sysmon_host", "auth_log", "alert"]
    event_type: str              # e.g., "process_creation", "tcp_syn", "login_failure"
    host: Optional[str] = None
    user: Optional[str] = None
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    source_port: Optional[int] = None
    destination_port: Optional[int] = None
    process_name: Optional[str] = None
    process_id: Optional[int] = None
    parent_process: Optional[str] = None
    command_line: Optional[str] = None
    severity: Literal["low", "medium", "high", "critical"] = "low"
    raw_reference: str           # Pointer back to original line / packet hash
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

**Missing Data Rule:** Fields not provided by a sensor are set to `None`. $\text{Unknown} \neq \text{False}$; missing data is never treated as negative evidence.

## 3.2 Security Alert Contract (`Alert`)
```python
class Alert(BaseModel):
    alert_id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    source: str                  # e.g., "catboost_classifier", "sigma_macro_rule"
    alert_type: str              # e.g., "suspicious_powershell_reverse_shell"
    severity: Literal["low", "medium", "high", "critical"]
    related_event_ids: List[UUID]
    detection_reason: str
    status: Literal["new", "investigating", "suppressed", "closed"] = "new"
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

## 3.3 Investigation Canonical Record (`Investigation`)
```python
class Investigation(BaseModel):
    investigation_id: UUID = Field(default_factory=uuid4)
    alert_id: Optional[UUID] = None
    title: str
    status: Literal["CREATED", "QUEUED", "RUNNING", "WAITING_REVIEW", "DEGRADED", "FINALIZED", "INCONCLUSIVE", "ESCALATED", "FAILED"]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    current_state_version: int = 1
    final_outcome: Optional[str] = None
```

## 3.4 Runtime State Contract (`InvestigationState`)
```python
class InvestigationState(BaseModel):
    investigation_id: UUID
    version: int
    status: str
    objective: str               # Boundaries preventing uncontrolled topic drift
    evidence: List[EvidenceItem]
    hypotheses: List[HypothesisItem]
    evidence_gaps: List[EvidenceGap]
    action_history: List[ExecutionRecord]
    decision_history: List[DecisionRecord]
    confidence_assessment: ConfidenceAssessment
    budget: InvestigationBudget
    updated_at: datetime
```

---

# 4. Action & Planning Contracts

## 4.1 Action Request Contract (`ActionRequest`)
```python
class ActionRequest(BaseModel):
    action_id: UUID = Field(default_factory=uuid4)
    capability_name: str
    objective: str
    target_gap_id: UUID
    input_parameters: Dict[str, Any]
    expected_information_gain: Literal["LOW", "MEDIUM", "HIGH"]
    rationale: str
    priority: Literal["critical", "high", "medium", "low"]
    action_signature: str        # Deterministic SHA256 parameter hash
```

## 4.2 Planner Decision Contract (`PlannerDecision`)
```python
class PlannerDecision(BaseModel):
    decision_id: UUID = Field(default_factory=uuid4)
    investigation_id: UUID
    state_version: int
    assessment_summary: str
    identified_gaps: List[EvidenceGap]
    candidate_actions: List[ActionRequest]
    selected_action: ActionRequest
    rationale: str
    termination_recommendation: Optional[Literal["CONTINUE", "FINALIZED", "INCONCLUSIVE", "ESCALATED"]] = None
```

---

# 5. External Knowledge vs. Evidence Schema

```python
class KnowledgeContext(BaseModel):
    context_id: UUID = Field(default_factory=uuid4)
    query: str
    source_document: str        # e.g., "MITRE-ATT&CK-v14.1"
    technique_id: Optional[str] # e.g., "T1059.001"
    retrieved_content: str
    similarity_score: float
    retrieval_timestamp: datetime = Field(default_factory=datetime.utcnow)
```
**Invariant:** `KnowledgeContext` is structurally isolated from `EvidenceItem`. It is never stored in the empirical evidence table.

---

# 6. REST & WebSocket API Contracts

## 6.1 Create & Start Investigation
- `POST /api/v1/investigations`
  - Input: `{ "alert_id": "ALT-101", "objective": "Investigate macro execution" }`
  - Response (201 Created): `{ "investigation_id": "...", "status": "CREATED" }`
- `POST /api/v1/investigations/{id}/start`
  - Response (202 Accepted): `{ "investigation_id": "...", "status": "QUEUED" }`

## 6.2 Get Investigation State Snapshot
- `GET /api/v1/investigations/{id}`
  - Response (200 OK):
    ```json
    {
      "investigation_id": "...",
      "status": "RUNNING",
      "state_version": 6,
      "confidence": 0.88,
      "current_objective": "Determine post-authentication process activity",
      "active_hypotheses": [...],
      "evidence_count": 8,
      "pending_approvals": 1
    }
    ```

## 6.3 Human Review Intervention
- `POST /api/v1/investigations/{id}/review`
  - Input:
    ```json
    {
      "recommendation_id": "...",
      "decision": "APPROVE",
      "analyst_id": "ANALYST_01",
      "rationale": "Verified C2 beaconing on edge firewall"
    }
    ```
  - Response (200 OK): `{ "status": "approved", "investigation_status": "RESUMED" }`

---

# 7. Five-Layer Validation Defense

```text
1. API Ingress Validation   : FastAPI + Pydantic rejects malformed HTTP payloads
2. Domain Entity Check      : State Manager checks existence of entities and foreign keys
3. Action Policy Validator  : Deterministic guardrails enforce budgets and duplicate bans
4. Capability Output Check  : Result processor validates worker returned types
5. Database Constraints     : PostgreSQL foreign keys, unique hashes, and optimistic lock checks
```

---

# 8. Data Ownership Matrix

| Data Asset | Authoritative Owner | Update Protocol |
| :--- | :--- | :--- |
| **Raw Telemetry** | Ingestion Service | Append-only batch load |
| **Normalized Events** | Telemetry Normalizer | Read-only to workers |
| **Alerts** | Detection Engine | Creates new investigations |
| **Investigation State** | State Manager | Atomic version increments ($V_n \to V_{n+1}$) |
| **Evidence Items** | State Manager | Immutable once committed |
| **Worker Results** | Worker Capability | Transient until validated |
| **Decisions & Audits** | Orchestrator Runtime | Append-only hash-chained logs |
| **Human Approvals** | SOC Analyst | Signed approval records |
