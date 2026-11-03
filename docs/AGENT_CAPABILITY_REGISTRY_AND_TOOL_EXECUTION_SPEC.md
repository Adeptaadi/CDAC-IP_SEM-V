# Project Sentinel
# Agent Capability Registry & Tool Execution Specification

**Document Type:** Technical Design Specification  
**Version:** 1.0  
**Status:** Proposed Architecture  
**Primary Focus:** Capability registration, agent contracts, tool discovery, execution control, permissions, and task lifecycle

---

## 1. Purpose

This document defines the architecture for registering, discovering, assigning, and executing capabilities within Project Sentinel.

Project Sentinel uses a Planner + Specialized Workers architecture. The Planner determines what work is required, while specialized workers execute bounded investigation tasks.

The system must provide a controlled mechanism through which the Planner can discover available capabilities and request their execution.

Without a capability registry and execution boundary, the architecture risks:

- Agents invoking tools outside their responsibilities.
- Inconsistent input and output formats.
- Unauthorized operations.
- Duplicate task execution.
- Unbounded retries.
- Difficult-to-debug agent behavior.
- Tight coupling between Planner logic and individual worker implementations.

The capability registry addresses these problems by separating task planning from capability execution.

**Core principle:** The Planner selects what should be done. The capability registry determines what can be done. The execution runtime determines whether and how it may be done.

## 2. Architectural Objectives

The subsystem must:

1. Provide a centralized registry of available capabilities.
2. Describe each capability through a machine-readable contract.
3. Allow the Planner to discover suitable capabilities.
4. Validate capability selection before execution.
5. Enforce input and output schemas.
6. Apply permission and risk policies.
7. Support synchronous and asynchronous execution.
8. Support bounded retries and failure handling.
9. Preserve task and execution provenance.
10. Support parallel execution where dependencies allow it.
11. Prevent arbitrary tool execution.
12. Allow new capabilities to be added without redesigning the Planner.

## 3. Architectural Position

The capability registry sits between the Planner and the actual worker implementations.

```text
                 INVESTIGATION STATE
                         |
                         v
                       PLANNER
                         |
                         v
                 PLAN PROPOSAL
                         |
                         v
                  PLAN VALIDATOR
                         |
                         v
                CAPABILITY REGISTRY
                         |
                +--------+--------+
                |        |        |
                v        v        v
             Detection Correlation Investigation
             Worker    Worker      Worker
                |        |        |
                +--------+--------+
                         |
                         v
                 TOOL EXECUTION LAYER
                         |
                         v
                 OUTPUT VALIDATION
                         |
                         v
                 INVESTIGATION STATE
                         |
                         v
                   PLANNER AGAIN
```

The architecture is dynamic.

The Planner may select different capabilities based on the current investigation state. It may also revisit previously executed capabilities when new evidence becomes available.

## 4. Terminology

| Term | Definition |
|---|---|
| Agent | A logical worker responsible for a defined class of tasks |
| Capability | A registered operation that can be requested by the Planner |
| Tool | A concrete operation or integration used to perform a capability |
| Task | A specific execution request associated with an investigation |
| Execution | An attempt to perform a task |
| Registry | Central catalog of approved capabilities |
| Policy | Rules governing whether a capability may execute |
| Contract | Defined input, output, and behavior requirements |
| Worker | Runtime implementation responsible for executing a capability |

A capability is a logical unit of work. It may use one or more tools internally.

For example, an `event_search` capability may query PostgreSQL, while a `knowledge_retrieval` capability may query ChromaDB through the RAG service.

The Planner should select capabilities rather than constructing direct database queries or arbitrary tool commands.

## 5. Capability Categories

Project Sentinel should organize capabilities by operational responsibility.

| Category | Example capabilities |
|---|---|
| Detection | Run detection, inspect detection findings |
| Correlation | Correlate events, resolve entities, build timelines |
| Investigation | Analyze evidence, test hypotheses, identify gaps |
| Retrieval | Search security knowledge, retrieve historical incidents |
| Reporting | Generate incident reports, summarize findings |
| Response | Recommend response, simulate approved playbook actions |
| System | Inspect task status, retrieve investigation state |

These are logical categories. Individual capabilities should be registered only when their implementation and contract are available.

## 6. Initial Capability Catalog

The following catalog defines the proposed MVP capabilities.

| Capability ID | Capability | Responsible worker | Risk |
|---|---|---|---|
| `event_search` | Search relevant security events | Investigation | Low |
| `run_detection` | Execute approved detection logic | Detection | Medium |
| `inspect_findings` | Retrieve and explain findings | Detection | Low |
| `correlate_events` | Identify relationships between events | Correlation | Low |
| `resolve_entities` | Normalize and relate entities | Correlation | Low |
| `build_timeline` | Construct an event timeline | Correlation | Low |
| `analyze_evidence` | Evaluate evidence against a hypothesis | Investigation | Medium |
| `retrieve_knowledge` | Search approved knowledge sources | Retrieval | Low |
| `retrieve_history` | Search authorized historical incidents | Retrieval | Medium |
| `generate_report` | Generate an evidence-grounded report | Reporting | Low |
| `recommend_response` | Recommend an approved response playbook | Response | Medium |
| `simulate_response` | Simulate an authorized response action | Response | Medium |

Risk classifications are proposed policy categories and must be confirmed against actual implementations.

The initial MVP should not expose unrestricted host, shell, or network administration tools to agents.

## 7. Capability Registry

### 7.1 Responsibilities

The registry maintains:

- Capability identifier.
- Capability name.
- Description.
- Category.
- Responsible worker.
- Input schema.
- Output schema.
- Required permissions.
- Risk classification.
- Timeout.
- Retry policy.
- Execution mode.
- Version.
- Availability status.

### 7.2 Capability registration

Example:

```json
{
  "capability_id": "correlate_events",
  "name": "Correlate Security Events",
  "description": "Identifies temporal and entity-based relationships between security events.",
  "category": "correlation",
  "worker": "correlation_agent",
  "version": "1.0.0",
  "risk_level": "low",
  "execution_mode": "synchronous",
  "permissions": [
    "events:read",
    "correlations:write"
  ],
  "enabled": true
}
```

### 7.3 Registry implementation

Suggested package:

```text
backend/
└── app/
    └── capabilities/
        ├── registry.py
        ├── manager.py
        ├── models.py
        ├── schemas.py
        ├── discovery.py
        ├── policies.py
        ├── permissions.py
        ├── executor.py
        ├── validator.py
        ├── errors.py
        └── implementations/
            ├── event_search.py
            ├── detection.py
            ├── correlation.py
            ├── investigation.py
            ├── retrieval.py
            ├── reporting.py
            └── response.py
```

### 7.4 Registration validation

A capability must not become available until:

- Its identifier is unique.
- Its input schema is valid.
- Its output schema is valid.
- Its implementation exists.
- Its required permissions are defined.
- Its risk level is assigned.
- Its timeout is configured.
- Its version is recorded.
- Its test suite passes.

An unavailable or invalid capability must not be advertised to the Planner.

## 8. Capability Contract

Every capability must implement a standard contract.

### 8.1 Input contract

Example for `correlate_events`:

```json
{
  "investigation_id": "INV-001",
  "event_refs": [
    "EVT-001",
    "EVT-002"
  ],
  "correlation_options": {
    "temporal_window_seconds": 300,
    "entity_matching": true
  }
}
```

### 8.2 Output contract

```json
{
  "status": "completed",
  "correlation_run_id": "CORR-001",
  "relationships": [
    {
      "source_event_id": "EVT-001",
      "target_event_id": "EVT-002",
      "relationship_type": "shared_source_ip"
    }
  ],
  "summary": "Two events share a normalized source IP address.",
  "evidence_refs": [
    "EVT-001",
    "EVT-002"
  ]
}
```

### 8.3 Contract requirements

Each capability must define:

- Required inputs.
- Optional inputs.
- Input constraints.
- Output structure.
- Error categories.
- Side effects.
- Permissions.
- Idempotency behavior.
- Execution timeout.
- Version compatibility.

A capability must not accept arbitrary unvalidated dictionaries where a strict schema is practical.

## 9. Capability Discovery

### 9.1 Purpose

The Planner must know which capabilities are available before proposing tasks.

The registry should expose a filtered capability catalog.

### 9.2 Discovery workflow

```text
Planner Requests Capabilities
             |
             v
      Registry Query
             |
             v
       Filter Disabled
             |
             v
       Filter Permissions
             |
             v
       Filter Task Context
             |
             v
       Return Capability Catalog
             |
             v
          Planner
```

### 9.3 Discovery filters

Capability discovery should consider:

- Capability status.
- Investigation context.
- Caller permissions.
- Required inputs.
- Capability dependencies.
- Risk policy.
- Current system availability.

### 9.4 Planner-facing catalog

The Planner should receive concise capability descriptions.

It does not need internal implementation details or unrestricted access to tool configuration.

Example:

```json
{
  "available_capabilities": [
    {
      "capability_id": "correlate_events",
      "description": "Identify relationships between supplied security events.",
      "required_inputs": [
        "investigation_id",
        "event_refs"
      ],
      "expected_output": "correlation_result"
    },
    {
      "capability_id": "retrieve_knowledge",
      "description": "Retrieve relevant information from approved security knowledge sources.",
      "required_inputs": [
        "query"
      ],
      "expected_output": "knowledge_results"
    }
  ]
}
```

The Planner may propose a capability identifier, but it cannot introduce a new identifier or change the capability's registered contract.

## 10. Planner-to-Capability Execution Contract

The Planner should produce task proposals.

The execution runtime converts approved proposals into registered capability invocations.

Example:

```json
{
  "task_id": "TASK-1001",
  "investigation_id": "INV-001",
  "capability_id": "correlate_events",
  "objective": "Identify relationships between suspicious authentication events",
  "priority": 1,
  "input": {
    "event_refs": [
      "EVT-001",
      "EVT-002"
    ]
  },
  "depends_on": [],
  "expected_output": "correlation_result"
}
```

The runtime must independently validate:

1. Capability existence.
2. Capability availability.
3. Caller authorization.
4. Input schema.
5. Resource limits.
6. Dependencies.
7. Risk policy.
8. Idempotency.
9. Execution timeout.

Only then may execution begin.

## 11. Tool Execution Architecture

### 11.1 Execution lifecycle

```text
Task Proposal
     |
     v
Task Validation
     |
     v
Capability Lookup
     |
     v
Permission Validation
     |
     v
Input Validation
     |
     v
Execution Policy
     |
     v
Capability Executor
     |
     v
Worker Implementation
     |
     v
Output Validation
     |
     v
Persist Task Result
     |
     v
Update Investigation State
     |
     v
Planner Re-evaluation
```

### 11.2 Executor responsibilities

The executor must:

- Resolve the registered capability.
- Create an execution record.
- Apply authorization.
- Validate arguments.
- Enforce timeout.
- Manage retries.
- Capture errors.
- Validate outputs.
- Persist execution metadata.
- Return a normalized result.

The executor must not allow the model to bypass the registry.

### 11.3 Proposed executor interface

```python
from typing import Any, Protocol

class Capability(Protocol):

    async def execute(
        self,
        inputs: dict[str, Any],
        context: dict[str, Any]
    ) -> dict[str, Any]:
        ...
```

The actual implementation should use validated Pydantic input and output models rather than unrestricted dictionaries.

### 11.4 Execution context

The execution context should contain:

- Investigation identifier.
- Task identifier.
- Execution identifier.
- Authorized actor.
- Granted permissions.
- Correlation identifier.
- Deadline.
- Trace identifier.

The context must be created by the trusted runtime, not generated by the Planner.

## 12. Permission and Risk Model

### 12.1 Permission categories

Suggested permissions:

| Permission | Meaning |
|---|---|
| `events:read` | Read authorized security events |
| `findings:read` | Read detection findings |
| `findings:write` | Create detection findings |
| `correlations:read` | Read correlation results |
| `correlations:write` | Create correlation results |
| `evidence:read` | Read investigation evidence |
| `evidence:write` | Attach validated evidence |
| `knowledge:read` | Search approved knowledge |
| `reports:write` | Generate reports |
| `response:recommend` | Recommend response actions |
| `response:simulate` | Simulate approved response actions |

Use least-privilege permissions.

A worker should receive only the permissions required for its assigned task.

### 12.2 Risk levels

| Risk | Description | Default treatment |
|---|---|---|
| Low | Read-only retrieval or analysis | Automated execution allowed |
| Medium | Writes investigation state or generates simulated actions | Policy-controlled execution |
| High | Could affect external systems or sensitive data | Explicit authorization and human approval |
| Critical | Potentially destructive or irreversible | Disabled unless separately approved and engineered |

The exact risk classification must be assigned to each implementation, not merely its capability name.

### 12.3 Human approval

For the MVP:

- Response recommendations may be generated automatically.
- Response simulations may execute within defined constraints.
- Real containment or system modification must remain disabled.
- Any future live response action requires a separate authorization design.

An LLM-generated approval is never valid authorization.

## 13. Task Execution Modes

### 13.1 Synchronous execution

Suitable for short operations:

- Read event references.
- Search knowledge.
- Retrieve findings.
- Validate input.
- Generate simple summaries.

### 13.2 Asynchronous execution

Suitable for longer operations:

- Large event searches.
- Batch correlation.
- Dataset processing.
- ML inference over large batches.
- Long-running investigation analysis.

### 13.3 Execution state

Suggested states:

```text
PENDING
   |
   v
VALIDATING
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
   +------> TIMED_OUT
   |
   +------> CANCELLED
   |
   +------> BLOCKED
```

The task lifecycle should be persisted.

The Planner must be able to inspect task status without relying on conversational context.

## 14. Parallel Execution and Dependencies

The Planner may propose multiple tasks when they are independent.

Example:

```text
                 Planner
                    |
           +--------+--------+
           |                 |
           v                 v
      Event Search       Knowledge Retrieval
           |                 |
           +--------+--------+
                    |
                    v
               State Update
                    |
                    v
              Planner Review
```

### 14.1 Dependency validation

Tasks may specify dependencies.

Example:

```json
{
  "task_id": "TASK-1003",
  "capability_id": "analyze_evidence",
  "depends_on": [
    "TASK-1001",
    "TASK-1002"
  ]
}
```

The execution runtime must validate the dependency graph.

It must reject:

- Unknown task dependencies.
- Self-dependencies.
- Cyclic dependencies.
- Dependencies belonging to another investigation.
- Execution before prerequisite completion.

### 14.2 Concurrency limits

Configure:

- Maximum concurrent tasks per investigation.
- Maximum concurrent tasks globally.
- Maximum concurrent model requests.
- Maximum queue length.
- Per-capability concurrency limits.

These limits should be based on hardware and workload benchmarks.

Parallelism must not create uncontrolled database contention or exhaust model resources.

## 15. Retries, Idempotency, and Failure Handling

### 15.1 Retry policy

Each capability should define:

- Maximum attempts.
- Retryable errors.
- Backoff strategy.
- Execution timeout.
- Failure escalation behavior.

Do not retry all failures indiscriminately.

For example:

| Failure | Retry policy |
|---|---|
| Temporary database outage | Retry |
| Temporary model unavailability | Retry within limit |
| Invalid input schema | Do not retry unchanged input |
| Permission denied | Do not retry |
| Missing required evidence | Return blocked result |
| Unsupported capability | Reject |
| Output validation failure | Limited repair or retry, if safe |

### 15.2 Idempotency

Every task should have an idempotency key.

Example:

```json
{
  "task_id": "TASK-1001",
  "idempotency_key": "INV-001-correlate-events-v1"
}
```

The key should represent the logical operation and its relevant input version.

Repeated requests must not create duplicate side effects.

### 15.3 Partial failure

If one task in a parallel group fails:

- Preserve successful task results.
- Record the failed task.
- Update investigation state.
- Allow the Planner to replan.
- Avoid automatically restarting all successful work.

The Planner should decide whether an alternative capability or additional evidence is required.

## 16. Output Validation

A worker response must pass validation before it is incorporated into investigation state.

Validation includes:

1. JSON parsing.
2. Schema validation.
3. Required-field checks.
4. Reference validation.
5. Permission validation.
6. Business-rule validation.
7. Provenance validation.

Example:

A correlation worker returns a relationship between two events.

The runtime must verify that:

- Both event identifiers exist.
- Both events belong to an accessible dataset or investigation scope.
- The relationship type is allowed.
- The correlation result has a valid provenance reference.

An invalid response must not become authoritative investigation state.

## 17. Capability Versioning

Every capability should have a version.

Version changes may affect:

- Input schema.
- Output schema.
- Execution behavior.
- Permission requirements.
- Resource requirements.

Example:

```json
{
  "capability_id": "correlate_events",
  "version": "1.1.0",
  "input_schema_version": "1.0",
  "output_schema_version": "1.1",
  "status": "active"
}
```

### 17.1 Compatibility rules

- Backward-compatible changes may increment the minor version.
- Breaking contract changes should increment the major version.
- Bug fixes should increment the patch version.
- Running tasks should retain their original capability version.

The exact semantic versioning policy should be enforced consistently.

## 18. Database Design

Suggested tables:

```text
capabilities
capability_versions
capability_permissions
capability_schemas
capability_executions
agent_tasks
task_dependencies
task_attempts
task_results
execution_audit
```

### 18.1 Capability table

```sql
CREATE TABLE capabilities (
    id UUID PRIMARY KEY,
    capability_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(100) NOT NULL,
    worker_id VARCHAR(100) NOT NULL,
    risk_level VARCHAR(30) NOT NULL,
    execution_mode VARCHAR(30) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 18.2 Execution table

```sql
CREATE TABLE capability_executions (
    id UUID PRIMARY KEY,
    task_id UUID NOT NULL,
    capability_id VARCHAR(100) NOT NULL,
    capability_version VARCHAR(30) NOT NULL,
    execution_status VARCHAR(30) NOT NULL,
    attempt_number INTEGER NOT NULL DEFAULT 1,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_code VARCHAR(100),
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

The final schema must be reconciled with the existing task and execution tables.

Do not duplicate existing task persistence structures.

## 19. LangGraph Integration

LangGraph should manage the investigation control flow.

The capability registry and executor should be invoked from controlled graph nodes.

Suggested graph:

```text
START
  |
  v
Load Investigation State
  |
  v
Planner Node
  |
  v
Plan Validation
  |
  v
Capability Discovery
  |
  v
Task Dispatch
  |
  v
Execution Runtime
  |
  v
Output Validation
  |
  v
State Update
  |
  v
Planner Re-evaluation
  |
  +------> More Tasks
  |
  +------> Human Review
  |
  +------> Completion
  |
  v
END
```

The graph is not a fixed sequence of agents.

The Planner may choose different registered capabilities and revisit previous capabilities based on the current evidence.

### 19.1 Runtime ownership

The following components own distinct responsibilities:

| Component | Responsibility |
|---|---|
| Planner | Selects investigation objectives and proposes tasks |
| Capability Registry | Defines available operations |
| Policy Engine | Determines whether an operation is permitted |
| Executor | Controls task execution |
| Worker | Performs assigned task |
| Validator | Checks result validity |
| State Manager | Persists accepted results |
| LangGraph | Coordinates investigation control flow |

## 20. Security Requirements

The capability execution boundary is a major security control.

Required safeguards:

- No arbitrary shell execution.
- No arbitrary SQL generated by the Planner.
- No unrestricted HTTP requests.
- No model-generated executable code.
- No direct LLM access to unrestricted database credentials.
- Strict capability allowlists.
- Least-privilege permissions.
- Input and output validation.
- Execution timeouts.
- Bounded retries.
- Audit logging.
- Investigation and tenant isolation.
- Human approval for sensitive actions.

Capability descriptions and retrieved content must be treated as data, not as authority to bypass permissions.

## 21. Observability

Every execution should be traceable.

Required identifiers:

- `investigation_id`
- `task_id`
- `execution_id`
- `capability_id`
- `capability_version`
- `worker_id`
- `attempt_number`
- `trace_id`

Suggested metrics:

```text
sentinel_capability_executions_total
sentinel_capability_failures_total
sentinel_capability_latency_seconds
sentinel_capability_retries_total
sentinel_capability_timeouts_total
sentinel_capability_blocked_total
sentinel_task_queue_depth
sentinel_task_success_rate
sentinel_parallel_tasks_active
```

Metrics should be filterable by capability and worker.

## 22. Evaluation Framework

The registry and execution architecture should be evaluated independently of detection accuracy.

| Metric | Purpose |
|---|---|
| Capability selection accuracy | Measures whether the Planner selects appropriate capabilities |
| Registry lookup success | Measures successful capability resolution |
| Input validation rate | Measures contract compliance |
| Output validation rate | Measures valid worker results |
| Execution success rate | Measures successful task execution |
| Retry recovery rate | Measures successful recovery after transient failures |
| Duplicate execution rate | Measures idempotency effectiveness |
| Permission violation rate | Measures unauthorized execution attempts |
| Task latency | Measures execution overhead |
| Parallel execution efficiency | Measures performance improvement from safe parallelism |

### 22.1 Orchestration experiments

Compare:

- Direct agent invocation vs registry-mediated execution.
- Unrestricted task input vs schema-validated input.
- Unbounded retries vs bounded retries.
- Sequential execution vs dependency-aware parallel execution.
- No capability versioning vs versioned execution.
- No permission validation vs policy-enforced execution.

The goal is to demonstrate reliability, security, and measurable execution efficiency.

## 23. Implementation Roadmap

### Phase 1 — Registry foundation

- Define capability metadata schema.
- Implement registry.
- Register initial capabilities.
- Add capability validation.
- Add availability checks.

### Phase 2 — Contracts

- Define input and output schemas.
- Implement Pydantic validation.
- Define error categories.
- Add capability versioning.
- Add contract tests.

### Phase 3 — Execution runtime

- Implement executor.
- Add permission validation.
- Add execution records.
- Implement timeouts.
- Add idempotency.

### Phase 4 — Planner integration

- Expose filtered capability discovery.
- Update Planner output schema.
- Validate proposed tasks.
- Integrate task dispatch with LangGraph.
- Add task status retrieval.

### Phase 5 — Advanced execution

- Add asynchronous tasks.
- Implement dependency graphs.
- Add concurrency controls.
- Add bounded retries.
- Add cancellation.

### Phase 6 — Security and evaluation

- Test unauthorized invocation.
- Test invalid inputs and outputs.
- Test duplicate execution.
- Test partial failure.
- Benchmark parallelism.
- Add execution dashboards.

## 24. Acceptance Criteria

| ID | Acceptance criterion |
|---|---|
| CAP-01 | All executable capabilities are registered |
| CAP-02 | Each capability has a defined contract |
| CAP-03 | Invalid capabilities cannot be registered |
| CAP-04 | Planner discovers capabilities through the registry |
| CAP-05 | Planner cannot introduce arbitrary capability identifiers |
| CAP-06 | Every task passes schema validation |
| CAP-07 | Permissions are checked before execution |
| CAP-08 | All executions are persisted |
| CAP-09 | Output validation occurs before state updates |
| CAP-10 | Retry behavior is bounded |
| CAP-11 | Idempotency prevents duplicate side effects |
| CAP-12 | Dependencies are validated |
| CAP-13 | Parallel execution respects configured limits |
| CAP-14 | Capability versions are recorded |
| CAP-15 | Unauthorized operations are rejected |
| CAP-16 | Execution failures preserve completed task results |
| CAP-17 | Capability execution is observable and auditable |

## 25. Key Architectural Decisions

| Decision | MVP position |
|---|---|
| Capability discovery | Central registry |
| Planner interface | Structured task proposals |
| Execution | Registry-mediated |
| Validation | Pydantic plus semantic checks |
| Permissions | Least-privilege capability policies |
| Execution framework | LangGraph integration |
| Task persistence | PostgreSQL |
| Cache and queue support | Redis where needed |
| Parallelism | Bounded and dependency-aware |
| Retries | Configurable and bounded |
| Idempotency | Required for side-effecting operations |
| Response execution | Simulation only |
| Tool access | Registered capabilities only |

## 26. Final Architectural Position

The capability registry and execution runtime provide the operational boundary between AI reasoning and actual system behavior.

The Planner should be able to reason dynamically about what needs to happen next, but it should not have unrestricted authority to execute operations.

The registry defines what operations exist. The policy engine defines what is allowed. The executor controls execution. Workers perform bounded tasks. Validators ensure that only acceptable results enter authoritative investigation state.

This architecture allows Project Sentinel to add specialized capabilities without turning the Planner into a collection of hardcoded agent calls.

The system's central differentiator remains dynamic orchestration, supported by a controlled and extensible capability execution layer.
