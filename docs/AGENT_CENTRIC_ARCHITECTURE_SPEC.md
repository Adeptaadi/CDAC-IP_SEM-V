# Project Sentinel — Agent-Centric Architecture Upgrade Specification

**Document Type:** Architecture Upgrade Specification  
**Version:** 1.0  
**Status:** Proposed  
**Architecture Focus:** Adaptive Multi-Agent Orchestration  
**Primary Principle:** Evidence-Guided, Non-Linear Investigation

---

# 1. Introduction

## 1.1 Purpose
This document defines the formal architectural upgrade specification for **Project Sentinel**.

The purpose of this upgrade is to reposition the system from a collection of cybersecurity detection, analysis, and AI components into an **orchestration-centric cybersecurity investigation platform**.

In the upgraded architecture, the central intelligence of the system is the **Agent Orchestration Core**.

Detection models, correlation engines, graph analysis, retrieval-augmented generation, databases, reporting components, and other services are treated as specialized capabilities that support the orchestrator.

### Primary Principle
> **Project Sentinel should not execute a predefined sequence of security analysis agents. It should dynamically determine what information is required, select the most appropriate capability, evaluate the result, update its understanding, and adapt the investigation accordingly.**

The resulting system is an **adaptive, evidence-driven, stateful multi-agent investigation architecture**.

---

# 2. Architectural Motivation

## 2.1 Limitations of a Conventional Pipeline
A conventional cybersecurity analysis system follows a fixed sequence:
`Telemetry` $\to$ `Detection` $\to$ `Correlation` $\to$ `Investigation` $\to$ `Report`.

While simple, it assumes every incident requires the same sequence. Real investigations are non-linear:
- Incident A: Correlation may provide sufficient evidence immediately.
- Incident B: External knowledge is required before deeper correlation can be performed.
- Incident C: New evidence contradicts the initial hypothesis, requiring backtracking to earlier assumptions.

## 2.2 Limitations of a Simple Multi-Agent System
Placing multiple LLM agents in a fixed chain (`Alert` $\to$ `Agent A` $\to$ `Agent B` $\to$ `Agent C`) does not make a system genuinely agentic—it remains a rigid linear pipeline.

## 2.3 Target Architecture: The Orchestration Loop
```text
                 ┌───────────────────────────┐
                 │   SECURITY INVESTIGATION  │
                 │         STATE             │
                 └─────────────┬─────────────┘
                               │
                               ▼
                 ┌───────────────────────────┐
                 │   ORCHESTRATION CORE      │
                 │                           │
                 │ Understand current state  │
                 │ Identify evidence gaps    │
                 │ Select next capability    │
                 │ Validate proposed action  │
                 └─────────────┬─────────────┘
                               │
                               ▼
                    Execute Capability
                               │
                               ▼
                     Structured Result
                               │
                               ▼
                    Update Investigation
                               │
                               ▼
                     Re-plan or Terminate
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
                 Continue              Finalize
```

---

# 3. Architectural Vision & Component Roles

## 3.1 System Identity
> **An evidence-driven, adaptive multi-agent cybersecurity investigation platform that dynamically coordinates specialized analytical capabilities based on the evolving state of an investigation.**

## 3.2 Role Repositioning Matrix
| Component | Traditional Pipeline Role | Upgraded Agent-Centric Role |
| :--- | :--- | :--- |
| **ML Detection** | Final attack classifier | Signal provider to the orchestrator |
| **Correlation Engine** | Fixed processing stage | On-demand evidence discovery capability |
| **Graph Analysis** | Independent analytics feature | Relationship & attack-path traversal capability |
| **RAG** | AI chatbot knowledge source | Context provider for investigation decisions |
| **Database (PostgreSQL)** | Raw event data store | Persistent investigation memory & state checkpoints |
| **Redis** | General cache | Operational coordination & task bus support |
| **Reporting** | Final pipeline stage | Presentation capability after validated conclusions |

---

# 4. System Architecture Blueprint

```text
╔════════════════════════════════════════════════════════════════════╗
║                         PROJECT SENTINEL                           ║
║       ADAPTIVE, EVIDENCE-DRIVEN AGENTIC INVESTIGATION SYSTEM       ║
╚════════════════════════════════════════════════════════════════════╝

                     ┌─────────────────────────┐
                     │   SECURITY SIGNALS      │
                     │  Detection / Alerts     │
                     └────────────┬────────────┘
                                  │
                                  ▼
              ┌────────────────────────────────────┐
              │     INVESTIGATION STATE LAYER      │
              │ Events • Evidence • Hypotheses     │
              │ Entities • Timeline • Confidence   │
              │ Tasks • Failures • Audit History   │
              └──────────────────┬─────────────────┘
                                 │
                                 ▼
        ┌──────────────────────────────────────────────┐
        │           ORCHESTRATION CORE                 │
        │  State Interpretation                        │
        │  Evidence Gap Analysis                       │
        │  Capability Selection                        │
        │  Action Validation                           │
        │  Replanning                                  │
        │  Termination and Escalation                  │
        └──────────────────────┬───────────────────────┘
                               │
       ┌───────────────────────┼────────────────────────┐
       │                       │                        │
       ▼                       ▼                        ▼
┌───────────────┐      ┌────────────────┐      ┌────────────────┐
│ CORRELATION   │      │ INVESTIGATION  │      │ KNOWLEDGE      │
│ CAPABILITY    │      │ CAPABILITY     │      │ CAPABILITY     │
└───────────────┘      └────────────────┘      └────────────────┘
       │                       │                        │
       ▼                       ▼                        ▼
┌───────────────┐      ┌────────────────┐      ┌────────────────┐
│ GRAPH / ENTITY│      │ EVIDENCE       │      │ RAG / SECURITY │
│ ANALYSIS      │      │ VALIDATION     │      │ KNOWLEDGE      │
└───────────────┘      └────────────────┘      └────────────────┘
                               │
                               ▼
                  ┌──────────────────────────┐
                  │  FINAL DECISION LAYER    │
                  │ Continue / Finalize /    │
                  │ Escalate / Respond       │
                  └─────────────┬────────────┘
                                ▼
                    Analyst Report / UI
```

---

# 5. The Orchestration Core: 6 Operational Questions

During every investigation cycle, the Orchestration Core resolves six explicit questions:

1. **What do we currently know?** (Examine events, entities, collected evidence, active hypotheses, and previous failures).
2. **What information is missing?** (Identify explicit evidence gaps, e.g., missing parent process, unverified C2 connection).
3. **Which capability can reduce this uncertainty?** (Goal-driven capability selection based on information needs).
4. **Is the proposed action valid?** (Deterministic verification of capability existence, parameters, retry limits, budget, and approval requirements).
5. **Did the action improve the investigation?** (Evaluate whether findings supported/contradicted hypotheses, failed, or revealed new gaps).
6. **Should the investigation continue?** (Determine whether to loop, re-plan, escalate to a human analyst, or finalize).

---

# 6. Investigation State Architecture

To ensure auditability, predictability, and reproducibility, the system **strictly avoids free-form agent-to-agent chatter**. All capability outputs pass through the structured `InvestigationState`:

```text
InvestigationState
├── Identity (investigation_id, incident_id, status)
├── Trigger (source, alert, initial events)
├── Investigation Context (events, entities, timeline)
├── Evidence (observations, supporting evidence, contradictory evidence)
├── Reasoning Context (hypotheses, evidence gaps, uncertainty)
├── Execution Context (completed tasks, pending tasks, failed tasks, retries)
├── Confidence (detection confidence, evidence sufficiency, investigation confidence)
├── Controls (step budget, time budget, escalation status)
└── Audit (decision history)
```

---

# 7. Tripartite Confidence Architecture

The platform rejects conflating multiple uncertainties into a single number:

```text
┌──────────────────────────┐
│   DETECTION CONFIDENCE   │  Probability from ML classifier / Sigma rules
└─────────────┬────────────┘
              │  (Does NOT prove an incident occurred)
              ▼
┌──────────────────────────┐
│   EVIDENCE SUFFICIENCY   │  Completeness ratio against hypothesis requirements
└─────────────┬────────────┘
              │  (Factual coverage, independent of LLM self-reporting)
              ▼
┌──────────────────────────┐
│ INVESTIGATION CONFIDENCE │  Posterior strength (evidence quality, lack of contradictions,
└──────────────────────────┘  validation checks)
```

---

# 8. Specialized Capabilities Catalog

1. **Correlation Capability:** Discovers related events across hosts, network flows, and time boundaries.
2. **Investigation Capability:** Evaluates collected evidence against candidate attack hypotheses.
3. **Knowledge Capability (RAG):** Context provider for ATT&CK techniques, CVEs, and playbooks.
   - *Core Invariant:* $\text{Observed Evidence} \neq \text{Retrieved Knowledge}$.
4. **Graph Analysis Capability (NetworkX):** Traverses attack paths and computes entity blast radius on demand.
5. **Evidence Validation Capability:** Strictly verifies whether proposed claims have raw evidence backing and lack unresolved contradictions before finalization.

---

# 9. Non-Linear Workflow Demonstrations

The architecture enables dynamic, scenario-dependent paths:

```text
Scenario A (Simple):
Alert ──► Correlation ──► Evidence Sufficient? [Yes] ──► Validate ──► Finalize

Scenario B (Context-Dependent):
Alert ──► Investigation ──► Context Missing ──► Knowledge Retrieval ──► Correlation ──► Validate ──► Finalize

Scenario C (Contradictory / Backtracking):
Alert ──► Investigation ──► Contradictory Evidence ──► Update Hypothesis ──► Graph Analysis ──► Re-plan ──► Further Investigation
```

---

# 10. Hybrid Decision Architecture & Failure Recovery

## 10.1 Division of Control
- **Adaptive Reasoning (LLM):** Ambiguous state interpretation, evidence gap generation, hypothesis formulation.
- **Deterministic Control (Python Rules):** Schema validation, execution budgets, step ceilings, retry limits, containment approval gates.

## 10.2 Failure Recovery Flow
```text
Capability Execution ──► Failure ──► Record Failure in State
                                           │
                           Retry Available? ├── Yes ──► Bounded Retry
                                           │
                                           └── No ───► Alternative Capability
                                                              │
                                                              └──► Human Escalation
```

---

# 11. Core Implementation Principles

1. **Orchestration Is the Core:** The primary value is adaptive investigation routing.
2. **State Is Explicit:** State is structured, versioned, and inspectable.
3. **Workers Are Specialized:** Capabilities have narrow, bounded execution scopes.
4. **Evidence Is Traceable:** Every claim in the report must map to concrete raw evidence IDs.
5. **Knowledge Is Not Evidence:** External documentation provides context, never proof of occurrence.
6. **Adaptation Must Be Bounded:** Explicit limits prevent runaway agent loops.
7. **Failures Must Be Preserved:** State is preserved even when individual workers fail.
8. **Improvements Must Be Measured:** Adaptive routing is scientifically compared against a fixed baseline.
