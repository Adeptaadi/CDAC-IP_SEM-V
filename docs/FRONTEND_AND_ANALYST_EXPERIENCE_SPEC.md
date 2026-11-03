# Project Sentinel
# Frontend & Analyst Experience Specification

**Document Type:** Technical and User Experience Design Specification  
**Version:** 1.0  
**Status:** Architecture Baseline  
**Primary Technologies:** React, TypeScript, Vite  
**Primary Focus:** Analyst workflows, dashboard architecture, alert investigation, evidence visualization, orchestration visibility, human-in-the-loop interaction, and frontend-backend integration.

---

# 1. Purpose

Project Sentinel is not only an automated security analysis system. It is also an **analyst-facing investigation workspace**.

The frontend provides the interface through which users can:

- View security alerts.
- Understand alert severity and confidence.
- Start and monitor investigations.
- Examine collected evidence.
- Review AI-generated findings.
- Approve or reject actions when human intervention is required.
- Review the final investigation result.

The fundamental user interaction model is:

```text
SECURITY DATA
     │
     ▼
DETECTION
     │
     ▼
ALERT
     │
     ▼
┌───────────────────┐
│ ANALYST WORKSPACE │
└─────────┬─────────┘
          │
          ▼
AI INVESTIGATION
          │
          ▼
EVIDENCE + FINDINGS
          │
          ▼
ANALYST DECISION
```

The frontend is therefore the **human interaction layer surrounding the agent orchestration system**.

---

# 2. Primary User

The primary user for the MVP is a **security analyst**.

The analyst does not need to understand:

- Internal LLM prompts.
- Agent implementation details.
- Database schemas.
- Internal workflow code.

The analyst should understand:

- What happened.
- Why the system considers it suspicious.
- What evidence has been collected.
- What the investigation is currently doing.
- How confident the system is.
- Whether human review is required.

The interface should transform internal system activity into an understandable investigation workflow.

---

# 3. Analyst Experience Principles

The frontend should follow five principles.

## 3.1 Evidence Before Conclusion

The interface should avoid presenting AI conclusions without supporting information.

```text
CONCLUSION
    │
    ▼
SUPPORTING FINDINGS
    │
    ▼
EVIDENCE
```

An analyst should be able to move backward from a conclusion to the evidence supporting it.

---

## 3.2 Transparency Without Excessive Complexity

The system should expose meaningful investigation progress without displaying internal chain-of-thought or unnecessary technical details.

Display:

- Current investigation stage.
- Actions performed.
- Evidence collected.
- Findings generated.
- Confidence level.

Do not require the analyst to understand the internal agent graph.

---

## 3.3 Human Control

The analyst remains able to:

- Start an investigation.
- Review evidence.
- Approve controlled actions.
- Reject actions.
- Escalate an incident.
- Close or dismiss an investigation.

---

## 3.4 Clear State Representation

The user should always understand the current state.

For example:

```text
ALERT
  │
  ▼
INVESTIGATION CREATED
  │
  ▼
EVIDENCE COLLECTION
  │
  ▼
ANALYSIS
  │
  ├── WAITING FOR REVIEW
  │
  └── COMPLETED
```

---

## 3.5 Progressive Detail

The dashboard should not display all technical information at once.

```text
LEVEL 1
Alert Summary

     │ Click
     ▼

LEVEL 2
Investigation Overview

     │ Click
     ▼

LEVEL 3
Evidence and Technical Details
```

This keeps the application understandable while retaining technical depth.

---

# 4. Frontend Architecture

The recommended frontend architecture is:

```text
┌─────────────────────────────────────┐
│            REACT FRONTEND           │
│                                     │
│  Pages                              │
│    │                                │
│    ▼                                │
│  UI Components                      │
│    │                                │
│    ▼                                │
│  Application State                  │
│    │                                │
│    ▼                                │
│  API Client                         │
└──────────────────┬──────────────────┘
                   │
                   │ HTTP / WebSocket
                   ▼
┌─────────────────────────────────────┐
│           FASTAPI BACKEND           │
└─────────────────────────────────────┘
```

The frontend should not directly connect to:

- PostgreSQL.
- ChromaDB.
- Redis.
- Agent workers.

All system access passes through the backend API.

---

# 5. Recommended Frontend Structure

```text
frontend/
│
├── src/
│   │
│   ├── main.tsx
│   ├── App.tsx
│   │
│   ├── pages/
│   │   ├── DashboardPage.tsx
│   │   ├── AlertsPage.tsx
│   │   └── InvestigationPage.tsx
│   │
│   ├── components/
│   │   ├── alerts/
│   │   ├── investigation/
│   │   ├── evidence/
│   │   └── common/
│   │
│   ├── services/
│   │   └── api.ts
│   │
│   ├── hooks/
│   │   ├── useAlerts.ts
│   │   └── useInvestigation.ts
│   │
│   ├── types/
│   │   ├── alert.ts
│   │   └── investigation.ts
│   │
│   └── utils/
│
└── package.json
```

The exact structure can evolve, but UI concerns, API access, and domain types should remain separated.

---

# 6. Primary Application Screens

The MVP should focus on the following screens.

| Screen | Primary Purpose |
|---|---|
| Dashboard | System overview |
| Alerts | Review available security alerts |
| Alert Details | Understand a specific alert |
| Investigation | Monitor AI investigation |
| Evidence View | Examine collected evidence |
| Final Report | Review investigation outcome |

The MVP does not need to implement every possible SOC dashboard feature.

The focus should remain on demonstrating the complete Project Sentinel workflow.

---

# 7. Dashboard

The dashboard provides an overview of the system.

Conceptually:

```text
┌───────────────────────────────────────────┐
│ PROJECT SENTINEL                          │
├───────────────────────────────────────────┤
│                                           │
│  Alerts        Active Investigations      │
│     12                 3                  │
│                                           │
│  High Priority Alerts                     │
│  ┌─────────────────────────────────────┐  │
│  │ Alert │ Severity │ Status │ Time    │  │
│  └─────────────────────────────────────┘  │
│                                           │
└───────────────────────────────────────────┘
```

Recommended dashboard information:

- Total alerts.
- Alerts by severity.
- Active investigations.
- Recently completed investigations.
- System status.

The dashboard should not become a purely decorative visualization layer. Every displayed metric should correspond to real system data.

---

# 8. Alerts Screen

The alerts screen provides a structured list of detected security signals.

Example:

```text
┌──────────────────────────────────────────────────┐
│ ALERTS                                           │
├──────────────────────────────────────────────────┤
│                                                  │
│ Severity │ Alert              │ Status           │
│──────────────────────────────────────────────────│
│ HIGH     │ Suspicious Process │ New              │
│ MEDIUM   │ Unusual Connection │ Investigating    │
│ LOW      │ Authentication     │ Resolved         │
│                                                  │
└──────────────────────────────────────────────────┘
```

Recommended filtering:

- Severity.
- Status.
- Time range.

For the MVP, filters should only be implemented when the backend supports them.

---

# 9. Alert Details Screen

The analyst selects an alert to understand the initial security signal.

The screen should display:

```text
ALERT
│
├── Title
├── Severity
├── Confidence
├── Detection Summary
├── Related Events
└── Investigation Status
```

Example information hierarchy:

```text
SUSPICIOUS PROCESS ACTIVITY
        │
        ├── Severity: High
        ├── Confidence: 82%
        │
        └── Why was this alert generated?
               │
               ▼
          Detection Summary
```

The interface should clearly distinguish an initial detection from a completed investigation.

---

# 10. Starting an Investigation

An investigation is initiated from an alert.

User flow:

```text
ANALYST
   │
   ▼
SELECT ALERT
   │
   ▼
REVIEW ALERT
   │
   ▼
START INVESTIGATION
   │
   ▼
INVESTIGATION CREATED
   │
   ▼
AI ORCHESTRATION STARTS
```

The frontend calls:

```text
POST /api/v1/investigations
```

The backend returns an investigation identifier.

The frontend then navigates to the investigation workspace.

---

# 11. Investigation Workspace

The investigation workspace is the most important frontend component.

It should answer five questions:

1. What is being investigated?
2. What is the current investigation status?
3. What actions has the system performed?
4. What evidence has been found?
5. What is the current conclusion?

Recommended layout:

```text
┌────────────────────────────────────────────────────┐
│ INVESTIGATION: INV-001                             │
├────────────────────────────────────────────────────┤
│                                                    │
│ Status: ACTIVE                                     │
│ Stage: Evidence Collection                         │
│ Confidence: 76%                                    │
│                                                    │
├───────────────────────┬────────────────────────────┤
│ INVESTIGATION FLOW    │ EVIDENCE                   │
│                       │                            │
│ ✓ Alert Analysis      │ • Process Event            │
│ ✓ Event Collection    │ • Network Activity         │
│ ● Correlation         │ • Detection Result         │
│ ○ Final Assessment    │                            │
│                       │                            │
└───────────────────────┴────────────────────────────┘
```

The exact visual design can change, but the information hierarchy should remain.

---

# 12. Investigation Progress

The frontend should represent progress as **system stages**, not internal agent reasoning.

Recommended stages:

```text
1. Investigation Created
2. Initial Evidence Review
3. Evidence Collection
4. Correlation and Analysis
5. Assessment
6. Completed or Escalated
```

The stage representation is:

```text
CREATED
   │
   ▼
EVIDENCE REVIEW
   │
   ▼
EVIDENCE COLLECTION
   │
   ▼
ANALYSIS
   │
   ▼
ASSESSMENT
   │
   ▼
COMPLETED
```

An implementation may map internal orchestration states to these user-facing stages.

---

# 13. Orchestration Visibility

The user should see what the system is doing without exposing hidden internal reasoning.

For example:

```text
SYSTEM ACTIVITY

✓ Initial alert analyzed

✓ Retrieved related events

✓ Correlated host activity

● Analyzing evidence

○ Generating assessment
```

Each item should represent an observable action or state transition.

This is preferable to displaying messages such as:

> The AI is thinking.

Project Sentinel should emphasize **evidence-based operations**, not the appearance of AI activity.

---

# 14. Evidence View

The evidence view is central to explainability.

Each evidence item should contain:

```text
EVIDENCE ITEM
│
├── Type
├── Source
├── Timestamp
├── Summary
├── Confidence
└── Related Entity
```

Example:

```text
Process Execution Event

Host: HOST-001
Time: 10:32:15
Source: Dataset Replay
Confidence: High

A process execution event was observed and linked
to the investigation timeline.
```

Where possible, the analyst should be able to inspect additional details.

---

# 15. Evidence Classification

The frontend should visually distinguish evidence categories.

Conceptually:

| Category | Meaning |
|---|---|
| Telemetry | Observed system activity |
| Detection | Rule or detector output |
| Correlation | Relationship between events |
| Analyst Input | Human-provided information |

The system should not visually present a hypothesis as if it were raw telemetry evidence.

---

# 16. Findings and Hypotheses

The investigation interface should distinguish:

```text
EVIDENCE
   ↓
SUPPORTED FINDING

HYPOTHESIS
   ↓
SUPPORTED / REJECTED / INCONCLUSIVE
```

A hypothesis card may contain:

- Hypothesis statement.
- Current status.
- Confidence.
- Supporting evidence references.

Example:

```text
HYPOTHESIS

Potential suspicious process execution.

Status: Supported
Confidence: 0.78

Supporting Evidence:
• Event EVT-102
• Detection DET-055
```

This provides transparency into the investigation process.

---

# 17. Confidence Presentation

Confidence should be presented carefully.

For example:

```text
High Confidence
82%
```

Confidence should not imply certainty.

The interface should use language such as:

- Confidence.
- Evidence support.
- Investigation assessment.

Avoid presenting a numerical confidence score as a guarantee that a conclusion is correct.

---

# 18. Human-in-the-Loop Interface

Some actions may require analyst review.

Example:

```text
ACTION REQUIRES REVIEW

Action:
Collect additional related telemetry.

Reason:
Additional evidence is required to assess the alert.

[Approve]    [Reject]
```

The user action flows to the backend:

```text
ANALYST DECISION
       │
       ▼
API
       │
       ▼
INVESTIGATION SERVICE
       │
       ▼
ORCHESTRATION STATE UPDATE
```

The decision becomes part of the investigation audit trail.

---

# 19. Escalation Experience

When the system cannot confidently complete an investigation, the user should see a clear escalation state.

Example:

```text
INVESTIGATION ESCALATED

Reason:
Insufficient evidence to confidently determine the
nature of the observed activity.

Recommended Action:
Analyst review required.
```

This is preferable to allowing the AI system to generate an unsupported final conclusion.

---

# 20. Final Investigation Report

When an investigation is complete, the frontend should present a structured report.

```text
INVESTIGATION SUMMARY
│
├── Alert Summary
├── Final Status
├── Key Findings
├── Supporting Evidence
├── Actions Performed
├── Confidence
└── Recommended Next Steps
```

The final report should distinguish:

```text
OBSERVED FACTS

SUPPORTED FINDINGS

SYSTEM INTERPRETATION

ANALYST DECISIONS
```

This distinction is particularly important for an AI-assisted security project.

---

# 21. Frontend Data Flow

The frontend should not maintain separate versions of critical investigation state.

The primary flow is:

```text
FASTAPI
   │
   ▼
API CLIENT
   │
   ▼
APPLICATION STATE
   │
   ▼
REACT COMPONENTS
   │
   ▼
ANALYST INTERFACE
```

When the investigation state changes:

```text
BACKEND STATE
      │
      ▼
API RESPONSE
      │
      ▼
FRONTEND STATE UPDATE
      │
      ▼
UI RERENDER
```

The backend remains the source of truth.

---

# 22. Investigation Status Updates

For the MVP, polling is sufficient.

Example:

```text
INVESTIGATION PAGE
       │
       ▼
GET /investigations/{id}
       │
       ▼
WAIT
       │
       ▼
REPEAT
```

The polling interval should be controlled to avoid unnecessary requests.

A future version may use:

```text
WebSocket
```

for real-time updates.

The frontend architecture should not depend so heavily on polling that WebSockets cannot later be introduced.

---

# 23. API Client Layer

API communication should be centralized.

Example structure:

```text
services/
└── api/
    ├── client.ts
    ├── alerts.ts
    └── investigations.ts
```

React components should avoid embedding low-level HTTP requests directly.

The preferred flow is:

```text
COMPONENT
    │
    ▼
HOOK
    │
    ▼
API SERVICE
    │
    ▼
FASTAPI
```

---

# 24. Frontend Error Handling

The user should receive meaningful error states.

Examples:

```text
Failed to load alerts.

Unable to retrieve investigation status.

The investigation service is temporarily unavailable.
```

The frontend should not expose internal stack traces or sensitive infrastructure details.

---

# 25. Loading States

Important operations should have clear loading states.

Examples:

```text
Loading alerts...

Creating investigation...

Retrieving evidence...

Investigation in progress...
```

The interface should distinguish between:

- Loading.
- Empty state.
- Error.
- Completed state.

---

# 26. Authentication Experience

If authentication is implemented in the MVP:

```text
USER
  │
  ▼
LOGIN
  │
  ▼
AUTHENTICATED SESSION
  │
  ▼
PROJECT SENTINEL WORKSPACE
```

Authentication should be handled centrally and should not be implemented separately by individual pages.

---

# 27. Frontend Security Principles

The frontend must:

- Avoid storing sensitive credentials unnecessarily.
- Use backend-provided authorization boundaries.
- Treat API responses as controlled data.
- Avoid exposing internal infrastructure information.
- Validate user interactions before submission.

However, authorization enforcement must remain on the backend.

> The frontend improves usability; it is not the security boundary.

---

# 28. Accessibility and Usability

The MVP interface should remain understandable and usable.

Basic requirements include:

- Clear labels.
- Readable text.
- Keyboard-accessible controls where practical.
- Status information that does not depend only on color.
- Clear error messages.

These improvements strengthen the overall quality of the project without requiring excessive UI complexity.

---

# 29. Recommended Component Hierarchy

```text
App
│
├── Dashboard
│
├── Alerts
│   ├── AlertList
│   └── AlertDetails
│
└── Investigation
    ├── InvestigationHeader
    ├── InvestigationProgress
    ├── ActivityTimeline
    ├── EvidencePanel
    ├── FindingsPanel
    └── AnalystActionPanel
```

This structure keeps major investigation functions independently manageable.

---

# 30. MVP Implementation Priority

## Phase 1 — Application Foundation

```text
1. Configure React and TypeScript.
2. Create application layout.
3. Configure API client.
4. Define frontend domain types.
```

## Phase 2 — Alert Experience

```text
5. Implement alert list.
6. Implement alert details.
7. Add filtering where supported.
```

## Phase 3 — Investigation Workspace

```text
8. Create investigation page.
9. Display status.
10. Display investigation stages.
11. Display evidence.
```

## Phase 4 — Analyst Interaction

```text
12. Add action approval.
13. Add action rejection.
14. Display escalation states.
15. Display final reports.
```

## Phase 5 — Quality

```text
16. Add loading states.
17. Add error handling.
18. Test API integration.
19. Improve accessibility.
```

---

# 31. Acceptance Criteria

The frontend is considered complete when:

### Analyst Workflow

- Alerts can be viewed.
- Alert details can be inspected.
- Investigations can be started.
- Investigation progress can be monitored.

### Explainability

- Evidence is visible.
- Findings reference supporting evidence.
- Hypotheses are distinguished from facts.
- Confidence is presented appropriately.

### Human Control

- Required actions can be reviewed.
- Analyst decisions are communicated to the backend.
- Escalated investigations are clearly identified.

### Integration

- The frontend communicates only through backend APIs.
- Investigation state is retrieved from the backend.
- Loading and failure states are handled.

---

# 32. Complete User Workflow

The complete analyst journey is:

```text
┌───────────────┐
│ SECURITY DATA │
└───────┬───────┘
        ▼
┌───────────────┐
│   DETECTION   │
└───────┬───────┘
        ▼
┌───────────────┐
│     ALERT     │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ ANALYST VIEWS │
│    ALERT      │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ INVESTIGATION │
│    STARTED    │
└───────┬───────┘
        │
        ▼
┌───────────────────────┐
│ AI ORCHESTRATION      │
│                       │
│ Evidence Collection   │
│ Correlation           │
│ Assessment            │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│ ANALYST WORKSPACE     │
│                       │
│ Evidence              │
│ Findings              │
│ Actions               │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│ FINAL ASSESSMENT      │
└───────────────────────┘
```

---

# 33. Final Design Principle

The frontend should make Project Sentinel's intelligence **observable and verifiable**.

The analyst should be able to answer:

```text
WHAT HAPPENED?

WHAT IS THE SYSTEM INVESTIGATING?

WHAT HAS THE SYSTEM DONE?

WHAT EVIDENCE SUPPORTS THE FINDING?

HOW CONFIDENT IS THE SYSTEM?

WHERE IS HUMAN REVIEW REQUIRED?
```

The frontend is therefore not simply a dashboard. It is the **human-facing evidence and control layer around the AI-driven investigation architecture**.

---

# Next Document

The next recommended specification is:

## Security, Authentication & Authorization Design Specification

This document will define the security architecture of Project Sentinel, including authentication, JWT handling, role-based authorization, API protection, secret management, input validation, service trust boundaries, audit requirements, and security controls around the AI agent and capability execution layers.
