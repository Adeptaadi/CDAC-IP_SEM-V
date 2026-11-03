# Project Sentinel
# Detailed Phase-wise Implementation Plan

**Document Type:** Software Implementation Roadmap  
**Version:** 1.0  
**Status:** Proposed Implementation Plan  
**Project:** AI-Powered Cyber Threat Detection and Investigation Platform

---

# 1. Executive Summary

## 1.1 Implementation objective

The objective is to implement Project Sentinel as an integrated AI-assisted cybersecurity detection and investigation platform.

The system will process cybersecurity datasets, identify suspicious activity, correlate related events, initiate investigations, dynamically coordinate specialized workers, retrieve cybersecurity knowledge, generate reports and simulate response actions under human oversight.

The implementation will be divided into 14 phases.

| Phase | Name | Primary outcome |
|---|---|---|
| 0 | Repository Audit and Architecture Alignment | Verified implementation baseline |
| 1 | Development Environment and Infrastructure | Working development environment |
| 2 | Database and Persistence Foundation | Durable application data model |
| 3 | Dataset Management and Replay | Reproducible telemetry input |
| 4 | Event Ingestion and Normalization | Canonical SecurityEvent pipeline |
| 5 | Detection Engine | Rule-based and ML-based detection |
| 6 | Correlation Engine | Entity and temporal correlation |
| 7 | Investigation Management | Persistent investigation lifecycle |
| 8 | Capability Registry and Task Executor | Controlled worker execution |
| 9 | Planner and Dynamic Orchestration | Non-linear multi-agent investigation |
| 10 | RAG and Evidence Integration | Grounded investigation |
| 11 | Reporting and Human-in-the-Loop Response | Complete investigation lifecycle |
| 12 | Frontend Integration | Functional SOC analyst dashboard |
| 13 | Evaluation, Security and Reliability | Validated system |
| 14 | Final Deployment and Demonstration | Demonstration-ready project |

**Important:** Phase 0 must happen before substantial code changes. The implementation status of the actual repository has not yet been verified. Existing modules should be reused where appropriate instead of creating duplicates.

---

# 2. Architecture Baseline

## 2.1 Target technology stack

| Component | Technology |
|---|---|
| Frontend | React + Vite |
| Backend | FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy 2.x |
| Migrations | Alembic |
| Task coordination | Redis |
| Vector database | ChromaDB |
| LLM runtime | Ollama |
| Agent orchestration | LangGraph |
| Containerization | Docker Compose |
| Evaluation | Python evaluation modules |

## 2.2 Target architecture

```text
                  SOC ANALYST
                       |
                       v
                REACT DASHBOARD
                       |
                       v
                  FASTAPI API
                       |
          +------------+------------+
          |            |            |
          v            v            v
      Alert Service  Investigation  Review
                        Service
                          |
                          v
                  LANGGRAPH RUNTIME
                          |
                       PLANNER
                          |
                 Dynamic Task Planning
                          |
          +---------------+----------------+
          |               |                |
          v               v                v
      Detection       Correlation      Investigation
       Worker           Worker            Worker
          |               |                |
          +---------------+----------------+
                          |
                     RAG SERVICE
                          |
                          v
                   REPORTING WORKER
                          |
                          v
                 RESPONSE SIMULATION
                          |
                          v
                    HUMAN REVIEW

              PERSISTENCE AND SERVICES
       PostgreSQL | Redis | ChromaDB | Ollama
```

## 2.3 Core architectural constraint

The Planner must dynamically select capabilities based on the evolving investigation state.

Do not implement this:

```text
Detection → Correlation → Investigation → Reporting
```

as an unconditional agent pipeline.

Instead, implement:

```text
Investigation State
        |
        v
      Planner
        |
        v
  Capability Selection
        |
        v
   Task Execution
        |
        v
  State Update
        |
        v
      Planner
        |
        +---- Continue
        |
        +---- Replan
        |
        +---- Request Review
        |
        +---- Complete
```

The Planner may revisit previously executed capabilities, request additional evidence or terminate when deterministic completion conditions are satisfied.

---

# 3. Phase 0 — Repository Audit and Architecture Alignment

<badge color="danger">Mandatory starting phase</badge>

## Objective

Establish the actual implementation status before changing the repository.

This phase prevents accidental duplication, incompatible architecture changes and unnecessary rewrites.

## Tasks

### 0.1 Repository inventory

Inspect:

- Root directory.
- Backend structure.
- Frontend structure.
- Dependency files.
- Configuration files.
- Docker configuration.
- Database models.
- Existing tests.
- Dataset files.
- Documentation.

Suggested commands:

```bash
pwd
ls -la
find . -maxdepth 3 -type f | sort
```

Exclude generated directories such as `node_modules`, `.venv`, `__pycache__` and build output.

### 0.2 Backend inspection

Identify:

- FastAPI application entry point.
- Existing API routers.
- Database initialization.
- SQLAlchemy models.
- Existing services.
- Existing agent implementations.
- Detection and correlation modules.
- Dataset ingestion code.
- RAG implementation.
- Authentication and authorization.

### 0.3 Frontend inspection

Identify:

- React entry point.
- Vite configuration.
- Routing.
- Dashboard pages.
- API client.
- Existing components.
- State-management approach.
- Authentication integration.
- Existing visualization libraries.

### 0.4 Dependency inspection

Verify installed versions of:

- FastAPI.
- SQLAlchemy.
- Alembic.
- LangGraph.
- Redis client.
- ChromaDB.
- Pydantic.
- React.
- Vite.

Do not perform broad dependency upgrades during this phase.

### 0.5 Existing functionality assessment

Classify each subsystem:

| Status | Meaning |
|---|---|
| Complete | Implemented and tested |
| Partial | Some functionality exists |
| Prototype | Experimental implementation |
| Placeholder | Interface or stub only |
| Missing | Not implemented |
| Blocked | Cannot proceed due to dependency or issue |

### 0.6 Architecture reconciliation

Compare the actual repository against:

1. Project Sentinel PRD and requirements, where available.
2. Project Sentinel architecture specifications.
3. API contracts.
4. Database schema specification.
5. Detection and correlation specification.
6. Agent capability and orchestration specifications.
7. Existing code.

Any conflicting implementation must be documented before changing it.

## Deliverables

- Repository inventory.
- Dependency inventory.
- Architecture-to-code mapping.
- Existing feature assessment.
- Missing-component list.
- Technical debt list.
- Prioritized implementation backlog.

## Exit criteria

- Actual backend and frontend frameworks confirmed.
- Existing database architecture confirmed.
- Existing agent architecture confirmed.
- Current tests executed.
- Existing code reuse opportunities identified.
- No unresolved architecture conflict affecting the next phase.

**Estimated effort:** 2–4 working days.

---

# 4. Phase 1 — Development Environment and Infrastructure

## Objective

Create a reproducible development environment in which all required services can start, communicate and be monitored.

## Tasks

### 1.1 Docker Compose setup

Configure services for:

- Backend.
- Frontend.
- PostgreSQL.
- Redis.
- ChromaDB.
- Ollama.

### 1.2 Environment configuration

Create:

```text
.env.example
```

Configure:

```env
APP_ENV=development
DEBUG=true

DATABASE_URL=
REDIS_URL=

OLLAMA_BASE_URL=
OLLAMA_MODEL=

CHROMA_HOST=
CHROMA_PORT=
```

Use actual application configuration names after inspecting the repository.

### 1.3 Backend initialization

Implement or verify:

- FastAPI startup.
- Configuration loading.
- Dependency injection.
- Health endpoint.
- CORS.
- Centralized exception handling.
- Structured logging.

### 1.4 Frontend initialization

Implement or verify:

- React/Vite startup.
- Application routing.
- API base URL configuration.
- Global error handling.
- Basic dashboard shell.

### 1.5 Infrastructure connectivity

Verify:

- Backend → PostgreSQL.
- Backend → Redis.
- Backend → ChromaDB.
- Backend → Ollama.
- Frontend → Backend.

### 1.6 Health checks

Implement separate health checks for:

- Liveness.
- Readiness.
- Dependency availability.

## Deliverables

- Working Docker Compose environment.
- Backend startup.
- Frontend startup.
- Environment template.
- Health endpoints.
- Initial logging configuration.

## Exit criteria

- All required services start.
- Backend can connect to infrastructure.
- Frontend can communicate with backend.
- Health checks report accurate service status.
- No secrets are hardcoded.

**Estimated effort:** 3–5 working days.

---

# 5. Phase 2 — Database and Persistence Foundation

## Objective

Implement durable persistence before building components that depend on investigation state and event history.

## Tasks

### 2.1 Database initialization

Configure:

- PostgreSQL connection.
- SQLAlchemy 2.x.
- Database session lifecycle.
- Alembic migrations.
- UUID conventions.
- Timestamp conventions.

### 2.2 Implement core models

Recommended initial order:

1. Users and roles.
2. Datasets.
3. Dataset files.
4. Replay sessions.
5. Security events.
6. Detection rules.
7. Model versions.
8. Detection findings.
9. Entities.
10. Entity relationships.
11. Incident candidates.
12. Investigations.
13. Investigation state versions.
14. Investigation events.

### 2.3 Implement orchestration models

After the basic investigation model:

- Capabilities.
- Capability versions.
- Planner runs.
- Planner decisions.
- Agent tasks.
- Task dependencies.
- Task attempts.
- Orchestration checkpoints.

### 2.4 Implement supporting models

- Evidence.
- Knowledge sources.
- Knowledge documents.
- Knowledge chunks.
- Human reviews.
- Reports.
- Response simulations.
- Audit logs.
- Evaluation runs.
- Evaluation results.
- Prompt versions.
- Outbox events.

### 2.5 Repository layer

Implement repositories for:

- Dataset persistence.
- Event persistence.
- Detection persistence.
- Investigation persistence.
- Task persistence.
- Evidence persistence.
- Knowledge persistence.

### 2.6 Transaction handling

Implement:

- Transaction boundaries.
- Optimistic concurrency for investigation state.
- Idempotency keys.
- Task attempt history.
- Transactional outbox.

## Deliverables

- Database models.
- Alembic migrations.
- Database repositories.
- Database initialization scripts.
- Persistence tests.

## Exit criteria

- Database can be created from an empty state.
- Migrations execute successfully.
- Core entities can be persisted and retrieved.
- Investigation state versions are maintained.
- Foreign-key constraints work.
- Concurrent state updates are handled safely.

**Estimated effort:** 5–8 working days.

---

# 6. Phase 3 — Dataset Management and Replay Engine

## Objective

Establish a controlled and reproducible source of cybersecurity telemetry.

## Tasks

### 3.1 Dataset inspection

Inspect the selected CSE-CIC-IDS2018 files.

Determine:

- Available files.
- File formats.
- Column names.
- Timestamp formats.
- Label columns.
- Missing values.
- Duplicate records.
- Data quality issues.

Do not finalize the canonical event schema before this inspection.

### 3.2 Dataset registration

Implement:

- Dataset metadata.
- Dataset file metadata.
- File checksums.
- File size validation.
- Source metadata.
- Dataset version information.

### 3.3 File validation

Validate:

- Format.
- Encoding.
- Header.
- Required fields.
- Record structure.
- File size.
- Parsing errors.

### 3.4 Replay engine

Implement:

- File reading.
- Batch processing.
- Configurable replay speed.
- Replay pause.
- Replay resume.
- Replay cancellation.
- Replay progress.
- Rejected-record accounting.

### 3.5 Ground-truth separation

Create a separate evaluation-only interface for dataset labels.

Normal detection and Planner services must not access ground-truth labels.

## Deliverables

- Dataset registry.
- Dataset validation service.
- Replay engine.
- Replay session tracking.
- Dataset metadata.
- Ground-truth isolation.

## Exit criteria

- A selected dataset can be registered.
- Dataset files are validated.
- Replay can be started and stopped.
- Records are processed in controlled batches.
- Replay statistics are persisted.
- Original source records remain traceable.

**Estimated effort:** 4–6 working days.

---

# 7. Phase 4 — Event Ingestion and Normalization

## Objective

Convert heterogeneous dataset records into a consistent internal event representation.

## Tasks

### 4.1 Canonical SecurityEvent design

Derive the schema from actual dataset fields.

Potential fields include:

- Event identifier.
- Event timestamp.
- Source IP.
- Destination IP.
- Source port.
- Destination port.
- Protocol.
- Flow duration.
- Packet counts.
- Byte counts.
- Dataset reference.
- Source record reference.
- Dataset-specific attributes.

These are candidate fields, not assumptions about the exact source files.

### 4.2 Normalization

Implement:

- Timestamp conversion.
- IP normalization.
- Port validation.
- Protocol normalization.
- Missing-value handling.
- Numeric conversion.
- Duplicate handling.

### 4.3 Ingestion pipeline

```text
Raw Dataset Record
        |
        v
Record Parser
        |
        v
Field Validation
        |
        v
Normalization
        |
        v
SecurityEvent
        |
        v
PostgreSQL
```

### 4.4 Error handling

Rejected records should include:

- Source file.
- Source record identifier or row position.
- Rejection reason.
- Processing timestamp.

### 4.5 Ingestion performance

Implement batch writes rather than individual database commits for every record.

Measure throughput before optimizing further.

## Deliverables

- SecurityEvent schema.
- Normalization service.
- Ingestion service.
- Rejected-record handling.
- Event persistence.
- Ingestion metrics.

## Exit criteria

- Selected source files can be ingested.
- Normalized events are persisted.
- Invalid records are handled without crashing the entire replay.
- Event provenance is preserved.
- Ground truth remains isolated.

**Estimated effort:** 4–6 working days.

---

# 8. Phase 5 — Detection Engine

## Objective

Identify suspicious activity through a hybrid detection architecture.

## Tasks

### 5.1 Detection architecture

Implement two independent detection approaches:

- Rule-based detection.
- ML-based detection.

Combine their outputs through a common detection-result contract.

### 5.2 Rule-based detection

Implement a configurable rule engine.

Responsibilities:

- Load enabled rules.
- Evaluate applicable event features.
- Produce findings.
- Assign severity.
- Record rule version.
- Provide a detection explanation.

### 5.3 ML-based detection

Inspect available labeled dataset features.

Implement the appropriate baseline models.

Potential models should be selected after data profiling rather than assumed in advance.

Required steps:

1. Feature selection.
2. Preprocessing.
3. Train/validation/test split.
4. Training.
5. Model persistence.
6. Inference.
7. Evaluation.

### 5.4 Leakage prevention

Ensure:

- Ground-truth labels are not inference features.
- Training and test splits avoid leakage.
- Related records are not unintentionally distributed across splits.
- Preprocessing is fitted only on training data.

### 5.5 Detection result contract

Every finding should contain:

- Finding ID.
- Event reference.
- Detection method.
- Predicted class.
- Severity.
- Confidence, if available.
- Rule or model version.
- Explanation.
- Detection timestamp.

### 5.6 Alert generation

Convert qualifying findings into alert records or alert projections according to the existing API design.

## Deliverables

- Rule engine.
- Baseline ML model.
- Detection service.
- Finding persistence.
- Alert integration.
- Detection evaluation scripts.

## Exit criteria

- Rule-based detection works.
- ML inference works.
- Detection outputs share a common schema.
- Finding provenance is preserved.
- Initial benchmark metrics are available.

**Estimated effort:** 6–9 working days.

---

# 9. Phase 6 — Correlation Engine

## Objective

Associate related security events and findings into incident candidates.

## Tasks

### 6.1 Entity resolution

Identify entities such as:

- IP addresses.
- Hosts.
- User accounts, where available.
- Network endpoints.
- Other relevant identifiers.

Normalize entity values.

### 6.2 Temporal correlation

Implement:

- Event time-window analysis.
- Related-event grouping.
- Sequence identification.
- Temporal ordering.

### 6.3 Relationship modeling

Create relationships between:

- Events.
- Findings.
- Entities.
- Incident candidates.

### 6.4 Correlation scoring

Implement a configurable score using relevant signals such as:

- Temporal proximity.
- Shared entities.
- Detection severity.
- Pattern similarity.
- Evidence support.

An illustrative scoring model:

\[
C = w_tT + w_eE + w_sS
\]

Where:

- \(T\) is temporal similarity.
- \(E\) is entity relationship strength.
- \(S\) is detection-pattern similarity.
- Weights must be tuned using validation data.

### 6.5 Incident candidate generation

Generate candidates when correlation criteria are satisfied.

Avoid treating every isolated finding as a confirmed incident.

## Deliverables

- Entity resolution service.
- Temporal correlation engine.
- Relationship persistence.
- Correlation scoring.
- Incident candidate generation.

## Exit criteria

- Related findings can be associated.
- Entity relationships are persisted.
- Temporal patterns can be identified.
- Incident candidates retain supporting references.
- Correlation can be evaluated independently.

**Estimated effort:** 4–6 working days.

---

# 10. Phase 7 — Investigation Management

## Objective

Implement the durable investigation lifecycle before introducing autonomous orchestration.

## Tasks

### 7.1 Investigation creation

Support creation from:

- Incident candidates.
- Analyst requests.
- Manual investigation initiation.

### 7.2 Investigation state machine

Implement statuses:

```text
created
queued
initializing
investigating
awaiting_review
paused
blocked
completed
closed
failed
cancelled
```

Validate all state transitions.

### 7.3 Investigation state

Implement structured state containing:

- Facts.
- Entities.
- Evidence references.
- Knowledge references.
- Hypotheses.
- Unresolved questions.
- Task history.
- Planner decisions.
- Execution constraints.
- Completion conditions.

### 7.4 State versioning

Implement:

- State snapshots.
- State version numbers.
- Optimistic concurrency.
- Investigation event history.

### 7.5 Evidence and hypothesis interfaces

Implement basic evidence and hypothesis persistence.

### 7.6 Investigation API

Implement:

- Create investigation.
- Retrieve investigation.
- List investigations.
- Update supported metadata.
- Pause.
- Resume.
- Cancel.
- Retrieve timeline.

## Deliverables

- Investigation service.
- State machine.
- State manager.
- State history.
- Investigation APIs.

## Exit criteria

- Investigation can be created and retrieved.
- Valid state transitions work.
- Invalid transitions are rejected.
- State versions are preserved.
- Investigation history is available.

**Estimated effort:** 4–6 working days.

---

# 11. Phase 8 — Capability Registry and Task Executor

<badge color="info">Critical orchestration dependency</badge>

## Objective

Build a controlled execution system through which the Planner can invoke specialized capabilities.

The registry and executor must be implemented before allowing the Planner to schedule arbitrary tasks.

## Tasks

### 8.1 Capability registry

Register capabilities such as:

| Capability | Purpose |
|---|---|
| `detection.analyze_events` | Run detection |
| `correlation.analyze_entities` | Entity correlation |
| `correlation.analyze_temporal_patterns` | Temporal analysis |
| `investigation.collect_evidence` | Evidence collection |
| `knowledge.retrieve_context` | RAG retrieval |
| `reporting.generate_report` | Report generation |
| `response.simulate_action` | Response simulation |

Names are proposed examples; the final registry should match actual service interfaces.

### 8.2 Capability contract

Every capability must declare:

- Identifier.
- Version.
- Description.
- Input schema.
- Output schema.
- Risk classification.
- Permission requirements.
- Timeout.
- Retry policy.
- Human-review requirement.

### 8.3 Task executor

Implement:

- Task validation.
- Task creation.
- Task dispatch.
- Task claiming.
- Worker invocation.
- Output validation.
- Result persistence.
- Retry management.
- Timeout management.

### 8.4 Task lifecycle

```text
proposed
   |
   v
validating
   |
   v
pending
   |
   v
queued
   |
   v
running
   |
   +------ completed
   |
   +------ failed
   |
   +------ blocked
   |
   +------ retrying
   |
   +------ cancelled
```

### 8.5 Reliability

Implement:

- Idempotency keys.
- Attempt records.
- Task dependencies.
- Concurrency limits.
- Transactional outbox.
- Durable task state.

### 8.6 Worker contracts

All workers should return validated structured outputs rather than arbitrary unstructured text.

## Deliverables

- Capability registry.
- Capability versions.
- Task executor.
- Task queue integration.
- Task lifecycle management.
- Worker interface.
- Execution tests.

## Exit criteria

- Capabilities can be registered and discovered.
- Invalid requests are rejected.
- Authorized tasks execute.
- Task outputs are validated.
- Retries are controlled.
- Duplicate delivery does not cause uncontrolled duplicate execution.

**Estimated effort:** 5–8 working days.

---

# 12. Phase 9 — Planner and Dynamic Multi-Agent Orchestration

<badge color="success">Core architectural differentiator</badge>

## Objective

Implement the Planner and LangGraph runtime that dynamically coordinates specialized workers.

This phase should begin only after the investigation state model, capability registry and task executor are sufficiently stable.

## Tasks

### 9.1 Planner interface

The Planner receives:

- Investigation state.
- Known facts.
- Evidence references.
- Hypotheses.
- Unresolved questions.
- Previous task results.
- Available capabilities.
- Execution constraints.

It produces a structured decision.

### 9.2 Planner decision types

Implement:

- `continue_investigation`
- `replan`
- `request_human_review`
- `complete_investigation`
- `escalate`
- `blocked`

### 9.3 Planner output validation

Validate:

- Decision type.
- Capability identifiers.
- Task input schemas.
- Task priorities.
- Dependency relationships.
- Resource limits.
- Completion conditions.

Invalid output must not reach the executor.

### 9.4 LangGraph implementation

Implement graph nodes for:

1. Investigation initialization.
2. State loading.
3. Planner execution.
4. Decision validation.
5. Task scheduling.
6. Task execution.
7. Result validation.
8. State update.
9. Human review.
10. Completion validation.

### 9.5 Dynamic orchestration

The Planner must support:

- Multiple capabilities in one cycle.
- Conditional task execution.
- Independent task parallelism.
- Sequential dependencies where necessary.
- Repeated capability invocation.
- Replanning after new evidence.
- Investigation pausing.
- Human review.
- Completion or escalation.

### 9.6 Non-linear investigation test

Create a test where:

1. The Planner initially selects correlation.
2. Correlation returns new relationships.
3. Investigation state changes.
4. Planner identifies a new unresolved question.
5. Planner invokes an additional capability.
6. New evidence is collected.
7. Planner reassesses the investigation.

This test is mandatory.

### 9.7 Completion validation

The Planner must not be allowed to complete an investigation merely because the LLM says it is complete.

Implement deterministic checks for:

- Outstanding tasks.
- Required evidence.
- Required report.
- Pending review.
- Blocked conditions.
- Investigation-specific completion requirements.

### 9.8 Recovery

Implement:

- LangGraph checkpointing.
- Durable investigation state.
- Resume after interruption.
- Task reconciliation.
- Retry limits.
- Planner cycle limits.

### 9.9 Resource controls

Set configurable limits for:

- Planner cycles.
- Tasks per investigation.
- Concurrent tasks.
- Worker execution time.
- LLM requests.
- Retry attempts.
- Token consumption, where measurable.

## Deliverables

- Planner implementation.
- LangGraph orchestration graph.
- Structured decision schema.
- Dynamic capability selection.
- State-driven replanning.
- Checkpoint recovery.
- Orchestration evaluation tests.

## Exit criteria

- Planner can dynamically select capabilities.
- Planner can invoke multiple workers.
- Planner can revisit capabilities.
- Planner can replan after new evidence.
- Invalid decisions are rejected.
- Completion is independently validated.
- Investigation can recover after interruption.

**Estimated effort:** 7–12 working days.

---

# 13. Phase 10 — RAG and Evidence Integration

## Objective

Ground investigation analysis in authoritative cybersecurity knowledge and preserve evidence provenance.

## Tasks

### 10.1 Knowledge-source registration

Register approved sources:

- MITRE ATT&CK.
- Sigma.
- CVE/NVD.
- CAPEC.
- Approved incident-response playbooks.

### 10.2 Knowledge ingestion

Implement:

- Document fetching or import.
- Parsing.
- Content normalization.
- Content hashing.
- Document versioning.
- Structure-aware chunking.

### 10.3 Embedding and indexing

Implement:

- Embedding generation.
- ChromaDB collections.
- Metadata filtering.
- Vector indexing.
- Index version tracking.

### 10.4 Retrieval

Implement:

- Semantic retrieval.
- Metadata filtering.
- Hybrid retrieval if supported.
- Reranking where justified.
- Context construction.

### 10.5 Evidence integration

Connect retrieved knowledge references with:

- Investigations.
- Hypotheses.
- Reports.
- Analyst conclusions.

### 10.6 Citation validation

Ensure:

- Source identifiers are preserved.
- Document versions are recorded.
- Retrieved content can be traced.
- Unsupported claims are not presented as established facts.

### 10.7 RAG security

Implement:

- Approved source restrictions.
- Prompt-injection handling.
- Untrusted-content boundaries.
- Retrieval output validation.

## Deliverables

- Knowledge ingestion service.
- ChromaDB integration.
- Retrieval service.
- Knowledge metadata persistence.
- Evidence integration.
- Citation support.

## Exit criteria

- Approved documents can be ingested.
- Relevant knowledge can be retrieved.
- Retrieval references are traceable.
- Investigation reports can cite knowledge sources.
- Untrusted retrieved instructions cannot authorize execution.

**Estimated effort:** 5–8 working days.

---

# 14. Phase 11 — Reporting and Human-in-the-Loop Response

## Objective

Complete the investigation lifecycle by generating analyst-ready reports and supporting safe response simulations.

## Tasks

### 11.1 Reporting worker

Generate reports containing:

- Executive summary.
- Incident classification.
- Severity.
- Timeline.
- Affected entities.
- Detection findings.
- Investigation hypotheses.
- Supporting evidence.
- Knowledge references.
- Recommendations.
- Confidence limitations.

### 11.2 Report validation

Validate:

- Required sections.
- Evidence references.
- Source citations.
- Consistency with investigation state.
- Separation of facts and hypotheses.

### 11.3 Human review

Implement:

- Review request creation.
- Review queue.
- Approval.
- Rejection.
- Request changes.
- Reviewer comments.
- Review history.

### 11.4 Response simulation

Implement simulation-only actions such as:

- Simulated IP blocking.
- Simulated endpoint isolation.
- Simulated account suspension.
- Simulated escalation.

### 11.5 Approval enforcement

Approval must be tied to:

- The proposed action.
- The target.
- The relevant investigation state version.

A changed action requires fresh approval.

### 11.6 Investigation closure

Implement finalization conditions and terminal-state validation.

## Deliverables

- Reporting worker.
- Report persistence.
- Report viewer API.
- Human-review workflow.
- Response simulation service.
- Investigation completion validation.

## Exit criteria

- Reports are generated.
- Reports reference supporting evidence.
- Human review works.
- Response actions remain simulation-only.
- Approval decisions are auditable.
- Investigations can be completed correctly.

**Estimated effort:** 5–7 working days.

---

# 15. Phase 12 — Frontend Integration

## Objective

Provide a complete SOC analyst interface connected to the backend APIs.

The frontend should be integrated progressively, not postponed entirely until backend development is finished.

## Tasks

### 12.1 Application shell

Implement:

- Navigation.
- Authentication screens.
- Dashboard layout.
- Global loading states.
- Error notifications.

### 12.2 Dashboard

Display:

- Total events.
- Alerts.
- Open investigations.
- Severity distribution.
- Recent activity.
- System status.

### 12.3 Dataset management

Implement:

- Dataset registration.
- File metadata.
- Replay controls.
- Replay progress.
- Validation results.

### 12.4 Alert management

Display:

- Alert list.
- Severity.
- Classification.
- Confidence.
- Timestamp.
- Related entities.

### 12.5 Investigation workspace

Implement:

- Investigation overview.
- Investigation timeline.
- Evidence viewer.
- Hypotheses.
- Unresolved questions.
- Task history.
- Planner decisions.

### 12.6 Agent activity view

Display:

- Planner cycles.
- Capability selection.
- Task status.
- Worker output summaries.
- Replanning activity.
- Execution errors.

This view should make dynamic orchestration visible to the analyst.

### 12.7 RAG and report viewer

Display:

- Retrieved knowledge.
- Source attribution.
- Evidence references.
- Final report.

### 12.8 Human-review interface

Implement:

- Pending review queue.
- Action details.
- Approval.
- Rejection.
- Comments.
- Review history.

### 12.9 Live updates

Use polling initially if it satisfies the MVP.

Introduce WebSockets or server-sent events only when needed for a better analyst experience.

## Deliverables

- Functional SOC dashboard.
- Dataset management screens.
- Alert views.
- Investigation workspace.
- Agent activity view.
- Evidence viewer.
- Reports.
- Review interface.

## Exit criteria

- Analyst can access the main workflows.
- UI reflects persisted backend state.
- API errors are handled.
- Agent execution activity is visible.
- Human review works from the interface.

**Estimated effort:** 7–10 working days.

---

# 16. Phase 13 — Evaluation, Security and Reliability

## Objective

Validate the integrated platform and establish reproducible performance evidence.

## Tasks

### 13.1 Unit tests

Test:

- Normalization.
- Detection rules.
- ML preprocessing.
- Correlation functions.
- State transitions.
- Capability validation.
- Task execution.
- Evidence validation.
- Report generation.

### 13.2 Integration tests

Test interactions between:

- Dataset and replay.
- Replay and ingestion.
- Ingestion and detection.
- Detection and correlation.
- Correlation and investigation.
- Planner and executor.
- Worker and state manager.
- RAG and investigation.
- Reporting and evidence.
- Review and response simulation.

### 13.3 End-to-end tests

Test the complete investigation lifecycle.

### 13.4 Benchmark evaluation

Implement and execute:

- B0: Rule-based detection.
- B1: Traditional ML detection.
- B2: Single-agent investigation.
- B3: Fixed multi-agent workflow.
- P1: Dynamic Planner orchestration.

### 13.5 Detection evaluation

Calculate:

- Precision.
- Recall.
- F1.
- FPR.
- Macro F1.
- Weighted F1.
- Balanced accuracy.

### 13.6 Orchestration evaluation

Calculate:

- Planner routing precision.
- Replanning effectiveness.
- Task success rate.
- Investigation success rate.
- Planner cycles.
- Unnecessary task count.
- Execution latency.

### 13.7 Evidence and reporting evaluation

Measure:

- Evidence completeness.
- Evidence precision.
- Citation coverage.
- Unsupported claim rate.
- Report completeness.

### 13.8 Security testing

Test:

- Authentication.
- Authorization.
- Prompt injection.
- Malformed Planner outputs.
- Unauthorized capability requests.
- Dataset upload validation.
- Secret handling.
- Human-review enforcement.

### 13.9 Reliability testing

Simulate:

- Ollama unavailable.
- Redis unavailable.
- ChromaDB unavailable.
- Worker crashes.
- Task timeouts.
- Interrupted investigations.
- Database connection failures.

### 13.10 Performance profiling

Measure:

- Ingestion throughput.
- Event query latency.
- Detection latency.
- Correlation latency.
- Planner latency.
- Task execution latency.
- Report generation latency.

## Deliverables

- Automated test suite.
- Evaluation scripts.
- Baseline comparison.
- Performance results.
- Security test report.
- Reliability report.
- Known limitations.

## Exit criteria

- Critical integration tests pass.
- Evaluation is reproducible.
- Ground-truth leakage is prevented.
- Security tests pass.
- Failure recovery works.
- No critical unresolved defects remain for the demonstration.

**Estimated effort:** 7–10 working days.

---

# 17. Phase 14 — Final Deployment and Demonstration

## Objective

Prepare a stable, reproducible and documented Project Sentinel demonstration environment.

## Tasks

### 14.1 Deployment hardening

- Disable debug mode.
- Validate secrets.
- Restrict service ports.
- Configure persistent volumes.
- Configure resource limits.
- Verify health checks.
- Verify backup procedures.

### 14.2 Dataset preparation

- Freeze selected dataset files.
- Record checksums.
- Prepare replay configuration.
- Verify attack scenarios.
- Validate evaluation labels.

### 14.3 Demonstration preparation

Prepare one primary investigation and at least one alternative scenario.

Ensure the primary demonstration shows:

- Detection.
- Correlation.
- Investigation.
- Planner decisions.
- Dynamic replanning.
- Evidence collection.
- RAG.
- Report generation.
- Human review.
- Response simulation.

### 14.4 Documentation

Complete:

- README.
- Installation guide.
- Architecture overview.
- API documentation.
- Dataset guide.
- Evaluation report.
- Security notes.
- Known limitations.
- Demonstration runbook.

### 14.5 Final validation

Run the complete demonstration from a clean environment.

Do not rely solely on a previously running development environment.

## Deliverables

- Demonstration-ready deployment.
- Final source code.
- Setup instructions.
- Evaluation report.
- Demonstration artifacts.
- Final handover package.

## Exit criteria

- System can be started reproducibly.
- Complete investigation workflow works.
- Evaluation results are available.
- Demonstration scenario is repeatable.
- Documentation matches the implemented system.

**Estimated effort:** 3–5 working days.

---

# 18. Overall Implementation Timeline

The following is an illustrative schedule for a small development team. It assumes one primary implementation stream, with frontend, evaluation and documentation work overlapping where dependencies permit.

| Phase | Estimated working days |
|---|---:|
| 0. Repository audit | 2–4 |
| 1. Infrastructure | 3–5 |
| 2. Database foundation | 5–8 |
| 3. Dataset management | 4–6 |
| 4. Ingestion and normalization | 4–6 |
| 5. Detection | 6–9 |
| 6. Correlation | 4–6 |
| 7. Investigation management | 4–6 |
| 8. Capability registry and executor | 5–8 |
| 9. Planner and orchestration | 7–12 |
| 10. RAG and evidence | 5–8 |
| 11. Reporting and review | 5–7 |
| 12. Frontend integration | 7–10 |
| 13. Evaluation and hardening | 7–10 |
| 14. Final deployment | 3–5 |

The sequential sum is approximately 65–110 working days.

This is a planning estimate, not a committed schedule. Reuse of existing modules, team size, LLM inference performance and dataset preparation may substantially change it.

---

# 19. Critical Path

The following dependencies determine the primary implementation sequence.

```text
Repository Audit
       |
       v
Infrastructure
       |
       v
Database Foundation
       |
       v
Dataset Management
       |
       v
Event Normalization
       |
       v
Detection
       |
       v
Correlation
       |
       v
Investigation State
       |
       v
Capability Registry
       |
       v
Task Executor
       |
       v
Planner and LangGraph
       |
       v
RAG and Evidence
       |
       v
Reporting and Human Review
       |
       v
End-to-End Integration
       |
       v
Evaluation and Demonstration
```

Frontend development should proceed in parallel after the API contracts are stable.

RAG ingestion and initial evaluation infrastructure can also be developed in parallel with detection and correlation.

---

# 20. Recommended Development Workstreams

For parallel development, divide work into the following streams.

| Workstream | Responsibilities |
|---|---|
| A — Backend and persistence | APIs, database, services and migrations |
| B — Detection and data engineering | Dataset inspection, replay, ingestion, detection |
| C — AI and orchestration | Capability registry, workers, Planner, LangGraph |
| D — Frontend | Dashboard, investigation workspace and review UI |
| E — Evaluation and security | Benchmarking, testing, security and reliability |

For a small team, these are responsibility areas rather than requirements for five separate developers.

### Integration rule

Every workstream must use shared API contracts, schemas and repository conventions.

Do not allow independent implementation streams to introduce incompatible representations of:

- SecurityEvent.
- DetectionFinding.
- Investigation.
- InvestigationState.
- AgentTask.
- Evidence.
- PlannerDecision.

---

# 21. Mandatory Milestone Gates

Development must not proceed to the next major subsystem merely because code has been written.

Each milestone requires demonstrable acceptance.

| Gate | Required proof |
|---|---|
| G0 | Repository assessment completed |
| G1 | Infrastructure starts reliably |
| G2 | Database migrations and persistence work |
| G3 | Dataset replay works |
| G4 | Normalized events persist correctly |
| G5 | Detection produces traceable findings |
| G6 | Correlation produces incident candidates |
| G7 | Investigation state is durable |
| G8 | Registered capabilities execute correctly |
| G9 | Planner performs non-linear orchestration |
| G10 | RAG and evidence are traceable |
| G11 | Reports and human review work |
| G12 | Frontend supports analyst workflows |
| G13 | Evaluation and security validation pass |
| G14 | Clean deployment and demonstration succeed |

If a gate fails, resolve the issue before treating dependent functionality as complete.

---

# 22. Definition of the Minimum Working System

The first major project objective should not be a polished dashboard or a large collection of agents.

It should be a minimal, fully working investigation workflow.

The minimum working system must demonstrate:

1. One selected dataset can be replayed.
2. Events can be normalized.
3. Suspicious events can be detected.
4. Related findings can be correlated.
5. An investigation can be created.
6. The Planner can choose a capability.
7. A worker can execute it.
8. The investigation state can be updated.
9. The Planner can re-evaluate the investigation.
10. The investigation can reach a validated completion state.

This is the earliest point at which the project's core architecture can be meaningfully demonstrated.

After this milestone, RAG, additional workers, reporting, UI refinement and advanced evaluation can expand the system.

---

# 23. Coding Agent Execution Rules

When using an AI coding agent to implement the project, follow these instructions.

## Rule 1 — Inspect before editing

The coding agent must inspect the existing repository and identify relevant files before proposing changes.

## Rule 2 — Preserve existing working functionality

Do not replace existing modules without proving that replacement is necessary.

## Rule 3 — Implement one phase at a time

Do not request implementation of the entire platform in one coding task.

## Rule 4 — Follow architecture contracts

Respect:

- API contracts.
- Database schema.
- Capability contracts.
- Investigation state model.
- Task lifecycle.
- Evidence provenance.
- Security boundaries.

## Rule 5 — Test every meaningful change

Run relevant unit and integration tests after implementation.

## Rule 6 — Do not fabricate implementation status

Clearly report:

- Implemented.
- Partially implemented.
- Not implemented.
- Blocked.
- Tested.
- Not tested.

## Rule 7 — Keep Planner autonomy bounded

The Planner must use registered capabilities. It must not receive unrestricted shell, database or infrastructure access.

## Rule 8 — Maintain reproducibility

Record model versions, prompt versions, dataset versions and evaluation configurations.

## Rule 9 — Avoid unrelated changes

A task targeting detection should not unnecessarily restructure authentication or the frontend.

## Rule 10 — Report exact changes

Every implementation task should report:

- Files created.
- Files modified.
- Files removed.
- Dependencies changed.
- Tests executed.
- Test outcomes.
- Remaining issues.

---

# 24. Recommended Immediate Execution Plan

The first five development tasks should be:

### Task 1 — Repository audit

Inspect the actual Project Sentinel repository and produce a repository assessment.

### Task 2 — Architecture gap analysis

Map actual modules to the target architecture and identify missing or conflicting components.

### Task 3 — Establish a working baseline

Run the current application, execute existing tests and record baseline failures.

### Task 4 — Finalize the implementation backlog

Convert the 14 phases into repository-specific development issues with dependencies and acceptance criteria.

### Task 5 — Begin infrastructure and database work

Only after the audit and architecture reconciliation, implement the first missing infrastructure components.

---

# 25. Final Implementation Strategy

The recommended implementation order is:

**First:** Establish the actual repository baseline and stabilize infrastructure.

**Second:** Build a reliable dataset-to-detection pipeline.

**Third:** Implement correlation and durable investigation management.

**Fourth:** Build the capability registry and task executor.

**Fifth:** Implement the Planner and dynamic LangGraph orchestration.

**Sixth:** Integrate RAG, evidence, reporting and human oversight.

**Seventh:** Complete frontend integration, evaluation, security and deployment.

The most important milestone is Phase 9.

Until the Planner can dynamically select capabilities, receive worker results, update investigation state and replan based on new evidence, Project Sentinel has not demonstrated its defining architectural contribution.

The development process should therefore prioritize a small but genuinely dynamic investigation system over a large collection of disconnected AI agents.

**Final implementation principle: Build the complete investigation lifecycle incrementally, validate every subsystem independently, and preserve dynamic Planner-driven orchestration throughout the project.**
