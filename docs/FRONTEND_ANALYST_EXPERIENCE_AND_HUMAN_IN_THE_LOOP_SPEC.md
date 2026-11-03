# Project Sentinel
# Frontend, Analyst Experience & Human-in-the-Loop Specification

**Document Type:** User Experience and Interaction Architecture Specification  
**Version:** 1.0  
**Status:** Architecture Baseline  
**Primary Focus:** Analyst workflows, frontend architecture, dashboards, investigation visualization, agent transparency, human review, approvals, escalation, and user interaction.

---

# 1. Purpose

Project Sentinel is an AI-assisted security investigation system. Its frontend is not simply a dashboard for displaying alerts.

The interface must allow an analyst to:

- Understand what triggered an alert.
- Start or review an investigation.
- Observe investigation progress.
- Understand which agents performed which tasks.
- Review collected evidence.
- Inspect the basis of system conclusions.
- Approve, reject, or override important decisions.

The central design principle is:

> **AI agents perform structured investigation work, while human analysts retain visibility and control over significant decisions.**

The complete interaction model is:

```text
SECURITY TELEMETRY
       │
       ▼
    DETECTION
       │
       ▼
      ALERT
       │
       ▼
┌──────────────────┐
│ ANALYST INTERFACE │
└────────┬─────────┘
         │
         ▼
   INVESTIGATION
         │
         ▼
 AGENT ORCHESTRATION
         │
         ▼
      EVIDENCE
         │
         ▼
 HUMAN REVIEW
         │
         ▼
 FINAL OUTCOME
```

---

# 2. Primary Users

For the MVP, Project Sentinel should focus on one primary user category.

## 2.1 Security Analyst

The analyst interacts with the system to:

- Monitor alerts.
- Review suspicious activity.
- Start investigations.
- Observe AI-assisted investigation progress.
- Review evidence.
- Make or approve final decisions.

The system should not assume that the analyst is an AI or orchestration expert.

Therefore, complex internal processing must be presented in a clear and understandable form.

---

# 3. User Experience Goals

The frontend should achieve five primary goals.

| Goal | Description |
|---|---|
| Visibility | Show what the system is doing |
| Explainability | Show why conclusions were reached |
| Control | Allow analysts to review important actions |
| Efficiency | Reduce unnecessary investigation effort |
| Traceability | Connect conclusions to evidence |

The UI should answer these questions at any time:

1. What happened?
2. Why was this flagged?
3. What is the investigation doing now?
4. What evidence has been found?
5. What does the system currently conclude?
6. What action is required from the analyst?

---

# 4. Frontend Architecture

The recommended frontend architecture is:

```text
┌──────────────────────────────┐
│          REACT UI            │
│                              │
│  Dashboard                   │
│  Alerts                      │
│  Investigation Workspace     │
│  Evidence Viewer             │
│  Review Actions              │
└───────────────┬──────────────┘
                │
                │ HTTPS / API
                ▼
┌──────────────────────────────┐
│        FASTAPI BACKEND       │
│                              │
│ API Layer                    │
│ Investigation Services       │
│ Orchestration                │
└──────────────────────────────┘
```

The frontend communicates only with the backend API.

It should not directly access:

- PostgreSQL.
- Redis.
- ChromaDB.
- The AI model.
- Internal agent services.

---

# 5. Core Application Areas

The MVP frontend should contain the following major areas:

```text
PROJECT SENTINEL
│
├── Dashboard
│
├── Alerts
│
├── Investigations
│   ├── Overview
│   ├── Agent Activity
│   ├── Evidence
│   └── Decision / Review
│
└── System Status
```

These areas should represent the user's workflow rather than the backend's internal folder structure.

---

# 6. Dashboard

The dashboard provides the initial system overview.

It should answer:

> **What requires attention right now?**

Recommended information includes:

- Number of active alerts.
- Investigation status summary.
- Severity distribution.
- Investigations requiring review.
- Recent investigation activity.

Conceptually:

```text
┌────────────────────────────────────┐
│          SENTINEL DASHBOARD        │
├──────────┬──────────┬──────────────┤
│ Alerts   │ Active   │ Review       │
│          │ Cases    │ Required     │
├──────────┴──────────┴──────────────┤
│        Recent Investigation        │
├────────────────────────────────────┤
│        System Activity             │
└────────────────────────────────────┘
```

The dashboard should prioritize operational awareness over excessive visual complexity.

---

# 7. Alert Management Interface

The alert interface is the entry point into investigation.

Each alert should display:

```text
Alert Title
Severity
Confidence
Status
Creation Time
Relevant Source Information
```

The analyst should be able to move from:

```text
ALERT LIST
    │
    ▼
ALERT DETAILS
    │
    ▼
START / VIEW INVESTIGATION
```

The alert page should clearly distinguish:

- Detection information.
- Investigation information.
- Final outcome.

These are related but not identical concepts.

---

# 8. Alert Detail View

The alert detail view should answer:

> **Why did the system create this alert?**

Recommended sections include:

### Summary

A concise description of the suspicious activity.

### Detection Information

- Detection type.
- Severity.
- Confidence.
- Detector source.

### Related Events

References to the telemetry that triggered the alert.

### Investigation Status

Whether an investigation has:

- Not started.
- Started.
- Is active.
- Requires review.
- Completed.

The conceptual flow is:

```text
ALERT
 │
 ├── WHY FLAGGED?
 │
 ├── RELATED EVENTS
 │
 └── INVESTIGATION STATUS
```

---

# 9. Investigation Workspace

The investigation workspace is the most important frontend component.

It represents the human-facing view of the orchestration system.

The workspace should contain four major areas:

```text
┌──────────────────────────────────────┐
│          INVESTIGATION               │
├────────────────┬─────────────────────┤
│ Investigation  │ Current Status      │
│ Summary        │                     │
├────────────────┼─────────────────────┤
│ Agent Activity │ Evidence            │
├────────────────┴─────────────────────┤
│ Decision / Analyst Review            │
└──────────────────────────────────────┘
```

The analyst should not need to inspect raw internal orchestration data to understand the investigation.

---

# 10. Investigation Status Model

The frontend should display the current state clearly.

A baseline state model is:

```text
CREATED
   │
   ▼
ACTIVE
   │
   ├──────────────► WAITING FOR REVIEW
   │                      │
   ▼                      ▼
COMPLETED              RESUMED
   │
   ▼
CLOSED
```

Failure states should also be visible.

For example:

```text
ACTIVE
  │
  ▼
PARTIALLY DEGRADED
```

The UI should not falsely indicate that an investigation completed successfully when critical agent tasks failed.

---

# 11. Agent Activity Visualization

Agent orchestration is a core feature of Project Sentinel.

However, the interface should not expose unnecessary implementation complexity.

The analyst should see:

- Which task is being performed.
- Which agent or specialist role is responsible.
- Current task status.
- Result summary.
- Relevant evidence produced.

Example:

```text
INVESTIGATION
│
├── Evidence Analysis Agent
│      └── Completed
│
├── Context Retrieval Agent
│      └── Completed
│
└── Investigation Analysis Agent
       └── In Progress
```

The purpose is transparency.

The analyst does not need to see raw prompts or internal model messages by default.

---

# 12. Agent Task Status

Each visible task should use a consistent status model.

| Status | Meaning |
|---|---|
| Pending | Task has not started |
| Running | Task is currently executing |
| Completed | Task finished successfully |
| Waiting | Task requires dependency or review |
| Failed | Task could not complete |
| Skipped | Task was intentionally not required |

This creates a common language between the backend and frontend.

---

# 13. Agent Result Presentation

Agent results should be presented as structured information.

The preferred pattern is:

```text
AGENT TASK
    │
    ▼
SUMMARY
    │
    ▼
KEY FINDINGS
    │
    ▼
SUPPORTING EVIDENCE
```

Avoid displaying a large unstructured AI response as the primary investigation interface.

The frontend should emphasize:

- Findings.
- Evidence.
- Confidence.
- Limitations.

---

# 14. Evidence Viewer

The evidence viewer is a critical trust component.

Every important investigation finding should, where possible, connect to supporting evidence.

The evidence interface should display:

```text
Evidence Summary
Evidence Type
Source
Collection Time
Relevance
Related Finding
```

The evidence chain is:

```text
FINDING
   │
   ▼
EVIDENCE
   │
   ▼
SOURCE REFERENCE
```

An analyst should be able to move from a conclusion toward its underlying evidence.

---

# 15. Evidence Categories

The UI can classify evidence broadly.

Examples include:

```text
Telemetry Evidence
Process Evidence
Network Evidence
Retrieved Knowledge
Agent Analysis
```

This classification helps the analyst distinguish:

> **What was directly observed**

from:

> **What was inferred or analyzed**

This distinction is important for trustworthy AI-assisted investigation.

---

# 16. Investigation Timeline

A chronological timeline provides an understandable view of the investigation.

Example:

```text
10:00  Alert Created
   │
10:01  Investigation Started
   │
10:02  Evidence Collection Completed
   │
10:03  Context Analysis Started
   │
10:04  Additional Evidence Found
   │
10:05  Analyst Review Requested
```

The timeline should be generated from auditable system events.

It should not depend solely on AI-generated summaries.

---

# 17. Human-in-the-Loop Model

Project Sentinel should not treat all AI decisions equally.

Human review should be introduced at important control points.

The model is:

```text
AI INVESTIGATION
       │
       ▼
CONFIDENCE / RISK ASSESSMENT
       │
 ┌─────┴─────┐
 │           │
NORMAL      REVIEW
 │           │
 ▼           ▼
CONTINUE    ANALYST
            │
            ▼
       APPROVE / REJECT
```

The exact confidence thresholds are implementation configuration rather than hardcoded frontend rules.

---

# 18. Analyst Review Queue

The system should provide a clear list of investigations requiring attention.

The review queue should show:

- Investigation identifier.
- Related alert.
- Priority.
- Reason review is required.
- Current investigation state.

Example reasons:

```text
Low confidence conclusion
Conflicting evidence
Agent execution failure
High-risk outcome
Manual review requested
```

The purpose is to make required human action explicit.

---

# 19. Analyst Actions

The MVP should support a limited and controlled set of analyst actions.

Recommended actions include:

```text
Approve Conclusion
Reject Conclusion
Request Additional Investigation
Close Investigation
```

Each significant action should be auditable.

```text
ANALYST ACTION
     │
     ▼
VALIDATION
     │
     ▼
STATE UPDATE
     │
     ▼
AUDIT RECORD
```

---

# 20. Manual Investigation Requests

An analyst should be able to request additional work without directly controlling low-level agent execution.

The interaction should be:

```text
ANALYST REQUEST
      │
      ▼
INVESTIGATION OBJECTIVE
      │
      ▼
ORCHESTRATOR
      │
      ▼
AGENT TASKS
```

Example:

> "Investigate related network activity."

The orchestration layer determines how to satisfy the request.

This preserves the separation between the user experience and agent implementation.

---

# 21. Confidence Presentation

Confidence should not be presented as an unexplained number.

The UI should indicate what the confidence refers to.

For example:

```text
Detection Confidence
Investigation Confidence
Evidence Relevance
```

These should not be mixed into one ambiguous value.

A recommended presentation model is:

```text
CONCLUSION
    │
    ├── Confidence
    ├── Supporting Evidence
    └── Known Limitations
```

---

# 22. Explainability Model

The frontend should support a simple explanation chain.

```text
WHAT HAPPENED?
       │
       ▼
WHY WAS IT FLAGGED?
       │
       ▼
WHAT DID THE AGENTS INVESTIGATE?
       │
       ▼
WHAT EVIDENCE WAS FOUND?
       │
       ▼
WHAT IS THE CURRENT CONCLUSION?
```

This sequence should guide the investigation interface.

---

# 23. Real-Time Updates

The MVP can initially use a simple polling approach for investigation status.

The conceptual flow is:

```text
FRONTEND
    │
    ▼
STATUS REQUEST
    │
    ▼
BACKEND
    │
    ▼
CURRENT INVESTIGATION STATE
```

A future enhancement may use:

- WebSockets.
- Server-Sent Events.

Real-time infrastructure should be introduced only when investigation responsiveness requires it.

---

# 24. Frontend State Model

The frontend should maintain separate states for:

```text
AUTHENTICATION STATE

APPLICATION DATA STATE

INVESTIGATION UI STATE

ASYNC REQUEST STATE
```

This prevents investigation data from becoming mixed with temporary interface behavior.

A conceptual model is:

```text
UI ACTION
   │
   ▼
API REQUEST
   │
   ▼
LOADING
   │
 ┌─┴──────┐
 │        │
SUCCESS  ERROR
 │        │
 ▼        ▼
UPDATE    DISPLAY
STATE     FAILURE
```

---

# 25. API Interaction Model

The frontend consumes backend-defined data contracts.

```text
FRONTEND COMPONENT
       │
       ▼
API CLIENT
       │
       ▼
BACKEND API
       │
       ▼
APPLICATION SERVICE
```

Frontend components should not contain backend business logic.

This improves maintainability and keeps the orchestration core independent of presentation technology.

---

# 26. Error Handling

Errors should be meaningful to the analyst.

Examples:

| Internal Condition | User-Facing Meaning |
|---|---|
| Agent timeout | Investigation task could not complete |
| AI unavailable | AI-assisted analysis temporarily unavailable |
| Capability failure | Evidence collection could not complete |
| Permission failure | Requested action is not authorized |

The UI should avoid exposing unnecessary internal stack traces.

However, it should not hide meaningful investigation failures.

---

# 27. System Status Interface

A basic system status view can help during development and demonstration.

It may display:

```text
Backend Status
Database Status
AI Service Availability
Vector Retrieval Availability
```

This view should distinguish system health from investigation conclusions.

For example:

> "AI service unavailable"

is an operational condition, not an investigation result.

---

# 28. Security Requirements for the Frontend

The frontend should follow the overall security architecture.

Important requirements include:

- No direct database credentials.
- Authentication through backend APIs.
- Authorization checks enforced by the backend.
- Sensitive data displayed only when required.
- No secrets stored in source code.

The frontend improves usability but does not replace backend security enforcement.

---

# 29. Usability Principles

The MVP interface should prioritize clarity.

Recommended principles:

### Progressive Detail

Show summaries first and detailed evidence when requested.

### Clear Status

The analyst should always understand whether the investigation is:

- Running.
- Waiting.
- Completed.
- Failed.

### Evidence Before Assertion

Where possible, conclusions should link to supporting information.

### Controlled Complexity

The user should not need to understand LangGraph, vector databases, or model adapters to use the system.

---

# 30. MVP Screen Set

The recommended MVP contains the following screens.

| Screen | Primary Purpose |
|---|---|
| Login | Authenticate user |
| Dashboard | System overview |
| Alerts | Review detected alerts |
| Alert Details | Understand the alert |
| Investigation Workspace | Monitor AI-assisted investigation |
| Evidence View | Inspect supporting evidence |
| Review Queue | Handle required human decisions |
| System Status | Basic operational visibility |

This scope provides a complete workflow without unnecessary UI expansion.

---

# 31. Complete Analyst Workflow

The complete user journey is:

```text
LOGIN
  │
  ▼
DASHBOARD
  │
  ▼
ALERT LIST
  │
  ▼
ALERT DETAILS
  │
  ▼
START / OPEN INVESTIGATION
  │
  ▼
OBSERVE AGENT ACTIVITY
  │
  ▼
REVIEW EVIDENCE
  │
  ▼
REVIEW CONCLUSION
  │
 ┌┴──────────────┐
 │               │
APPROVE       REQUEST MORE
 │             INVESTIGATION
 ▼               │
CLOSE           ▼
             ORCHESTRATOR
```

---

# 32. Frontend Data Flow

The complete interaction between the analyst and backend is:

```text
ANALYST
   │
   ▼
REACT FRONTEND
   │
   ▼
FASTAPI API
   │
   ▼
APPLICATION SERVICES
   │
   ▼
ORCHESTRATOR
   │
   ├──────────► AGENTS
   │
   ├──────────► CAPABILITIES
   │
   └──────────► DATA SERVICES
                     │
                     ▼
                  RESULTS
                     │
                     ▼
                 BACKEND API
                     │
                     ▼
                  FRONTEND
                     │
                     ▼
                  ANALYST
```

The user interacts with the investigation through stable application APIs rather than directly with AI agents.

---

# 33. Acceptance Criteria

The frontend and human interaction layer is considered complete when:

### Alert Workflow

- Analysts can view alerts.
- Alert details explain the detection context.
- Investigations can be opened or initiated.

### Investigation Visibility

- Investigation status is visible.
- Agent tasks have understandable states.
- Significant failures are visible.

### Evidence

- Evidence is presented in structured form.
- Evidence can be connected to its source.
- Conclusions can reference supporting evidence.

### Human Control

- Investigations requiring review are clearly identified.
- Analysts can approve or reject significant outcomes.
- Manual requests can be submitted through controlled workflows.

### Architecture

- The frontend communicates only through backend APIs.
- Backend orchestration remains independent of UI implementation.
- UI state is separated from durable investigation state.

---

# 34. Complete Human-in-the-Loop Architecture

```text
                         ┌──────────────┐
                         │   ANALYST    │
                         └──────┬───────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │    FRONTEND      │
                       │   REACT / UI     │
                       └────────┬─────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │     FASTAPI      │
                       │   APPLICATION    │
                       └────────┬─────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ ORCHESTRATION    │
                       └────────┬─────────┘
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
                 AGENTS    CAPABILITIES   KNOWLEDGE
                    │           │           │
                    └───────────┼───────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │    EVIDENCE      │
                       └────────┬─────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │    CONCLUSION    │
                       └────────┬─────────┘
                                │
                     ┌──────────┴──────────┐
                     ▼                     ▼
                  CONTINUE              REVIEW
                     │                     │
                     └──────────┬──────────┘
                                ▼
                             ANALYST
```

---

# 35. Final Design Principle

The frontend should make Project Sentinel's intelligence **observable, understandable, and controllable**.

The system should not present AI-generated conclusions as unexplained answers.

The complete philosophy is:

```text
AI AGENTS
    +
STRUCTURED ORCHESTRATION
    +
TRACEABLE EVIDENCE
    +
CLEAR VISIBILITY
    +
HUMAN CONTROL
    =
TRUSTWORTHY AI-ASSISTED INVESTIGATION
```

The frontend therefore acts as the bridge between the complex internal agent orchestration architecture and the human security analyst.

Its primary responsibility is to ensure that the analyst can always understand:

> **What the system knows, what it is doing, why it is doing it, and when human judgment is required.**

---

# Next Recommended Document

## API Contract & Integration Specification

This should be the next document because all major architectural layers have now been defined. The API specification will formally connect them by defining:

- API resource boundaries.
- Request and response schemas.
- Authentication requirements.
- Alert endpoints.
- Investigation endpoints.
- Evidence endpoints.
- Analyst review endpoints.
- Error contracts.
- Pagination and filtering.
- API versioning.
- Frontend-to-backend integration flows.

This document will convert the architecture into a set of concrete integration contracts that can guide implementation of both the frontend and backend.
