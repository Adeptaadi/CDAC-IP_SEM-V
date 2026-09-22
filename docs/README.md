# Project Sentinel — Documentation Hub

Welcome to the centralized documentation repository for **Project Sentinel**, an Agentic AI-powered Autonomous Cyber Threat Hunting Platform built for CDAC / Semester V Industry Project (Problem Statement Sr. No. 25).

---

## 1. Primary Specifications & Design Documents

| Document | Purpose & Scope | Link |
| :--- | :--- | :--- |
| **Problem Statement** | Official CDAC / Semester V Problem Statement specification (Sr. No. 25). | [PROBLEM_STATEMENT.md](./PROBLEM_STATEMENT.md) |
| **Implementation Specification (IS)** | Concrete mathematical algorithms, DDL schemas, logit confidence updates, utility functions, and contracts. | [Implementation_Specification.md](./Implementation_Specification.md) |
| **Product Requirements (PRD)** | Functional & non-functional requirements, user personas, threat models, and SOC acceptance criteria. | [PRD.md](./PRD.md) |
| **Software Design (SDD)** | 3-tier polyglot architecture, REST/WebSocket API endpoints, and database models. | [SDD.md](./SDD.md) |
| **Agent Architecture (AAD)** | Multi-agent autonomous intelligence blueprint, Planner state machine, and communication contracts. | [AAD.md](./AAD.md) |
| **AI Design (AIDD)** | Local LLM sidecar orchestration, prompt framework, and RAG knowledge retrieval pipeline. | [AIDD.md](./AIDD.md) |
| **Test-Driven Design (TDD)** | Test suite architecture, pytest fixtures, and scientific evaluation methodologies. | [TDD.md](./TDD.md) |

---

## 2. Architecture Decision Records (ADRs)

All major architectural, database, dataset, and LLM orchestration decisions are tracked in `docs/decisions/`:

| ADR Record | Title & Summary | Status | Link |
| :--- | :--- | :--- | :--- |
| **ADR-001** | **3-Tier Polyglot Persistence Architecture**<br>PostgreSQL 15 (relational truth & audit logs) + ChromaDB (vector embeddings) + Redis 7 (caching). | `ACCEPTED` | [ADR-001-database.md](./decisions/ADR-001-database.md) |
| **ADR-002** | **CSE-CIC-IDS2018 5-Scenario Suite Benchmark Telemetry**<br>Preprocessed and aligned 5-attack benchmark covering Infiltration, Brute Force, Web SQLi, Botnet C2, and DoS. | `ACCEPTED` | [ADR-002-dataset-selection.md](./decisions/ADR-002-dataset-selection.md) |
| **ADR-003** | **Local-First Air-Gapped LLM Integration & Deterministic Safety Fallback**<br>Air-gapped local Ollama (Qwen2.5) with strict JSON formatting and zero-crash deterministic fallback guards. | `ACCEPTED` | [ADR-003-llm-orchestration-and-fallback.md](./decisions/ADR-003-llm-orchestration-and-fallback.md) |

---

## 3. Reference Documentation

Supplemental materials, prompt framework guidelines, task lists, and specifications are archived in `docs/reference/`:

- [AISPEC.md](./reference/AISPEC.md): AI specification and agent interface contracts.
- [PRD_v2.md](./reference/PRD_v2.md): Product requirements revision draft.
- [PROMPT_FRAMEWORK.md](./reference/PROMPT_FRAMEWORK.md): SOC prompt engineering framework and grounding rules.
- [TASKLIST.md](./reference/TASKLIST.md): Original development tasklist checklist.
- [TDD_v2.md](./reference/TDD_v2.md): Test design documentation revision draft.

---

## 4. End-to-End System Pipeline

```
                                    ┌───────────────────────────┐
                                    │    React 18 Vite SOC UI   │
                                    │   (Investigation Studio)  │
                                    └─────────────┬─────────────┘
                                                  │ REST / WebSocket
                                                  ▼
                                    ┌───────────────────────────┐
                                    │  FastAPI Gateway Layer    │
                                    └─────────────┬─────────────┘
                                                  │
                                                  ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│ Autonomous Planner Agent (`backend/app/planner/engine.py`)                                    │
│ Observe ──► Query RAG ──► Utility Maximize (IS §3.2) ──► Dispatch Worker ──► Logit Bayesian │
└─────────────────────────────────────────────────┬─────────────────────────────────────────────┘
                                                  │
                  ┌───────────────────────────────┴───────────────────────────────┐
                  ▼                                                               ▼
┌───────────────────────────────────────────┐                   ┌─────────────────────────────────┐
│ 5 Specialized Worker Agents               │                   │ Knowledge & RAG Layer           │
│ • DetectionWorker     (Anomaly heuristics)│◄──────────────────┤ • Persistent ChromaDB Vectors   │
│ • CorrelationWorker   (Entity graph)      │                   │ • MITRE ATT&CK v14 Playbooks    │
│ • InvestigationWorker (Hypotheses)        │                   │ • Cosine + Reliability Weight   │
│ • ReportingWorker     (Twin-tier summaries│                   └─────────────────────────────────┘
│ • ResponseWorker      (HITL Authorization)│
└───────────────────────────────────────────┘
```
