# Project Sentinel — Detailed Implementation Roadmap & Development Blueprint (DIRDB)

**Document Type:** Master Implementation Specification  
**Version:** 1.0  
**Status:** Proposed Architecture Upgrade  
**Primary Focus:** Development phases, implementation order, repository structure, milestones, integration, testing, and delivery  
**Related Components:** Ingestion Pipeline, Investigation State, Orchestration Core, Capabilities, Analyst UI, Evaluation Engine

---

# 1. Purpose

Project Sentinel contains several interconnected technical systems:

- Telemetry ingestion
- Event normalization
- Detection and alerting
- Investigation state management
- AI-driven orchestration
- Specialized investigation capabilities
- Knowledge retrieval
- Evidence validation
- Human analyst interaction
- Evaluation infrastructure

Attempting to build all components simultaneously would create unnecessary integration risk.

This roadmap defines the correct implementation dependency order.

The central development principle is:

> **Build a reliable investigation state and orchestration foundation first. Add intelligence and supporting capabilities incrementally.**

The recommended progression is:

```text
FOUNDATION
    ↓
DATA PIPELINE
    ↓
INVESTIGATION STATE
    ↓
ORCHESTRATION CORE
    ↓
CAPABILITIES
    ↓
AI ENHANCEMENT
    ↓
USER EXPERIENCE
    ↓
EVALUATION
```

---

# 2. Development Strategy

The project should not begin with the frontend or the LLM.

The core system should be developed from the inside outward.

```text
                  ┌─────────────────────┐
                  │   FRONTEND / UI     │
                  └──────────┬──────────┘
                             │
                  ┌──────────▼──────────┐
                  │     FASTAPI API     │
                  └──────────┬──────────┘
                             │
              ┌──────────────▼──────────────┐
              │     ORCHESTRATION CORE      │
              │                              │
              │ State + Planner + Policy     │
              └──────────────┬──────────────┘
                             │
                ┌────────────┼────────────┐
                ▼            ▼            ▼
           CAPABILITIES   DATA LAYER    KNOWLEDGE
```

The **Orchestration Core** is the architectural center.

Everything else either:
1. Supplies information to it,
2. Executes work for it, or
3. Presents its results.

---

# 3. Recommended Repository Structure

A modular monorepo structure is recommended.

```text
project-sentinel/
│
├── .env.example
├── docker-compose.yml
├── README.md
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   │
│   └── app/
│       │
│       ├── main.py
│       ├── config.py
│       │
│       ├── api/
│       │   ├── routes/
│       │   │   ├── investigations.py
│       │   │   ├── alerts.py
│       │   │   └── health.py
│       │
│       ├── domain/
│       │   ├── events.py
│       │   ├── alerts.py
│       │   ├── investigations.py
│       │   ├── evidence.py
│       │   └── hypotheses.py
│       │
│       ├── orchestration/
│       │   ├── graph.py
│       │   ├── planner.py
│       │   ├── state_manager.py
│       │   ├── policy.py
│       │   ├── termination.py
│       │   └── scoring.py
│       │
│       ├── capabilities/
│       │   ├── base.py
│       │   ├── registry.py
│       │   ├── correlation.py
│       │   ├── knowledge.py
│       │   └── validation.py
│       │
│       ├── ingestion/
│       │   ├── parser.py
│       │   ├── normalizer.py
│       │   └── loaders/
│       │
│       ├── detection/
│       │   ├── rules.py
│       │   └── service.py
│       │
│       ├── knowledge/
│       │   ├── retrieval.py
│       │   ├── embeddings.py
│       │   └── documents.py
│       │
│       ├── persistence/
│       │   ├── database.py
│       │   ├── models/
│       │   └── repositories/
│       │
│       ├── services/
│       │   ├── investigation_service.py
│       │   └── evaluation_service.py
│       │
│       └── tests/
│
├── frontend/
│   ├── Dockerfile
│   └── src/
│       ├── pages/
│       ├── components/
│       └── services/
│
├── evaluation/
│   ├── scenarios/
│   ├── baselines/
│   ├── metrics/
│   └── experiments/
│
└── docs/
```

This structure separates:
- Domain logic
- Infrastructure
- Orchestration
- Capabilities
- Evaluation

---

# 4. Development Phases

The recommended implementation contains eight phases.

| Phase | Focus |
|---|---|
| 0 | Architecture freeze and environment |
| 1 | Domain models and data pipeline |
| 2 | Investigation state foundation |
| 3 | Deterministic orchestration baseline |
| 4 | Capability framework |
| 5 | Adaptive AI orchestration |
| 6 | Frontend and analyst workflow |
| 7 | Evaluation and experimental validation |

The phases should be completed in dependency order.

---

# PHASE 0 — Architecture Freeze & Environment

## Objective

Create a stable development environment before implementing business logic.

### 4.1 Required Services

The initial environment should contain:

```text
Docker Compose
│
├── PostgreSQL
├── Redis
├── Backend
├── Frontend
└── ChromaDB (when knowledge retrieval begins)
```

Ollama should be configured according to the final deployment decision.

### 4.2 Environment Verification

Before development continues, verify:

```text
Backend Health Endpoint        ✓
PostgreSQL Connection          ✓
Redis Connection               ✓
Frontend Startup               ✓
Container Networking           ✓
```

Do not implement complex functionality until the basic environment is stable.

### Phase 0 Deliverables

- Docker Compose environment
- Environment configuration
- FastAPI bootstrap
- PostgreSQL connectivity
- Basic frontend
- Health checks

---

# PHASE 1 — Domain Models & Data Pipeline

## Objective

Create the structured data foundation.

The system should first understand:

```text
What is an event?
What is an alert?
What is an investigation?
What is evidence?
```

### 5.1 Implement Pydantic Domain Models

Initial models:

```text
NormalizedEvent
Alert
Investigation
Evidence
Hypothesis
InvestigationState
ActionRequest
CapabilityResult
```

These models should be implemented before complex services.

### 5.2 Dataset Adapter

The selected dataset should not directly determine the entire application architecture.

Instead:

```text
Dataset
   │
   ▼
Dataset Adapter
   │
   ▼
Normalization Layer
   │
   ▼
NormalizedEvent
```

This allows future datasets to use different adapters.

### 5.3 Initial Dataset Workflow

```text
Dataset File
    │
    ▼
Loader
    │
    ▼
Parser
    │
    ▼
Normalizer
    │
    ▼
Validation
    │
    ▼
Normalized Event Store
```

The output must preserve a reference to the original dataset record.

### Phase 1 Deliverables

- Dataset loader
- Parser
- Normalization layer
- Event validation
- Normalized event storage
- Unit tests

---

# PHASE 2 — Investigation State Foundation

## Objective

Build the canonical state model before building adaptive agents. This is one of the most important phases.

### 6.1 State Manager

The State Manager controls investigation state updates.

```text
Current State
      │
      ▼
Proposed Change
      │
      ▼
Validate
      │
      ▼
Merge
      │
      ▼
Version
      │
      ▼
Persist
```

Capabilities should not directly modify the state.

### 6.2 Initial Investigation Lifecycle

Implement:

```text
CREATED
   ↓
QUEUED
   ↓
RUNNING
   ↓
WAITING_REVIEW
   ↓
FINALIZED
```

Additional outcomes:
```text
INCONCLUSIVE
ESCALATED
FAILED
```

### 6.3 State Persistence

Initially store:
- Investigation metadata
- Current state version
- Evidence
- Hypotheses
- Action history
- Final outcome

PostgreSQL should remain the authoritative persistent store.

### Phase 2 Deliverables

- Investigation database schema
- State Manager
- State versioning
- Investigation lifecycle
- Audit records
- State integrity tests

---

# PHASE 3 — Deterministic Orchestration Baseline

## Objective

Build a non-AI baseline before introducing adaptive planning. This is critical for both engineering and evaluation.

### 7.1 Baseline Workflow

```text
Alert
  │
  ▼
Create Investigation
  │
  ▼
Run Correlation
  │
  ▼
Run Validation
  │
  ▼
Generate Outcome
```

The sequence is fixed.

### 7.2 Why Build This First?

It provides:

```text
Working Investigation Pipeline
          +
Integration Baseline
          +
Experimental Comparison
          +
Fallback Architecture
```

If the AI Planner fails, a controlled deterministic workflow can serve as a fallback.

### Phase 3 Deliverables

- Fixed workflow engine
- Basic action execution
- Baseline investigation results
- Baseline metrics

---

# PHASE 4 — Capability Framework

## Objective

Create reusable investigation capabilities. The capabilities perform work; they do not control the investigation.

### 8.1 Capability Base Interface

Conceptually:

```text
Capability
│
├── name
├── input_schema
├── output_schema
└── execute()
```

Every capability follows the same contract.

### 8.2 Capability Registry

```text
Orchestrator
     │
     ▼
Capability Registry
     │
 ┌───┼────┐
 ▼   ▼    ▼
C1  C2   C3
```

The Orchestrator selects a capability by name and contract. It does not need to understand implementation details.

### 8.3 First Capabilities

Start with a small set:
- **Correlation Capability**: Find relationships between events.
- **Knowledge Capability**: Retrieve contextual security information.
- **Validation Capability**: Check whether findings are supported.

Do not add many capabilities initially.

### Phase 4 Deliverables

- Base capability interface
- Registry
- Correlation capability
- Knowledge capability
- Validation capability
- Capability result validation

---

# PHASE 5 — Adaptive AI Orchestration

## Objective

Introduce the project's central intelligence layer. Only begin this phase when the deterministic pipeline works.

### 9.1 Orchestration Loop

The core loop is:

```text
READ STATE
    │
    ▼
ASSESS EVIDENCE
    │
    ▼
IDENTIFY GAPS
    │
    ▼
SELECT ACTION
    │
    ▼
VALIDATE ACTION
    │
    ▼
EXECUTE CAPABILITY
    │
    ▼
UPDATE STATE
    │
    ▼
REASSESS
```

### 9.2 Planner Implementation

The Planner receives a controlled state summary. It produces:
- Assessment
- Evidence Gaps
- Candidate Actions
- Selected Action
- Rationale
- Termination Recommendation

The Planner must produce structured output.

### 9.3 Hybrid Decision Strategy

The recommended implementation is not purely LLM-driven.

```text
                    DECISION ENGINE
                           │
              ┌────────────┼────────────┐
              ▼                         ▼
      DETERMINISTIC                 LLM
        CONTROLS                 REASONING
              │                         │
              └────────────┬────────────┘
                           ▼
                     FINAL ACTION
```

- **Deterministic logic controls**: Budgets, allowed actions, termination limits, validation, policy.
- **LLM supports**: Gap interpretation, action reasoning, candidate prioritization.

### 9.4 LangGraph Integration

LangGraph should represent the investigation workflow.

```text
START
  │
  ▼
ASSESS
  │
  ▼
PLAN
  │
  ▼
POLICY CHECK
  │
  ├── REJECT → PLAN
  │
  ▼
EXECUTE
  │
  ▼
UPDATE STATE
  │
  ▼
TERMINATE?
  │
  ├── NO → ASSESS
  │
  └── YES → END
```

The graph provides explicit control over the adaptive loop.

### Phase 5 Deliverables

- Planner
- Structured LLM output
- LangGraph workflow
- Policy layer
- Budget enforcement
- Action scoring
- LLM fallback strategy

---

# PHASE 6 — Frontend & Analyst Workflow

## Objective

Expose the investigation system to the user. The frontend should reflect the real investigation state, not act as an isolated dashboard.

### 10.1 Primary User

The primary user is an analyst. The analyst needs to answer:
```text
What happened?
What evidence exists?
What is the system doing?
Why did it choose that action?
What conclusion was reached?
```

### 10.2 Recommended Screens

1. **Dashboard**: Shows alerts, active investigations, investigation status.
2. **Investigation View**: Shows timeline, evidence, hypotheses, actions, current status, confidence gauge.
3. **Decision View**: Shows evidence gap, selected action, rationale, outcome.
4. **Final Report**: Shows findings, evidence references, confidence, limitations.

### Phase 6 Deliverables

- Investigation dashboard
- Investigation detail view
- Timeline visualization
- Evidence display
- Human review controls
- Final report view

---

# PHASE 7 — Evaluation & Experimental Validation

## Objective

Prove the value of the architecture through reproducible experiments.

### 11.1 Scenario Runner

Create a controlled evaluation runner.

```text
Scenario
   │
   ▼
Configuration
   │
   ├── Baseline
   ├── Full System
   └── Ablation
   │
   ▼
Investigation Run
   │
   ▼
Metric Collection
```

### 11.2 Required Experiments

- **Experiment 1 — Baseline**: Fixed investigation workflow.
- **Experiment 2 — Full System**: Adaptive orchestration.
- **Experiment 3 — Without RAG**: Evaluate knowledge retrieval contribution.
- **Experiment 4 — Without Validation**: Evaluate evidence validation.
- **Experiment 5 — Failure Recovery**: Test LLM or capability failure.

### Phase 7 Deliverables

- Scenario definitions
- Ground truth
- Metrics engine
- Experiment runner
- Result storage
- Charts and evaluation report

---

# 12. Implementation Dependency Graph

The following sequence must be maintained:

```text
ENVIRONMENT
     │
     ▼
DOMAIN MODELS
     │
     ▼
DATA NORMALIZATION
     │
     ▼
INVESTIGATION STATE
     │
     ▼
DETERMINISTIC BASELINE
     │
     ▼
CAPABILITY FRAMEWORK
     │
     ▼
ADAPTIVE PLANNER
     │
     ▼
LANGGRAPH WORKFLOW
     │
     ▼
FRONTEND
     │
     ▼
EVALUATION
```

Skipping this sequence increases integration complexity.

---

# 13. Team Workstream Distribution

For a small team, development can be parallelized after the core contracts are defined:

- **Workstream A — Data & Backend**: Dataset integration, normalization, detection, database models.
- **Workstream B — Orchestration**: State Manager, Planner, LangGraph, Policy, Capabilities.
- **Workstream C — Frontend & Evaluation**: Analyst interface, visualization, scenario framework, metrics, reports.

All workstreams must use the same domain contracts.

---

# 14. Recommended 3–4 Month Timeline

| Period | Primary Work |
|---|---|
| Weeks 1–2 | Architecture, environment, contracts |
| Weeks 3–4 | Dataset integration and normalization |
| Weeks 5–6 | Investigation state and persistence |
| Weeks 7–8 | Baseline workflow and capabilities |
| Weeks 9–10 | Adaptive orchestration and LLM integration |
| Weeks 11–12 | Frontend and analyst workflow |
| Weeks 13–14 | Testing and failure handling |
| Weeks 15–16 | Experiments, results, documentation |

The timeline should be adjusted according to team size and actual progress.

---

# 15. Milestone Gates

| Gate | Title | Verification Condition |
|---|---|---|
| **Gate 1** | Environment | All services start successfully. |
| **Gate 2** | Data | Dataset records become valid normalized events. |
| **Gate 3** | State | Investigation state persists and versions correctly. |
| **Gate 4** | Baseline | A complete investigation runs without AI planning. |
| **Gate 5** | Capabilities | Capabilities return validated structured results. |
| **Gate 6** | Adaptive Orchestration | System selects actions based on investigation state. |
| **Gate 7** | User Workflow | An analyst can observe and review an investigation. |
| **Gate 8** | Evaluation | Baseline and proposed architecture produce comparable metrics. |

---

# 16. Definition of Done

A feature is complete only when it satisfies:

```text
IMPLEMENTED + VALIDATED + TESTED + OBSERVABLE + DOCUMENTED
```

For example, a new capability must include:
- Input contract
- Output contract
- Unit tests
- Failure behavior
- Audit logging
- Documentation

---

# 17. Risk-Based Development Priorities

The highest-risk component is the adaptive orchestration layer. Therefore, it should be validated early enough to allow redesign:

```text
1. Investigation State
2. Capability Contract
3. Baseline Workflow
4. Adaptive Planner
5. Dataset Depth
6. Frontend Sophistication
```

This prevents the project from spending excessive time on UI before validating its core innovation.

---

# 18. MVP Boundary

### In Scope for MVP:
- One normalized telemetry pipeline
- Three realistic investigation scenarios
- Investigation state management
- Three core capabilities (Correlation, Knowledge, Validation)
- Deterministic baseline
- Adaptive orchestration
- Basic RAG
- Analyst investigation interface
- Evaluation metrics

### Out of Scope for Initial MVP:
- Large-scale real-time SIEM processing
- Dozens of independent agents
- Full autonomous incident response containment
- Enterprise-scale distributed deployment

Sophistication must come from **architecture quality and measurable reasoning**, not uncontrolled scope.

---

# 19. Post-MVP Enhancements

After the core architecture is stable:
- Streaming Ingestion
- Additional Capabilities
- More Attack Scenarios
- Advanced Confidence Calibration
- Multi-Model Routing
- Capability Performance Learning
- Advanced Human Collaboration
- Distributed Workers

---

# 20. Complete Development Workflow

```text
                    PROJECT START
                         │
                         ▼
                  DEFINE CONTRACTS
                         │
                         ▼
                 BUILD ENVIRONMENT
                         │
                         ▼
                  INTEGRATE DATA
                         │
                         ▼
                BUILD STATE FOUNDATION
                         │
                         ▼
                BUILD BASELINE SYSTEM
                         │
                         ▼
               BUILD CAPABILITY LAYER
                         │
                         ▼
               BUILD ADAPTIVE PLANNER
                         │
                         ▼
                 INTEGRATE LANGGRAPH
                         │
                         ▼
                  BUILD ANALYST UI
                         │
                         ▼
                  TEST FAILURES
                         │
                         ▼
                 RUN EXPERIMENTS
                         │
                         ▼
                 ANALYZE RESULTS
                         │
                         ▼
                   FINAL DELIVERY
```

---

# 21. Final Implementation Principle

The complete development strategy is:

```text
FIRST:
Make the system deterministic and observable.

THEN:
Make it modular and extensible.

THEN:
Make the orchestration adaptive.

FINALLY:
Prove that the adaptation provides measurable value.
```

The project's technical strength comes from a clear chain of evidence:

> **Well-defined data → controlled state → specialized capabilities → adaptive orchestration → measurable evaluation.**
