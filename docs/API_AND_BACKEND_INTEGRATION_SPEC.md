# Project Sentinel
# API & Backend Integration Specification

**Document Type:** Technical Design Specification  
**Version:** 1.0  
**Status:** Architecture Baseline  
**Primary Technology:** FastAPI  
**Primary Focus:** Backend architecture, API contracts, service integration, asynchronous investigation execution, frontend communication, authentication boundaries, error handling, and system integration.

---

# 1. Purpose

The backend is the operational integration layer of Project Sentinel.

It connects:

- The user-facing frontend.
- Telemetry ingestion.
- Detection and alert generation.
- Investigation lifecycle management.
- AI agent orchestration.
- Capability execution.
- PostgreSQL persistence.
- Knowledge retrieval.

The backend must provide a clear boundary between the user interface and internal system components.

The high-level architecture is:

```text id="api001"
┌──────────────────────────────────────────────┐
│                 FRONTEND                     │
│              React / TypeScript              │
└───────────────────────┬──────────────────────┘
                        │
                    HTTP / WS
                        │
                        ▼
┌──────────────────────────────────────────────┐
│                FASTAPI BACKEND               │
│                                              │
│  API Routes → Services → Domain Components   │
└───────────┬──────────────┬────────────┬──────┘
            │              │            │
            ▼              ▼            ▼
       PostgreSQL      AI Orchestrator  ChromaDB
                           │
                           ▼
                    Agent Capabilities
```

The backend should act as the **controlled entry point and integration boundary** for the system.

---

# 2. Backend Architectural Principles

The backend follows several core principles.

## 2.1 API Routes Should Remain Thin

API routes should primarily handle:

- Request validation.
- Authentication.
- Authorization.
- Calling application services.
- Returning standardized responses.

They should not contain:

- Agent reasoning logic.
- Complex detection algorithms.
- Direct database business logic.
- Long-running investigation workflows.

The preferred flow is:

```text id="api002"
API REQUEST
     │
     ▼
ROUTER
     │
     ▼
SERVICE
     │
     ▼
DOMAIN / ORCHESTRATION
     │
     ▼
REPOSITORY / CAPABILITY
```

---

## 2.2 AI Orchestration Is a Domain Component

The API should not implement the investigation logic itself.

Instead:

```text id="api003"
API
 │
 ▼
Investigation Service
 │
 ▼
Investigation Orchestrator
 │
 ├── Planner
 ├── Workers
 ├── Capabilities
 └── State Manager
```

This ensures that the agent orchestration can evolve independently from the API layer.

---

## 2.3 Long-Running Work Must Not Block Requests

AI investigations may take longer than a normal API request.

Therefore:

```text id="api004"
CLIENT REQUEST
      │
      ▼
CREATE INVESTIGATION
      │
      ▼
RETURN INVESTIGATION ID
      │
      ▼
BACKGROUND EXECUTION
```

The client can subsequently retrieve the current state.

---

# 3. Recommended Backend Structure

```text id="api005"
backend/
│
├── app/
│   │
│   ├── main.py
│   ├── config.py
│   │
│   ├── api/
│   │   ├── router.py
│   │   ├── dependencies.py
│   │   │
│   │   └── routes/
│   │       ├── health.py
│   │       ├── ingestion.py
│   │       ├── alerts.py
│   │       ├── investigations.py
│   │       └── system.py
│   │
│   ├── schemas/
│   │   ├── common.py
│   │   ├── alert.py
│   │   └── investigation.py
│   │
│   ├── services/
│   │   ├── ingestion_service.py
│   │   ├── alert_service.py
│   │   └── investigation_service.py
│   │
│   ├── orchestration/
│   │   ├── planner.py
│   │   ├── state.py
│   │   ├── workflow.py
│   │   └── recovery.py
│   │
│   ├── capabilities/
│   │   ├── registry.py
│   │   └── telemetry_query.py
│   │
│   ├── database/
│   ├── knowledge/
│   └── core/
│
└── tests/
```

The exact folder structure may evolve, but the architectural separation should remain.

---

# 4. API Versioning

The API should use explicit versioning from the beginning.

Recommended baseline:

```text id="api006"
/api/v1/
```

Example:

```text id="api007"
GET /api/v1/alerts
GET /api/v1/investigations/{id}
POST /api/v1/investigations
```

This allows future API changes without immediately breaking clients.

---

# 5. API Domain Groups

The MVP API should be divided into the following groups.

| Domain | Responsibility |
|---|---|
| Health | System availability |
| Ingestion | Dataset and replay operations |
| Alerts | Alert retrieval and management |
| Investigations | Investigation lifecycle |
| System | System metadata and configuration |

The API should avoid exposing internal agent implementation details unnecessarily.

---

# 6. Health API

## Endpoint

```text id="api008"
GET /api/v1/health
```

## Response

```json id="api009"
{
  "status": "healthy",
  "timestamp": "2026-11-02T10:30:00Z"
}
```

A more detailed internal health endpoint may check:

- PostgreSQL connectivity.
- Redis availability.
- AI model availability.
- ChromaDB availability.

These detailed diagnostics should be protected if they expose internal infrastructure information.

---

# 7. Ingestion API

The ingestion API controls dataset processing.

## Start Ingestion

```text id="api010"
POST /api/v1/ingestion/runs
```

Example request:

```json id="api011"
{
  "source_id": "dataset-001",
  "mode": "batch",
  "configuration": {
    "batch_size": 1000
  }
}
```

Example response:

```json id="api012"
{
  "run_id": "ING-001",
  "status": "pending"
}
```

The API request should create the ingestion run and delegate actual processing to the ingestion service.

---

# 8. Replay API

Replay is used to reproduce security scenarios.

## Start Replay

```text id="api013"
POST /api/v1/replays
```

Example request:

```json id="api014"
{
  "source_id": "dataset-001",
  "speed": "max",
  "start_timestamp": null,
  "end_timestamp": null
}
```

The response should identify the replay run.

```json id="api015"
{
  "replay_id": "REP-001",
  "status": "started"
}
```

---

# 9. Alert API

The frontend requires access to detected alerts.

## List Alerts

```text id="api016"
GET /api/v1/alerts
```

Supported filtering can include:

```text id="api017"
status
severity
start_time
end_time
limit
offset
```

Example response:

```json id="api018"
{
  "items": [
    {
      "id": "ALT-001",
      "title": "Suspicious process activity",
      "severity": "high",
      "confidence": 0.82,
      "status": "new",
      "created_at": "2026-11-02T10:30:00Z"
    }
  ],
  "total": 1
}
```

---

# 10. Alert Details API

## Endpoint

```text id="api019"
GET /api/v1/alerts/{alert_id}
```

The response should provide:

- Alert metadata.
- Detection summary.
- Associated evidence references.
- Current investigation status.

The response should avoid returning uncontrolled raw telemetry volumes by default.

---

# 11. Investigation Creation API

An investigation can be created from an alert.

## Endpoint

```text id="api020"
POST /api/v1/investigations
```

Example request:

```json id="api021"
{
  "alert_id": "ALT-001",
  "priority": "high"
}
```

Processing flow:

```text id="api022"
REQUEST
   │
   ▼
VALIDATE ALERT
   │
   ▼
CREATE INVESTIGATION
   │
   ▼
PERSIST INITIAL STATE
   │
   ▼
QUEUE / START ORCHESTRATION
   │
   ▼
RETURN INVESTIGATION ID
```

Example response:

```json id="api023"
{
  "investigation_id": "INV-001",
  "status": "created"
}
```

---

# 12. Investigation Status API

## Endpoint

```text id="api024"
GET /api/v1/investigations/{investigation_id}
```

Example response:

```json id="api025"
{
  "id": "INV-001",
  "status": "active",
  "confidence": 0.76,
  "current_stage": "evidence_collection",
  "created_at": "2026-11-02T10:30:00Z"
}
```

The API returns the externally relevant investigation state rather than internal prompt or chain-of-thought information.

---

# 13. Investigation Evidence API

## Endpoint

```text id="api026"
GET /api/v1/investigations/{investigation_id}/evidence
```

The response contains evidence references and summaries.

Example:

```json id="api027"
{
  "investigation_id": "INV-001",
  "items": [
    {
      "id": "EVD-001",
      "type": "telemetry",
      "summary": "Process execution observed on host HOST-001",
      "confidence": 0.9
    }
  ]
}
```

The evidence API is important because it provides analyst visibility into why a conclusion was reached.

---

# 14. Investigation Actions API

The investigation may require human review.

## Retrieve Actions

```text id="api028"
GET /api/v1/investigations/{investigation_id}/actions
```

## Approve an Action

```text id="api029"
POST /api/v1/investigations/{investigation_id}/actions/{action_id}/approve
```

## Reject an Action

```text id="api030"
POST /api/v1/investigations/{investigation_id}/actions/{action_id}/reject
```

This creates a clear human-in-the-loop boundary.

---

# 15. Investigation Completion API

Once an investigation reaches a terminal state:

```text id="api031"
GET /api/v1/investigations/{investigation_id}/report
```

The final report should contain:

- Investigation summary.
- Key evidence.
- Findings.
- Confidence.
- Actions performed.
- Analyst decisions.

The final report should clearly distinguish:

```text id="api032"
VERIFIED EVIDENCE

from

AI-GENERATED INTERPRETATION
```

---

# 16. Standard Response Structure

API responses should follow consistent conventions.

Successful list responses:

```json id="api033"
{
  "items": [],
  "total": 0
}
```

Successful single-object responses:

```json id="api034"
{
  "id": "resource-id",
  "status": "active"
}
```

Error responses:

```json id="api035"
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested investigation does not exist",
    "request_id": "REQ-001"
  }
}
```

---

# 17. Error Classification

The backend should classify errors.

| Category | Example |
|---|---|
| Validation | Invalid request |
| Authentication | Invalid credentials |
| Authorization | Insufficient permission |
| Not Found | Missing investigation |
| Conflict | Invalid state transition |
| Dependency | Database or AI service unavailable |
| Internal | Unexpected error |

This provides predictable behavior for both the frontend and internal services.

---

# 18. Investigation State Transitions

The backend must prevent invalid state changes.

Recommended model:

```text id="api036"
CREATED
   │
   ▼
ACTIVE
   │
   ├────────► WAITING_FOR_REVIEW
   │                │
   │                ▼
   │             ACTIVE
   │
   ├────────► ESCALATED
   │
   ├────────► COMPLETED
   │
   └────────► FAILED
```

State transitions should be validated by the investigation service rather than directly changed by API routes.

---

# 19. Background Processing

Long-running operations should execute outside the primary request lifecycle.

Examples:

```text id="api037"
dataset ingestion
dataset replay
AI investigation
knowledge indexing
report generation
```

The architectural flow is:

```text id="api038"
API REQUEST
     │
     ▼
CREATE JOB / STATE
     │
     ▼
BACKGROUND EXECUTOR
     │
     ▼
UPDATE PERSISTENT STATE
```

The exact task execution technology can be selected during implementation.

---

# 20. Redis and Background Task Support

Redis can provide temporary operational support.

Potential uses include:

```text id="api039"
task queue coordination
temporary task state
caching
rate limiting
```

However:

> Redis should not be the only record of an investigation or critical system action.

Durable state remains in PostgreSQL.

---

# 21. Frontend Update Strategy

The frontend needs updates when investigation state changes.

There are two possible MVP approaches.

## Option A — Polling

```text id="api040"
FRONTEND
   │
   ├── GET Investigation Status
   │
   └── Repeat at controlled interval
```

Advantages:

- Simple.
- Reliable.
- Easy to debug.

## Option B — WebSockets

```text id="api041"
BACKEND
   │
   ▼
WEBSOCKET CONNECTION
   │
   ▼
REAL-TIME STATUS UPDATE
   │
   ▼
FRONTEND
```

### MVP Recommendation

Use **polling initially** unless real-time visualization becomes a core demonstration requirement.

The architecture should allow WebSockets to be added later.

---

# 22. Authentication Boundary

Authentication requirements should remain configurable until finalized.

For the MVP, the backend can support:

```text id="api042"
USER
 │
 ▼
LOGIN
 │
 ▼
JWT
 │
 ▼
PROTECTED API REQUEST
```

The authentication layer should remain separate from the investigation logic.

Future authentication mechanisms may include:

- OIDC.
- Enterprise identity providers.
- LDAP integration.

The MVP should not embed authentication assumptions inside core orchestration components.

---

# 23. Authorization Model

At a minimum, future roles can include:

| Role | Typical Access |
|---|---|
| Analyst | View and manage investigations |
| Administrator | System configuration |
| Service | Internal component access |

The exact RBAC policy should be finalized based on project requirements.

---

# 24. Request Correlation

Each important request should have a correlation identifier.

```text id="api043"
CLIENT REQUEST
     │
     ▼
REQUEST ID
     │
     ├── API LOG
     ├── SERVICE LOG
     └── BACKGROUND JOB
```

Example:

```text id="api044"
X-Request-ID: REQ-12345
```

This helps trace an operation across the system.

---

# 25. API Logging

API logs should include:

```text id="api045"
request_id
endpoint
method
response_status
duration
timestamp
```

Sensitive data such as credentials, tokens, or unnecessary raw telemetry should not be logged.

---

# 26. Integration with AI Orchestration

The API interacts with the orchestration system through application services.

```text id="api046"
FRONTEND
   │
   ▼
INVESTIGATION API
   │
   ▼
INVESTIGATION SERVICE
   │
   ▼
ORCHESTRATION ENGINE
   │
   ├── State Manager
   ├── Planner
   ├── Worker Execution
   └── Recovery Manager
```

The API layer should not need to know the internal reasoning strategy used by the Planner.

---

# 27. LLM Failure Integration

An AI service failure should not automatically destroy the investigation.

The failure flow should be:

```text id="api047"
AGENT CALL
    │
    ▼
TIMEOUT / FAILURE
    │
    ▼
RETRY POLICY
    │
    ├── SUCCESS → CONTINUE
    │
    └── FAILURE
          │
          ▼
    PERSIST FAILURE STATE
          │
          ▼
    FALLBACK / HUMAN REVIEW
```

The API should expose an appropriate investigation state, such as:

```text id="api048"
waiting
failed
escalated
```

It should not falsely report that an investigation was successfully completed.

---

# 28. API Security Principles

The backend should enforce:

- Input validation.
- Authentication.
- Authorization.
- Rate controls where appropriate.
- Structured error handling.
- Controlled capability execution.

A critical rule is:

> User input must never be directly converted into unrestricted database queries or agent tool execution instructions.

All actions must pass through validated application contracts.

---

# 29. API Testing Strategy

The API should be tested at several levels.

## Unit Tests

Test:

```text id="api049"
service logic
state transitions
validation rules
```

## Integration Tests

Test:

```text id="api050"
API → Service → Database
```

## End-to-End Tests

Test:

```text id="api051"
Alert
  │
  ▼
Investigation Creation
  │
  ▼
Orchestration
  │
  ▼
Status Retrieval
```

---

# 30. Recommended Implementation Sequence

## Phase 1 — Foundation

```text id="api052"
1. Create FastAPI application.
2. Add configuration management.
3. Add health endpoint.
4. Configure database dependency.
5. Configure API versioning.
```

## Phase 2 — Core APIs

```text id="api053"
6. Implement ingestion APIs.
7. Implement alert APIs.
8. Implement investigation APIs.
9. Implement standardized responses.
```

## Phase 3 — Orchestration Integration

```text id="api054"
10. Connect investigation service.
11. Add background execution.
12. Persist status updates.
13. Add failure handling.
```

## Phase 4 — Frontend Integration

```text id="api055"
14. Connect alert dashboard.
15. Connect investigation views.
16. Implement status polling.
17. Add analyst action endpoints.
```

## Phase 5 — Security and Validation

```text id="api056"
18. Add authentication.
19. Add authorization boundaries.
20. Add request correlation.
21. Add API tests.
```

---

# 31. Acceptance Criteria

The backend integration layer is complete when:

### API

- APIs use consistent versioning.
- Requests are validated.
- Errors follow a consistent structure.
- Investigation state can be retrieved.

### Architecture

- Routes remain thin.
- Business logic exists in services.
- Orchestration remains independent from API routes.
- Database access follows controlled boundaries.

### Asynchronous Processing

- Long-running investigations do not block API requests.
- Investigation state persists.
- Failed executions are visible.

### Frontend Integration

- Alerts can be retrieved.
- Investigations can be started.
- Investigation status can be monitored.
- Evidence can be viewed.

### Security

- Authentication boundaries are established.
- Unauthorized actions are rejected.
- Sensitive information is not unnecessarily exposed.

---

# 32. Complete Backend Request Flow

The following represents a typical user interaction.

```text id="api057"
┌──────────────┐
│   ANALYST    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   FRONTEND   │
└──────┬───────┘
       │ API Request
       ▼
┌──────────────┐
│   FASTAPI    │
│    ROUTE     │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   SERVICE    │
└──────┬───────┘
       │
       ▼
┌──────────────────────┐
│ INVESTIGATION SYSTEM │
└──────┬───────────────┘
       │
       ├── PostgreSQL
       ├── AI Orchestrator
       ├── Capabilities
       └── Knowledge Retrieval
              │
              ▼
       PERSISTED STATE
              │
              ▼
          API RESPONSE
              │
              ▼
          FRONTEND
```

---

# 33. Final Design Principle

The FastAPI backend is the **integration boundary**, not the intelligence engine.

Its responsibility is to provide a reliable pathway:

```text id="api058"
USER REQUEST
     │
     ▼
VALIDATED API
     │
     ▼
APPLICATION SERVICE
     │
     ▼
CONTROLLED SYSTEM COMPONENTS
     │
     ▼
PERSISTED RESULT
     │
     ▼
USER VISIBILITY
```

The architecture keeps the AI orchestration at the core of investigation while ensuring that user interaction, persistence, security, and asynchronous processing remain independently manageable.

---

# Next Document

The next recommended document is:

## Frontend & Analyst Experience Specification

It will define the React application architecture, dashboard structure, alert and investigation views, evidence visualization, investigation progress display, analyst interaction workflows, API integration, and the user experience required to demonstrate Project Sentinel effectively.
