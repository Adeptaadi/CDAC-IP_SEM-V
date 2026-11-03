# Project Sentinel
# API Contract & Integration Specification

**Document Type:** Technical Interface Specification  
**Version:** 1.0  
**Status:** Architecture Baseline  
**Primary Focus:** API boundaries, request/response contracts, authentication, integration flows, error handling, and communication between the frontend and backend.

---

# 1. Purpose

Project Sentinel contains multiple architectural layers:

- React frontend.
- FastAPI backend.
- Detection pipeline.
- Agent orchestration layer.
- Investigation services.
- Evidence management.
- Retrieval and knowledge services.
- PostgreSQL and supporting infrastructure.

These components require clear communication boundaries.

The API layer acts as the controlled entry point to the system.

```text
ANALYST
   │
   ▼
FRONTEND
   │ HTTPS
   ▼
API CONTRACT
   │
   ▼
APPLICATION SERVICES
   │
   ├── Alerts
   ├── Investigations
   ├── Evidence
   ├── Review
   └── System Status
```

The primary principle is:

> **The frontend requests application operations through stable APIs. Internal orchestration, agents, databases, and AI services remain behind the backend boundary.**

---

# 2. API Design Principles

The Project Sentinel API should follow these principles.

## 2.1 Resource-Oriented Design

Major application objects are represented as resources.

```text
/users
/alerts
/investigations
/evidence
/reviews
```

---

## 2.2 Stable External Contracts

The frontend should depend on documented request and response schemas rather than internal implementation details.

For example:

```text
Frontend
    │
    ▼
Investigation API Contract
    │
    ▼
Application Service
    │
    ▼
Orchestration Implementation
```

The orchestrator can evolve without requiring unnecessary frontend changes.

---

## 2.3 No Direct Infrastructure Access

The API is the only normal application boundary for the frontend.

The frontend must not directly communicate with:

- PostgreSQL.
- Redis.
- ChromaDB.
- Ollama.
- Agent execution internals.

---

## 2.4 Explicit State

Responses should expose meaningful application states.

For example:

```text
pending
running
waiting_review
completed
failed
```

The frontend should not infer investigation state from incomplete internal information.

---

# 3. API Base Structure

A recommended API structure is:

```text
/api/v1
│
├── /auth
├── /alerts
├── /investigations
├── /evidence
├── /reviews
└── /system
```

Versioning provides a controlled mechanism for future changes.

---

# 4. Common Response Structure

API responses should be predictable.

A successful response can follow this conceptual structure:

```json
{
  "data": {},
  "meta": {}
}
```

An error response can follow:

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested investigation was not found."
  }
}
```

The exact implementation can use standard FastAPI and HTTP response behavior, but consistency should be maintained.

---

# 5. Authentication API

Authentication is an application-level concern.

For the MVP, the recommended approach is JWT-based authentication.

## 5.1 Login

```text
POST /api/v1/auth/login
```

### Request

```json
{
  "username": "analyst",
  "password": "password"
}
```

### Response

```json
{
  "access_token": "jwt-token",
  "token_type": "bearer"
}
```

The token represents the authenticated user for subsequent API requests.

---

## 5.2 Current User

```text
GET /api/v1/auth/me
```

Example response:

```json
{
  "id": "user-001",
  "username": "analyst",
  "role": "analyst"
}
```

---

# 6. Alert API

Alerts represent security events requiring attention or investigation.

The primary endpoints are:

```text
GET    /alerts
GET    /alerts/{alert_id}
POST   /alerts/{alert_id}/investigations
```

---

## 6.1 List Alerts

```text
GET /api/v1/alerts
```

Recommended query parameters:

```text
status
severity
limit
offset
```

Example:

```text
GET /api/v1/alerts?status=open&severity=high
```

Example response:

```json
{
  "data": [
    {
      "id": "alert-001",
      "title": "Suspicious Process Activity",
      "severity": "high",
      "confidence": 0.87,
      "status": "open",
      "created_at": "2026-01-01T10:00:00Z"
    }
  ],
  "meta": {
    "total": 1
  }
}
```

---

# 7. Alert Detail API

```text
GET /api/v1/alerts/{alert_id}
```

The response should include:

- Alert summary.
- Detection context.
- Severity.
- Confidence.
- Related event references.
- Investigation status.

Example:

```json
{
  "data": {
    "id": "alert-001",
    "title": "Suspicious Process Activity",
    "severity": "high",
    "confidence": 0.87,
    "status": "open",
    "related_events": [
      "event-001",
      "event-002"
    ]
  }
}
```

Large raw telemetry should not necessarily be returned in every alert response.

Detailed evidence should be retrieved through dedicated interfaces.

---

# 8. Create Investigation

An investigation can be initiated from an alert.

```text
POST /api/v1/alerts/{alert_id}/investigations
```

The backend performs:

```text
API REQUEST
    │
    ▼
VALIDATE ALERT
    │
    ▼
CREATE INVESTIGATION
    │
    ▼
INITIALIZE ORCHESTRATION
    │
    ▼
RETURN INVESTIGATION
```

Example response:

```json
{
  "data": {
    "investigation_id": "inv-001",
    "alert_id": "alert-001",
    "status": "created"
  }
}
```

The API should return quickly rather than waiting for the entire AI investigation to complete.

---

# 9. Investigation API

Recommended endpoints:

```text
GET  /investigations
GET  /investigations/{investigation_id}
POST /investigations/{investigation_id}/actions
GET  /investigations/{investigation_id}/timeline
```

---

# 10. Investigation Detail

```text
GET /api/v1/investigations/{investigation_id}
```

The response represents the current durable state.

Example:

```json
{
  "data": {
    "id": "inv-001",
    "alert_id": "alert-001",
    "status": "running",
    "priority": "high",
    "started_at": "2026-01-01T10:01:00Z",
    "summary": null
  }
}
```

The API should distinguish between:

```text
CURRENT SYSTEM STATE
```

and:

```text
FINAL INVESTIGATION CONCLUSION
```

A running investigation may not yet have a valid conclusion.

---

# 11. Investigation State Model

The API should use controlled state values.

```text
created
   │
   ▼
running
   │
   ├──────► waiting_review
   │              │
   ▼              ▼
completed ◄── resumed
   │
   ▼
closed
```

Possible additional state:

```text
failed
```

State transitions must be validated by the backend.

The frontend should not directly modify an investigation's state without an authorized action.

---

# 12. Agent Activity API

Agent execution details should be exposed in a controlled form.

Recommended endpoint:

```text
GET /api/v1/investigations/{investigation_id}/tasks
```

Example response:

```json
{
  "data": [
    {
      "task_id": "task-001",
      "agent_type": "evidence_analysis",
      "status": "completed",
      "summary": "Relevant process activity identified."
    },
    {
      "task_id": "task-002",
      "agent_type": "context_retrieval",
      "status": "running"
    }
  ]
}
```

The response exposes meaningful workflow information without exposing internal prompts or hidden orchestration details.

---

# 13. Evidence API

Evidence should be accessed through dedicated endpoints.

```text
GET /api/v1/investigations/{investigation_id}/evidence
GET /api/v1/evidence/{evidence_id}
```

The evidence list should provide summary information.

Example:

```json
{
  "data": [
    {
      "id": "evidence-001",
      "type": "telemetry",
      "summary": "Unusual child process execution.",
      "source_type": "normalized_event",
      "relevance_score": 0.91
    }
  ]
}
```

Detailed source data can be requested separately.

---

# 14. Evidence Detail

```text
GET /api/v1/evidence/{evidence_id}
```

A response should provide sufficient information for traceability.

Example:

```json
{
  "data": {
    "id": "evidence-001",
    "type": "telemetry",
    "summary": "Unusual child process execution.",
    "source_type": "normalized_event",
    "source_reference": "event-1024",
    "collected_at": "2026-01-01T10:03:00Z",
    "relevance_score": 0.91
  }
}
```

The source reference connects evidence to the data lifecycle.

---

# 15. Investigation Timeline API

The frontend requires a chronological view of activity.

```text
GET /api/v1/investigations/{investigation_id}/timeline
```

Example response:

```json
{
  "data": [
    {
      "timestamp": "2026-01-01T10:01:00Z",
      "event_type": "investigation_started",
      "summary": "Investigation started."
    },
    {
      "timestamp": "2026-01-01T10:02:00Z",
      "event_type": "agent_task_completed",
      "summary": "Evidence analysis completed."
    }
  ]
}
```

Timeline records should be generated from system events.

---

# 16. Analyst Action API

Analyst actions should be expressed as controlled commands.

Recommended endpoint:

```text
POST /api/v1/investigations/{investigation_id}/actions
```

Example request:

```json
{
  "action": "approve_conclusion",
  "comment": "Evidence reviewed and accepted."
}
```

Other actions may include:

```text
reject_conclusion
request_additional_investigation
close_investigation
```

The backend validates whether the action is appropriate for the current state.

---

# 17. Additional Investigation Request

The analyst may request additional investigation without directly assigning low-level agent tasks.

Example:

```json
{
  "action": "request_additional_investigation",
  "objective": "Investigate related network activity."
}
```

The flow is:

```text
ANALYST
   │
   ▼
API ACTION
   │
   ▼
APPLICATION SERVICE
   │
   ▼
ORCHESTRATOR
   │
   ▼
TASK PLANNING
   │
   ▼
AGENT EXECUTION
```

This maintains the orchestrator's role as the central decision layer.

---

# 18. Review Queue API

The analyst requires a list of investigations needing attention.

```text
GET /api/v1/reviews
```

Each record should include:

```text
investigation_id
priority
reason
status
created_at
```

Example reasons:

- Conflicting evidence.
- Low confidence.
- High-risk conclusion.
- Agent failure.
- Explicit human review requirement.

---

# 19. System Status API

A limited system status endpoint may support development and operational visibility.

```text
GET /api/v1/system/status
```

Conceptual response:

```json
{
  "data": {
    "api": "healthy",
    "database": "healthy",
    "ai_service": "available",
    "retrieval_service": "available"
  }
}
```

Operational health must not be confused with investigation status.

---

# 20. Error Contract

The API should use meaningful HTTP status codes.

| Status | Meaning |
|---|---|
| 200 | Successful request |
| 201 | Resource created |
| 400 | Invalid request |
| 401 | Authentication required |
| 403 | Action not authorized |
| 404 | Resource not found |
| 409 | Invalid state or conflict |
| 422 | Validation failure |
| 500 | Unexpected server failure |
| 503 | Required service unavailable |

A structured error should contain:

```text
error code
human-readable message
optional details
```

Internal implementation details should not be exposed to the frontend.

---

# 21. AI and Agent Failure Representation

An AI service failure should not always appear as a complete application failure.

For example:

```text
AGENT TASK FAILURE
       │
       ▼
TASK STATUS = FAILED
       │
       ▼
INVESTIGATION CONTINUES
       │
       ▼
REVIEW OR FALLBACK
```

The API should communicate the actual state.

Example:

```json
{
  "data": {
    "task_id": "task-002",
    "status": "failed",
    "reason": "AI service timeout"
  }
}
```

This supports the system's fault-tolerant investigation architecture.

---

# 22. Pagination

List endpoints should support pagination.

Recommended parameters:

```text
limit
offset
```

Example:

```text
GET /api/v1/alerts?limit=20&offset=0
```

Response metadata:

```json
{
  "meta": {
    "total": 100,
    "limit": 20,
    "offset": 0
  }
}
```

---

# 23. Filtering

Major list endpoints should support controlled filters.

Examples:

```text
GET /alerts?status=open
GET /alerts?severity=high
GET /investigations?status=waiting_review
```

Filters should be explicitly documented rather than accepting arbitrary database query parameters.

---

# 24. API Authentication Flow

The complete authentication flow is:

```text
ANALYST
   │
   ▼
LOGIN REQUEST
   │
   ▼
AUTH API
   │
   ▼
IDENTITY VALIDATION
   │
   ▼
JWT ISSUED
   │
   ▼
AUTHENTICATED API REQUEST
```

Protected endpoints validate authentication before application processing.

---

# 25. Authorization Boundary

Authorization should be enforced by backend services.

The model is:

```text
REQUEST
   │
   ▼
AUTHENTICATION
   │
   ▼
AUTHORIZATION
   │
   ▼
APPLICATION ACTION
```

The frontend can hide unavailable actions for usability, but backend authorization remains mandatory.

---

# 26. API-to-Orchestration Boundary

The API layer should not contain agent workflow logic.

The architecture should remain:

```text
API
 │
 ▼
APPLICATION SERVICE
 │
 ▼
ORCHESTRATION SERVICE
 │
 ▼
AGENT / CAPABILITY EXECUTION
```

For example, this API request:

```text
POST /investigations/{id}/actions
```

should not directly invoke an individual agent.

Instead, it communicates an application-level intent to the orchestration layer.

---

# 27. Complete Integration Flow

The complete frontend-to-agent workflow is:

```text
┌──────────────┐
│   ANALYST    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   FRONTEND   │
└──────┬───────┘
       │ HTTPS
       ▼
┌──────────────┐
│   FASTAPI    │
│     API      │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ APPLICATION  │
│   SERVICE    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ ORCHESTRATOR │
└──────┬───────┘
       │
 ┌─────┼─────┐
 ▼     ▼     ▼
AGENT CAP.  RAG
 │     │     │
 └─────┼─────┘
       │
       ▼
┌──────────────┐
│   EVIDENCE   │
│   & STATE    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ API RESPONSE │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   FRONTEND   │
└──────────────┘
```

---

# 28. API Acceptance Criteria

The API layer is complete when:

### Authentication

- Protected resources require authentication.
- User identity is available to application services.

### Alerts

- Alerts can be listed and viewed.
- Alert context is available.
- Investigations can be initiated.

### Investigations

- Investigation state can be retrieved.
- Agent task progress is visible.
- Timeline information is available.

### Evidence

- Evidence can be listed and inspected.
- Evidence maintains source references.

### Human Review

- Review-required investigations can be listed.
- Analysts can submit authorized actions.
- Significant actions are auditable.

### Reliability

- Errors use consistent contracts.
- AI and agent failures are represented accurately.
- The API does not expose internal infrastructure details.

---

# 29. Final API Design Principle

The API layer provides a stable bridge between human interaction and the intelligent investigation system.

The complete responsibility chain is:

```text
FRONTEND
    │
    │ User Intent
    ▼
API
    │
    │ Application Request
    ▼
APPLICATION SERVICE
    │
    │ Investigation Objective
    ▼
ORCHESTRATOR
    │
    │ Execution Plan
    ▼
AGENTS + CAPABILITIES
    │
    │ Findings and Evidence
    ▼
APPLICATION STATE
    │
    │ Structured Results
    ▼
API
    │
    ▼
ANALYST
```

The API must therefore remain focused on **application contracts**, while the orchestration layer remains responsible for **intelligent investigation execution**.

---

# Next Recommended Document

## Security Architecture & Threat Model Specification

The next document should define the security posture of Project Sentinel itself.

It should cover:

- Assets requiring protection.
- Trust boundaries.
- Threat actors and threat scenarios.
- Authentication and authorization.
- Secret management.
- Agent and tool security.
- Prompt injection risks.
- RAG security.
- API security.
- Database protection.
- Audit logging.
- Container and deployment security.
- Security acceptance criteria.

This is the next logical step because Project Sentinel is itself a security-oriented system and its AI, agent, data, and infrastructure boundaries should be formally protected.
