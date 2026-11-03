# Project Sentinel — Documentation Hub

Welcome to the centralized documentation repository for **Project Sentinel**, an Agentic AI-powered Autonomous Cyber Threat Hunting Platform built for CDAC / Semester V Industry Project (Problem Statement Sr. No. 25).

---

## 1. Primary Specifications & Design Documents

| Document | Purpose & Scope | Link |
| :--- | :--- | :--- |
| **Complete Remaining Technical Documentation Roadmap** | 10-document remaining specification roadmap across 4 delivery phases: detection, capabilities, evaluation, implementation, and ops. | [COMPLETE_REMAINING_TECHNICAL_DOCUMENTATION_ROADMAP.md](./COMPLETE_REMAINING_TECHNICAL_DOCUMENTATION_ROADMAP.md) |
| **Project Upgrade Implementation Plan** | Master 8-phase implementation roadmap for upgrading the project: architecture gap analysis, sequencing, milestones, and validation gates. | [PROJECT_UPGRADE_IMPLEMENTATION_PLAN.md](./PROJECT_UPGRADE_IMPLEMENTATION_PLAN.md) |
| **Detailed Phase-wise Implementation Plan** | Definitive 15-phase operational roadmap (Phases 0–14): repo audit, infrastructure, persistence, replay, dynamic LangGraph planner, HITL, gates G0–G14, and 10 coding agent execution rules. | [DETAILED_PHASE_WISE_IMPLEMENTATION_PLAN.md](./DETAILED_PHASE_WISE_IMPLEMENTATION_PLAN.md) |
| **Detection, Correlation & Investigation Engine Spec (DCIES)** | Concrete JSON schemas, deterministic detection rules, entity extraction, correlation algorithms, mathematical scoring formulas, and policy termination. | [DETECTION_CORRELATION_AND_INVESTIGATION_ENGINE_SPEC.md](./DETECTION_CORRELATION_AND_INVESTIGATION_ENGINE_SPEC.md) |
| **Capability & Tool Implementation Spec (CTIS)** | The 7 core capability tool contracts, execution lifecycle, Pydantic schemas, circuit breakers, timeout matrices, and action utility scoring. | [CAPABILITY_AND_TOOL_IMPLEMENTATION_SPEC.md](./CAPABILITY_AND_TOOL_IMPLEMENTATION_SPEC.md) |
| **AI Agent Orchestration & Planner Implementation Spec (AOPIS)** | LangGraph 10-node stateful workflow, ContextPackage schema, loop prevention signatures, tri-partitioned memory, and planner metrics. | [AI_AGENT_ORCHESTRATION_AND_PLANNER_IMPLEMENTATION_SPEC.md](./AI_AGENT_ORCHESTRATION_AND_PLANNER_IMPLEMENTATION_SPEC.md) |
| **Data Platform, Storage & RAG Implementation Spec (DPSRIS)** | Polyglot persistence: PostgreSQL system of record, Redis 7 operational caches/locks, ChromaDB RAG vector collections, and data lineage. | [DATA_PLATFORM_STORAGE_AND_RAG_IMPLEMENTATION_SPEC.md](./DATA_PLATFORM_STORAGE_AND_RAG_IMPLEMENTATION_SPEC.md) |
| **Telemetry Ingestion, Normalization & Detection Pipeline Spec (TINDPIS)** | Dataset adapters, canonical event schema, batch vs. streaming replay, deduplication, rule evaluation engine, and alert generation. | [TELEMETRY_INGESTION_NORMALIZATION_AND_DETECTION_PIPELINE_SPEC.md](./TELEMETRY_INGESTION_NORMALIZATION_AND_DETECTION_PIPELINE_SPEC.md) |
| **RAG & Cybersecurity Knowledge Layer Spec (RAGCKLS)** | ChromaDB vector retrieval, semantic-aware chunking, multi-factor scoring, prompt injection defense, and epistemic evidence separation. | [RAG_AND_CYBERSECURITY_KNOWLEDGE_LAYER_SPEC.md](./RAG_AND_CYBERSECURITY_KNOWLEDGE_LAYER_SPEC.md) |
| **Data Ingestion & Telemetry Processing Spec (DITPS)** | TelemetryAdapter interface, canonical event schema, batch vs. replay modes, deduplication fingerprints, and data quality metrics. | [DATA_INGESTION_AND_TELEMETRY_PROCESSING_SPEC.md](./DATA_INGESTION_AND_TELEMETRY_PROCESSING_SPEC.md) |
| **Database & Persistence Design Spec (DPDS)** | PostgreSQL 15 DDL schemas, `alert_events` mapping, hybrid state snapshot persistence, indexes, transaction boundaries, and Alembic migrations. | [DATABASE_AND_PERSISTENCE_DESIGN_SPEC.md](./DATABASE_AND_PERSISTENCE_DESIGN_SPEC.md) |
| **API & Backend Integration Spec (ABIS)** | FastAPI backend integration boundary: REST contracts, async background investigation workers, state synchronization, RBAC boundaries, and structured error models. | [API_AND_BACKEND_INTEGRATION_SPEC.md](./API_AND_BACKEND_INTEGRATION_SPEC.md) |
| **Frontend & Analyst Experience Spec (FAES)** | React/TypeScript investigation studio: progressive detail hierarchy, evidence vs. hypothesis presentation, HITL action review, and state synchronization. | [FRONTEND_AND_ANALYST_EXPERIENCE_SPEC.md](./FRONTEND_AND_ANALYST_EXPERIENCE_SPEC.md) |
| **Security, Authentication & Authorization Design Spec (SAADS)** | Multi-tier security boundaries: JWT RBAC, capability registry sandboxing, prompt injection defense, audit trails, and bounded AI autonomy. | [SECURITY_AUTHENTICATION_AND_AUTHORIZATION_DESIGN_SPEC.md](./SECURITY_AUTHENTICATION_AND_AUTHORIZATION_DESIGN_SPEC.md) |
| **Observability, Monitoring & Auditability Spec (OMAS)** | Operational visibility: structured logging, distributed request/investigation tracing, agent execution records, capability metrics, and audit event separation. | [OBSERVABILITY_MONITORING_AND_AUDITABILITY_SPEC.md](./OBSERVABILITY_MONITORING_AND_AUDITABILITY_SPEC.md) |
| **Testing, Validation & Evaluation Strategy (TVES)** | Multi-level QA and empirical evaluation: 3 attack scenarios, detection F1, evidence precision/recall, conclusion accuracy, and comparative baseline experiments. | [TESTING_VALIDATION_AND_EVALUATION_STRATEGY.md](./TESTING_VALIDATION_AND_EVALUATION_STRATEGY.md) |
| **Deployment, Environment & DevOps Spec (DEDOS)** | Containerized architecture: Docker Compose multi-service topologies, host-bound Ollama GPU integration, startup sequencing, Alembic migrations, and readiness probes. | [DEPLOYMENT_ENVIRONMENT_AND_DEVOPS_SPEC.md](./DEPLOYMENT_ENVIRONMENT_AND_DEVOPS_SPEC.md) |
| **Data Management, Dataset Governance & Telemetry Lifecycle Spec (DMDGTLS)** | Complete data lifecycle: dataset registration checksums, canonical event model, evidence provenance chains, ground-truth management, and evaluation reproducibility. | [DATA_MANAGEMENT_DATASET_GOVERNANCE_AND_TELEMETRY_LIFECYCLE_SPEC.md](./DATA_MANAGEMENT_DATASET_GOVERNANCE_AND_TELEMETRY_LIFECYCLE_SPEC.md) |
| **Frontend, Analyst Experience & Human-in-the-Loop Spec (FAE-HITLS)** | Human-in-the-loop interaction architecture: review queue triggers, structured agent task states, evidence viewer, auditable analyst decisions, and progress transparency. | [FRONTEND_ANALYST_EXPERIENCE_AND_HUMAN_IN_THE_LOOP_SPEC.md](./FRONTEND_ANALYST_EXPERIENCE_AND_HUMAN_IN_THE_LOOP_SPEC.md) |
| **API Contract & Integration Spec (ACIS)** | Technical interface contracts: REST resource endpoints (`/auth`, `/alerts`, `/investigations`, `/evidence`, `/reviews`, `/system`), async task progress, and standard error envelopes. | [API_CONTRACT_AND_INTEGRATION_SPEC.md](./API_CONTRACT_AND_INTEGRATION_SPEC.md) |
| **Security Architecture & Threat Model Spec (SATMS)** | Comprehensive threat modeling (5 assets, 4 trust boundaries), prompt injection defense, capability least-privilege, and fail-safe autonomy safeguards. | [SECURITY_ARCHITECTURE_AND_THREAT_MODEL_SPEC.md](./SECURITY_ARCHITECTURE_AND_THREAT_MODEL_SPEC.md) |
| **Observability, Monitoring & Operational Diagnostics Spec (OMODS)** | Multi-layer diagnostics: correlation identifiers (`request_id`, `investigation_id`, `task_id`), task lifecycle metrics, error categorization, and health probes. | [OBSERVABILITY_MONITORING_AND_OPERATIONAL_DIAGNOSTICS_SPEC.md](./OBSERVABILITY_MONITORING_AND_OPERATIONAL_DIAGNOSTICS_SPEC.md) |
| **Testing, Validation & Evaluation Strategy Spec (PS-TEST-001)** | Formal evaluation framework: 5-level testing, baseline hierarchy (B0–B3 vs P1), Orchestration Quality Score (OQS), 7-factor ablation, and statistical rigor. | [TESTING_VALIDATION_AND_EVALUATION_STRATEGY_SPEC.md](./TESTING_VALIDATION_AND_EVALUATION_STRATEGY_SPEC.md) |
| **Model Architecture, Selection & Optimization Spec (MASOS)** | LLM adapter layer: Planner vs. specialist roles, Pydantic structured output validation, concurrency limiters, quantization, and evaluation matrix. | [MODEL_ARCHITECTURE_SELECTION_AND_OPTIMIZATION_SPEC.md](./MODEL_ARCHITECTURE_SELECTION_AND_OPTIMIZATION_SPEC.md) |
| **Memory Architecture & Lifecycle Spec (MALS)** | Tripartite memory architecture (Working, Episodic, Semantic), MemoryService abstraction, PostgreSQL/Redis/ChromaDB allocation, and context builder. | [MEMORY_ARCHITECTURE_AND_LIFECYCLE_SPEC.md](./MEMORY_ARCHITECTURE_AND_LIFECYCLE_SPEC.md) |
| **RAG & Knowledge Engineering Spec (RKES)** | Hybrid retrieval pipeline (Dense Vector + Exact Identifiers + Metadata), structure-aware chunking, evidence vs. knowledge citation enforcement, and injection defense. | [RAG_AND_KNOWLEDGE_ENGINEERING_SPEC.md](./RAG_AND_KNOWLEDGE_ENGINEERING_SPEC.md) |
| **Detection & Correlation Engine Technical Spec (DCETS)** | CSE-CIC-IDS2018 replay, canonical event normalization, hybrid rules & ML detection, entity resolution, temporal correlation scoring, and Planner handoff. | [DETECTION_AND_CORRELATION_ENGINE_SPEC.md](./DETECTION_AND_CORRELATION_ENGINE_SPEC.md) |
| **Agent Capability Registry & Tool Execution Spec (ACRTES)** | Capability contracts, centralized registry discovery, Pydantic execution runtime, least-privilege permissions, risk tiering, and LangGraph dispatch. | [AGENT_CAPABILITY_REGISTRY_AND_TOOL_EXECUTION_SPEC.md](./AGENT_CAPABILITY_REGISTRY_AND_TOOL_EXECUTION_SPEC.md) |
| **Investigation State Machine & Orchestration Runtime Spec (ISMORS)** | Goal-driven non-linear control loop, independent investigation/task state machines, LangGraph checkpointing, replanning bounds, and deterministic termination. | [INVESTIGATION_STATE_MACHINE_AND_ORCHESTRATION_RUNTIME_SPEC.md](./INVESTIGATION_STATE_MACHINE_AND_ORCHESTRATION_RUNTIME_SPEC.md) |
| **Database Schema & Persistence Architecture Spec (DSPAS)** | Logical relational data model across 14 domains, optimistic concurrency, transactional outbox pattern, ground-truth isolation, and ChromaDB recovery. | [DATABASE_SCHEMA_AND_PERSISTENCE_ARCHITECTURE_SPEC.md](./DATABASE_SCHEMA_AND_PERSISTENCE_ARCHITECTURE_SPEC.md) |
| **Deployment Security Hardening & Production Readiness Spec (DSHPRS)** | Production-readiness baseline: non-root container isolation, secrets governance, network segmentation, AI privilege boundaries, and simulated response safety. | [DEPLOYMENT_SECURITY_HARDENING_AND_PRODUCTION_READINESS_SPEC.md](./DEPLOYMENT_SECURITY_HARDENING_AND_PRODUCTION_READINESS_SPEC.md) |
| **End-to-End System Integration & Implementation Blueprint (EESI-IB)** | Master integration architecture: subsystem boundaries, end-to-end data flow, LangGraph control graph, 8-milestone plan, and P0-P2 priorities. | [END_TO_END_SYSTEM_INTEGRATION_AND_IMPLEMENTATION_BLUEPRINT.md](./END_TO_END_SYSTEM_INTEGRATION_AND_IMPLEMENTATION_BLUEPRINT.md) |
| **Detailed AI, RAG & Model Strategy Spec (AIRMSS)** | LLM routing, AI Planner reasoning cycle, RAG pipeline, context token budgeting, grounded reasoning safeguards, and deterministic fallback. | [DETAILED_AI_RAG_AND_MODEL_STRATEGY_SPEC.md](./DETAILED_AI_RAG_AND_MODEL_STRATEGY_SPEC.md) |
| **Detailed Data Architecture & Investigation State Spec (DAISS)** | Canonical telemetry normalization, 5 data layers, dual timestamping, evidence lineage, PostgreSQL + ChromaDB + Redis storage boundaries, and 5 integrity rules. | [DETAILED_DATA_ARCHITECTURE_AND_INVESTIGATION_STATE_SPEC.md](./DETAILED_DATA_ARCHITECTURE_AND_INVESTIGATION_STATE_SPEC.md) |
| **Detailed Agent & Capability Design Spec (DACDS)** | Agent responsibilities, capability contracts, hybrid decision architecture, 4-tier memory, and complete responsibility matrix. | [DETAILED_AGENT_AND_CAPABILITY_DESIGN_SPEC.md](./DETAILED_AGENT_AND_CAPABILITY_DESIGN_SPEC.md) |
| **Detailed Implementation Roadmap & Blueprint (DIRDB)** | Master 8-phase implementation dependency order, milestone gates (Gates 1–8), risk priorities, MVP boundaries, and monorepo structure. | [DETAILED_IMPLEMENTATION_ROADMAP_AND_DEVELOPMENT_BLUEPRINT.md](./DETAILED_IMPLEMENTATION_ROADMAP_AND_DEVELOPMENT_BLUEPRINT.md) |
| **Evaluation, Testing & Experimental Methodology Spec (ETEMS)** | 5-level testing framework, baseline comparative experiments (Fixed vs. Adaptive), evidence coverage/precision, action utility, and 7-scenario ablation matrix. | [EVALUATION_TESTING_AND_EXPERIMENTAL_METHODOLOGY_SPEC.md](./EVALUATION_TESTING_AND_EXPERIMENTAL_METHODOLOGY_SPEC.md) |
| **Detailed Data, State & Interface Spec (DSIS)** | Complete data schemas: Pydantic contracts, normalized events, action/decision requests, API routes, and 5-layer validation. | [DETAILED_DATA_STATE_AND_INTERFACE_SPEC.md](./DETAILED_DATA_STATE_AND_INTERFACE_SPEC.md) |
| **Security, Reliability & Governance Spec (SRGS)** | Governance architecture: bounded autonomy, RBAC, HITL protocol, circuit breakers, loop prevention, and cryptographic audit logs. | [SECURITY_RELIABILITY_AND_GOVERNANCE_SPEC.md](./SECURITY_RELIABILITY_AND_GOVERNANCE_SPEC.md) |
| **Implementation & Runtime Architecture Spec (IRAS)** | Complete runtime services, FastAPI/LangGraph runtime, Redis background queue, failure recovery matrix, and modular folder structure. | [IMPLEMENTATION_AND_RUNTIME_ARCHITECTURE_SPEC.md](./IMPLEMENTATION_AND_RUNTIME_ARCHITECTURE_SPEC.md) |
| **Evidence, Confidence & Evaluation Spec (ECES)** | 3-layer evaluation framework, 5 evidence quality dimensions, claim-based confidence, and Fixed vs. Adaptive baseline experiments. | [EVIDENCE_CONFIDENCE_AND_EVALUATION_SPEC.md](./EVIDENCE_CONFIDENCE_AND_EVALUATION_SPEC.md) |
| **Adaptive Planning & Decision Spec (APDS)** | Decision algorithms, evidence-gap reasoning, candidate action scoring, loop prevention, and stop conditions. | [ADAPTIVE_PLANNING_AND_DECISION_SPEC.md](./ADAPTIVE_PLANNING_AND_DECISION_SPEC.md) |
| **Capability & Agent Interface Spec (CAIS)** | Standard contracts for specialized capabilities, dynamic registry, `CapabilityRequest`/`Result`, and failure recovery. | [CAPABILITY_AND_AGENT_INTERFACE_SPEC.md](./CAPABILITY_AND_AGENT_INTERFACE_SPEC.md) |
| **Investigation State & Evidence Spec (ISES)** | Data model and state lifecycle: evidence taxonomy, hypothesis states, contradiction ledger, and PostgreSQL schema. | [INVESTIGATION_STATE_AND_EVIDENCE_SPEC.md](./INVESTIGATION_STATE_AND_EVIDENCE_SPEC.md) |
| **Orchestration Design Document (ODD)** | Detailed technical design of the Orchestration Core: 6 components, lifecycle states, LangGraph nodes, action validator, and metrics. | [ORCHESTRATION_DESIGN_DOCUMENT.md](./ORCHESTRATION_DESIGN_DOCUMENT.md) |
| **Agent-Centric Architecture Spec** | Formal architecture specification: orchestration core, 6 operational questions, non-linear workflows, and tripartite confidence. | [AGENT_CENTRIC_ARCHITECTURE_SPEC.md](./AGENT_CENTRIC_ARCHITECTURE_SPEC.md) |
| **Agent-Centric Implementation Plan** | Master roadmap for adaptive, evidence-driven multi-agent orchestration, capability contracts, and baseline comparative evaluation. | [AGENT_CENTRIC_ORCHESTRATION_PLAN.md](./AGENT_CENTRIC_ORCHESTRATION_PLAN.md) |
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
