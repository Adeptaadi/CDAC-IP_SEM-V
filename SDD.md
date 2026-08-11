# System Design Document (SDD)

**Project Name:** Agentic AI-powered Autonomous Cyber Threat Hunting Platform

**Version:** 1.0

**Status:** Draft

**Document Type:** System Design Document (SDD)

**Prepared By:** Solution Architecture Team

---

# Table of Contents

1. Executive Summary
2. Purpose
3. Scope
4. Architecture Goals
5. Quality Attributes
6. Architectural Drivers
7. Architecture Principles
8. System Context
9. Layered Architecture
10. High-Level Component Architecture
11. Core Components

---

# 1 Executive Summary

## 1.1 Purpose

The System Design Document (SDD) defines the complete software architecture of the Agentic AI-powered Autonomous Cyber Threat Hunting Platform.

Unlike the Product Requirements Document (PRD), which defines product behavior, and the Agent Architecture Document (AAD), which defines autonomous reasoning, this document specifies how the complete software system is engineered.

This document describes

- Software architecture
- System components
- Layer interactions
- Runtime services
- Data flow
- Deployment architecture
- Infrastructure
- Engineering decisions

---

## 1.2 Intended Audience

This document is intended for

- Solution Architects
- Backend Engineers
- Frontend Engineers
- AI Engineers
- DevOps Engineers
- Database Engineers
- Project Review Committee

---

## 1.3 Relationship with Other Documents

| Document | Purpose |
|----------|---------|
| PRD | Defines what the product should do |
| AAD | Defines how autonomous agents behave |
| SDD | Defines how the software system is built |
| AIDD | Defines AI implementation |
| TDD | Defines implementation details |

---

# 2 Purpose

The objective of this document is to translate product requirements and agent architecture into an implementable enterprise software architecture.

The design must satisfy the following constraints.

- Modular
- Explainable
- Extensible
- Maintainable
- Scalable
- Fault tolerant
- Suitable for continuous telemetry processing

---

# 3 Scope

The System Design Document covers

- Presentation Layer
- Backend Services
- Agent Runtime
- Knowledge Layer
- Persistence Layer
- Service Communication
- Component Responsibilities
- Deployment Model

The following topics are intentionally excluded.

- Prompt engineering
- LLM implementation
- Database schema
- REST API specification
- CI/CD implementation

These are documented separately.

---

# 4 Architecture Goals

The architecture is designed to achieve the following goals.

---

## Goal 1

Support autonomous investigations.

The architecture must allow the Planning Agent to dynamically coordinate worker agents without predefined workflows.

---

## Goal 2

Support continuous telemetry.

Incoming events should be processed continuously.

The platform should behave as a continuously running SOC assistant.

---

## Goal 3

Support explainability.

Every investigation should remain explainable.

Planner decisions

↓

Worker outputs

↓

Evidence

↓

Reports

must remain traceable.

---

## Goal 4

Support modularity.

Every major capability should exist independently.

Examples

Detection

Correlation

Investigation

Reporting

Response

Knowledge Retrieval

Dashboard

---

## Goal 5

Support extensibility.

Future worker agents should be added without redesigning existing components.

---

## Goal 6

Support maintainability.

Responsibilities should remain clearly separated.

Low coupling.

High cohesion.

---

## Goal 7

Support future enterprise deployment.

Although MVP runs locally,

the architecture should allow migration to

- Kubernetes
- Cloud
- Enterprise SIEM

without redesign.

---

# 5 Quality Attributes

The architecture prioritizes the following software qualities.

---

## Availability

The platform should remain operational during long-running investigations.

Failure of one worker agent should not terminate the investigation.

---

## Reliability

Investigation state shall remain consistent.

Planner decisions shall be recoverable.

---

## Scalability

New worker agents shall be deployable independently.

Knowledge sources shall scale independently.

Storage shall scale independently.

---

## Performance

Planner decisions should complete with low latency.

Dashboard updates should appear in near real time.

---

## Security

Authentication required.

Authorization enforced.

Audit logging mandatory.

Sensitive investigation data protected.

---

## Explainability

Every AI decision shall remain explainable.

This quality takes precedence over opaque automation.

---

## Maintainability

Independent modules

Independent services

Clear interfaces

Minimal dependencies

---

## Testability

Every service shall be independently testable.

Planner logic

↓

Worker logic

↓

Knowledge retrieval

↓

Dashboard

can all be validated separately.

---

# 6 Architectural Drivers

The following requirements drive the architecture.

---

## Product Drivers

- Continuous monitoring
- Autonomous investigation
- Human-on-the-loop
- Explainable AI
- Dashboard
- Minimal human intervention

---

## Technical Drivers

- Continuous event stream
- Shared investigation memory
- RAG
- Planner orchestration
- Worker specialization

---

## Business Drivers

- Industry-grade architecture
- Demonstrable Agentic AI
- Future extensibility

---

# 7 Architecture Principles

---

## Principle 1

Layered Architecture

Each layer performs one responsibility.

Presentation

↓

Application

↓

Agent

↓

Knowledge

↓

Data

---

## Principle 2

Single Orchestrator

Only the Planning Agent coordinates investigations.

No distributed decision making.

---

## Principle 3

Shared Investigation State

Workers collaborate through shared state.

Workers never communicate directly.

---

## Principle 4

Service Independence

Every service shall be independently deployable.

---

## Principle 5

Technology Independence

Architecture should not depend on

LangGraph

CrewAI

AutoGen

Specific LLMs

Specific databases

Implementation choices remain replaceable.

---

## Principle 6

State Driven Architecture

Investigations evolve through state updates.

Not through predefined workflows.

---

## Principle 7

Evidence Driven Reasoning

All planner decisions originate from

Evidence

↓

Knowledge

↓

Reasoning

↓

Decision

---

# 8 System Context

The platform operates between security telemetry sources and human analysts.

```
              Security Telemetry

        Network Logs

        Authentication Logs

        System Events

                │

                ▼

        Agentic AI Platform

                │

                ▼

          SOC Dashboard

                │

                ▼

           Human Analyst
```

The platform consumes telemetry.

The platform produces investigations.

---

# 9 Layered Architecture

The software follows a five-layer architecture.

```
┌────────────────────────────────────────────┐
│           Presentation Layer               │
│                                            │
│      React Dashboard                       │
│      Analyst Interface                     │
└────────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────┐
│           Application Layer                │
│                                            │
│ FastAPI                                    │
│ REST APIs                                  │
│ WebSocket                                  │
│ Authentication                             │
└────────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────┐
│              Agent Layer                   │
│                                            │
│ Planning Agent                             │
│ Detection Agent                            │
│ Correlation Agent                          │
│ Investigation Agent                        │
│ Reporting Agent                            │
│ Response Agent                             │
└────────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────┐
│            Knowledge Layer                 │
│                                            │
│ MITRE ATT&CK                               │
│ Historical Incidents                       │
│ Playbooks                                  │
│ RAG                                        │
│ Vector Database                            │
└────────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────┐
│               Data Layer                   │
│                                            │
│ PostgreSQL                                │
│ Redis                                     │
│ Investigation Store                       │
│ Dataset Repository                        │
└────────────────────────────────────────────┘
```

Each layer communicates only with adjacent layers.

---

# 10 High-Level Component Architecture

```
                        React Dashboard
                               │
                     REST / WebSocket
                               │
                      FastAPI Backend
                               │
      ┌──────────────┬──────────┬──────────────┐
      ▼              ▼          ▼              ▼
 Planner      Investigation   Knowledge    Authentication
 Service         Service       Service        Service
      │              │          │
      └──────────────┼──────────┘
                     ▼
          Shared Investigation Store
                     │
      ┌──────────────┼──────────────┐
      ▼              ▼              ▼
 PostgreSQL      ChromaDB         Redis
```

---

# 11 Core Components

The platform consists of the following logical components.

---

## Presentation Layer

Responsibilities

- Dashboard
- Visualization
- Investigation Explorer
- Reports
- User Interaction

No business logic.

---

## API Layer

Responsibilities

- REST APIs
- WebSocket
- Authentication
- Authorization
- Request validation

No investigation logic.

---

## Planner Service

Responsibilities

- Planning
- Decision making
- Worker coordination
- Goal management
- State updates

This is the brain of the platform.

---

## Worker Services

Responsibilities

Detection

Correlation

Investigation

Reporting

Response

Each service performs one capability.

---

## Shared Investigation Store

Single source of truth.

Contains

Investigations

Evidence

Timeline

Confidence

Planner Decisions

Worker Outputs

---

## Knowledge Service

Provides

MITRE ATT&CK

Historical Incidents

Playbooks

Threat Intelligence

through retrieval.

---

## Persistence Layer

Stores

Investigations

Reports

Knowledge

Logs

Configuration

Historical Data

Planner History

Worker History

---

# End of SDD Part 1

Next Part

12. Backend Service Architecture

13. Planner Runtime Architecture

14. Worker Runtime Architecture

15. Event Processing Architecture

16. Investigation Processing Architecture

17. Service Communication

18. Runtime Sequence Diagrams



---

# 12 Backend Service Architecture

## 12.1 Overview

The backend follows a **modular service-oriented architecture** where each major responsibility is encapsulated within a dedicated service.

Unlike a traditional monolithic application, each service owns a well-defined responsibility while collaborating through shared interfaces.

```
                    Backend

          ┌──────────────────────────┐
          │      FastAPI Gateway      │
          └─────────────┬────────────┘
                        │
 ┌──────────┬───────────┼───────────┬──────────┐
 ▼          ▼           ▼           ▼          ▼
Planner  Investigation Knowledge  Report   Auth
Service     Service      Service   Service Service
                        │
                        ▼
               Shared Investigation Store
```

---

## 12.2 Backend Modules

| Module | Responsibility |
|---------|---------------|
| API Gateway | Client communication |
| Planner Service | Investigation orchestration |
| Worker Runtime | Executes worker tasks |
| Investigation Service | Investigation persistence |
| Knowledge Service | RAG & MITRE retrieval |
| Report Service | Report generation |
| Notification Service | Alerts & notifications |
| Authentication Service | User authentication |

---

## 12.3 API Gateway

### Responsibilities

The API Gateway acts as the entry point into the backend.

Responsibilities include

- REST API
- Authentication
- Authorization
- Request validation
- Rate limiting
- WebSocket management

The gateway **never contains business logic**.

---

## 12.4 Planner Service

The Planner Service contains the autonomous reasoning engine.

Responsibilities

- Goal management
- Planning cycle
- Worker selection
- Confidence updates
- Investigation lifecycle
- Escalation

The planner is state-aware.

It owns the investigation.

---

## 12.5 Worker Runtime Service

The Worker Runtime executes specialized worker agents.

Responsibilities

- Worker loading
- Worker execution
- Retry
- Timeouts
- Result validation

The runtime never decides which worker executes.

Only the planner performs scheduling.

---

## 12.6 Investigation Service

Responsible for

- Investigation CRUD
- Timeline
- Evidence storage
- Hypothesis storage
- Planner history
- Worker history

Provides

```
Planner

↓

Investigation Service

↓

Database
```

---

## 12.7 Knowledge Service

Provides external cybersecurity knowledge.

Sources

- MITRE ATT&CK
- Historical Incidents
- Playbooks
- Threat Intelligence

Responsibilities

- Semantic retrieval
- Embedding search
- Document ranking
- Context assembly

---

## 12.8 Report Service

Responsible for

- Technical Reports
- Executive Reports
- Markdown Export
- PDF Export
- Report Versioning

Reports remain immutable after generation.

---

## 12.9 Notification Service

Responsible for

Dashboard Notifications

Planner Escalations

Critical Incidents

Approval Requests

Future

Email

Slack

Microsoft Teams

---

# 13 Planner Runtime Architecture

## 13.1 Runtime Overview

The Planning Agent executes continuously.

Unlike request-response systems,

the planner behaves as an event-driven runtime.

```
Event

↓

Planner Runtime

↓

Planning Cycle

↓

Task Assignment

↓

Worker Execution

↓

State Update

↓

Repeat
```

---

## 13.2 Planner Components

```
Planner Runtime

├── Goal Manager

├── State Manager

├── Task Dispatcher

├── Decision Engine

├── Confidence Engine

├── Memory Manager

└── Explainability Engine
```

---

## Goal Manager

Responsibilities

- Create goals
- Update goals
- Prioritize goals
- Archive completed goals

---

## State Manager

Maintains

Current Investigation

Evidence

Timeline

Confidence

Hypotheses

Worker Status

Planner Decisions

---

## Decision Engine

Determines

Next Worker

Next Goal

Planner Action

Stopping Conditions

---

## Task Dispatcher

Creates tasks.

Assigns workers.

Tracks execution.

Receives results.

---

## Confidence Engine

Calculates

Investigation Confidence

Updates confidence

after every meaningful investigation change.

---

## Explainability Engine

Responsible for

Planner reasoning

Decision explanation

Confidence explanation

Worker justification

---

# 14 Worker Runtime Architecture

## Overview

The Worker Runtime provides a generic execution environment.

All worker agents share the same lifecycle.

```
Receive Task

↓

Load Context

↓

Load Knowledge

↓

Execute

↓

Validate Result

↓

Return Output
```

---

## Worker Manager

Loads

Detection Agent

Correlation Agent

Investigation Agent

Reporting Agent

Response Agent

Future agents can be registered dynamically.

---

## Worker Lifecycle

```
Idle

↓

Assigned

↓

Loading Context

↓

Executing

↓

Completed

↓

Waiting
```

---

## Worker Context

Every worker receives

Investigation ID

Task

Goal

Evidence

Knowledge

Planner Context

Configuration

---

## Worker Result

Every worker returns

Status

Confidence

Evidence

Recommendations

Suggested Next Tasks

Observations

---

# 15 Event Processing Architecture

## Overview

Security telemetry enters the system continuously.

```
Incoming Events

↓

Validation

↓

Normalization

↓

Investigation Lookup

↓

Planner
```

---

## Event Validation

Checks

Timestamp

Schema

Required Fields

Integrity

Invalid events

↓

Rejected

---

## Event Normalization

Different datasets produce different formats.

Normalization converts events into

Common Event Schema

Fields

Timestamp

Source

Destination

Protocol

User

Host

Event Type

Severity

---

## Investigation Lookup

Determine

Existing Investigation?

↓

Yes

↓

Update Investigation

↓

Planner

No

↓

Create Investigation

↓

Planner

---

# 16 Investigation Processing Architecture

## Investigation Lifecycle

```
Create Investigation

↓

Planner

↓

Assign Worker

↓

Worker Result

↓

Update State

↓

Planner

↓

Goal Complete?
```

---

## Investigation Components

Every investigation consists of

Metadata

Timeline

Evidence

Confidence

Hypotheses

Reports

Recommendations

Planner History

Worker History

---

## Planner Loop

```
Read State

↓

Evaluate

↓

Assign Worker

↓

Receive Output

↓

Update State

↓

Repeat
```

---

# 17 Service Communication

## Communication Model

The architecture follows

Planner-Centric Communication.

```
Planner

↓

Worker

↓

Planner

↓

Worker

↓

Planner
```

Workers never communicate directly.

---

## Communication Types

Planner

↓

Worker

Task Assignment

---

Worker

↓

Planner

Task Result

---

Planner

↓

Knowledge Service

Knowledge Request

---

Knowledge

↓

Planner

Retrieved Context

---

Planner

↓

Investigation Service

State Update

---

Investigation Service

↓

Database

Persistence

---

Dashboard

↓

Planner

Analyst Action

---

## Communication Pattern

The platform primarily follows an

Asynchronous Request–Response Pattern.

Planner

↓

Queue Task

↓

Worker

↓

Result

↓

Planner

Future versions may replace the in-memory dispatcher with

Redis Streams

RabbitMQ

Apache Kafka

without changing planner logic.

---

# 18 Runtime Sequence Diagram

## New Investigation

```
Security Event

↓

API Gateway

↓

Normalization

↓

Planner

↓

Detection Agent

↓

Planner

↓

Correlation Agent

↓

Planner

↓

Investigation Agent

↓

Planner

↓

Knowledge Service

↓

Planner

↓

Reporting Agent

↓

Planner

↓

Dashboard
```

This represents one possible execution.

Another investigation may execute

```
Planner

↓

Investigation Agent

↓

Planner

↓

Response Agent

↓

Planner

↓

Reporting Agent
```

Execution order remains dynamic.

---

## Existing Investigation

```
New Event

↓

Investigation Lookup

↓

Existing Investigation

↓

Planner

↓

Update Confidence

↓

Assign Worker

↓

Update Timeline

↓

Dashboard
```

---

## Human Intervention

```
Analyst

↓

Dashboard

↓

API Gateway

↓

Planner

↓

Pause Investigation

↓

Persist State

↓

Dashboard Updated
```

---

# 19 Runtime State Synchronization

Every planner cycle synchronizes

- Investigation Metadata
- Evidence
- Timeline
- Confidence
- Active Tasks
- Completed Tasks
- Hypotheses
- Reports
- Recommendations
- Worker Status

Synchronization ensures all workers receive a consistent investigation context.

---

# End of SDD Part 2

Next Part

20. Database Architecture

21. PostgreSQL Schema

22. Shared Investigation Store

23. Redis Cache

24. ChromaDB & Vector Storage

25. Knowledge Repository

26. API Design

27. Authentication & Authorization



---

# 20 Database Architecture

## 20.1 Overview

The platform uses a **polyglot persistence architecture**, selecting the most appropriate storage technology for each type of data instead of relying on a single database.

Each datastore has a clearly defined responsibility.

```
                    Data Layer

        ┌────────────────────────────────┐
        │   Shared Investigation Store    │
        └──────────────┬─────────────────┘
                       │
      ┌────────────────┼─────────────────┐
      ▼                ▼                 ▼
 PostgreSQL         Redis           ChromaDB
(Relational DB)   (Cache/State)   (Vector Store)
```

---

## 20.2 Database Responsibilities

| Database | Responsibility |
|------------|---------------|
| PostgreSQL | Persistent operational data |
| Redis | Runtime cache & task queue |
| ChromaDB | Knowledge embeddings |
| File Storage | Reports & exported files |

---

## 20.3 Why Multiple Databases?

Different data has different access patterns.

Examples

Investigation Metadata

↓

Relational

↓

PostgreSQL

---

Planner Working State

↓

Fast Read/Write

↓

Redis

---

MITRE Knowledge

↓

Semantic Search

↓

ChromaDB

---

Generated Reports

↓

Files

↓

Storage

---

# 21 PostgreSQL Architecture

## Purpose

PostgreSQL stores all persistent business data.

Planner state is reconstructed from PostgreSQL whenever required.

---

## Primary Entities

```
PostgreSQL

├── Users

├── Investigations

├── Evidence

├── Timeline

├── Hypotheses

├── Planner Decisions

├── Worker Results

├── Reports

├── Recommendations

├── Audit Logs

└── Configuration
```

---

## Investigation Table

Stores

Investigation ID

Status

Severity

Priority

Current Goal

Current Confidence

Created Time

Updated Time

Assigned Analyst

---

## Evidence Table

Stores

Evidence ID

Investigation ID

Evidence Type

Source

Timestamp

Collector

Confidence

Validation Status

---

## Timeline Table

Stores

Chronological investigation events.

Timeline remains append-only.

---

## Planner Decision Table

Stores

Decision ID

Goal

Reason

Confidence

Selected Worker

Timestamp

Execution Duration

---

## Worker Result Table

Stores

Worker

Task

Status

Evidence

Confidence

Execution Time

Planner Reference

---

## Report Table

Stores

Report Metadata

Version

Export Location

Creation Time

Report Type

---

## Audit Log

Every important system action is stored.

Examples

Planner Decisions

Worker Executions

User Login

Analyst Approval

Investigation Closed

---

# 22 Shared Investigation Store

## Overview

The Shared Investigation Store is the **single source of truth** for all active investigations.

Every planner decision and worker execution references this store.

Workers never maintain independent copies of investigation state.

---

## Investigation Structure

```
Investigation

├── Metadata

├── Current Goal

├── Planner State

├── Timeline

├── Evidence

├── Hypotheses

├── Worker Results

├── Reports

├── Recommendations

├── Audit History

└── Confidence
```

---

## Investigation Lifecycle

```
Created

↓

Planner

↓

Worker Updates

↓

Planner Updates

↓

Report

↓

Closed

↓

Archive
```

---

## State Consistency

The Investigation Store guarantees

- Single source of truth
- Version consistency
- Transactional updates
- Planner ownership

---

# 23 Redis Architecture

## Purpose

Redis provides high-speed runtime storage.

Redis is not the system of record.

---

## Responsibilities

Working Memory

Planner Cache

Session Store

Task Queue

Active Investigations

WebSocket Sessions

Rate Limiting

---

## Cached Objects

```
Redis

├── Active Investigations

├── Current Planner State

├── Worker Queue

├── User Sessions

├── Dashboard Cache

└── Temporary Results
```

---

## Cache Strategy

Read

↓

Redis

↓

Miss?

↓

PostgreSQL

↓

Update Redis

---

## Expiration Policy

Planner Cache

30 minutes

Sessions

Configurable

Task Queue

Until Completed

---

# 24 ChromaDB Architecture

## Purpose

ChromaDB stores vector embeddings for semantic retrieval.

The planner retrieves cybersecurity knowledge through similarity search.

---

## Stored Collections

MITRE ATT&CK

Historical Investigations

Response Playbooks

Threat Intelligence

Sigma Rules (Future)

CAPEC (Future)

---

## Retrieval Flow

```
Planner

↓

Knowledge Request

↓

Embedding

↓

Vector Search

↓

Relevant Documents

↓

Planner
```

---

## Document Metadata

Each vector contains

Document ID

Source

Category

Embedding

Reference

Version

Tags

---

## Similarity Search

Planner retrieves

Top-K

Most Relevant

Knowledge Items

for the current investigation.

---

# 25 Knowledge Repository

## Purpose

Provides trusted cybersecurity knowledge.

Knowledge is separated from planner logic.

---

## Repository Structure

```
Knowledge

├── MITRE

├── Historical Incidents

├── Playbooks

├── IOC Library

├── Threat Intelligence

└── Documentation
```

---

## Knowledge Categories

### MITRE

Techniques

Tactics

Procedures

---

### Historical Incidents

Previous investigations

Evidence

Reports

Lessons Learned

---

### Playbooks

Recommended

Containment

Recovery

Investigation

Procedures

---

## Knowledge Updates

Knowledge may be

Added

Updated

Versioned

Archived

without affecting planner logic.

---

# 26 API Architecture

## Overview

The platform exposes REST APIs for dashboard communication.

Future versions may expose gRPC or GraphQL.

---

## API Categories

Authentication

Investigations

Reports

Planner

Knowledge

Dashboard

Administration

---

## Investigation APIs

Examples

```
GET

/investigations

GET

/investigations/{id}

POST

/investigations

PATCH

/investigations/{id}

DELETE

/investigations/{id}
```

---

## Planner APIs

```
POST

/planner/start

POST

/planner/pause

POST

/planner/resume

POST

/planner/replan

GET

/planner/status
```

---

## Report APIs

```
GET

/reports

GET

/reports/{id}

POST

/reports/export
```

---

## Knowledge APIs

```
GET

/knowledge/search

GET

/knowledge/mitre

GET

/knowledge/playbooks
```

---

## Dashboard APIs

```
GET

/dashboard/overview

GET

/dashboard/live

GET

/dashboard/history
```

---

## API Design Principles

RESTful

Versioned

Stateless

JSON Responses

Consistent Error Handling

---

# 27 Authentication & Authorization

## Authentication

The MVP uses JWT-based authentication.

```
User

↓

Login

↓

JWT Issued

↓

Subsequent Requests

↓

JWT Validation
```

---

## Authorization

Role-Based Access Control (RBAC)

Roles

SOC Analyst

SOC Manager

Administrator

Research User

---

## Permission Matrix

| Resource | Analyst | Manager | Admin |
|-----------|----------|----------|-------|
| View Investigations | ✓ | ✓ | ✓ |
| Approve Responses | ✓ | ✓ | ✓ |
| Delete Investigations | ✗ | ✗ | ✓ |
| Manage Users | ✗ | ✗ | ✓ |
| Configure Platform | ✗ | ✗ | ✓ |

---

## Session Management

JWT

Refresh Token

Session Expiration

Logout

Session Revocation

---

## API Security

HTTPS

JWT

Rate Limiting

Input Validation

Output Sanitization

Audit Logging

---

# 28 Data Consistency Strategy

The architecture follows

Planner-Owned Consistency.

Rules

- Planner is the only component that updates investigation state.
- Workers submit results.
- Investigation Service performs transactional persistence.
- Dashboard consumes read-only projections.

This avoids concurrent modification conflicts.

---

# 29 Storage Summary

| Storage | Purpose |
|----------|---------|
| PostgreSQL | Persistent operational data |
| Redis | Runtime cache & task queue |
| ChromaDB | Semantic knowledge retrieval |
| File Storage | Reports & exports |

---

# End of SDD Part 3

Next Part

30. Frontend Architecture

31. Dashboard Architecture

32. Deployment Architecture

33. Docker Compose

34. Logging & Monitoring

35. Error Handling

36. Performance

37. Scalability

38. Technology Stack

39. Project Folder Structure

40. Architecture Decisions

41. Future Scaling

42. Appendix


---

# 30 Frontend Architecture

## 30.1 Overview

The frontend provides the primary interaction layer between the SOC analyst and the autonomous investigation platform.

Unlike traditional dashboards that simply visualize alerts, the frontend visualizes the **entire investigation lifecycle**, including planner reasoning, worker activity, confidence evolution, evidence, and recommendations.

The frontend shall be implemented as a Single Page Application (SPA).

---

## 30.2 Design Goals

The frontend shall

- Minimize analyst effort
- Present explainable AI decisions
- Visualize autonomous investigations
- Support real-time updates
- Allow analyst intervention
- Remain responsive

---

## 30.3 Frontend Modules

```
Frontend

├── Authentication

├── Dashboard

├── Investigation Explorer

├── Timeline

├── Evidence Viewer

├── Reports

├── Planner Activity

├── Recommendations

├── Analytics

└── Settings
```

---

## 30.4 Component Responsibilities

### Dashboard

Responsibilities

- Active Investigations
- KPIs
- Notifications
- Planner Status

---

### Investigation Explorer

Displays

- Investigation Metadata
- Evidence
- Timeline
- Planner Decisions
- Worker Outputs
- Reports

---

### Planner Activity

Displays

Planning Cycle

Worker Selection

Confidence

Reasoning

Goal Progress

---

### Reports

Allows

View

Export

Version History

---

### Settings

Manage

Users

Knowledge

Platform Configuration

Preferences

---

# 31 Dashboard Architecture

## Overview

The dashboard follows an investigation-centric design.

```
Dashboard

│

├── SOC Overview

├── Live Investigations

├── Investigation Details

│      ├── Timeline

│      ├── Evidence

│      ├── Planner

│      ├── Workers

│      ├── Reports

│      └── Recommendations

├── Analytics

├── History

└── Settings
```

---

## Dashboard Layout

```
+------------------------------------------------------+

Header

+--------------------+---------------------------------+

Sidebar              Main Workspace

                    Active Investigations

                    Planner Activity

                    Timeline

                    Reports

                    Recommendations

+------------------------------------------------------+
```

---

## Live Dashboard Updates

Dashboard updates occur through WebSockets.

Examples

Planner Decision

↓

Dashboard Update

Worker Completed

↓

Dashboard Update

New Evidence

↓

Dashboard Update

Report Generated

↓

Dashboard Update

---

## Dashboard Widgets

### Overview

- Active Investigations
- Critical Alerts
- Average Confidence
- Planner Utilization
- Worker Utilization

---

### Investigation Widget

Displays

Severity

Priority

Confidence

Planner Status

Current Goal

---

### Timeline Widget

Chronological Investigation

---

### Evidence Widget

Evidence Cards

Evidence Confidence

Evidence Source

---

### Recommendation Widget

Recommended Action

Risk

Impact

Approval Required

---

# 32 Deployment Architecture

## Overview

The MVP is deployed using Docker Compose.

Future enterprise deployment shall support Kubernetes.

---

## MVP Deployment

```
+--------------------------------------+

Docker Compose

|

+--------------------------------------+

Frontend Container

Backend Container

Planner Container

Worker Runtime

PostgreSQL

Redis

ChromaDB

Ollama

+--------------------------------------+
```

---

## Future Enterprise Deployment

```
Load Balancer

↓

API Gateway

↓

Backend Cluster

↓

Planner Cluster

↓

Worker Pool

↓

Database Cluster

↓

Knowledge Cluster
```

---

## Deployment Layers

Presentation

↓

Application

↓

Agent Runtime

↓

Knowledge

↓

Persistence

---

# 33 Docker Architecture

## Containers

```
Docker

├── frontend

├── backend

├── planner

├── workers

├── postgres

├── redis

├── chromadb

├── ollama
```

---

## Container Responsibilities

Frontend

React UI

---

Backend

REST APIs

Authentication

WebSocket

---

Planner

Planning Cycle

Decision Engine

---

Workers

Detection

Correlation

Investigation

Reporting

Response

---

Database

Persistent Storage

---

Redis

Working Memory

Task Queue

---

ChromaDB

Knowledge Retrieval

---

Ollama

LLM Runtime

---

# 34 Logging & Monitoring

## Logging Goals

Every significant system event shall be logged.

---

## Log Categories

Planner Logs

Worker Logs

System Logs

Authentication Logs

API Logs

Database Logs

Dashboard Logs

---

## Planner Logs

Stores

Planner Decision

Reason

Confidence

Worker Selection

Execution Time

---

## Worker Logs

Stores

Worker

Task

Execution Time

Result

Confidence

---

## Investigation Logs

Stores

Evidence Updates

Timeline

Hypothesis Changes

Recommendations

---

## Monitoring Metrics

CPU

Memory

Planner Latency

Worker Latency

Investigation Throughput

API Response Time

Database Performance

Knowledge Retrieval Time

---

# 35 Error Handling

## Philosophy

System failures should not terminate investigations.

---

## Worker Failure

```
Worker Failure

↓

Planner Detects

↓

Retry

↓

Alternative Worker

↓

Escalate
```

---

## Planner Failure

```
Planner Restart

↓

Recover State

↓

Continue Investigation
```

---

## Database Failure

Planner

↓

Retry

↓

Queue Update

↓

Persist Later

---

## API Failure

Return

Structured Error

Error Code

Timestamp

Correlation ID

---

# 36 Performance Architecture

## Objectives

Low latency planning

Efficient retrieval

Fast dashboard updates

Continuous monitoring

---

## Performance Targets

Planner Decision

< 3 seconds

---

Knowledge Retrieval

< 2 seconds

---

Dashboard Refresh

Near Real-Time

---

API Response

< 500 ms

---

Worker Execution

Task Dependent

---

# 37 Scalability

## Horizontal Scaling

Worker Runtime

↓

More Worker Instances

---

Planner

Future

Leader Election

Planner Cluster

---

Knowledge Layer

Additional Vector Stores

---

Database

Read Replicas

Future

---

## Scalability Strategy

```
Users

↓

Frontend

↓

API

↓

Planner

↓

Task Queue

↓

Worker Pool
```

Worker Pool size may increase without changing planner logic.

---

# 38 Technology Stack

## Frontend

React

TypeScript

TailwindCSS

React Router

Axios

Recharts

---

## Backend

FastAPI

Python

Pydantic

SQLAlchemy

---

## AI

LangGraph

LangChain

Ollama

Qwen / Llama

Sentence Transformers

---

## Storage

PostgreSQL

Redis

ChromaDB

---

## Deployment

Docker

Docker Compose

Future

Kubernetes

---

## Version Control

Git

GitHub

---

# 39 Project Folder Structure

```
project-root

├── frontend/

│   ├── src/

│   ├── components/

│   ├── pages/

│   ├── services/

│   └── assets/

│

├── backend/

│   ├── api/

│   ├── planner/

│   ├── workers/

│   ├── knowledge/

│   ├── services/

│   ├── database/

│   ├── models/

│   └── utils/

│

├── datasets/

├── reports/

├── docs/

├── docker/

├── tests/

└── scripts/
```

---

# 40 Architecture Decisions (ADRs)

## ADR-001

Use Planner + Specialized Workers.

Reason

Improves modularity and explainability.

---

## ADR-002

Use Shared Investigation State.

Reason

Single source of truth.

---

## ADR-003

Use PostgreSQL for operational data.

Reason

Strong consistency and relational queries.

---

## ADR-004

Use Redis for runtime state.

Reason

Low-latency access and task queuing.

---

## ADR-005

Use ChromaDB for semantic retrieval.

Reason

Efficient vector similarity search.

---

## ADR-006

Use LangGraph for orchestration.

Reason

Native support for stateful, graph-based agent workflows.

---

## ADR-007

Use Ollama for local LLM inference.

Reason

Offline capability, privacy, and reproducibility.

---

## ADR-008

Human-on-the-loop approval for containment actions.

Reason

Prevent unsafe autonomous actions.

---

# 41 Future Scaling Strategy

Future enterprise deployment may introduce

- Multiple Planner replicas with leader election
- Distributed Worker Pools
- Kafka for event streaming
- Redis Streams for task dispatch
- Kubernetes orchestration
- Multi-region deployment
- Multi-tenant support
- External SIEM integrations
- Enterprise Identity Providers
- Cloud-native object storage
- Distributed vector databases

The software architecture has been designed so these enhancements can be introduced with minimal changes to the core planner and worker logic.

---

# 42 System Design Summary

The Agentic AI-powered Autonomous Cyber Threat Hunting Platform adopts a **layered, service-oriented, planner-centric architecture**.

Key architectural characteristics include:

- Layered architecture separating presentation, application, agent, knowledge, and data concerns.
- A single Planning Agent responsible for autonomous reasoning and orchestration.
- Specialized Worker Agents that execute focused cybersecurity tasks.
- A Shared Investigation Store as the single source of truth.
- Polyglot persistence using PostgreSQL, Redis, and ChromaDB.
- Knowledge-grounded reasoning through Retrieval-Augmented Generation (RAG).
- Real-time analyst interaction via a React dashboard and WebSockets.
- Human-on-the-loop oversight for all containment recommendations.
- Modular services that support future scaling to distributed, cloud-native deployments.

The architecture intentionally separates **decision-making**, **execution**, **knowledge retrieval**, and **persistence**, enabling an explainable, extensible, and maintainable Agentic AI platform suitable for both an industry-sponsored academic project and future enterprise evolution.

---

# End of System Design Document (SDD)
