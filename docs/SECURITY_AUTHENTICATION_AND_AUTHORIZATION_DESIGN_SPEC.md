# Project Sentinel
# Security, Authentication & Authorization Design Specification

**Document Type:** Security Architecture Specification  
**Version:** 1.0  
**Status:** Architecture Baseline  
**Primary Focus:** Authentication, authorization, API security, secret management, trust boundaries, auditability, AI-agent security, capability controls, and secure operational design.

---

# 1. Purpose

Project Sentinel processes security telemetry and uses an AI-driven orchestration system to investigate suspicious activity.

This creates multiple security boundaries that must be protected:

- User-to-frontend access.
- Frontend-to-backend communication.
- Backend API access.
- Database access.
- AI model access.
- Agent-to-capability execution.
- Internal service communication.
- Investigation and audit data.

The objective of this specification is to ensure that Project Sentinel follows a **controlled and defensible security architecture**.

The core principle is:

```text
TRUST NOTHING IMPLICITLY

VALIDATE INPUTS
CONTROL ACCESS
LIMIT CAPABILITIES
RECORD IMPORTANT ACTIONS
```

---

# 2. Security Architecture Overview

The high-level security model is:

```text
                    ┌─────────────────┐
                    │      USER       │
                    └────────┬────────┘
                             │
                      Authentication
                             │
                             ▼
                    ┌─────────────────┐
                    │    FRONTEND     │
                    └────────┬────────┘
                             │
                       Protected API
                             │
                             ▼
┌────────────────────────────────────────────────────┐
│                  FASTAPI BACKEND                   │
│                                                    │
│ Authentication │ Authorization │ Validation        │
└───────────┬──────────────────────────────┬─────────┘
            │                              │
            ▼                              ▼
     ┌──────────────┐              ┌──────────────┐
     │ PostgreSQL   │              │ Orchestration│
     │ Durable Data │              │    System    │
     └──────────────┘              └──────┬───────┘
                                          │
                                   Controlled Access
                                          │
                                          ▼
                                  ┌───────────────┐
                                  │ CAPABILITIES  │
                                  │   / TOOLS     │
                                  └───────────────┘
```

Every transition between components should have a clearly defined trust boundary.

---

# 3. Security Design Principles

Project Sentinel should follow the following principles.

## 3.1 Least Privilege

Each user and component receives only the permissions required to perform its function.

Examples:

- An analyst can review investigations.
- A service account can perform its assigned internal operation.
- An AI agent cannot receive unrestricted database access.

---

## 3.2 Defense in Depth

Security should not depend on a single mechanism.

For example:

```text
AUTHENTICATION
      +
AUTHORIZATION
      +
INPUT VALIDATION
      +
CAPABILITY CONTROLS
      +
AUDIT LOGGING
```

Multiple controls reduce the consequences of a single failure.

---

## 3.3 Explicit Trust Boundaries

Project Sentinel should clearly define where trust changes.

```text
UNTRUSTED INPUT
      │
      ▼
VALIDATION BOUNDARY
      │
      ▼
APPLICATION
      │
      ▼
CONTROLLED INTERNAL COMPONENT
```

No external input should automatically be trusted simply because it passes through another component.

---

## 3.4 Fail Securely

When a security-critical dependency fails, the system should not silently grant access or perform an uncontrolled action.

Examples:

```text
Authentication unavailable
        │
        ▼
Reject protected request
```

```text
Capability authorization uncertain
        │
        ▼
Do not execute capability
```

---

# 4. Threat Surface

The major security surfaces include:

| Surface | Primary Risk |
|---|---|
| Frontend | Unauthorized user access |
| API | Invalid or malicious requests |
| Authentication | Credential or token misuse |
| Database | Unauthorized data access |
| Telemetry | Malformed or hostile input |
| AI agents | Prompt injection or uncontrolled decisions |
| Capabilities | Unauthorized execution |
| Secrets | Credential exposure |
| Logs | Sensitive data leakage |

The architecture should address each surface separately.

---

# 5. Authentication Model

For the MVP, the recommended authentication model is:

```text
USER
 │
 ▼
LOGIN
 │
 ▼
AUTHENTICATION SERVICE
 │
 ▼
SIGNED ACCESS TOKEN
 │
 ▼
PROTECTED API REQUEST
```

A JWT-based mechanism can provide a practical baseline.

The authentication implementation should remain isolated from:

- Detection logic.
- Investigation logic.
- Agent orchestration.
- Capability execution.

---

# 6. JWT Security Design

A protected request follows this flow:

```text
CLIENT
  │
  │ Authorization Token
  ▼
FASTAPI AUTH MIDDLEWARE
  │
  ├── Verify token
  ├── Validate expiry
  ├── Extract identity
  └── Determine role
          │
          ▼
    AUTHORIZED ROUTE
```

The backend must validate the token for every protected request.

The frontend must not be treated as the authority for user identity or permissions.

---

# 7. Password Handling

If local credentials are implemented for the MVP:

```text
PASSWORD
   │
   ▼
SECURE PASSWORD HASHING
   │
   ▼
POSTGRESQL
```

The system must not store plaintext passwords.

The implementation should use an established password-hashing mechanism rather than custom cryptographic logic.

---

# 8. Authorization Model

Authorization determines what an authenticated user may do.

The recommended baseline is role-based access control.

## Initial Roles

| Role | Responsibilities |
|---|---|
| Analyst | Review alerts and investigations |
| Administrator | Manage system-level configuration |
| Service | Internal service-to-service operations |

A more detailed permission model can be added if required.

---

# 9. Authorization Flow

```text
AUTHENTICATED USER
        │
        ▼
REQUEST ACTION
        │
        ▼
IDENTIFY REQUIRED PERMISSION
        │
        ▼
CHECK USER ROLE
        │
   ┌────┴─────┐
   │          │
ALLOW       DENY
   │          │
   ▼          ▼
EXECUTE     ERROR
```

Authorization should always be enforced by the backend.

A hidden frontend button is not an authorization control.

---

# 10. API Security

Every API request should pass through defined controls.

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
REQUEST VALIDATION
   │
   ▼
SERVICE LOGIC
   │
   ▼
CONTROLLED RESPONSE
```

The API layer should validate:

- Request structure.
- Field types.
- Required fields.
- Allowed values.
- Resource access permissions.

---

# 11. Input Validation

All external input should be considered untrusted.

This includes:

- API requests.
- Query parameters.
- Uploaded datasets.
- Telemetry fields.
- Analyst-provided text.
- External knowledge content.

The validation boundary is:

```text
UNTRUSTED DATA
      │
      ▼
SCHEMA VALIDATION
      │
      ▼
NORMALIZATION
      │
      ▼
INTERNAL PROCESSING
```

Pydantic schemas provide a suitable validation mechanism for FastAPI requests.

---

# 12. Database Security

The database contains durable system state.

This may include:

- Alerts.
- Investigations.
- Evidence metadata.
- Audit records.
- User information.

Database access should follow:

```text
APPLICATION
     │
     ▼
DATABASE ACCESS LAYER
     │
     ▼
POSTGRESQL
```

Components should not construct uncontrolled database operations directly from user or agent-generated input.

---

# 13. Database Credentials

Database credentials must not be hardcoded in:

- Source code.
- Frontend applications.
- Public repositories.
- Documentation examples containing production credentials.

The recommended approach is:

```text
ENVIRONMENT / SECRET STORE
           │
           ▼
APPLICATION CONFIGURATION
           │
           ▼
DATABASE CONNECTION
```

A `.env.example` file may contain placeholder values, but not real secrets.

---

# 14. Secret Management

The following values should be treated as secrets:

- JWT signing keys.
- Database passwords.
- External API credentials.
- Model service credentials, if applicable.
- Production service tokens.

Secrets should be injected through controlled configuration.

The system should ensure:

```text
SECRET
  │
  ├── Not committed to source control
  ├── Not returned by APIs
  └── Not written to normal application logs
```

---

# 15. Telemetry Security

Telemetry is a primary input source.

It should not automatically be trusted because it originates from a security dataset.

The pipeline should perform:

```text
RAW EVENT
   │
   ▼
STRUCTURAL VALIDATION
   │
   ▼
NORMALIZATION
   │
   ▼
QUALITY CHECK
   │
   ▼
INTERNAL EVENT
```

Malformed events should be:

- Rejected.
- Quarantined.
- Logged appropriately.

They should not cause uncontrolled failures in the main pipeline.

---

# 16. AI Agent Security Model

The AI agent layer requires special security controls.

The fundamental rule is:

> An AI model does not receive unrestricted authority over the system.

The correct architecture is:

```text
AI AGENT
   │
   ▼
PROPOSED ACTION
   │
   ▼
POLICY / VALIDATION
   │
   ▼
CAPABILITY REGISTRY
   │
   ▼
CONTROLLED EXECUTION
```

The model can participate in reasoning and planning, but execution remains controlled by the application.

---

# 17. Agent Capability Boundaries

Agents should not have direct unrestricted access to:

- PostgreSQL.
- Operating system commands.
- Arbitrary network endpoints.
- Environment secrets.

Instead:

```text
AGENT
  │
  ▼
CAPABILITY REQUEST
  │
  ▼
CAPABILITY VALIDATION
  │
  ▼
APPROVED CAPABILITY
  │
  ▼
CONTROLLED RESULT
```

Each capability should define:

- Its purpose.
- Accepted input schema.
- Output schema.
- Permission requirements.
- Execution limits.

---

# 18. Capability Registry Security

The capability registry acts as an execution control point.

Conceptually:

```text
CAPABILITY REQUEST
       │
       ▼
IS CAPABILITY REGISTERED?
       │
       ▼
IS INPUT VALID?
       │
       ▼
IS ACTION PERMITTED?
       │
       ▼
EXECUTE
```

An agent should not be able to invent a new executable tool by generating text.

Only registered and implemented capabilities can execute.

---

# 19. Prompt Injection Considerations

Project Sentinel may process untrusted text through:

- Telemetry fields.
- Knowledge documents.
- Analyst input.
- External data.

This data must not automatically be treated as trusted instructions for an AI agent.

The conceptual boundary is:

```text
EXTERNAL CONTENT
       │
       ▼
DATA / EVIDENCE
       │
       X
       │
NOT SYSTEM INSTRUCTIONS
```

The orchestration layer should preserve the distinction between:

- System instructions.
- Agent task instructions.
- Retrieved evidence.
- User-generated content.

---

# 20. Agent Output Validation

AI-generated output should not be directly trusted.

Where structured output is required:

```text
LLM OUTPUT
    │
    ▼
STRUCTURED SCHEMA
    │
    ▼
VALIDATION
    │
 ┌──┴────────┐
 │           │
VALID       INVALID
 │           │
 ▼           ▼
CONTINUE   RETRY / FALLBACK
```

This is particularly important for:

- Investigation plans.
- Capability requests.
- State transitions.
- Final findings.

---

# 21. Human-in-the-Loop Security

Certain actions should require explicit analyst approval.

The flow is:

```text
SYSTEM PROPOSES ACTION
         │
         ▼
ACTION REQUIRES REVIEW
         │
         ▼
ANALYST APPROVES / REJECTS
         │
         ▼
DECISION VALIDATED
         │
         ▼
STATE UPDATED
```

The approval itself must be authorized and auditable.

The system should record:

- Who made the decision.
- What was approved or rejected.
- When the decision occurred.
- Which investigation was affected.

---

# 22. Investigation State Security

Investigation state transitions must be controlled.

For example:

```text
ACTIVE
  │
  ├──► WAITING_FOR_REVIEW
  │
  ├──► COMPLETED
  │
  └──► ESCALATED
```

An external request should not be able to arbitrarily change:

```text
FAILED → COMPLETED
```

without passing through the appropriate application logic.

State transition validation belongs in the service or orchestration layer.

---

# 23. Audit Logging

Project Sentinel should maintain audit records for important actions.

Important events include:

```text
User authentication events
Investigation creation
Investigation state changes
Analyst approvals and rejections
Capability execution
Critical system failures
```

The conceptual structure is:

```text
ACTION
  │
  ▼
AUDIT EVENT
  │
  ▼
DURABLE AUDIT RECORD
```

Audit records should be distinguishable from normal application debugging logs.

---

# 24. Audit Record Model

A baseline audit record can contain:

```text
audit_id
timestamp
actor_type
actor_id
action_type
resource_type
resource_id
outcome
request_id
metadata
```

Example:

```text
Actor: analyst-001
Action: investigation.action.approved
Resource: investigation/INV-001
Outcome: success
```

Sensitive values should not be unnecessarily stored in audit metadata.

---

# 25. Request Correlation

Security-relevant operations should be traceable.

```text
USER REQUEST
     │
     ▼
REQUEST ID
     │
     ├── API LOG
     ├── SERVICE LOG
     ├── AGENT EVENT
     └── AUDIT RECORD
```

This makes investigation of system behavior significantly easier.

---

# 26. Error Handling Security

Errors returned to users should be informative without exposing internal details.

For example:

```text
Unable to complete the request.
```

is appropriate for an unexpected internal failure.

The backend may log the detailed cause internally using a request identifier.

The API should avoid returning:

- Database connection strings.
- Stack traces.
- Internal file paths.
- Secret values.

---

# 27. Rate and Resource Controls

The system should prevent unnecessary resource exhaustion.

Potential controls include:

- Request size limits.
- Controlled pagination.
- Investigation concurrency limits.
- AI call timeouts.
- Capability execution limits.

Example:

```text
REQUEST
   │
   ▼
RESOURCE LIMIT CHECK
   │
 ┌─┴────────┐
 │          │
ALLOW      REJECT
```

These controls become more important as the orchestration system handles multiple investigations.

---

# 28. AI Service Failure Security

An unavailable AI service should not cause the system to bypass security controls.

The failure model is:

```text
AGENT CALL
   │
   ▼
FAILURE
   │
   ▼
RETRY POLICY
   │
   ├── SUCCESS → CONTINUE
   │
   └── FAILURE
          │
          ▼
    SAFE INVESTIGATION STATE
          │
          ▼
    ESCALATE / WAIT FOR REVIEW
```

The system must not generate a fabricated successful result when an investigation could not be completed.

---

# 29. Service Trust Boundaries

Internal services should have clearly defined responsibilities.

```text
FRONTEND
   │
   ▼
BACKEND API
   │
   ├── Database Access
   │
   └── Orchestration
           │
           ▼
      Capabilities
```

A component should communicate through its intended interface rather than bypassing architectural boundaries.

For example:

```text
Frontend → PostgreSQL
```

should never be permitted.

---

# 30. Container and Deployment Security

Docker provides packaging and environment consistency but does not automatically make the application secure.

Deployment should consider:

- Separate service configuration.
- Environment-specific secrets.
- Minimal container images.
- Avoiding unnecessary exposed ports.
- Controlled service networking.

The conceptual deployment boundary is:

```text
EXTERNAL ACCESS
       │
       ▼
FRONTEND / API
       │
       ▼
INTERNAL SERVICES
       │
       ├── PostgreSQL
       ├── Redis
       ├── Vector Store
       └── AI Services
```

Infrastructure services should not be unnecessarily exposed outside the application environment.

---

# 31. Security Testing

Security validation should be included in testing.

## API Tests

Test:

- Unauthenticated requests.
- Unauthorized requests.
- Invalid input.
- Invalid state transitions.

## Authentication Tests

Test:

- Invalid credentials.
- Expired tokens.
- Missing tokens.

## Agent Security Tests

Test:

- Invalid capability requests.
- Malformed agent output.
- Untrusted content presented to the agent.
- Capability authorization failures.

---

# 32. Security Acceptance Criteria

The MVP security baseline is achieved when:

### Authentication

- Protected APIs require authentication.
- Credentials are not stored in plaintext.
- Tokens are validated by the backend.

### Authorization

- Sensitive operations require appropriate permissions.
- Frontend controls are not relied upon as the authorization boundary.

### API Protection

- Requests are validated.
- Errors do not expose internal implementation details.
- Sensitive data is not unnecessarily returned.

### AI and Agents

- Agents cannot directly execute unrestricted operations.
- Capability requests are validated.
- AI output is checked before controlling system actions.
- Untrusted content is treated as data rather than instructions.

### Auditability

- Important actions generate audit records.
- Investigation actions can be correlated using identifiers.
- Analyst approvals and rejections are recorded.

---

# 33. Security Architecture Summary

The complete security model is:

```text
                         USER
                          │
                    AUTHENTICATION
                          │
                          ▼
                    AUTHORIZATION
                          │
                          ▼
                    INPUT VALIDATION
                          │
                          ▼
                    APPLICATION
                          │
              ┌───────────┴───────────┐
              │                       │
              ▼                       ▼
         PERSISTENCE             ORCHESTRATION
                                      │
                                      ▼
                              POLICY CONTROLS
                                      │
                                      ▼
                                CAPABILITIES
                                      │
                                      ▼
                               AUDIT RECORDS
```

Every important action should pass through one or more explicit controls.

---

# 34. Final Design Principle

Project Sentinel must treat its AI orchestration system as a **powerful but controlled component**.

The final security philosophy is:

```text
AI CAN ANALYZE

AI CAN PLAN

AI CAN PROPOSE

BUT

THE SYSTEM VALIDATES

THE SYSTEM CONTROLS EXECUTION

THE ANALYST RETAINS OVERSIGHT
```

This architecture supports the project's primary objective: building a sophisticated AI-driven investigation system without allowing the intelligence layer to bypass the security, reliability, and accountability boundaries of the overall platform.

---

# Next Document

The next recommended document is:

## Observability, Monitoring & Auditability Specification

It will define the operational visibility architecture for Project Sentinel, including structured logging, metrics, distributed request correlation, agent and orchestration observability, investigation traces, performance monitoring, failure monitoring, dashboards, and the distinction between application logs and security audit records.
