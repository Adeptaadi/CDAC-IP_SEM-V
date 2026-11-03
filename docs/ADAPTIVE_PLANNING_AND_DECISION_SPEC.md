# Project Sentinel — Adaptive Planning & Decision Specification (APDS)

**Document Type:** Core Orchestration and Decision Design Specification  
**Version:** 1.0  
**Status:** Proposed Architecture Upgrade  
**Primary Focus:** Adaptive Planning, Evidence-Gap Reasoning, Action Selection, Replanning, and Investigation Termination  
**Related Components:** Orchestration Core, Action Validator, Capability Registry, State Manager

---

# 1. Purpose & The Non-Linear Loop

This document formalizes the decision algorithms, prioritization policies, candidate scoring models, replanning triggers, and termination conditions for the **Project Sentinel Orchestration Core**.

### Core Operational Sequence
```text
┌─────────────────────────────────────┐
│ 1. Read Current Investigation State │  <-- Compact DecisionContext
└──────────────────┬──────────────────┘
                   ▼
┌─────────────────────────────────────┐
│ 2. Check Terminal and Safety Rules  │  <-- Deterministic budget & timeout checks
└──────────────────┬──────────────────┘
                   ▼
┌─────────────────────────────────────┐
│ 3. Evaluate Evidence & Hypotheses   │  <-- Assess stances & contradictions
└──────────────────┬──────────────────┘
                   ▼
┌─────────────────────────────────────┐
│ 4. Identify & Prioritize Gaps       │  <-- Critical > High > Medium > Low
└──────────────────┬──────────────────┘
                   ▼
┌─────────────────────────────────────┐
│ 5. Generate Candidate Actions       │  <-- Registry compatibility filter
└──────────────────┬──────────────────┘
                   ▼
┌─────────────────────────────────────┐
│ 6. Score and Rank Actions           │  <-- Multi-factor scoring model
└──────────────────┬──────────────────┘
                   ▼
┌─────────────────────────────────────┐
│ 7. Validate Selected Action         │  <-- Deterministic schema, budget, loop check
└──────────────────┬──────────────────┘
                   ▼
┌─────────────────────────────────────┐
│ 8. Execute Capability               │  <-- Isolated execution
└──────────────────┬──────────────────┘
                   ▼
┌─────────────────────────────────────┐
│ 9. Update State and Replan / Stop   │  <-- Non-linear state mutation
└──────────────────┴──────────────────┘
```

---

# 2. Decision Context Model (`DecisionContext`)

To prevent token blowout and hallucination, the Planner receives an engineered, compact context:

```python
class DecisionContext(BaseModel):
    investigation_id: UUID
    current_status: str
    current_objective: str
    active_hypotheses: List[Dict[str, Any]] # statement, confidence, stance summary
    key_supporting_evidence: List[str]     # summaries of strongest empirical facts
    key_contradictions: List[str]          # unresolved conflicting evidence
    unresolved_evidence_gaps: List[Dict[str, Any]] # id, description, priority
    recent_execution_signatures: List[str] # prevents duplicate loops
    available_capabilities: List[str]      # enabled & compatible capabilities
    remaining_budget: Dict[str, int]       # steps_left, retries_left, time_left
    investigation_metrics: Dict[str, float]# detection_conf, sufficiency, posterior
```

---

# 3. Deterministic Safety Boundaries & Budget Enforcement

The LLM is **never** permitted to decide when to stop tracking its own compute limits. Bounded execution is deterministically enforced before every planning step:

```text
InvestigationBudget:
- max_steps: 10 (Default)
- max_duration_seconds: 600
- max_retries_per_worker: 2
- max_duplicate_signatures: 0 (Strictly enforced)
```

| Boundary Trigger | Automated Enforcement Action |
| :--- | :--- |
| `current_steps >= max_steps` | Halt loop; transition to `BUDGET_EXHAUSTED` |
| `now() >= deadline` | Halt loop; preserve partial state; mark `TIMEOUT` |
| `worker_retries > limit` | Defer capability; mark gap unresolved; re-plan alternative |
| `signature in recent_signatures` | Reject action; force alternative gap selection |

---

# 4. Evidence Gap Taxonomy & Prioritization

The platform rejects vague goals ("investigate more"). Gaps are concrete information deficits:

```text
Evidence Gap Sources:
├── Hypothesis Uncertainty (e.g. "Did authenticated session execute processes?")
├── Contradiction Conflict (e.g. "Source IP is internal admin but login time is 03:00 AM")
├── Missing Technical Context (e.g. "Is encoded PowerShell string known adversary tool?")
└── Validation Failure (e.g. "Forensic claim lacks raw network flow citation")
```

### Gap Priority Matrix
| Priority Level | Criteria | Execution Policy |
| :--- | :--- | :--- |
| **Critical** | Missing fact that directly decides benign vs. malicious | Must resolve or explicitly declare unavailable before finalizing |
| **High** | Strong determinant of posterior confidence | High scoring weight during candidate selection |
| **Medium** | Corroborating secondary context | Invoked only after critical/high gaps are addressed |
| **Low** | Descriptive / auxiliary framing | Deferrable under budget pressure |

---

# 5. Candidate Action Scoring & Ranking Algorithm

Candidate actions generated for the priority gap are evaluated across six dimensions:

$$\text{Action Score} = (R \cdot w_R) + (I \cdot w_I) + (D \cdot w_D) - C - K - P_{\text{redundant}}$$

Where:
- **$R$ (Relevance):** Direct alignment with the selected gap category ($0 \dots 3$).
- **$I$ (Expected Information Gain):** Potential uncertainty reduction ($1 = \text{Low}, 2 = \text{Med}, 3 = \text{High}$).
- **$D$ (Reliability):** Empirical dependability of the capability ($1 = \text{LLM inference}, 3 = \text{Deterministic log query}$).
- **$C$ (Execution Cost):** Compute, token, or network latency penalty ($0 \dots 2$).
- **$K$ (Operational Risk):** Probability of timeout or unrecoverable error ($0 \dots 2$).
- **$P_{\text{redundant}}$ (Redundancy Penalty):** $+100$ penalty if action signature matches previous execution without state change.

---

# 6. Action Signature & Loop Prevention

To prevent infinite loops, every proposed action computes a deterministic signature:

$$\text{Sig} = \text{SHA256}(\text{Capability} \,\|\, \text{Target Entity} \,\|\, \text{Time Window} \,\|\, \text{Normalized Parameters})$$

**Re-execution Rule:** A previously executed signature is rejected **unless**:
1. A new entity was discovered that expands the scope.
2. The time window is materially altered ($\ge 20\%$ expansion).
3. The previous execution failed due to a transient dependency.

---

# 7. Structured Planner Output Contract (`PlanningProposal`)

The LLM Planner is bound to output strict JSON conforming to:

```python
class PlanningProposal(BaseModel):
    investigation_assessment: str
    selected_evidence_gap_id: UUID
    candidate_actions: List[str]
    recommended_action: str # Name of registered capability
    target_parameters: Dict[str, Any]
    expected_information_value: Literal["LOW", "MEDIUM", "HIGH"]
    rationale: str
    fallback_action: Optional[str] = None
```

Free-form text reasoning is rejected by the Action Validator.

---

# 8. Replanning Triggers

The system automatically pivots its strategy when the following conditions occur:

1. **New Empirical Evidence:** Correlation reveals an unexpected process or remote IP $\to$ Generates new gap $\to$ Pivots to Knowledge or Graph.
2. **Contradiction Detected:** New fact contradicts active hypothesis $\to$ Decrements confidence $\to$ Generates counter-hypothesis.
3. **Capability Failure / `NO_RESULT`:** Worker fails or finds no telemetry $\to$ Backtracks $\to$ Selects fallback capability.
4. **Sufficiency Achieved:** Critical gaps resolved $\to$ Transitions directly to Evidence Validation.

---

# 9. Evidence Sufficiency & Investigation Termination

Termination requires satisfying objective verification criteria, **not** merely high model probability:

```text
Critical Evidence Gaps Resolved?
              │
      ┌───────┴───────┐
     Yes              No
      │               │
Contradictions   Can Gap Be Resolved?
Evaluated?            │
      │           ┌───┴───┐
     Yes         Yes      No
      │           │       │
Validation    Continue  Escalate to Analyst (INCONCLUSIVE)
Passed?
      │
     Yes
      ▼
FINALIZED (Generate Forensic Report)
```

### Termination Outlays
- `FINALIZED`: All critical gaps addressed, contradictions resolved, claims validated.
- `INCONCLUSIVE`: Necessary telemetry missing in environment; cannot responsibly prove maliciousness.
- `ESCALATED`: High-impact containment required, or severe unresolvable contradiction.
- `BUDGET_EXHAUSTED`: Maximum steps reached; partial forensic state exported.
