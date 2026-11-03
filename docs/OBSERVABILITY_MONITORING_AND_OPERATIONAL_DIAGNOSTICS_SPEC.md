# Project Sentinel
# Observability, Monitoring & Operational Diagnostics Specification

**Document Type:** Operational Architecture Specification  
**Version:** 1.0  
**Status:** Architecture Baseline  
**Primary Focus:** System observability, application monitoring, agent tracing, orchestration diagnostics, metrics, logging, health monitoring, and operational troubleshooting.

---

# 1. Purpose

Project Sentinel is a multi-layered AI-assisted security investigation system.

A single investigation may involve:

- Telemetry ingestion.
- Data normalization.
- Detection logic.
- Alert generation.
- Investigation creation.
- Agent orchestration.
- Multiple agent tasks.
- RAG retrieval.
- Capability execution.
- Evidence collection.
- Analyst review.

A failure or incorrect result can occur at any point in this workflow.

Therefore, the system requires observability across the complete execution path.

The central principle is:

> **Every important system operation should produce enough structured information to explain what happened, where it happened, and why the workflow reached its current state.**

---

# 2. Observability Objectives

The observability architecture has six primary objectives.

| Objective | Purpose |
|---|---|
| Visibility | Understand the current state of the system |
| Traceability | Follow an operation across components |
| Diagnostics | Identify the source of failures |
| Performance Analysis | Measure execution time and resource behavior |
| Agent Accountability | Understand agent and orchestration decisions |
| Evaluation | Collect measurable operational results |

These objectives apply to both infrastructure and the AI orchestration layer.

---

# 3. Observability Scope

Project Sentinel should observe the following layers:

```text
┌──────────────────────────────┐
│         FRONTEND             │
├──────────────────────────────┤
│         FASTAPI API          │
├──────────────────────────────┤
│    APPLICATION SERVICES      │
├──────────────────────────────┤
│     AGENT ORCHESTRATOR       │
├──────────────┬───────────────┤
│    AGENTS    │  CAPABILITIES │
├──────────────┼───────────────┤
│      RAG / RETRIEVAL         │
├──────────────┴───────────────┤
│   POSTGRES / REDIS / VECTOR  │
│         INFRASTRUCTURE       │
└──────────────────────────────┘
```

Observability should not be limited to server CPU usage or application errors.

The agent workflow itself is a first-class observable system.

---

# 4. The Three Core Observability Signals

The baseline implementation should collect three categories of telemetry.

## 4.1 Logs

Logs describe discrete events.

Examples:

```text
Investigation created
Agent task started
Capability execution failed
Database connection lost
```

---

## 4.2 Metrics

Metrics measure numerical system behavior.

Examples:

```text
API response time
Agent execution duration
Investigation completion time
Task failure rate
```

---

## 4.3 Traces

Traces connect related operations.

For example:

```text
API REQUEST
    │
    ▼
INVESTIGATION CREATED
    │
    ▼
ORCHESTRATOR
    │
    ├── Agent A
    │
    ├── Agent B
    │
    └── RAG Retrieval
```

A trace allows the system to connect these operations as part of one investigation workflow.

---

# 5. Correlation Architecture

Every significant investigation should have a unique correlation identifier.

The recommended identifiers are:

```text
request_id
investigation_id
task_id
trace_id
```

Their purposes are:

| Identifier | Purpose |
|---|---|
| request_id | Tracks an API request |
| investigation_id | Tracks the complete investigation |
| task_id | Tracks a specific orchestrated task |
| trace_id | Connects distributed operations |

A log record can therefore contain:

```json
{
  "timestamp": "2026-11-02T10:30:00Z",
  "level": "INFO",
  "investigation_id": "inv-001",
  "task_id": "task-014",
  "trace_id": "trace-abc",
  "event": "agent_task_started"
}
```

This enables cross-layer diagnostics.

---

# 6. Investigation Execution Trace

A complete investigation should be observable as a workflow.

```text
ALERT
  │
  ▼
INVESTIGATION CREATED
  │
  ▼
ORCHESTRATOR
  │
  ├──────────────┐
  ▼              ▼
TASK A          TASK B
  │              │
  ▼              ▼
AGENT           AGENT
  │              │
  └──────┬───────┘
         │
         ▼
EVIDENCE SYNTHESIS
         │
         ▼
CONCLUSION
```

The system should record major transitions rather than logging every internal model token or implementation detail.

---

# 7. Structured Logging

Logs should be structured rather than relying only on free-form text.

A recommended common schema is:

```text
timestamp
level
service
event
message
request_id
investigation_id
task_id
trace_id
error_code
```

Not every field is required for every event.

The important principle is consistency.

---

# 8. Log Levels

The MVP should use standard log levels.

| Level | Usage |
|---|---|
| DEBUG | Detailed development diagnostics |
| INFO | Normal system operations |
| WARNING | Unexpected but recoverable conditions |
| ERROR | Operation failure |
| CRITICAL | Severe system failure |

Example:

```text
INFO     investigation_created
INFO     agent_task_started
WARNING  retrieval_result_low_confidence
ERROR    llm_request_timeout
```

---

# 9. Event Classification

Events should be classified by subsystem.

Recommended categories:

```text
api
authentication
ingestion
detection
investigation
orchestration
agent
capability
retrieval
database
infrastructure
```

This allows operational filtering.

For example:

```text
category=agent
investigation_id=inv-001
```

can retrieve agent-specific events for one investigation.

---

# 10. Agent Execution Monitoring

Each agent task should expose a controlled execution lifecycle.

```text
CREATED
   │
   ▼
QUEUED
   │
   ▼
RUNNING
   │
   ├──────► FAILED
   │
   └──────► COMPLETED
```

Each transition should be observable.

Recommended task fields:

```text
task_id
investigation_id
agent_type
status
created_at
started_at
completed_at
duration_ms
retry_count
failure_reason
```

---

# 11. Agent Trace Record

A conceptual agent execution record is:

```json
{
  "task_id": "task-014",
  "investigation_id": "inv-001",
  "agent_type": "evidence_analysis",
  "status": "completed",
  "started_at": "2026-11-02T10:31:00Z",
  "completed_at": "2026-11-02T10:31:08Z",
  "duration_ms": 8000
}
```

Sensitive internal prompts or confidential data should not automatically be written into general-purpose logs.

---

# 12. Orchestrator Observability

The orchestrator is the central control component and requires dedicated visibility.

The system should record:

- Investigation received.
- Planning started.
- Tasks created.
- Tasks assigned.
- Dependencies identified.
- Retry decisions.
- Fallback decisions.
- Review escalation.
- Final workflow status.

Conceptually:

```text
INVESTIGATION
      │
      ▼
ORCHESTRATOR DECISION
      │
      ▼
DECISION EVENT
      │
      ├── Plan Created
      ├── Task Scheduled
      ├── Retry Selected
      ├── Fallback Selected
      └── Human Review Required
```

This makes the orchestration process demonstrable and diagnosable.

---

# 13. Orchestration Decision Logging

Important orchestration decisions should contain a structured explanation.

A conceptual schema is:

```text
decision_id
investigation_id
decision_type
reason
input_state
selected_action
timestamp
```

Example:

```json
{
  "decision_type": "human_review_required",
  "reason": "Conflicting evidence and insufficient confidence",
  "selected_action": "escalate_to_analyst"
}
```

The objective is not to expose hidden model reasoning.

The objective is to record the **system-level decision and the operational reason for that decision**.

---

# 14. Capability Monitoring

Every capability invoked by an agent should be observable.

The capability lifecycle is:

```text
AGENT REQUEST
     │
     ▼
CAPABILITY VALIDATION
     │
 ┌───┴────┐
 │        │
ALLOW    DENY
 │        │
 ▼        ▼
EXECUTE  RECORD
 │
 ▼
RESULT
```

Recommended metrics:

- Invocation count.
- Success rate.
- Failure rate.
- Average execution time.
- Timeout count.
- Permission denial count.

---

# 15. RAG and Retrieval Monitoring

The retrieval system should be monitored separately from agent execution.

Important events include:

```text
Retrieval request
Documents retrieved
No relevant context found
Low relevance result
Vector database unavailable
```

Recommended retrieval metrics:

| Metric | Purpose |
|---|---|
| Retrieval latency | Measures retrieval performance |
| Result count | Measures amount of returned context |
| Empty retrieval rate | Identifies knowledge gaps |
| Relevance score distribution | Supports retrieval evaluation |

The system should distinguish:

```text
NO RELEVANT CONTEXT FOUND
```

from:

```text
RETRIEVAL SYSTEM FAILED
```

These represent different operational conditions.

---

# 16. LLM and AI Service Monitoring

The AI service should be treated as an external dependency.

Important metrics include:

```text
llm_request_count
llm_success_count
llm_failure_count
llm_timeout_count
llm_latency_ms
```

A conceptual success rate is:

\[
LLM\ Success\ Rate =
\frac{Successful\ Requests}
{Total\ Requests}
\times 100
\]

For example:

```text
95 successful requests
5 failed requests

LLM Success Rate = 95%
```

This measures service reliability, not the intelligence or accuracy of the agent.

---

# 17. Agent Reliability Metrics

Agent execution reliability can be measured separately.

## Task Success Rate

\[
Task\ Success\ Rate =
\frac{Completed\ Tasks}
{Total\ Tasks}
\times 100
\]

## Task Failure Rate

\[
Task\ Failure\ Rate =
\frac{Failed\ Tasks}
{Total\ Tasks}
\times 100
\]

## Average Task Duration

\[
Average\ Duration =
\frac{\sum Task\ Duration}
{Number\ of\ Tasks}
\]

These metrics allow comparison between agent types and workflows.

---

# 18. Investigation Lifecycle Metrics

The complete investigation should also be measured.

Recommended metrics:

| Metric | Meaning |
|---|---|
| Investigation count | Number of investigations created |
| Completion rate | Percentage reaching completion |
| Review escalation rate | Percentage requiring human review |
| Average investigation time | End-to-end execution time |
| Failure rate | Percentage ending in failure |

The end-to-end duration is:

\[
Investigation\ Duration =
Completion\ Time - Creation\ Time
\]

---

# 19. Application Performance Monitoring

The FastAPI service should monitor:

- Request count.
- Response latency.
- Error rate.
- Endpoint performance.

A useful latency metric is:

\[
Average\ API\ Latency =
\frac{\sum Response\ Times}
{Total\ Requests}
\]

Important endpoints can be measured separately.

---

# 20. Error Classification

Errors should not all be recorded as generic failures.

Recommended categories:

```text
VALIDATION_ERROR
AUTHENTICATION_ERROR
AUTHORIZATION_ERROR
DATABASE_ERROR
RETRIEVAL_ERROR
LLM_TIMEOUT
AGENT_EXECUTION_ERROR
CAPABILITY_ERROR
INFRASTRUCTURE_ERROR
```

This enables meaningful diagnostics.

For example:

```text
100 errors
 ├── 60 validation errors
 ├── 25 LLM timeouts
 └── 15 database failures
```

This provides more value than a single generic error count.

---

# 21. Failure Propagation Monitoring

The system should record how failures affect the investigation.

```text
COMPONENT FAILURE
       │
       ▼
TASK FAILURE
       │
       ▼
ORCHESTRATOR EVALUATION
       │
  ┌────┼─────┐
  ▼    ▼     ▼
RETRY FALLBACK REVIEW
```

The selected path should be recorded.

This is important for demonstrating the project's fault-tolerant agent architecture.

---

# 22. Health Checks

Each major service should expose a health status.

Conceptually:

```text
/health
```

The system can distinguish:

```text
HEALTHY
DEGRADED
UNAVAILABLE
```

For example:

| Service | Possible Status |
|---|---|
| Backend API | Healthy |
| PostgreSQL | Healthy |
| Redis | Healthy |
| ChromaDB | Degraded |
| AI Service | Unavailable |

---

# 23. Readiness vs Liveness

The deployment architecture should distinguish two concepts.

## Liveness

Answers:

> Is the service process running?

## Readiness

Answers:

> Is the service ready to perform its intended operations?

For example:

```text
Backend Process Running
        │
        ▼
Database Connection?
        │
        ▼
Required Dependencies Available?
        │
        ▼
READY
```

This distinction becomes important when services are deployed using containers.

---

# 24. Operational Dashboard

The MVP should provide a simple operational view.

Recommended sections:

### System Health

```text
API          ✓ Healthy
Database     ✓ Healthy
Redis        ✓ Healthy
AI Service   ⚠ Degraded
```

### Investigation Activity

```text
Active Investigations: 4
Waiting for Review: 2
Completed Today: 12
```

### Agent Activity

```text
Tasks Running: 3
Tasks Failed: 1
Average Duration: 6.2 seconds
```

This dashboard is operational and should remain separate from the analyst's incident investigation dashboard.

---

# 25. Investigation Diagnostic View

For an individual investigation, the system should make the workflow visible.

```text
INVESTIGATION: inv-001

[✓] Alert Received
[✓] Plan Created
[✓] Evidence Analysis
[✓] Context Retrieval
[!] Network Analysis Failed
[✓] Fallback Completed
[→] Waiting for Analyst Review
```

This representation is valuable during:

- Development.
- Testing.
- Demonstration.
- Failure diagnosis.

---

# 26. Observability Data Flow

The complete data flow is:

```text
SYSTEM COMPONENT
       │
       ▼
STRUCTURED EVENT
       │
       ▼
LOG / METRIC / TRACE
       │
       ▼
OBSERVABILITY STORAGE
       │
       ▼
DASHBOARD / DIAGNOSTICS
```

All major components should use a consistent correlation model.

---

# 27. Sensitive Data in Observability

Observability must not become a source of data leakage.

Logs should avoid storing:

- Passwords.
- JWT secrets.
- Database credentials.
- Full confidential prompts where unnecessary.
- Sensitive raw telemetry without justification.

The principle is:

> **Log operational context, not unrestricted sensitive content.**

---

# 28. Alerting for System Failures

Operational alerts should be generated for significant infrastructure conditions.

Examples:

```text
Database unavailable
Repeated AI service failures
High API error rate
Agent task failure spike
```

A basic operational alert flow is:

```text
METRIC / ERROR
      │
      ▼
THRESHOLD CHECK
      │
      ▼
SYSTEM ALERT
      │
      ▼
OPERATOR ACTION
```

This is separate from the cybersecurity alerts processed by Project Sentinel itself.

---

# 29. Observability Technology Baseline

The exact tooling can evolve, but the architecture should support:

| Requirement | Recommended Approach |
|---|---|
| Application logs | Python structured logging |
| API monitoring | FastAPI middleware and metrics |
| Agent tracing | Structured orchestration events |
| Metrics | Prometheus-compatible metrics |
| Visualization | Grafana or equivalent |
| Distributed tracing | OpenTelemetry-compatible tracing |
| Health monitoring | API health endpoints |

For the MVP, implementation complexity should remain proportional to project requirements.

The architecture is more important than deploying every possible observability platform.

---

# 30. Minimum MVP Observability Requirements

The first implementation phase should provide:

### Logging

- Structured application logs.
- Investigation IDs.
- Task IDs.
- Error classification.

### Agent Visibility

- Task lifecycle events.
- Agent execution duration.
- Task failure reason.

### Orchestrator Visibility

- Plan creation.
- Task assignment.
- Retry and fallback events.
- Review escalation.

### Infrastructure

- Basic health checks.
- Database connectivity status.
- AI service availability.

### Metrics

- API error rate.
- Agent task success rate.
- Investigation duration.
- AI request failures.

---

# 31. Advanced Observability Enhancements

These can be implemented after the baseline.

```text
Distributed tracing
Agent performance comparison
Prompt and response version tracking
Cost tracking
Model performance comparison
Automated anomaly detection for system metrics
```

These should be prioritized only when they provide measurable value.

---

# 32. Operational Troubleshooting Workflow

When an investigation does not complete correctly:

```text
INVESTIGATION ISSUE
       │
       ▼
CHECK INVESTIGATION STATE
       │
       ▼
CHECK ORCHESTRATION EVENTS
       │
       ▼
CHECK AGENT TASKS
       │
       ▼
CHECK CAPABILITY / RAG EVENTS
       │
       ▼
CHECK DEPENDENCY HEALTH
       │
       ▼
IDENTIFY FAILURE
```

The correlation identifiers connect these layers.

---

# 33. Observability Acceptance Criteria

The observability architecture is complete when:

### Logging

- Significant operations generate structured events.
- Errors contain meaningful classifications.
- Investigation and task identifiers are propagated.

### Agent Operations

- Agent task lifecycle is visible.
- Execution duration is measurable.
- Failures have recorded reasons.

### Orchestration

- Major decisions are observable.
- Retries and fallbacks are recorded.
- Review escalation is traceable.

### Infrastructure

- Major dependencies expose health information.
- Service degradation can be identified.

### Metrics

- API performance is measurable.
- Agent reliability is measurable.
- Investigation duration is measurable.

### Security

- Sensitive secrets are not exposed through logs.
- Observability data maintains appropriate access boundaries.

---

# 34. Complete Observability Architecture

```text
                         PROJECT SENTINEL
                                │
       ┌────────────────────────┼────────────────────────┐
       ▼                        ▼                        ▼
    LOGS                     METRICS                  TRACES
       │                        │                        │
       ├── API Events           ├── API Latency          ├── Request Flow
       ├── Agent Events         ├── Task Success         ├── Investigation
       ├── Orchestration        ├── Failure Rate         ├── Agent Execution
       ├── Capability Events    └── Investigation Time   └── Capability Flow
       │                        │                        │
       └────────────────────────┼────────────────────────┘
                                │
                                ▼
                     OPERATIONAL DIAGNOSTICS
                                │
                 ┌──────────────┼──────────────┐
                 ▼              ▼              ▼
              HEALTH        DASHBOARD      TROUBLESHOOTING
```

---

# 35. Final Principle

Project Sentinel's observability architecture should provide visibility into both the **technical operation of the platform** and the **execution of the AI-driven investigation workflow**.

The complete operational model is:

```text
SYSTEM ACTIVITY
      │
      ▼
STRUCTURED OBSERVABILITY DATA
      │
      ├── Logs
      ├── Metrics
      └── Traces
      │
      ▼
CORRELATED SYSTEM VIEW
      │
      ▼
DIAGNOSIS + EVALUATION + IMPROVEMENT
```

The most important principle is:

> **If an investigation succeeds, fails, retries, escalates, or produces an unexpected result, Project Sentinel should provide enough operational evidence to determine what happened without treating the AI orchestration layer as an invisible black box.**

---

# Next Recommended Document

## Testing, Validation & Evaluation Strategy Specification

The next document should define how the complete Project Sentinel system will be tested and how its results will be evaluated.

It should cover:

- Unit testing.
- Integration testing.
- API testing.
- Agent testing.
- Orchestrator testing.
- RAG evaluation.
- Detection evaluation.
- Attack scenario testing.
- Fault injection.
- Performance testing.
- Baseline comparison.
- Accuracy, precision, recall, and F1-score.
- Agent success and reliability metrics.
- End-to-end acceptance testing.

This is the next critical document because the project's architectural sophistication must ultimately be supported by **measurable, reproducible results**.
