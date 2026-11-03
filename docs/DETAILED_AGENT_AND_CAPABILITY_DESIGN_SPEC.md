# Project Sentinel — Detailed Agent and Capability Design Specification (DACDS)

**Document Type:** Core AI and Orchestration Architecture Specification  
**Version:** 1.0  
**Status:** Proposed Architecture Upgrade  
**Primary Focus:** Agent responsibilities, capability contracts, orchestration logic, decision-making, state communication, and failure handling  
**Related Components:** Investigation Planner, Policy Controller, Capability Registry, Result Validator, State Manager, Termination Controller

---

# 1. Purpose

The central intelligence of Project Sentinel is not based on multiple agents freely communicating with one another.

Instead, the system uses a **controlled orchestration architecture**.

The architecture separates:

```text
THINKING
   ↓
DECISION
   ↓
EXECUTION
   ↓
VALIDATION
   ↓
STATE UPDATE
```

This separation is essential because an investigation system requires:
- Predictability
- Traceability
- Controlled execution
- Clear responsibility boundaries
- Reliable failure handling

The primary design principle is:

> **The Planner decides what should happen. Capabilities perform the work. The State Manager preserves the truth of the investigation.**

---

# 2. Core Orchestration Architecture

The complete interaction model is:

```text
                         ┌──────────────────────┐
                         │   INVESTIGATION      │
                         │      STATE           │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │      PLANNER         │
                         │  Assessment & Plan   │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   POLICY / SAFETY    │
                         │      CONTROL         │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ CAPABILITY REGISTRY  │
                         └──────────┬───────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              ▼                     ▼                     ▼
       CORRELATION            KNOWLEDGE              VALIDATION
       CAPABILITY             CAPABILITY             CAPABILITY
              │                     │                     │
              └─────────────────────┼─────────────────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    RESULT VALIDATOR  │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    STATE MANAGER     │
                         └──────────┬───────────┘
                                    │
                                    ▼
                              REASSESS
```

The loop continues until a controlled termination condition is reached.

---

# 3. What Is an Agent in Project Sentinel?

The word **agent** should be used carefully. An agent is not simply any component that uses an LLM.

For Project Sentinel, an agent-like component has the ability to:
1. Observe the investigation state.
2. Reason about the current situation.
3. Select an appropriate next action.
4. Evaluate the result.
5. Adapt its next decision.

The primary autonomous reasoning component is therefore:

```text
INVESTIGATION PLANNER
```

Other components should primarily be implemented as **specialized capabilities**. This design avoids unnecessary multi-agent complexity.

---

# 4. The Investigation Planner

## 4.1 Primary Responsibility

The Planner is responsible for answering:

> **Given the current investigation state, what should happen next?**

The Planner does not directly:
- Query databases.
- Search telemetry.
- Modify persistent state.
- Call external services without control.

Instead, it produces a structured decision.

## 4.2 Planner Input

The Planner receives a controlled summary:

```text
PlannerInput
│
├── investigation_id
├── current_status
├── alert_summary
│
├── evidence_summary
├── evidence_gaps
│
├── active_hypotheses
├── action_history
│
├── available_capabilities
├── remaining_budget
└── current_confidence
```

The Planner should not receive unlimited raw telemetry by default. This prevents excessive context size and reduces uncontrolled reasoning.

## 4.3 Planner Output

The Planner must return structured output:

```text
PlannerDecision
│
├── assessment
├── identified_gaps
│
├── candidate_actions
│
├── selected_action
├── action_parameters
│
├── rationale
│
├── expected_information_gain
│
└── termination_recommendation
```

Free-form output alone should not control system execution.

---

# 5. Planner Decision Cycle

The Planner follows a repeated decision cycle:

```text
CURRENT STATE
      │
      ▼
UNDERSTAND EVIDENCE
      │
      ▼
IDENTIFY WHAT IS UNKNOWN
      │
      ▼
SELECT POSSIBLE ACTIONS
      │
      ▼
ESTIMATE VALUE
      │
      ▼
SELECT NEXT ACTION
      │
      ▼
EXECUTE THROUGH CAPABILITY
```

The key concept is the **evidence gap**. The system should not ask *"What action can I perform?"* It should ask:

> **What important information is currently missing?**

The action is then selected specifically to reduce that gap.

---

# 6. Evidence Gap Model

An evidence gap represents an unresolved investigation question:
- Unknown source process
- Unknown relationship between events
- Unknown relevance of an attack technique
- Conflicting evidence
- Insufficient evidence for conclusion

```text
EvidenceGap
│
├── gap_id
├── description
├── priority
├── related_hypothesis
├── possible_resolution_methods
└── status
```

The Planner should prioritize unresolved, high-impact gaps.

---

# 7. Hybrid Decision Architecture

Project Sentinel does not allow the LLM to have unrestricted control.

```text
                ┌───────────────────────┐
                │  DETERMINISTIC LAYER  │
                │                       │
                │ • Budgets             │
                │ • Policies            │
                │ • Validation          │
                │ • Allowed Actions     │
                └───────────┬───────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │     LLM PLANNER       │
                │                       │
                │ • Interpretation      │
                │ • Gap Analysis        │
                │ • Prioritization      │
                └───────────┬───────────┘
                            │
                            ▼
                    STRUCTURED DECISION
```

The LLM contributes intelligence; the deterministic layer provides hard boundaries.

---

# 8. Action Selection

The Planner may identify multiple candidate actions. The system scores them before execution:

```text
Action Score = Information Gain + Relevance + Hypothesis Impact - Execution Cost - Redundancy
```

| Factor | Meaning |
|---|---|
| **Information Gain** | How much uncertainty may be reduced |
| **Relevance** | Relationship to current alert and entities |
| **Hypothesis Impact** | Ability to confirm or reject a hypothesis |
| **Cost** | Processing time or latency |
| **Redundancy** | Penalty if the action was already attempted |

---

# 9. Deterministic Action Filter

Before an action is executed, it passes through policy validation:

```text
Planner Decision
       │
       ▼
Action Validator
       │
       ├── Allowed?
       │
       ├── Budget Available?
       │
       ├── Duplicate?
       │
       └── Valid Parameters?
              │
        ┌─────┴─────┐
        ▼           ▼
      ACCEPT      REJECT
        │           │
        ▼           ▼
     EXECUTE     REPLAN
```

This prevents invalid LLM decisions from directly affecting the workflow.

---

# 10. Capability Architecture

A capability is a specialized service that performs a defined investigation task.

Every capability follows the same conceptual contract:

```text
INPUT
  │
  ▼
VALIDATE
  │
  ▼
EXECUTE
  │
  ▼
STRUCTURED RESULT
```

A capability should not:
- Make final investigation decisions.
- Directly change the global investigation state.
- Call another capability without orchestration approval.

---

# 11. Base Capability Contract

Each capability exposes:

```text
Capability
│
├── capability_id
├── name
├── description
│
├── input_schema
├── output_schema
│
├── cost_estimate
├── timeout
│
└── execute()
```

This makes capabilities discoverable and replaceable.

---

# 12. Capability Result Contract

Every capability returns a standardized result:

```text
CapabilityResult
│
├── execution_id
├── capability_id
├── status
│
├── findings
├── evidence
├── confidence
│
├── limitations
├── execution_time
│
└── error
```

Status values:
```text
SUCCESS
PARTIAL_SUCCESS
NO_FINDINGS
FAILED
TIMEOUT
```

A failed capability should still return useful structured information about the failure.

---

# 13. Correlation Capability

## Purpose
Analyzes relationships between telemetry events:
- Common entities
- Temporal relationships
- Process parent-child relationships
- Network relationships
- Related alert activity

## Workflow
```text
Investigation Context
        │
        ▼
Select Relevant Events
        │
        ▼
Extract Entities
        │
        ▼
Apply Correlation Rules
        │
        ▼
Rank Relationships
        │
        ▼
Return Findings
```

## Contracts
- **Input (`CorrelationRequest`)**: `investigation_id`, `seed_events`, `entities`, `time_window`, `correlation_parameters`.
- **Output (`CorrelationResult`)**: `related_events`, `discovered_entities`, `relationships`, `timeline`, `confidence`.

---

# 14. Knowledge Capability

## Purpose
Provides contextual domain information from MITRE ATT&CK, threat intelligence, and documentation. It does not generate evidence of what occurred; it provides knowledge to help interpret evidence:

```text
TELEMETRY ────► Evidence of What Happened
KNOWLEDGE ────► Context About What It May Mean
```

## Contracts
- **Input (`KnowledgeRequest`)**: `investigation_context`, `query`, `entity_context`, `retrieval_limit`.
- **Output (`KnowledgeResult`)**: `retrieved_documents`, `relevance_scores`, `source_metadata`, `limitations`.

---

# 15. Evidence Validation Capability

## Purpose
Evaluates whether findings and claims are sufficiently supported:
- Is the claim supported?
- What empirical evidence supports it?
- What evidence contradicts it?
- What remains uncertain?

## Contracts
- **Output (`ValidationResult`)**: `claim`, `supporting_evidence`, `conflicting_evidence`, `validation_status`, `confidence`.

---

# 16. State Manager

The State Manager is the authoritative controller of investigation state:
```text
Validate Updates ──► Merge Results ──► Version State ──► Persist Changes ──► Maintain History
```

The Planner does not own the state. Capabilities do not own the state. **The State Manager owns the state.**

---

# 17. State Update Flow

```text
CAPABILITY RESULT
        │
        ▼
RESULT VALIDATION
        │
        ▼
STATE UPDATE REQUEST
        │
        ▼
STATE MANAGER
        │
        ├── Schema Validation
        ├── Reference Validation
        ├── Version Check
        │
        ▼
NEW STATE VERSION
```

Every state mutation generates an incremented version and an immutable audit event.

---

# 18. Investigation Memory

Investigation memory is partitioned into 4 distinct stores:

```text
INVESTIGATION MEMORY
│
├── Structured State      (Current facts, entities, hypotheses)
│
├── Evidence Store        (Raw/normalized empirical artifacts)
│
├── Decision History      (Action requests, justifications, scores)
│
└── Knowledge Context     (Retrieved MITRE ATT&CK / threat intel context)
```

---

# 19. Decision History

Every Planner decision is immutably logged:

```text
DecisionRecord
│
├── timestamp
├── state_version
├── evidence_gaps
├── candidate_actions
├── selected_action
├── rationale
└── outcome
```

---

# 20. Policy Controller

The Policy Controller is deterministic and verifies:
- Capability exists in the registry.
- Parameters conform to schema.
- Action is permitted under active RBAC and safety rules.
- Budget remains.
- Action is not duplicate/redundant.

---

# 21. Investigation Budget

Limits prevent runaway execution:

```text
InvestigationBudget
│
├── maximum_steps
├── maximum_capability_calls
├── maximum_duration
└── maximum_retries
```

---

# 22. Termination Controller

Evaluates whether to continue or stop based on:
- Evidence Sufficiency
- Confidence Threshold
- Remaining High-Priority Gaps
- Budget Depletion
- Human Review Triggers

Possible outcomes:
```text
RESOLVED
INCONCLUSIVE
ESCALATED
BUDGET_EXHAUSTED
FAILED
```

---

# 23. Human Escalation

Autonomous investigation pauses and escalates when:
- Confidence remains low despite budget usage.
- Evidence exhibits unresolved contradictions.
- Critical evidence cannot be acquired.
- Budget is exhausted without resolution.
- Policy mandates human oversight (e.g., destructive actions).

---

# 24. Confidence Model

Confidence combines empirical support and uncertainty reduction:

```text
Investigation Confidence = Evidence Support + Consistency + Coverage - Uncertainty
```

Confidence is strictly mathematical and explainable; it is never based solely on LLM self-assessment.

---

# 25. Failure Handling Architecture

```text
COMPONENT FAILURE
       │
       ▼
DETECT
       │
       ▼
CLASSIFY
       │
       ▼
RETRY?
       │
   ┌───┴────┐
   ▼        ▼
  YES       NO
   │        │
RETRY    FALLBACK
            │
            ▼
       DEGRADE / ESCALATE
```

- **Planner Failure**: Preserve state, log error, retry up to limit, fallback to deterministic heuristic planner, escalate if needed.
- **Capability Failure**: Record error, attempt retry or alternative capability, continue with recorded limitation.
- **Knowledge Failure**: Record limitation, continue evidence-based investigation without RAG, discount contextual confidence.

---

# 26. Complete Investigation Sequence

```text
1. ALERT CREATED
        │
        ▼
2. INVESTIGATION INITIALIZED
        │
        ▼
3. STATE ASSESSED
        │
        ▼
4. EVIDENCE GAPS IDENTIFIED
        │
        ▼
5. CANDIDATE ACTIONS GENERATED
        │
        ▼
6. ACTION SCORED
        │
        ▼
7. POLICY VALIDATION
        │
        ▼
8. CAPABILITY EXECUTION
        │
        ▼
9. RESULT VALIDATION
        │
        ▼
10. STATE UPDATED
        │
        ▼
11. TERMINATION CHECK
        │
    ┌───┴────┐
    ▼        ▼
 CONTINUE    STOP
    │         │
    └─────────┘
```

---

# 27. Responsibility Matrix

| Component | Thinks | Decides | Executes | Stores Truth |
|---|---|---|---|---|
| **Planner** | Yes | Yes | No | No |
| **Policy Controller** | No | Validates | No | No |
| **Capability** | Limited | No | Yes | No |
| **Result Validator** | Evaluates | No | No | No |
| **State Manager** | No | No | No | Yes |
| **Termination Controller** | Rule-based | Stops/continues | No | No |

---

# 28. Recommended Implementation Priority

```text
1. State Manager
       ↓
2. Capability Contract
       ↓
3. Capability Registry
       ↓
4. Policy Controller
       ↓
5. Deterministic Planner
       ↓
6. LLM Planner
       ↓
7. Action Scoring
       ↓
8. Termination Controller
       ↓
9. Failure Recovery
```

---

# 29. Central Architectural Principle

```text
                 ┌─────────────────┐
                 │  CURRENT STATE  │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │     PLANNER     │
                 │ "What is next?" │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ POLICY CONTROL  │
                 │ "Is it allowed?"│
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │   CAPABILITY    │
                 │ "Do the work."  │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ STATE MANAGER   │
                 │ "Update truth." │
                 └────────┬────────┘
                          │
                          └───────────► Repeat
```

> **Intelligence determines what information is needed. Specialized capabilities obtain or analyze that information. Deterministic controls constrain execution. The investigation state preserves the evidence-based truth.**
