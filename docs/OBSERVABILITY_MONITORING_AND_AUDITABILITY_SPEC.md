# Project Sentinel
# Observability, Monitoring & Auditability Specification

**Document Type:** Operational Architecture Specification  
**Version:** 1.0  
**Status:** Architecture Baseline  
**Primary Focus:** Structured logging, metrics, tracing, agent observability, orchestration monitoring, auditability, failure analysis, and operational visibility.

---

# 1. Purpose

Project Sentinel contains multiple interconnected components:

- Telemetry ingestion.
- Data normalization.
- Detection.
- Alert management.
- AI-driven investigation.
- Agent orchestration.
- Capability execution.
- Knowledge retrieval.
- Analyst interaction.

A failure or performance problem in any one of these components can affect the overall investigation workflow.

Therefore, the system must provide answers to questions such as:

- What is the system currently doing?
- Where did a request fail?
- How long did an investigation take?
- Which agent or capability performed an action?
- What evidence was used during an investigation?
- Why was an investigation escalated?
- Did an AI or infrastructure dependency fail?
- Which user approved or rejected an action?

The observability architecture should make the system **operationally understandable, traceable, and auditable**.

---

# 2. Core Observability Model

Project Sentinel should use three primary forms of operational visibility:

```text
LOGS
 │
 │ What happened?
 │
 ▼
METRICS
 │
 │ How is the system performing?
 │
 ▼
TRACES
 │
 │ How did an operation move through the system?
 │
 ▼
AUDIT RECORDS
 │
 │ Who performed an important action and what was the result?
```

These components serve different purposes and should not be treated as identical.

| Component | Primary Question |
|---|---|
| Logs | What happened? |
| Metrics | How much or how often? |
| Traces | What path did an operation follow? |
| Audit Records | Who did what and when? |

---

# 3. Observability Architecture

The overall flow is:

```text
┌─────────────────────────────────────────────────┐
│                PROJECT SENTINEL                 │
│                                                 │
│  Ingestion → Detection → Investigation          │
│                         │                       │
│                         ▼                       │
│                   Orchestration                 │
│                         │                       │
│                   ┌─────┴─────┐                 │
│                   ▼           ▼                 │
│                 Agents    Capabilities           │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│             OBSERVABILITY LAYER                 │
│                                                 │
│ Structured Logs                                 │
│ Metrics                                         │
│ Traces                                          │
│ Audit Events                                    │
└─────────────────────────────────────────────────┘
                     │
                     ▼
              Operational Analysis
```

Observability should be integrated into each major subsystem rather than added only after development is complete.

---

# 4. Design Principles

The observability architecture should follow these principles.

## 4.1 Correlation

Events belonging to the same operation should be traceable.

For example:

```text
REQUEST
   │
   ├── API LOG
   ├── INVESTIGATION EVENT
   ├── AGENT EXECUTION
   └── CAPABILITY RESULT
```

All of these should be connected through common identifiers where appropriate.

---

## 4.2 Structured Data

Logs should use structured fields instead of relying only on unstructured messages.

Preferred concept:

```json
{
  "event": "investigation_started",
  "investigation_id": "INV-001",
  "request_id": "REQ-001",
  "timestamp": "2026-11-02T10:30:00Z"
}
```

Structured logging improves:

- Filtering.
- Searching.
- Aggregation.
- Automated analysis.

---

## 4.3 Meaningful Events

The system should log meaningful lifecycle events.

Avoid logging excessive internal information without purpose.

A useful event answers at least one of:

- What happened?
- When did it happen?
- Which component was involved?
- What was the result?
- Which operation does it belong to?

---

## 4.4 Separation of Concerns

Operational logs and security audit records should remain conceptually separate.

```text
APPLICATION LOG

"The database query completed in 42 ms."
```

is different from:

```text
AUDIT EVENT

"Analyst approved investigation action."
```

The first supports system operations.

The second supports accountability.

---

# 5. Correlation Identifiers

Project Sentinel should use identifiers to connect operations.

Recommended identifiers include:

```text
request_id
investigation_id
alert_id
run_id
trace_id
agent_execution_id
```

Not every event requires every identifier.

The goal is to maintain enough context to reconstruct important workflows.

---

# 6. Request Correlation Flow

A typical API request follows:

```text
ANALYST
   │
   ▼
API REQUEST
   │
   │ request_id
   ▼
APPLICATION SERVICE
   │
   │ request_id
   ▼
INVESTIGATION
   │
   │ investigation_id
   ▼
AGENT ORCHESTRATION
   │
   │ agent_execution_id
   ▼
CAPABILITY EXECUTION
```

A failure can then be traced back through the workflow.

---

# 7. Structured Logging Standard

Every important log event should contain a consistent baseline.

Recommended fields:

| Field | Purpose |
|---|---|
| timestamp | Time of event |
| level | Severity |
| component | Source subsystem |
| event | Event name |
| request_id | Request correlation |
| investigation_id | Investigation correlation |
| message | Human-readable context |

Additional metadata should be added only when useful.

---

# 8. Log Severity Levels

A consistent severity model should be used.

| Level | Meaning |
|---|---|
| DEBUG | Detailed development information |
| INFO | Normal lifecycle event |
| WARNING | Unexpected but recoverable condition |
| ERROR | Operation failed |
| CRITICAL | Serious system-level failure |

Examples:

```text
INFO
Investigation created.

WARNING
LLM response timeout. Retry scheduled.

ERROR
Investigation execution failed.

CRITICAL
Primary persistence service unavailable.
```

Production logging should avoid excessive DEBUG-level output unless explicitly enabled.

---

# 9. Telemetry Pipeline Observability

The ingestion pipeline should expose important processing information.

Key events include:

```text
ingestion_started
batch_received
event_normalized
event_rejected
batch_completed
ingestion_completed
ingestion_failed
```

Important measurements include:

```text
events_processed
events_rejected
normalization_failures
processing_duration
```

This allows the team to determine whether dataset problems originate from:

- Input quality.
- Schema incompatibility.
- Normalization logic.
- Infrastructure failures.

---

# 10. Detection Observability

The detection layer should provide visibility into:

- Detection execution.
- Number of events evaluated.
- Alerts generated.
- Detection failures.
- Processing duration.

Example event:

```json
{
  "event": "alert_generated",
  "alert_id": "ALT-001",
  "detection_id": "DET-001",
  "severity": "high",
  "confidence": 0.82
}
```

The observability system should record detection activity without unnecessarily duplicating large volumes of raw telemetry.

---

# 11. Investigation Lifecycle Observability

Every major investigation transition should be observable.

Recommended events:

```text
investigation_created
investigation_started
investigation_stage_changed
investigation_waiting_for_review
investigation_escalated
investigation_completed
investigation_failed
```

Example:

```text
INVESTIGATION CREATED
        │
        ▼
INVESTIGATION STARTED
        │
        ▼
EVIDENCE COLLECTION
        │
        ▼
ANALYSIS
        │
        ▼
COMPLETED
```

Each important transition should be recorded with:

```text
previous_state
new_state
timestamp
reason
investigation_id
```

---

# 12. Agent Orchestration Observability

This is one of the most important observability areas.

The system should make agent activity visible at the **action level**, not expose hidden reasoning.

Recommended events:

```text
agent_task_assigned
agent_execution_started
agent_capability_requested
agent_capability_completed
agent_execution_completed
agent_execution_failed
```

The observability record should focus on:

- Agent role.
- Assigned task.
- Input reference.
- Capability used.
- Result status.
- Duration.

It should not require storing hidden reasoning traces.

---

# 13. Agent Execution Model

A typical agent operation is:

```text
ORCHESTRATOR
      │
      ▼
ASSIGN TASK
      │
      ▼
AGENT EXECUTION
      │
      ├── Request Capability
      │
      ▼
CAPABILITY RESULT
      │
      ▼
VALIDATE RESULT
      │
      ▼
RETURN SUMMARY
      │
      ▼
ORCHESTRATOR
```

Observability should record the transitions between these stages.

---

# 14. Agent Execution Record

A conceptual agent execution record may include:

```text
agent_execution_id
investigation_id
agent_role
task_type
started_at
completed_at
status
capabilities_used
failure_reason
```

This allows the system to answer:

> Which agent handled this task, and what happened?

without requiring exposure of private internal reasoning.

---

# 15. Capability Execution Observability

Capabilities represent controlled actions.

Each execution should generate a meaningful operational event.

Example:

```json
{
  "event": "capability_execution_completed",
  "capability": "telemetry_query",
  "investigation_id": "INV-001",
  "status": "success",
  "duration_ms": 142
}
```

Important capability metrics include:

- Execution count.
- Success rate.
- Failure rate.
- Average duration.
- Timeout count.

---

# 16. AI Model Observability

The system should monitor AI service interactions.

Important measurements may include:

```text
model_request_count
model_response_time
model_timeout_count
model_failure_count
retry_count
```

For development and evaluation, additional information may include:

- Model identifier.
- Request type.
- Output validation status.

Sensitive prompts, evidence, or secrets should not automatically be written to operational logs.

---

# 17. Failure Monitoring

Failures should be categorized.

Recommended categories:

| Category | Example |
|---|---|
| Infrastructure | Database unavailable |
| Validation | Invalid agent output |
| Dependency | AI service timeout |
| Capability | Tool execution failed |
| Application | Unexpected code error |
| Workflow | Invalid state transition |

A clear failure classification makes debugging significantly easier.

---

# 18. Investigation Failure Flow

The system should record how failures are handled.

```text
OPERATION
    │
    ▼
FAILURE
    │
    ▼
CLASSIFY FAILURE
    │
    ├── RETRYABLE
    │      │
    │      ▼
    │     RETRY
    │
    └── NON-RETRYABLE
           │
           ▼
      SAFE STATE
           │
           ▼
   ESCALATE / FAIL
```

The investigation record should indicate the actual outcome.

The system must not hide failed operations behind a false successful state.

---

# 19. Metrics Architecture

Metrics provide quantitative visibility into system behavior.

The system should monitor metrics at several levels.

```text
SYSTEM METRICS
      │
      ├── API
      ├── Ingestion
      ├── Detection
      ├── Investigation
      ├── Agents
      └── Capabilities
```

---

# 20. API Metrics

Recommended measurements:

```text
request_count
request_duration
error_count
response_status_count
```

Useful questions include:

- Which endpoints are used most often?
- Which requests are slow?
- Are error rates increasing?

---

# 21. Investigation Metrics

Important investigation metrics include:

```text
investigations_created
investigations_completed
investigations_escalated
investigations_failed
average_investigation_duration
```

A useful derived metric is:

### Investigation Completion Rate

\[
CompletionRate =
\frac{CompletedInvestigations}
{StartedInvestigations}
\]

This metric should be interpreted alongside failures and escalations.

---

# 22. Agent Metrics

Agent orchestration should be evaluated quantitatively.

Recommended metrics:

```text
agent_tasks_started
agent_tasks_completed
agent_task_failures
average_agent_duration
capability_requests
```

A basic success metric is:

\[
AgentSuccessRate =
\frac{SuccessfulTasks}
{TotalTasks}
\]

This measures execution success, not intelligence accuracy.

The distinction is important.

---

# 23. Agent Quality vs Operational Success

The system should distinguish between:

```text
OPERATIONAL SUCCESS
```

and:

```text
INVESTIGATION QUALITY
```

For example:

```text
Agent successfully completed its assigned task
```

does not necessarily mean:

```text
The investigation conclusion was correct.
```

Evaluation of reasoning quality should use separate project evaluation metrics.

---

# 24. Trace Model

A trace represents the path of an operation.

Example:

```text
TRACE: INVESTIGATION INV-001

API Request
    │
    ▼
Create Investigation
    │
    ▼
Orchestrator
    │
    ├── Agent A
    │     └── Capability X
    │
    ├── Agent B
    │     └── Capability Y
    │
    ▼
Assessment
    │
    ▼
Completion
```

Tracing is particularly useful for understanding complex multi-step investigations.

---

# 25. Trace Boundaries

Recommended trace boundaries include:

- API request.
- Investigation creation.
- Investigation execution.
- Agent task.
- Capability execution.

The system does not need distributed tracing for every small function call during the MVP.

Tracing should focus on meaningful workflow boundaries.

---

# 26. Dashboard Requirements

The operational dashboard should provide visibility into:

```text
SYSTEM HEALTH

API STATUS

ACTIVE INVESTIGATIONS

AGENT ACTIVITY

CAPABILITY SUCCESS

RECENT FAILURES
```

The operational dashboard is different from the analyst dashboard.

The analyst dashboard focuses on security investigations.

The operational dashboard focuses on the health of Project Sentinel itself.

---

# 27. Alerting and Monitoring

During the MVP, monitoring can begin with simple operational checks.

Important conditions include:

```text
High API failure rate
Database unavailable
Repeated AI service failures
High investigation failure rate
Capability execution failures
```

The project does not necessarily require a complex production alerting platform for the academic MVP.

The architecture should, however, clearly identify what conditions should be monitored.

---

# 28. Auditability Model

Auditability answers accountability questions.

The audit flow is:

```text
IMPORTANT ACTION
       │
       ▼
IDENTIFY ACTOR
       │
       ▼
RECORD ACTION
       │
       ▼
RECORD OUTCOME
       │
       ▼
PERSIST AUDIT EVENT
```

Important actors may include:

```text
analyst
administrator
system
agent_orchestrator
```

The actor type should be explicitly recorded.

---

# 29. Analyst Action Auditing

Analyst actions should be auditable.

Examples:

```text
investigation_started
action_approved
action_rejected
investigation_escalated
investigation_closed
```

Each record should include:

```text
actor_id
action
resource
timestamp
outcome
```

This provides a clear record of human involvement.

---

# 30. Data Protection in Observability

Observability systems can themselves create a security risk.

Logs should not unnecessarily contain:

- Passwords.
- JWT tokens.
- Database connection strings.
- Secret keys.
- Complete sensitive prompts.
- Excessive raw telemetry.

The principle is:

```text
OBSERVABILITY DATA
       │
       ▼
ENOUGH TO UNDERSTAND THE SYSTEM

NOT ENOUGH TO EXPOSE UNNECESSARY SECRETS
```

---

# 31. Retention Considerations

For the MVP, retention policies can remain simple.

However, the architecture should distinguish between:

| Data | Typical Purpose |
|---|---|
| Application logs | Debugging and operations |
| Metrics | Performance analysis |
| Traces | Workflow analysis |
| Audit records | Accountability |

These categories may require different retention strategies in a production system.

---

# 32. Testing Observability

Observability should itself be tested.

Example tests:

### Request Correlation Test

Verify that:

```text
API Request
   │
   ▼
Service Log
   │
   ▼
Agent Event
```

contains the correct correlation context.

### Agent Failure Test

Simulate:

```text
LLM Timeout
```

Verify that:

- The failure is logged.
- Retry activity is visible.
- Investigation state is updated.

### Capability Test

Verify that capability execution generates:

```text
start event
result event
duration information
```

---

# 33. MVP Implementation Priority

## Phase 1 — Logging Foundation

```text
1. Configure structured logging.
2. Add request identifiers.
3. Add consistent log levels.
4. Add major application lifecycle events.
```

## Phase 2 — Workflow Visibility

```text
5. Log investigation state transitions.
6. Log agent task lifecycle events.
7. Log capability execution.
8. Record dependency failures.
```

## Phase 3 — Metrics

```text
9. Measure API performance.
10. Measure ingestion processing.
11. Measure investigation outcomes.
12. Measure agent and capability reliability.
```

## Phase 4 — Auditability

```text
13. Define audit event schema.
14. Record analyst actions.
15. Record important system actions.
16. Implement audit queries where required.
```

---

# 34. Observability Acceptance Criteria

The observability baseline is complete when:

### Logging

- Major system events are recorded.
- Logs use consistent structured fields.
- Failures contain useful diagnostic context.

### Correlation

- Important workflows can be connected using identifiers.
- Investigation operations can be traced across major components.

### Agents

- Agent task execution is observable.
- Capability usage is recorded.
- Failures are distinguishable from successful execution.

### Metrics

- API performance can be measured.
- Investigation outcomes can be measured.
- Agent operational reliability can be measured.

### Auditability

- Important human actions are recorded.
- Critical system actions have an audit trail.
- Audit records are separated conceptually from normal logs.

---

# 35. Complete Observability Flow

The complete model is:

```text
┌───────────────────────────────────────────┐
│               PROJECT SENTINEL            │
│                                                 │
│  User → API → Investigation → Agents      │
│                            │              │
│                            ▼              │
│                       Capabilities         │
└───────────────────────┬───────────────────┘
                        │
                        ▼
              ┌──────────────────┐
              │ OBSERVABILITY    │
              │                  │
              │ Logs             │
              │ Metrics          │
              │ Traces           │
              │ Audit Events     │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ SYSTEM INSIGHT   │
              │                  │
              │ Health           │
              │ Performance      │
              │ Failures         │
              │ Accountability   │
              └──────────────────┘
```

---

# 36. Final Design Principle

A sophisticated agentic system should not be evaluated only by whether it produces a final answer.

Project Sentinel must also make its **operational behavior observable**.

The core principle is:

```text
THE SYSTEM SHOULD BE ABLE TO EXPLAIN

WHAT IT DID

WHEN IT DID IT

WHICH COMPONENT PERFORMED THE ACTION

WHAT THE RESULT WAS

AND WHETHER THE OPERATION SUCCEEDED OR FAILED
```

This observability architecture supports reliable development, debugging, evaluation, and demonstration of the Project Sentinel platform.

---

# Next Document

The next recommended document is:

## Testing, Validation & Evaluation Strategy

This document will define the complete testing hierarchy for Project Sentinel, including unit testing, integration testing, end-to-end workflow testing, agent evaluation, detection evaluation, failure testing, dataset validation, performance testing, and the quantitative metrics required to demonstrate that the project performs better than its baseline.
