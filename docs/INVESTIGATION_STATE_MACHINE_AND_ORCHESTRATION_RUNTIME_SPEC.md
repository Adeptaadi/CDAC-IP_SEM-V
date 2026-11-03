# Project Sentinel
# Investigation State Machine & Orchestration Runtime Specification

**Document Type:** Technical Design Specification  
**Version:** 1.0  
**Status:** Proposed Architecture  
**Primary Focus:** Investigation lifecycle, Planner runtime, dynamic task orchestration, state transitions, replanning, checkpointing, and recovery

---

## 1. Purpose

This document defines the investigation state machine and orchestration runtime for Project Sentinel.

The orchestration runtime is the central execution component of the system. It coordinates the Planner, specialized workers, capability registry, memory service, detection engine, correlation engine, and human analyst.

Unlike a conventional automated pipeline, Project Sentinel must not execute every investigation through a predefined sequence of agents.

Instead, the system must dynamically determine what work is required based on:

- Current investigation state.
- Available evidence.
- Detection findings.
- Correlation results.
- Unresolved hypotheses.
- Previous task results.
- Available capabilities.
- Execution constraints.
- Analyst decisions.

The Planner continuously evaluates investigation progress and determines the next appropriate action.

**Core principle:** Project Sentinel is a goal-driven, stateful, non-linear multi-agent system. Its execution path must emerge from investigation requirements rather than a fixed sequence of worker invocations.

## 2. Architectural Objectives

The orchestration runtime must:

1. Maintain authoritative investigation state.
2. Coordinate Planner decisions and specialist execution.
3. Support dynamic task generation.
4. Support parallel and sequential task execution.
5. Handle task dependencies.
6. Support repeated investigation and replanning cycles.
7. Prevent duplicate task execution.
8. Enforce task and execution limits.
9. Support human review and intervention.
10. Persist checkpoints.
11. Recover from failures and application restarts.
12. Enforce investigation completion criteria.
13. Preserve evidence provenance.
14. Provide complete execution observability.
15. Support deterministic evaluation of orchestration behavior.

## 3. Architectural Position

The orchestration runtime coordinates the major subsystems.

```text
                  DATA INGESTION
                        |
                        v
                DETECTION ENGINE
                        |
                        v
               CORRELATION ENGINE
                        |
                        v
               INCIDENT CANDIDATE
                        |
                        v
                ORCHESTRATION RUNTIME
                        |
          +-------------+-------------+
          |             |             |
          v             v             v
       PLANNER       MEMORY       CAPABILITY
       MODEL         SERVICE       REGISTRY
          |                           |
          v                           v
     PLAN PROPOSAL              TASK EXECUTOR
          |                           |
          v                           v
     PLAN VALIDATOR             SPECIALIZED
          |                      WORKERS
          |                           |
          +-------------+-------------+
                        |
                        v
                RESULT VALIDATION
                        |
                        v
               INVESTIGATION STATE
                        |
                        v
                  PLANNER AGAIN
                        |
          +-------------+-------------+
          |             |             |
          v             v             v
       CONTINUE       REVIEW       COMPLETE
```

The orchestration runtime is responsible for coordinating these components.

It does not replace their internal responsibilities.

| Component | Responsibility |
|---|---|
| Planner | Determines investigation objectives and proposes tasks |
| LangGraph runtime | Coordinates execution and control flow |
| Capability registry | Defines available operations |
| Policy engine | Enforces execution permissions and constraints |
| Task executor | Executes validated tasks |
| Specialized workers | Perform bounded investigation operations |
| Memory service | Provides current and historical context |
| State manager | Maintains authoritative investigation state |
| Validator | Checks plans and task results |
| Human analyst | Reviews findings and controls sensitive decisions |

## 4. Core Architectural Principle: Dynamic Orchestration

### 4.1 Fixed workflow versus dynamic orchestration

A fixed workflow might look like:

```text
Detection
   |
   v
Correlation
   |
   v
Investigation
   |
   v
RAG
   |
   v
Reporting
   |
   v
Response
```

This is not the intended architecture.

Not every incident requires every capability.

For example:

- A simple detection finding may require only a short investigation.
- A suspicious authentication sequence may require event correlation and account activity searches.
- A possible web attack may require different evidence and knowledge retrieval.
- Conflicting findings may require additional investigation.
- An incomplete task may require the Planner to revisit an earlier capability.

Project Sentinel must therefore use a dynamic approach.

```text
                 INVESTIGATION OBJECTIVE
                          |
                          v
                    PLANNER
                          |
                          v
                 SELECT NEXT OBJECTIVE
                          |
                          v
                  VALIDATE PROPOSAL
                          |
                          v
                  EXECUTE CAPABILITIES
                          |
                          v
                   COLLECT RESULTS
                          |
                          v
                  UPDATE STATE
                          |
                          v
                    PLANNER
                          |
               +----------+----------+
               |          |          |
               v          v          v
            Continue    Replan     Complete
               |          |          |
               +----------+----------+
                          |
                          v
                   NEXT DECISION
```

The Planner may revisit any suitable capability based on the current state.

### 4.2 Investigation as a control loop

The central orchestration loop is:

1. Read investigation state.
2. Construct Planner context.
3. Ask the Planner for a decision.
4. Validate the proposed decision.
5. Execute permitted tasks.
6. Validate task results.
7. Update investigation state.
8. Persist a checkpoint.
9. Re-evaluate the investigation.

This continues until the investigation reaches an accepted terminal state or requires human intervention.

## 5. Investigation State Machine

### 5.1 Investigation states

The investigation state machine represents the lifecycle of an investigation.

Proposed states:

| State | Meaning |
|---|---|
| `created` | Investigation record has been created |
| `queued` | Investigation is waiting for execution |
| `initializing` | Initial context and resources are being prepared |
| `investigating` | Planner and specialist capabilities are actively working |
| `awaiting_review` | Human review or approval is required |
| `paused` | Execution has been intentionally paused |
| `blocked` | Investigation cannot progress because a required dependency is unavailable |
| `completed` | Investigation has successfully completed |
| `closed` | Investigation has been formally closed |
| `failed` | Investigation encountered an unrecoverable execution failure |
| `cancelled` | Investigation was explicitly cancelled |

### 5.2 State transition diagram

```text
CREATED
   |
   v
QUEUED
   |
   v
INITIALIZING
   |
   v
INVESTIGATING <------------------+
   |                             |
   |                             |
   +------> AWAITING_REVIEW      |
   |              |              |
   |              v              |
   |         INVESTIGATING       |
   |                             |
   +------> PAUSED               |
   |              |              |
   |              v              |
   |         INVESTIGATING       |
   |                             |
   +------> BLOCKED              |
   |              |              |
   |              v              |
   |         INVESTIGATING       |
   |                             |
   +------> COMPLETED            |
   |              |              |
   |              v              |
   +----------> CLOSED           |
   |
   +------> FAILED
   |
   +------> CANCELLED
```

This diagram describes the principal lifecycle.

The implementation must define permitted transitions explicitly rather than allowing arbitrary state updates.

### 5.3 Terminal states

The following are terminal for the active execution lifecycle:

- `completed`
- `closed`
- `failed`
- `cancelled`

A terminal investigation should not resume silently.

If further investigation becomes necessary, the system should use an explicitly authorized reopen or create a linked follow-up investigation.

## 6. State Transition Rules

Every state transition must pass through a state-transition validator.

Example:

| Current state | Requested state | Allowed |
|---|---|---|
| `created` | `queued` | Yes |
| `queued` | `initializing` | Yes |
| `initializing` | `investigating` | Yes |
| `investigating` | `awaiting_review` | Yes |
| `investigating` | `paused` | Yes |
| `investigating` | `blocked` | Yes |
| `investigating` | `completed` | Yes, after validation |
| `paused` | `investigating` | Yes |
| `blocked` | `investigating` | Yes, after recovery |
| `awaiting_review` | `investigating` | Yes, after review |
| `completed` | `investigating` | No, not without explicit reopen |
| `cancelled` | `investigating` | No |

Additional transitions may be defined for administrative reopening, but they must be explicit and auditable.

### 6.1 Transition metadata

Every transition should record:

```json
{
  "investigation_id": "INV-001",
  "previous_state": "investigating",
  "new_state": "awaiting_review",
  "transition_reason": "Response recommendation requires analyst approval",
  "triggered_by": "orchestration_runtime",
  "timestamp": "2026-08-01T10:30:00Z",
  "state_version": 14
}
```

The example is illustrative.

## 7. Task State Machine

Investigation state and task state must be separate.

An investigation may remain in `investigating` while several tasks are running, completed, or failed.

### 7.1 Task states

| State | Meaning |
|---|---|
| `proposed` | Planner has proposed the task |
| `validating` | Task is being validated |
| `pending` | Task has been accepted |
| `queued` | Task is waiting for execution |
| `running` | Worker is executing |
| `completed` | Task completed successfully |
| `failed` | Task failed |
| `blocked` | Required input or dependency is unavailable |
| `retrying` | Task is undergoing an authorized retry |
| `cancelled` | Task was cancelled |
| `skipped` | Task was not executed because it was no longer required |

### 7.2 Task lifecycle

```text
PROPOSED
   |
   v
VALIDATING
   |
   +------> REJECTED
   |
   v
PENDING
   |
   v
QUEUED
   |
   v
RUNNING
   |
   +------> COMPLETED
   |
   +------> FAILED
   |
   +------> BLOCKED
   |
   +------> RETRYING
   |
   +------> CANCELLED
```

A retry should create a new execution attempt while preserving the logical task identity.

### 7.3 Logical task versus execution attempt

A task represents the intended operation.

An execution attempt represents one attempt to perform it.

Example:

```json
{
  "task_id": "TASK-001",
  "capability_id": "correlate_events",
  "status": "completed",
  "attempts": [
    {
      "attempt": 1,
      "status": "failed",
      "error_code": "TEMPORARY_DATABASE_ERROR"
    },
    {
      "attempt": 2,
      "status": "completed"
    }
  ]
}
```

This distinction is necessary for reliable retry behavior and accurate evaluation.

## 8. Investigation State Model

The state manager should maintain a structured representation of the investigation.

### 8.1 Proposed state structure

```json
{
  "investigation_id": "INV-001",
  "state_version": 1,
  "status": "investigating",
  "objective": "Investigate suspected credential compromise",
  "trigger": {
    "candidate_id": "INC-CAND-001",
    "finding_refs": [
      "FIND-001"
    ]
  },
  "facts": [],
  "hypotheses": [],
  "evidence_refs": [],
  "knowledge_refs": [],
  "tasks": [],
  "unresolved_questions": [],
  "planner_decisions": [],
  "constraints": {
    "max_tasks": 20,
    "max_parallel_tasks": 3,
    "max_replans": 10,
    "response_execution_enabled": false
  },
  "completion_status": null,
  "created_at": "2026-08-01T10:00:00Z",
  "updated_at": "2026-08-01T10:00:00Z"
}
```

This is a logical state representation. The final structure must be reconciled with the database and memory specifications.

### 8.2 State ownership

The orchestration runtime owns authoritative state transitions.

Workers return results.

The state manager decides whether validated results can be incorporated.

The Planner receives a read-only state snapshot and proposes subsequent actions.

The Planner must not directly overwrite authoritative investigation state.

### 8.3 State updates

State changes should be explicit events or validated updates.

Examples:

- `FindingAttached`
- `EvidenceAdded`
- `HypothesisCreated`
- `HypothesisUpdated`
- `TaskCreated`
- `TaskCompleted`
- `TaskFailed`
- `PlannerDecisionAccepted`
- `AnalystReviewSubmitted`
- `InvestigationPaused`
- `InvestigationCompleted`

This provides a traceable history of how the investigation evolved.

## 9. Planner Runtime

### 9.1 Planner responsibilities

The Planner is the central reasoning component.

It must:

1. Read the latest investigation snapshot.
2. Identify the current investigation objective.
3. Review confirmed findings.
4. Review unresolved hypotheses.
5. Identify missing evidence.
6. Inspect completed and active tasks.
7. Discover available capabilities.
8. Select suitable next tasks.
9. Determine whether parallel execution is appropriate.
10. Decide whether investigation can conclude.
11. Replan when results are insufficient.
12. Request human review when necessary.

### 9.2 Planner does not execute tasks

The Planner generates proposals.

It does not:

- Directly call arbitrary tools.
- Execute SQL.
- Modify investigation records.
- Bypass capability permissions.
- Approve sensitive response operations.
- Override task execution limits.

These responsibilities belong to deterministic runtime components.

### 9.3 Planner input

The Planner should receive a compact snapshot.

```json
{
  "investigation_id": "INV-001",
  "objective": "Investigate suspected credential compromise",
  "current_state": "investigating",
  "facts": [
    "Repeated authentication failures",
    "A successful authentication followed"
  ],
  "hypotheses": [
    {
      "id": "HYP-001",
      "description": "Possible account compromise",
      "status": "under_investigation"
    }
  ],
  "unresolved_questions": [
    "Was the successful login followed by suspicious activity?"
  ],
  "completed_tasks": [
    {
      "task_id": "TASK-001",
      "capability_id": "correlate_events"
    }
  ],
  "active_tasks": [],
  "available_capabilities": [
    "event_search",
    "analyze_evidence",
    "retrieve_knowledge",
    "generate_report"
  ],
  "constraints": {
    "max_parallel_tasks": 3,
    "remaining_task_budget": 15
  }
}
```

### 9.4 Planner output

```json
{
  "decision": "continue_investigation",
  "reasoning_summary": "The authentication sequence is suspicious, but subsequent account activity has not been examined.",
  "tasks": [
    {
      "task_id": "TASK-002",
      "capability_id": "event_search",
      "objective": "Search for activity associated with the account after successful authentication",
      "priority": 1,
      "depends_on": [],
      "required_inputs": [
        "account_identifier",
        "time_window"
      ]
    }
  ],
  "completion_criteria": [
    "Subsequent account activity has been assessed"
  ]
}
```

The runtime validates this response before creating tasks.

## 10. Planner Decision Types

The Planner should return one of a finite set of decisions.

| Decision | Meaning |
|---|---|
| `continue_investigation` | More investigation tasks are required |
| `replan` | Existing tasks or strategy need modification |
| `request_human_review` | Analyst intervention is required |
| `complete_investigation` | Investigation completion criteria are satisfied |
| `escalate` | Investigation should be escalated |
| `blocked` | Investigation cannot currently progress |

### 10.1 Decision validation

The runtime must verify:

- Decision is valid.
- Investigation is in a compatible state.
- Required tasks are present when continuing.
- Completion criteria are satisfied before completion.
- Human review is genuinely required for review decisions.
- Blocked reasons are recorded.
- Task and replan budgets are respected.

A model-generated completion decision is not sufficient by itself to complete an investigation.

## 11. Dynamic Task Planning

### 11.1 Task generation

The Planner creates tasks according to unresolved investigation objectives.

For example:

An investigation may contain:

- Suspicious authentication findings.
- Correlated source addresses.
- An unresolved account activity question.

The Planner may create:

1. An event search task.
2. A knowledge retrieval task.

These may run in parallel if they do not depend on each other's outputs.

### 11.2 Task proposal structure

Every task must include:

- Task identifier.
- Capability identifier.
- Objective.
- Priority.
- Required inputs.
- Expected output.
- Dependencies.
- Execution constraints.

### 11.3 Plan validation

Before accepting a plan, validate:

1. Capability exists.
2. Capability is enabled.
3. Inputs are valid.
4. Permissions are sufficient.
5. Dependencies exist.
6. Dependency graph has no cycles.
7. Task count is within budget.
8. Parallelism is within limits.
9. No unauthorized operation is proposed.
10. Task is relevant to the investigation objective.

Invalid tasks must be rejected without executing the rest of the invalid proposal.

Where safe, independently valid tasks may be retained, but the accepted plan must be recorded explicitly.

## 12. Dynamic Replanning

Replanning is one of the central features of Project Sentinel.

The Planner must be able to change its approach when new evidence or task results change the investigation state.

### 12.1 Replanning triggers

Replanning may occur when:

- A task completes.
- A task fails.
- New evidence is discovered.
- A hypothesis is contradicted.
- A capability becomes unavailable.
- A new finding is generated.
- An analyst provides feedback.
- A previous task produces incomplete results.
- A completion criterion remains unsatisfied.

### 12.2 Replanning example

Initial finding:

Multiple failed authentication attempts followed by successful authentication.

First Planner decision:

- Correlate authentication events.
- Search subsequent account activity.

New evidence:

Suspicious activity appears after successful authentication.

Second Planner decision:

- Retrieve relevant ATT&CK knowledge.
- Analyze the new evidence.
- Examine related source entities.

New evidence:

No additional suspicious activity is found.

Third Planner decision:

- Assess whether evidence is sufficient.
- Generate an investigation report.
- Request analyst review if required.

This illustrates why the investigation cannot be represented as a fixed sequence.

### 12.3 Replanning limits

Unbounded replanning can cause:

- Excessive model calls.
- Repeated tasks.
- Infinite investigation loops.
- Unnecessary latency.
- Resource exhaustion.

Configure:

- Maximum replans.
- Maximum tasks.
- Maximum attempts per task.
- Maximum investigation duration.
- Maximum model token budget.

If a limit is reached, the system should request human review or enter a controlled blocked state.

## 13. Task Dependencies and Parallel Execution

### 13.1 Dependency graph

Tasks may depend on earlier task results.

Example:

```text
TASK-001: Search authentication events
                 |
                 v
TASK-002: Correlate authentication events
                 |
                 v
TASK-003: Analyze correlated findings
```

However, unrelated tasks may execute in parallel.

```text
                  PLANNER
                     |
           +---------+---------+
           |                   |
           v                   v
      Event Search       Knowledge Retrieval
           |                   |
           +---------+---------+
                     |
                     v
              State Update
                     |
                     v
               PLANNER AGAIN
```

### 13.2 Dependency validation

The runtime must reject:

- Self-dependencies.
- Unknown task references.
- Cyclic dependencies.
- Cross-investigation dependencies.
- Execution before prerequisite completion.

### 13.3 Concurrency controls

Configure:

- Maximum parallel tasks per investigation.
- Maximum concurrent investigations.
- Maximum concurrent model calls.
- Maximum capability executions.
- Per-worker concurrency limits.

Concurrency values must be determined through benchmarking.

### 13.4 Parallel result aggregation

When several tasks complete:

1. Validate each result independently.
2. Persist successful results.
3. Record failed results.
4. Resolve state update conflicts.
5. Construct a new investigation snapshot.
6. Trigger Planner re-evaluation.

Do not wait for unrelated failed tasks before preserving successful results.

## 14. Investigation Completion Logic

### 14.1 Completion is not a model opinion

An investigation should only complete when predefined conditions are satisfied.

The Planner may recommend completion, but the runtime must validate it.

### 14.2 Completion criteria

Potential conditions:

- Required findings have been reviewed.
- Relevant evidence has been collected.
- Material hypotheses have been resolved or explicitly marked inconclusive.
- Contradictions have been addressed.
- Required tasks are complete or explicitly waived.
- A final investigation disposition exists.
- Required analyst approvals have been obtained.

Not every investigation needs every condition.

Completion criteria should be appropriate to the investigation objective.

### 14.3 Completion validation

```text
Planner Recommends Completion
             |
             v
      Completion Validator
             |
      +------+------+
      |             |
      v             v
   Satisfied     Unsatisfied
      |             |
      v             v
  Complete       Replan /
 Investigation   Human Review
```

### 14.4 Completion outcomes

Suggested outcomes:

| Outcome | Meaning |
|---|---|
| `confirmed_threat` | Evidence supports a confirmed threat |
| `likely_threat` | Evidence strongly suggests a threat but is incomplete |
| `benign` | Activity is assessed as benign |
| `inconclusive` | Available evidence is insufficient |
| `false_positive` | Initial alert was determined to be incorrect |
| `escalated` | Further investigation is required outside the current scope |

These outcomes must remain distinct from investigation lifecycle states.

## 15. Human-in-the-Loop Integration

Project Sentinel uses a human-on-the-loop model.

Agents may investigate autonomously within defined constraints, while analysts retain review, approval, and override authority.

### 15.1 Human intervention points

Human review may be requested for:

- High-impact conclusions.
- Conflicting findings.
- Low-confidence or inconclusive investigations.
- Sensitive response recommendations.
- Policy violations.
- Investigation budget exhaustion.
- Explicit analyst escalation.

### 15.2 Review workflow

```text
Planner Decision
      |
      v
Human Review Required
      |
      v
Investigation Awaiting Review
      |
      v
Analyst Reviews Evidence
      |
      +----------+-----------+
      |          |           |
      v          v           v
   Approve    Reject       Request
                          More Work
      |          |           |
      +----------+-----------+
                 |
                 v
          State Update
                 |
                 v
           Planner Again
```

### 15.3 Analyst actions

The analyst should be able to:

- Approve a recommendation.
- Reject a recommendation.
- Request additional investigation.
- Add evidence.
- Correct an incorrect finding.
- Pause an investigation.
- Resume an investigation.
- Cancel an investigation.
- Override an automated classification with an audited reason.

### 15.4 Approval security

Approval must be tied to an authenticated user and an authorized action.

A model response, agent message, or retrieved document must never count as analyst approval.

## 16. Checkpointing and Persistence

### 16.1 Purpose

Checkpointing allows an investigation to resume after:

- Application restart.
- Worker failure.
- Model timeout.
- Database interruption.
- Infrastructure failure.
- Manual pause.

### 16.2 Checkpoint contents

A checkpoint should contain:

- Investigation state.
- State version.
- Current objective.
- Accepted Planner decision.
- Task statuses.
- Completed task references.
- Active execution references.
- Evidence references.
- Hypotheses.
- Unresolved questions.
- Execution counters.
- Relevant configuration versions.

### 16.3 Checkpoint lifecycle

```text
Task Result Validated
        |
        v
State Update
        |
        v
Persist State
        |
        v
Create Checkpoint
        |
        v
Continue Execution
```

Persist checkpoints after meaningful state changes, not only when the entire investigation completes.

### 16.4 Persistence strategy

PostgreSQL should remain the authoritative store.

Redis may accelerate short-lived execution operations.

LangGraph checkpoint persistence should be configured to use a durable backend appropriate to the deployment.

The checkpoint representation must be consistent with the application's authoritative investigation state.

Do not maintain conflicting independent copies of the same state without an explicit reconciliation mechanism.

## 17. Failure Recovery

### 17.1 Application restart

On restart:

1. Identify non-terminal investigations.
2. Load the latest persisted state.
3. Inspect incomplete task executions.
4. Reconcile execution status.
5. Check task idempotency.
6. Resume eligible tasks.
7. Trigger Planner re-evaluation.

### 17.2 Worker failure

If a worker fails:

- Persist the failure.
- Preserve completed work.
- Apply retry policy.
- Update investigation state.
- Allow the Planner to choose an alternative strategy.

### 17.3 Planner failure

If the Planner is unavailable:

- Preserve investigation state.
- Retain completed task results.
- Mark planning as temporarily unavailable.
- Retry according to policy.
- Do not invent the next task.

### 17.4 Capability unavailable

If a required capability becomes unavailable:

- Mark the task as blocked.
- Record the reason.
- Update available capability discovery.
- Allow the Planner to propose an alternative.
- Request human review if no safe alternative exists.

### 17.5 Partial execution failure

Suppose three parallel tasks are running and one fails.

The runtime must preserve the other two successful results.

The Planner should receive the updated state and determine whether the failed task needs retry, replacement, or cancellation.

## 18. LangGraph Runtime Design

### 18.1 Graph responsibilities

LangGraph should coordinate:

- State loading.
- Planner invocation.
- Plan validation.
- Capability discovery.
- Task dispatch.
- Result collection.
- State updates.
- Human review interrupts.
- Checkpointing.
- Termination.

### 18.2 Proposed logical graph

```text
START
  |
  v
Load Investigation State
  |
  v
Build Planner Context
  |
  v
Planner Node
  |
  v
Validate Decision
  |
  +------> Invalid Plan ------> Record Rejection
  |                                  |
  |                                  v
  |                             Bounded Replan
  |
  v
Discover Capabilities
  |
  v
Validate Tasks
  |
  v
Create Task Records
  |
  v
Dispatch Eligible Tasks
  |
  v
Execute Workers
  |
  v
Validate Results
  |
  v
Update Investigation State
  |
  v
Persist Checkpoint
  |
  v
Evaluate Next Decision
  |
  +------> Continue
  |
  +------> Replan
  |
  +------> Human Review
  |
  +------> Complete
  |
  v
 END
```

This is a logical representation. The implementation may use multiple graph nodes, subgraphs, conditional edges, and interrupt mechanisms.

### 18.3 Graph state

Example:

```python
from typing import TypedDict, Any

class InvestigationGraphState(TypedDict):
    investigation_id: str
    state_version: int
    investigation_status: str
    objective: str
    planner_context: dict[str, Any]
    planner_decision: dict[str, Any] | None
    proposed_tasks: list[dict[str, Any]]
    task_results: list[dict[str, Any]]
    evidence_refs: list[str]
    unresolved_questions: list[str]
    replan_count: int
    error: str | None
```

The production graph state should avoid storing unnecessarily large raw evidence payloads.

Use references to persisted records instead.

### 18.4 Graph persistence

Every graph execution should be associated with an investigation identifier.

The checkpoint identifier should be stable and should not accidentally combine unrelated investigations.

The application should also persist its own state version and task records so that graph recovery can be reconciled with the authoritative database.

## 19. Database Architecture

Suggested logical tables:

```text
investigations
investigation_state
investigation_state_versions
investigation_transitions
investigation_events
planner_decisions
planner_runs
agent_tasks
task_dependencies
task_attempts
task_results
execution_checkpoints
human_reviews
investigation_hypotheses
investigation_evidence
```

The actual implementation must reuse existing tables where appropriate.

Do not create duplicate task or investigation structures if they already exist.

### 19.1 Investigation table

```sql
CREATE TABLE investigations (
    id UUID PRIMARY KEY,
    investigation_code VARCHAR(100) UNIQUE NOT NULL,
    objective TEXT NOT NULL,
    status VARCHAR(30) NOT NULL,
    outcome VARCHAR(50),
    state_version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);
```

### 19.2 Planner decision table

```sql
CREATE TABLE planner_decisions (
    id UUID PRIMARY KEY,
    investigation_id UUID NOT NULL
        REFERENCES investigations(id),
    decision_type VARCHAR(50) NOT NULL,
    reasoning_summary TEXT,
    proposed_plan JSONB,
    validation_status VARCHAR(30) NOT NULL,
    planner_model_version VARCHAR(100),
    prompt_version VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 19.3 Investigation transition table

```sql
CREATE TABLE investigation_transitions (
    id UUID PRIMARY KEY,
    investigation_id UUID NOT NULL
        REFERENCES investigations(id),
    previous_state VARCHAR(30),
    new_state VARCHAR(30) NOT NULL,
    transition_reason TEXT,
    triggered_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 19.4 State consistency

Use transactions for related state updates.

Use optimistic concurrency through `state_version` or equivalent locking.

An update based on an outdated state version must not silently overwrite newer state.

## 20. API Integration

The frontend and external clients should interact with the orchestration runtime through the API layer.

They should not invoke Planner or worker implementations directly.

### 20.1 Investigation creation

```http
POST /api/v1/investigations
```

### 20.2 Investigation retrieval

```http
GET /api/v1/investigations/{investigation_id}
```

### 20.3 Pause investigation

```http
POST /api/v1/investigations/{investigation_id}/pause
```

### 20.4 Resume investigation

```http
POST /api/v1/investigations/{investigation_id}/resume
```

### 20.5 Cancel investigation

```http
POST /api/v1/investigations/{investigation_id}/cancel
```

### 20.6 Retrieve task history

```http
GET /api/v1/investigations/{investigation_id}/tasks
```

### 20.7 Submit analyst review

```http
POST /api/v1/investigations/{investigation_id}/reviews
```

All state-changing endpoints must enforce authorization, validate transitions, and create audit records.

## 21. Runtime Resource Controls

The orchestration runtime must prevent investigations from consuming unlimited resources.

Configure limits for:

| Resource | Control |
|---|---|
| Total tasks | Maximum tasks per investigation |
| Replanning | Maximum Planner cycles |
| Task retries | Maximum attempts per task |
| Model calls | Maximum calls per investigation |
| Model tokens | Input and output budgets |
| Parallelism | Maximum concurrent tasks |
| Duration | Maximum investigation runtime |
| Memory context | Maximum context size |
| Queue | Maximum pending tasks |

When a limit is reached, the runtime should record the reason and transition to an appropriate state, generally `awaiting_review` or `blocked`.

Limits must be configurable and measurable.

## 22. Observability

Orchestration must be fully traceable.

### 22.1 Required identifiers

- `investigation_id`
- `state_version`
- `planner_run_id`
- `decision_id`
- `task_id`
- `execution_id`
- `attempt_number`
- `checkpoint_id`
- `trace_id`

### 22.2 Suggested metrics

```text
sentinel_investigations_created_total
sentinel_investigations_completed_total
sentinel_investigations_failed_total
sentinel_planner_runs_total
sentinel_planner_latency_seconds
sentinel_replans_total
sentinel_tasks_created_total
sentinel_tasks_completed_total
sentinel_tasks_failed_total
sentinel_task_retries_total
sentinel_investigation_duration_seconds
sentinel_checkpoint_failures_total
sentinel_human_review_wait_seconds
sentinel_active_investigations
```

### 22.3 Operational dashboards

Recommended dashboard sections:

- Active investigations.
- Investigation state distribution.
- Planner decisions.
- Task execution status.
- Replanning frequency.
- Failed and blocked tasks.
- Model invocation latency.
- Investigation completion time.
- Human review backlog.
- Resource utilization.

## 23. Orchestration Evaluation

The orchestration engine must be evaluated independently from the detection engine.

### 23.1 Core metrics

| Metric | Purpose |
|---|---|
| Task selection accuracy | Measures appropriateness of Planner task choices |
| Routing precision | Measures whether selected capabilities are suitable |
| Routing recall | Measures whether required capabilities are selected |
| Plan validity rate | Measures valid structured plans |
| Replanning effectiveness | Measures recovery after incomplete results |
| Termination accuracy | Measures appropriate investigation completion |
| Task completion rate | Measures successful task execution |
| Repeated task rate | Measures unnecessary duplicate work |
| Investigation success rate | Measures successful end-to-end investigations |
| Planning latency | Measures orchestration overhead |
| Investigation duration | Measures total investigation time |

### 23.2 Orchestration Quality Score

The proposed Orchestration Quality Score from the evaluation specification may be used.

\[
OQS = 0.25R + 0.20P + 0.25C + 0.15F + 0.15T
\]

Where:

- \(R\): Routing quality.
- \(P\): Planning efficiency.
- \(C\): Completion correctness.
- \(F\): Recovery effectiveness.
- \(T\): Termination correctness.

Each component is normalized to the interval \([0,1]\).

This is a proposed Project Sentinel evaluation index, not a standardized industry metric.

The exact calculation of each component must be documented before experimental use.

### 23.3 Baseline comparisons

Compare the proposed orchestration architecture against:

| Baseline | Description |
|---|---|
| B0 | Rule-based detection without agent investigation |
| B1 | Traditional ML detection |
| B2 | Single-agent investigation |
| B3 | Fixed multi-agent workflow |
| P1 | Dynamic Planner-based multi-agent orchestration |

The critical research comparison is B3 versus P1.

This determines whether dynamic planning provides measurable benefits over a fixed multi-agent workflow.

### 23.4 Ablation experiments

Recommended experiments:

- Planner without memory.
- Planner with working memory only.
- Planner with episodic memory.
- Planner with RAG.
- Planner without dynamic replanning.
- Sequential execution versus controlled parallel execution.
- Planner with unrestricted proposals versus validated capability execution.

Measure task quality, completion, latency, repeated work, and resource consumption.

## 24. Testing Strategy

### 24.1 State machine tests

Test:

- Every permitted state transition.
- Every prohibited state transition.
- Terminal-state behavior.
- Pause and resume.
- Cancellation.
- Human review transitions.
- Invalid transition requests.

### 24.2 Planner tests

Test:

- Valid plans.
- Invalid plans.
- Empty plans.
- Unsupported capabilities.
- Missing inputs.
- Excessive task generation.
- Premature completion.
- Unnecessary repeated tasks.
- Replanning after incomplete results.

### 24.3 Recovery tests

Test:

- Application restart during execution.
- Worker crash.
- Planner timeout.
- Database interruption.
- Redis unavailability.
- Duplicate task dispatch.
- Checkpoint restoration.
- Partial parallel execution failure.

### 24.4 Concurrency tests

Test:

- Multiple simultaneous tasks.
- Concurrent state updates.
- Dependency enforcement.
- Task cancellation during execution.
- Duplicate requests.
- Resource limit enforcement.

## 25. Implementation Roadmap

### Phase 1 — State model

- Define investigation states.
- Define task states.
- Define permitted transitions.
- Implement state manager.
- Add state versioning.
- Add transition audit records.

### Phase 2 — Planner runtime

- Implement Planner input context.
- Implement structured decision output.
- Add plan validation.
- Integrate capability discovery.
- Implement task creation.

### Phase 3 — Execution orchestration

- Integrate capability executor.
- Add task dependencies.
- Implement parallel execution.
- Add retry and timeout policies.
- Implement result aggregation.

### Phase 4 — Dynamic replanning

- Trigger Planner after task results.
- Support task replacement.
- Support hypothesis updates.
- Add replan limits.
- Implement completion validation.

### Phase 5 — Persistence and recovery

- Integrate LangGraph checkpointing.
- Persist investigation state.
- Implement restart recovery.
- Reconcile incomplete executions.
- Add idempotency controls.

### Phase 6 — Human interaction and evaluation

- Add pause and resume.
- Add review interrupts.
- Add analyst decisions.
- Implement orchestration metrics.
- Run baseline and ablation experiments.

## 26. Acceptance Criteria

| ID | Acceptance criterion |
|---|---|
| ORCH-01 | Investigation states are explicitly defined |
| ORCH-02 | Invalid state transitions are rejected |
| ORCH-03 | Investigation and task states are independent |
| ORCH-04 | Planner receives an authoritative state snapshot |
| ORCH-05 | Planner generates structured task proposals |
| ORCH-06 | Plans are validated before execution |
| ORCH-07 | Capability discovery is registry-based |
| ORCH-08 | Tasks support dependencies |
| ORCH-09 | Independent tasks support bounded parallel execution |
| ORCH-10 | Task results are validated before state updates |
| ORCH-11 | Planner can dynamically replan |
| ORCH-12 | Replanning and resource limits are enforced |
| ORCH-13 | Investigation completion requires runtime validation |
| ORCH-14 | Human review interrupts execution when required |
| ORCH-15 | Investigation state survives application restart |
| ORCH-16 | Checkpoints are persisted |
| ORCH-17 | Duplicate execution is controlled through idempotency |
| ORCH-18 | Partial failures preserve successful task results |
| ORCH-19 | Orchestration metrics are measurable |
| ORCH-20 | Dynamic orchestration is evaluated against fixed workflow baselines |

## 27. Key Architectural Decisions

| Decision | MVP position |
|---|---|
| Orchestration architecture | Planner + Specialized Workers |
| Execution framework | LangGraph |
| Workflow behavior | Dynamic and non-linear |
| Investigation state | Explicit state machine |
| Task state | Independent state machine |
| Planner output | Structured proposals |
| Task execution | Capability registry and executor |
| State ownership | Orchestration runtime |
| Persistence | PostgreSQL |
| Checkpointing | Durable LangGraph-compatible persistence |
| Parallelism | Bounded and dependency-aware |
| Replanning | Triggered by meaningful state changes |
| Termination | Deterministic completion validation |
| Human oversight | Human-on-the-loop |
| Recovery | Checkpoint-based and idempotent |

## 28. Final Architectural Position

The Investigation State Machine and Orchestration Runtime form the operational core of Project Sentinel.

Detection and correlation identify suspicious activity. The Planner evaluates the available information and decides what investigation work is required. Specialized workers execute bounded capabilities. Their results update authoritative investigation state, which becomes the basis for the next Planner decision.

This creates a continuous investigation control loop rather than a fixed agent pipeline.

The most important architectural distinction is the separation between reasoning and execution:

- The Planner reasons about what should happen.
- The validator determines whether a proposal is acceptable.
- The capability registry defines available operations.
- The executor controls how operations run.
- The workers perform bounded tasks.
- The state manager preserves authoritative progress.
- The completion validator determines whether investigation can end.

A reliable implementation of this control loop is the foundation of Project Sentinel's multi-agent architecture and its primary technical differentiator.
