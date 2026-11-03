# Project Sentinel — Capability & Tool Implementation Specification (CTIS)

**Document Type:** Technical Design and Implementation Specification  
**Version:** 1.0  
**Status:** Architecture Baseline  
**Primary Focus:** Capability registry, tool contracts, execution lifecycle, validation, permissions, failure handling, and integration with AI orchestration.  
**Related Components:** Capability Registry, Policy Engine, Capability Executor, Result Validator, AI Planner, State Manager

---

# 1. Purpose

Project Sentinel uses AI agents to investigate cybersecurity incidents. However, an AI Planner should not directly access databases, execute arbitrary code, or manipulate the investigation state without control.

Instead, the Planner operates through a controlled set of **capabilities**.

A capability is a well-defined system operation that:
- Has a specific analytical purpose.
- Accepts strictly validated input schemas.
- Produces deterministic, structured output.
- Operates within defined RBAC permissions.
- Records execution metadata and telemetry.
- Fails safely without cascading crashes.
- Can be measured, profiled, and evaluated.

The core interaction model is:

```text
AI PLANNER
    │
    │ Selects an allowed action
    ▼
CAPABILITY REGISTRY
    │
    │ Validates capability and contract
    ▼
POLICY / PERMISSION CHECK
    │
    ▼
CAPABILITY EXECUTOR
    │
    ▼
STRUCTURED RESULT
    │
    ▼
RESULT VALIDATOR
    │
    ▼
INVESTIGATION STATE
```

> **The Planner decides what information or operation is needed. Capabilities perform the actual controlled work.**

---

# 2. What Is a Capability?

A capability is the atomic operational unit available to the orchestration layer.

Examples:
- `event_query`
- `entity_lookup`
- `event_correlation`
- `timeline_builder`
- `knowledge_retrieval`
- `evidence_validation`
- `report_generation`

A capability is **not necessarily an AI agent**:

```text
AI PLANNER (Agent)
    ├── Reasons about the investigation state
    ├── Identifies evidence gaps
    ├── Selects next actions
    └── Interprets validated findings

CAPABILITY (Tool)
    ├── Performs a specific deterministic or scoped analytical task
    ├── Exposes strict Pydantic input/output contracts
    └── Returns structured data without modifying global state
```

This prevents unnecessary multi-agent communication complexity.

---

# 3. Capability Architecture

```text
┌──────────────────────────────────────────┐
│                AI PLANNER                │
│                                          │
│  Objective → Evidence Gaps → Next Action │
└────────────────────┬─────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────┐
│            CAPABILITY REGISTRY           │
│                                          │
│  Available Capabilities                  │
│  Input Schemas                           │
│  Permissions                             │
│  Metadata                                │
└────────────────────┬─────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────┐
│              POLICY ENGINE               │
│                                          │
│  Is action allowed?                      │
│  Is budget available?                    │
│  Are parameters valid?                   │
└────────────────────┬─────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────┐
│           CAPABILITY EXECUTOR            │
│                                          │
│  Timeout                                 │
│  Retry                                   │
│  Circuit Breaker                         │
│  Execution                               │
└────────────────────┬─────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────┐
│             RESULT VALIDATOR             │
│                                          │
│  Schema Validation                       │
│  Evidence Validation                     │
│  Result Classification                   │
└────────────────────┬─────────────────────┘
                     │
                     ▼
             INVESTIGATION STATE
```

---

# 4. Capability Registry

The Capability Registry is the authoritative source of available operations. The Planner must never invoke an unregistered capability.

## 4.1 Registry Responsibilities
- Capability identifier & semantic description
- Input and output schemas
- Permission requirements
- Timeout configuration
- Retry policies & circuit breaker thresholds
- Cost estimates & historical reliability metrics
- Live availability status

## 4.2 Capability Registration Schema

```json
{
  "capability_id": "event_query",
  "version": "1.0",

  "name": "Event Query",

  "description": "Retrieves normalized events based on validated filters.",

  "input_schema_version": "1.0",
  "output_schema_version": "1.0",

  "permission_level": "read",

  "timeout_seconds": 10,

  "retry_policy": {
    "max_attempts": 2,
    "retryable_errors": [
      "timeout",
      "temporary_service_error"
    ]
  },

  "estimated_cost": 0.1,

  "enabled": true
}
```

---

# 5. Standard Capability Request Contract

```json
{
  "request_id": "REQ-001",

  "investigation_id": "INV-001",

  "action_id": "ACT-001",

  "capability_id": "event_query",

  "input": {},

  "requested_by": "planner",

  "state_version": 5,

  "requested_at": "2026-11-02T12:00:00Z"
}
```

---

# 6. Standard Capability Response Contract

```json
{
  "request_id": "REQ-001",

  "capability_id": "event_query",

  "status": "success",

  "result": {},

  "metadata": {
    "execution_time_ms": 245,
    "attempt": 1
  },

  "evidence_references": [],

  "error": null
}
```

### Allowed Status Values:
- `success`: Execution completed with findings.
- `no_result`: Execution succeeded cleanly but found 0 matches.
- `partial_success`: Execution succeeded partially; valid partial findings returned.
- `failed`: Execution failed due to runtime or service error.
- `timeout`: Execution exceeded configured timeout limit.
- `denied`: Policy or budget check rejected execution.

---

# 7. Capability Execution Lifecycle

```text
REQUEST ──► INPUT VALIDATION ──► POLICY CHECK ──► BUDGET CHECK ──► EXECUTION ──┬──► RESULT VALIDATION ──► AUDIT RECORD ──► RESPONSE
                                                                               │
                                                                               └──► (Failure) ──► RETRY POLICY / CIRCUIT BREAKER
```

---

# 8. Input & Policy Validation

1. **Input Validation**: Rejects malformed JSON, missing fields, or invalid types before any database query executes.
2. **Policy Validation**: Verifies that capability is enabled, caller possesses permission, investigation is in `RUNNING` status, and budget remains.

---

# 9. Seven Core Capabilities

---

## 10. Capability 1 — Event Query (`event_query`)

### Purpose
Retrieves normalized telemetry relevant to the investigation without exposing raw SQL or arbitrary filters.

### Input Schema
```json
{
  "time_range": {
    "start": "2026-11-02T09:00:00Z",
    "end": "2026-11-02T10:00:00Z"
  },

  "entities": [
    {
      "entity_type": "host",
      "value": "host-01"
    }
  ],

  "event_types": [
    "network_connection"
  ],

  "limit": 100
}
```

### Output Schema
```json
{
  "events": [
    {
      "event_id": "evt_001",
      "event_type": "network_connection",
      "occurred_at": "2026-11-02T09:30:00Z",
      "entity_refs": [
        "ENT-001"
      ]
    }
  ],

  "total_matches": 1,

  "returned_count": 1
}
```

---

## 11. Capability 2 — Entity Lookup (`entity_lookup`)

### Purpose
Retrieves historical context, activity frequency, and known associations for a pivot entity.

### Input Schema
```json
{
  "entity_type": "host",
  "entity_value": "host-01"
}
```

### Output Schema
```json
{
  "entity": {
    "entity_id": "ENT-001",
    "entity_type": "host",
    "normalized_value": "host-01"
  },

  "related_event_count": 24,

  "first_seen": "2026-11-02T08:00:00Z",
  "last_seen": "2026-11-02T10:30:00Z"
}
```

---

## 12. Capability 3 — Event Correlation (`event_correlation`)

### Purpose
Performs deterministic multi-dimensional correlation (entity overlap + temporal proximity) from seed events.

### Input Schema
```json
{
  "seed_event_ids": [
    "evt_001"
  ],

  "time_window_seconds": 600,

  "correlation_methods": [
    "entity",
    "temporal"
  ],

  "minimum_score": 0.60
}
```

### Output Schema
```json
{
  "correlations": [
    {
      "related_event_id": "evt_002",
      "correlation_type": "entity_temporal",
      "score": 0.82,

      "shared_entities": [
        "host-01"
      ],

      "time_difference_seconds": 120
    }
  ]
}
```

---

## 13. Capability 4 — Timeline Builder (`timeline_builder`)

### Purpose
Sorts and groups correlated events chronologically, generating a human-readable investigation sequence.

### Input Schema
```json
{
  "event_ids": [
    "evt_001",
    "evt_002",
    "evt_003"
  ]
}
```

### Output Schema
```json
{
  "timeline": [
    {
      "timestamp": "2026-11-02T09:00:00Z",
      "event_id": "evt_001",
      "summary": "Observed network connection."
    }
  ]
}
```

---

## 14. Capability 5 — Knowledge Retrieval (`knowledge_retrieval`)

### Purpose
Executes semantic RAG over MITRE ATT&CK chunks in ChromaDB to supply domain context.

### Input Schema
```json
{
  "query": "What behavior is associated with this network pattern?",

  "top_k": 5,

  "filters": {
    "knowledge_domain": "attack_techniques"
  }
}
```

### Output Schema
```json
{
  "documents": [
    {
      "document_id": "DOC-001",
      "title": "Relevant Security Technique",
      "content": "Retrieved content excerpt.",
      "relevance_score": 0.88,
      "source_reference": "knowledge://DOC-001"
    }
  ]
}
```

> **Safety Rule**: Retrieved knowledge is *contextual domain information*, never empirical evidence of what occurred.

---

## 15. Capability 6 — Evidence Validation (`evidence_validation`)

### Purpose
Validates whether a proposed claim is grounded by empirical telemetry evidence.

### Input Schema
```json
{
  "claim": "The observed activity is related to the investigated scenario.",

  "evidence_ids": [
    "EVD-001",
    "EVD-002"
  ]
}
```

### Output Schema
```json
{
  "validation_status": "supported",

  "support_score": 0.81,

  "supporting_evidence": [
    "EVD-001",
    "EVD-002"
  ],

  "conflicting_evidence": [],

  "unresolved_questions": [
    "Additional host activity may require review."
  ]
}
```

---

## 16. Capability 7 — Report Generation (`report_generation`)

### Purpose
Generates a structured, auditable report from finalized state facts, evidence, and timeline.

### Input Schema
```json
{
  "investigation_id": "INV-001",

  "include_timeline": true,

  "include_evidence": true,

  "include_actions": true
}
```

### Output Schema
```json
{
  "report_id": "RPT-001",

  "summary": "Investigation completed.",

  "sections": [
    "summary",
    "timeline",
    "evidence",
    "actions",
    "outcome"
  ],

  "generated_at": "2026-11-02T12:30:00Z"
}
```

---

# 17. Operational Safeguards: Timeouts, Retries & Circuit Breakers

### 17.1 Timeout Matrix
| Capability | Timeout | Permission | Risk Level |
|---|---:|---|---|
| `event_query` | 10 seconds | Read | Low |
| `entity_lookup` | 5 seconds | Read | Low |
| `event_correlation` | 15 seconds | Read/Compute | Low |
| `timeline_builder` | 10 seconds | Compute | Low |
| `knowledge_retrieval` | 15 seconds | Read | Low |
| `evidence_validation` | 10 seconds | Compute | Medium |
| `report_generation` | 30 seconds | Write | Medium |

### 17.2 Exponential Backoff Retries
$$\text{Delay}_n = \text{BaseDelay} \times 2^{(n-1)}$$
Only retryable errors (`timeout`, `temporary_service_error`) trigger retries; deterministic errors (`invalid_input`, `policy_denied`) immediately return failure.

### 17.3 Circuit Breaker States
```text
CLOSED ──► (5 Consecutive Failures) ──► OPEN (Requests blocked for 60s) ──► HALF-OPEN ──► (2 Successes) ──► CLOSED
```

---

# 18. Capability Reliability & Utility Scoring

$$\text{Success Rate} = \frac{\text{Successful Executions}}{\text{Total Executions}}$$

$$\text{Useful Result Rate} = \frac{\text{Results Used in Investigation}}{\text{Successful Executions}}$$

### Action Utility Formula for Planner Action Selection:
$$U_a = \frac{IG_a \times R_a \times P_a}{C_a}$$
Where $IG_a$ is expected gap reduction, $R_a$ is historical reliability, $P_a$ is gap priority, and $C_a$ is estimated execution cost.

---

# 19. Execution Audit Record Schema

```json
{
  "execution_id": "EXEC-001",

  "investigation_id": "INV-001",

  "capability_id": "event_query",

  "request_id": "REQ-001",

  "status": "success",

  "execution_time_ms": 245,

  "attempts": 1,

  "started_at": "2026-11-02T12:00:00Z",
  "completed_at": "2026-11-02T12:00:01Z"
}
```

---

# 20. End-to-End Orchestration Loop

```text
INVESTIGATION STATE ──► AI PLANNER (Identify Gaps) ──► SELECT ACTION ──► REGISTRY ──► POLICY ENGINE ──► EXECUTOR ──► RESULT VALIDATOR ──► STATE MANAGER ──► REPLAN / TERMINATE
```

> **The AI Planner provides intelligence and decision-making. The capability layer provides controlled execution. The policy layer provides safety. The state layer provides continuity and auditability.**
