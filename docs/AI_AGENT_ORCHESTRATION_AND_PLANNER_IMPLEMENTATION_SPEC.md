# Project Sentinel — AI Agent Orchestration & Planner Implementation Specification (AOPIS)

**Document Type:** Core Technical Design Specification  
**Version:** 1.0  
**Status:** Architecture Baseline  
**Primary Focus:** AI orchestration, Planner design, agent coordination, LangGraph workflow, context management, replanning, guardrails, and evaluation.  
**Related Components:** LangGraph Orchestration Core, AI Planner, Policy Engine, Capability Registry, State Manager, Outcome Evaluator

---

# 1. Purpose

The **AI Agent Orchestration Layer** is the central intelligence of Project Sentinel.

Detection engines identify suspicious activity. Correlation engines identify relationships. Capabilities retrieve and process information.

The orchestration layer determines:
- What should be investigated next.
- Which evidence gaps are most important.
- Which capability should be used.
- What information is sufficient to support a conclusion.
- When the investigation should continue.
- When the investigation should stop.
- When the case should be escalated to an analyst.

> **The AI system does not directly control infrastructure. It reasons over the investigation state and selects controlled actions through the Capability Layer.**

---

# 2. Core Orchestration Philosophy

Project Sentinel avoids multi-agent sprawl by employing a **planner-centered orchestration model**:

```text
                         INVESTIGATION
                             INPUT
                                │
                                ▼
                    ┌─────────────────────┐
                    │   ORCHESTRATOR      │
                    │                     │
                    │ Controls workflow   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │       PLANNER       │
                    │                     │
                    │ Determines next     │
                    │ investigation step  │
                    └──────────┬──────────┘
                               │
               ┌───────────────┼────────────────┐
               ▼               ▼                ▼
          Evidence         Capability        Termination
           Analysis         Selection          Decision
               │               │                │
               └───────────────┼────────────────┘
                               ▼
                     CONTROLLED EXECUTION
```

The Planner is the **decision-making component**, not the owner of system execution.

---

# 3. Agent Architecture

```text
                         ┌──────────────────┐
                         │   ORCHESTRATOR   │
                         └────────┬─────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │          PLANNER          │
                    │                           │
                    │ Objective                 │
                    │ Evidence Gaps             │
                    │ Action Selection          │
                    └─────────────┬─────────────┘
                                  │
              ┌───────────────────┼────────────────────┐
              ▼                   ▼                    ▼
     ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
     │ Evidence        │  │ Knowledge      │  │ Outcome        │
     │ Reasoning       │  │ Context        │  │ Evaluation     │
     │ Component       │  │ Component      │  │ Component      │
     └────────────────┘  └────────────────┘  └────────────────┘
              │                   │                    │
              └───────────────────┼────────────────────┘
                                  ▼
                           PLANNER DECISION
```

### Responsibility Breakdown:
- **Orchestrator**: Controls workflow and state transitions across the graph.
- **Planner**: Identifies evidence gaps and selects next candidate actions.
- **Evidence Evaluator**: Evaluates claim support, corroboration, and contradictions.
- **Knowledge Context**: Retrieves contextual domain information without fabricating evidence.
- **Outcome Evaluator**: Checks stop conditions, evidence coverage, and confidence.
- **Capability Layer**: Executes controlled operations and returns validated results.

---

# 4. LangGraph 10-Node Workflow

LangGraph manages the investigation workflow as a stateful, cyclic directed graph:

```text
1. initialize_investigation
2. analyze_investigation_state
3. evaluate_evidence
4. planner
5. policy_check
6. execute_capability
7. validate_result
8. update_investigation_state
9. evaluate_outcome
10. finalize_or_escalate
```

```text
                ┌─────────────────────────────────┐
                │ 1. initialize_investigation     │
                └───────────────┬─────────────────┘
                                │
                                ▼
                ┌─────────────────────────────────┐
                │ 2. analyze_investigation_state  │
                └───────────────┬─────────────────┘
                                │
                                ▼
                ┌─────────────────────────────────┐
                │ 3. evaluate_evidence            │
                └───────────────┬─────────────────┘
                                │
                                ▼
                ┌─────────────────────────────────┐
                │ 4. planner                      │
                └───────────────┬─────────────────┘
                                │
                                ▼
                ┌─────────────────────────────────┐
                │ 5. policy_check                 │
                └───────┬─────────────────┬───────┘
                        │ Approved        │ Rejected
                        ▼                 ▼
        ┌─────────────────────────┐  ┌──────────────┐
        │ 6. execute_capability   │  │ Replan Path  │
        └───────────────┬─────────┘  └──────┬───────┘
                        │                   │
                        ▼                   │
        ┌─────────────────────────┐         │
        │ 7. validate_result      │         │
        └───────────────┬─────────┘         │
                        │                   │
                        ▼                   │
        ┌─────────────────────────┐         │
        │ 8. update_state         │         │
        └───────────────┬─────────┘         │
                        │                   │
                        ▼                   │
        ┌─────────────────────────┐         │
        │ 9. evaluate_outcome     │         │
        └───────┬─────────────────┘         │
                │                           │
          ┌─────┴──────┬────────────┐       │
          ▼            ▼            ▼       │
       COMPLETE     ESCALATE     REPLAN ◄───┘
          │            │            │
          ▼            ▼            └───────► (Back to Node 2)
  10. finalize_or_escalate
```

---

# 5. Node Specifications

## 5.1 Node 1 — `initialize_investigation`
- **Input**: `alert_id`, `triggering_event_ids`.
- **Responsibilities**: Assign UUID `investigation_id`, load triggering telemetry, initialize step and time budgets, commit State Version 1.

## 5.2 Node 2 — `analyze_investigation_state`
Prepares a compact, token-budgeted `ContextPackage`:

```json
{
  "investigation_id": "INV-001",
  "objective": "Determine whether the alert represents the defined attack scenario.",
  "confirmed_facts": [],
  "active_hypotheses": [],
  "evidence_gaps": [],
  "conflicting_evidence": [],
  "previous_actions": [],
  "available_capabilities": [],
  "remaining_budget": {
    "actions": 8,
    "model_calls": 6
  }
}
```

## 5.3 Node 3 — `evaluate_evidence`
Calculates empirical evidence strength ($E_s$), corroboration ($C$), and evidence coverage:
$$\text{Coverage} = \frac{G_r}{G_t}$$

### Gap Prioritization Formula:
$$G_p = 0.50I + 0.30U + 0.20R$$
Where $I$ is investigation impact, $U$ is uncertainty reduction potential, and $R$ is relevance to the investigation objective.

## 5.4 Node 4 — `planner`
Produces a machine-validated `PlannerDecision`:

```json
{
  "decision_type": "execute_action",
  "selected_capability": "event_query",
  "parameters": {
    "entity": "host-01",
    "time_window_minutes": 30
  },
  "target_evidence_gap": "GAP-001",
  "expected_information_gain": 0.75,
  "priority": "high",
  "reason_summary": "Retrieve related activity to address the highest-priority unresolved evidence gap.",
  "confidence": 0.82
}
```

## 5.5 Node 5 — `policy_check`
Validates schema compliance, capability enablement, budget limits, and loop prevention signatures.

## 5.6 Node 6 — `execute_capability`
Passes authorized requests to the capability executor under timeout and circuit breaker controls.

## 5.7 Node 7 — `validate_result`
Verifies source lineage, status codes, and non-empty payload integrity.

## 5.8 Node 8 — `update_investigation_state`
Applies atomic state mutation under optimistic locking ($\text{ExpectedVersion} = \text{CurrentVersion}$).

## 5.9 Node 9 — `evaluate_outcome`
Evaluates termination criteria: Auto-Resolve ($\ge 0.85$ confidence + $\ge 0.80$ coverage), Analyst Review ($0.60 - 0.84$), Inconclusive ($< 0.60$), or Continue/Replan.

## 5.10 Node 10 — `finalize_or_escalate`
Produces final report, sets terminal state, and notifies analysts if escalation is triggered.

---

# 6. Loop Prevention Mechanism

To prevent infinite loops and repeated actions:

```json
{
  "action_signature": "event_query:host-01:30min",
  "execution_count": 2,
  "useful_result_count": 0,
  "last_result": "no_result"
}
```

$$\text{IF } \text{execution\_count} \ge 2 \land \text{useful\_result\_count} = 0 \implies \text{Reduce priority to } 0 \text{ \& enforce alternative action.}$$

---

# 7. Tri-Partitioned Memory & Context Management

```text
┌────────────────────────────────────────────────────────┐
│ ACTIVE CONTEXT (Working Memory)                        │
│ Objective • Active Facts • Top Gaps • Budget           │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ INVESTIGATION MEMORY (Incident State)                  │
│ Full Action History • Evidence References • Versions   │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ LONG-TERM STORAGE (Cold / Reference)                   │
│ Raw Telemetry • MITRE ATT&CK • Audit Log Chains        │
└────────────────────────────────────────────────────────┘
```

The Planner receives **only** the active context package, preventing context window saturation and reasoning degradation.

---

# 8. Hallucination Control Taxonomy

Every proposition in the investigation belongs to a strict epistemic category:

1. **FACT**: Must have an explicit `evidence_id` referencing a canonical telemetry event.
2. **HYPOTHESIS**: Explicitly tagged as unconfirmed; subject to verification or rejection.
3. **INTERPRETATION**: Analytical reasoning that links observed facts to MITRE patterns.
4. **KNOWLEDGE CONTEXT**: Background information retrieved via RAG; can *never* become empirical evidence of an incident on its own.

---

# 9. Planner Performance Metrics

$$\text{Action Efficiency} = \frac{\text{Useful Actions}}{\text{Total Actions}}$$

$$\text{Gap Resolution Rate} = \frac{\text{Resolved Gaps}}{\text{Total Identified Gaps}}$$

$$\text{Unproductive Action Rate} = \frac{\text{Actions With No Useful Result}}{\text{Total Actions}}$$

$$\text{Completion Rate} = \frac{\text{Completed Investigations}}{\text{Total Investigations}}$$

---

# 10. Final Architecture Principle

> **The Planner decides what to investigate. Evidence determines what can be concluded. Capabilities perform controlled operations. Policies enforce boundaries. The state preserves continuity.**
