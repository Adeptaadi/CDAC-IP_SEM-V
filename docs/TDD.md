# Technical Design Document (TDD)

**Project Name:** Agentic AI-powered Autonomous Cyber Threat Hunting Platform

**Version:** 1.0

**Status:** Draft

**Document Type:** Technical Design Document (TDD)

---

# Table of Contents

1. Executive Summary
2. Development Objectives
3. Technology Stack
4. Project Structure
5. Coding Standards
6. Backend Module Design
7. Frontend Module Design
8. Agent Runtime Design
9. Shared State Implementation
10. Configuration Management

---

# 1 Executive Summary

## Purpose

This document translates the architecture defined in the System Design Document into an implementation-ready technical specification.

It defines

- Project organization
- Module responsibilities
- Coding conventions
- Runtime implementation
- Package structure
- Internal interfaces
- Configuration
- Development guidelines

Unlike the SDD, this document is written for developers.

---

# 2 Development Objectives

The implementation shall satisfy the following goals.

- Modular codebase
- Low coupling
- High cohesion
- Testability
- Readability
- Extensibility
- Clear ownership

Every module should have one responsibility.

---

# 3 Technology Stack

## Frontend

- React
- TypeScript
- TailwindCSS
- React Router
- Axios
- Recharts

---

## Backend

- Python 3.12+
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic

---

## AI

- LangGraph
- LangChain
- Ollama
- Qwen 3 Instruct
- Sentence Transformers

---

## Database

- PostgreSQL
- Redis
- ChromaDB

---

## DevOps

- Docker
- Docker Compose
- Git
- GitHub

---

# 4 Project Structure

```

project-root

├── frontend/

├── backend/

│

├── api/

├── planner/

├── workers/

│     ├── detection/

│     ├── correlation/

│     ├── investigation/

│     ├── reporting/

│     └── response/

│

├── runtime/

├── knowledge/

├── memory/

├── database/

├── services/

├── models/

├── schemas/

├── prompts/

├── utils/

├── tests/

│

├── datasets/

├── reports/

├── docker/

└── docs/

```

---

# 5 Coding Standards

## General Principles

- One class, one responsibility.
- One module, one capability.
- Avoid circular dependencies.
- Prefer composition over inheritance.
- Use dependency injection where appropriate.

---

## Naming Conventions

### Files

snake_case.py

---

### Classes

PascalCase

Example

InvestigationService

PlannerEngine

DetectionWorker

---

### Variables

snake_case

---

### Constants

UPPER_CASE

---

### API Endpoints

kebab-case

Example

```
/api/investigations
/api/planner/status
```

---

# 6 Backend Module Design

The backend is organized into independent modules.

## API Module

Responsibilities

- Request validation
- Authentication
- Response formatting
- WebSocket handling

No business logic.

---

## Planner Module

Contains

- Goal Manager
- Decision Engine
- Task Dispatcher
- Confidence Engine
- Planner State

Owns the planning cycle.

---

## Worker Module

Each worker is isolated.

Example

```
workers/

├── detection/

├── correlation/

├── investigation/

├── reporting/

└── response/
```

Each worker contains

- Prompt
- Tools
- Executor
- Validator

---

## Runtime Module

Responsible for

- Worker scheduling
- Queue management
- Retry policy
- Timeout management
- Execution monitoring

---

## Knowledge Module

Contains

- RAG
- Embeddings
- Vector search
- Context assembly
- Document loaders

---

## Memory Module

Contains

Working Memory

Long-Term Memory

State Synchronization

Checkpoint Manager

---

## Database Module

Contains

Repositories

ORM Models

Migrations

Transactions

Connection Pool

---

# 7 Frontend Module Design

The frontend follows feature-based organization.

```
src/

├── pages/

├── layouts/

├── components/

├── hooks/

├── services/

├── stores/

├── types/

├── utils/

└── assets/
```

---

## Major Pages

- Login
- Dashboard
- Investigation
- Reports
- Analytics
- Settings

---

## Shared Components

- Sidebar
- Navbar
- Timeline
- Evidence Table
- Planner Activity
- Confidence Indicator
- Report Viewer

---

# 8 Agent Runtime Design

The runtime manages all agent execution.

```
Planner

↓

Task Queue

↓

Worker Runtime

↓

Result Validator

↓

State Update

↓

Planner
```

Responsibilities

- Dispatch workers
- Validate outputs
- Retry failures
- Monitor execution
- Collect metrics

---

# 9 Shared State Implementation

The Shared Investigation State is represented as a domain object.

```
InvestigationState

├── metadata

├── goal

├── evidence

├── timeline

├── hypotheses

├── confidence

├── planner_history

├── worker_history

├── reports

└── recommendations
```

Only the Planner modifies this object.

Workers receive a read-only snapshot and return a delta (changes), not direct mutations.

---

# 10 Configuration Management

Configuration is centralized.

```
config/

├── app.yaml

├── ai.yaml

├── database.yaml

├── security.yaml

└── logging.yaml
```

Configuration categories

- AI models
- Planner thresholds
- Confidence thresholds
- Database connections
- Authentication
- Logging
- Feature flags

Configuration should be environment-specific (development, testing, production) and loaded through a single configuration service.

---

# End of TDD Part 1

Next Part

11. Internal Interfaces

12. Planner Implementation

13. Worker Implementation

14. Repository Pattern

15. Service Layer

16. Testing Strategy

17. Error Handling

18. Logging

19. CI/CD

20. Build & Release

21. Coding Checklist

22. Implementation Roadmap


---

# 11 Internal Interfaces

## 11.1 Purpose

Internal interfaces define how software modules communicate while remaining loosely coupled.

Every module exposes a well-defined interface and hides its implementation details.

The architecture follows the Dependency Inversion Principle.

```
Presentation

↓

API Layer

↓

Service Layer

↓

Agent Runtime

↓

Repositories

↓

Database
```

---

## 11.2 Interface Design Principles

Every interface shall

- Have a single responsibility
- Be implementation independent
- Return structured objects
- Throw standardized exceptions
- Avoid exposing infrastructure details

---

## 11.3 Planner Interface

Responsibilities

- Start Investigation
- Pause Investigation
- Resume Investigation
- Stop Investigation
- Replan Investigation
- Get Planner Status
- Assign Task
- Receive Worker Result

Example

```python
class PlannerInterface:

    start_investigation()

    pause()

    resume()

    assign_worker()

    receive_result()

    update_state()
```

---

## 11.4 Worker Interface

All workers implement the same contract.

```python
class Worker:

    execute(task)

    validate()

    return_result()
```

Required methods

- execute()
- validate_output()
- get_capabilities()
- health_check()

---

## 11.5 Knowledge Interface

Provides

- Semantic Search
- MITRE Lookup
- Historical Incident Search
- Playbook Retrieval

```python
search(query)

retrieve_mitre()

retrieve_playbook()

retrieve_history()
```

---

## 11.6 Memory Interface

Responsibilities

Load Investigation

Save Investigation

Checkpoint

Restore

Archive

---

## 11.7 Report Interface

Responsibilities

Generate Report

Export PDF

Export Markdown

Load Report

Version Report

---

# 12 Planner Implementation

## 12.1 Overview

The Planner is implemented as a deterministic orchestration engine augmented by an LLM for reasoning.

Only reasoning is delegated to AI.

Everything else remains software logic.

---

## 12.2 Planner Components

```
Planner

├── Goal Manager

├── State Manager

├── Decision Engine

├── Confidence Engine

├── Task Dispatcher

├── Memory Manager

├── Explainability Engine

└── Runtime Controller
```

---

## 12.3 Planner Startup

Initialization Steps

Load Configuration

↓

Connect Database

↓

Connect Vector DB

↓

Load Knowledge

↓

Initialize Memory

↓

Initialize Runtime

↓

Start Planning Loop

---

## 12.4 Planning Loop

Pseudo Code

```python
while planner.running:

    event = wait_for_event()

    state = load_state()

    goal = evaluate_goal()

    decision = reason()

    task = create_task()

    dispatch(task)

    update_state()
```

---

## 12.5 Goal Manager

Responsibilities

Maintain

- Active Goals
- Goal Priority
- Goal Dependencies
- Goal Completion

Only planner may modify goals.

---

## 12.6 Decision Engine

Responsible for

Choosing Worker

Prioritizing Tasks

Updating Confidence

Selecting Next Objective

Escalating Investigation

---

## 12.7 Task Dispatcher

Creates

Task Object

↓

Places into Queue

↓

Worker Executes

↓

Receives Result

↓

Updates State

---

## 12.8 Planner Checkpointing

Planner checkpoints

Current Goal

Current Investigation

Current Tasks

Confidence

Memory

Planner History

Checkpoint Frequency

Configurable

---

# 13 Worker Implementation

## 13.1 Worker Architecture

Each worker follows identical implementation.

```
Worker

↓

Receive Task

↓

Load Context

↓

Retrieve Knowledge

↓

Execute

↓

Validate

↓

Return Result
```

---

## 13.2 Worker Package Structure

```
workers/

detection/

correlation/

investigation/

reporting/

response/

Each package contains

agent.py

prompt.py

tools.py

validator.py

schemas.py
```

---

## 13.3 Detection Worker

Components

Prompt

Detection Tools

Feature Extractor

Validator

Output Formatter

---

## 13.4 Correlation Worker

Components

Timeline Builder

Relationship Finder

Merge Engine

Validator

---

## 13.5 Investigation Worker

Components

Hypothesis Builder

Evidence Collector

Knowledge Retriever

Reasoner

Validator

---

## 13.6 Reporting Worker

Components

Summary Generator

Markdown Formatter

PDF Generator

Report Validator

---

## 13.7 Response Worker

Components

Playbook Lookup

Risk Estimator

Containment Generator

Recommendation Validator

---

## 13.8 Worker Output

Every worker returns

```json
{
 "worker":"Investigation",

 "status":"Completed",

 "confidence":0.82,

 "observations":[],

 "evidence":[],

 "recommendations":[],

 "next_tasks":[]
}
```

---

## 13.9 Worker Validation

Every output is validated before planner consumption.

Checks include

Required Fields

Confidence Range

Evidence Presence

Schema Validation

---

# 14 Repository Pattern

## Purpose

Repositories isolate business logic from persistence.

Services never interact with databases directly.

---

## Repository Structure

```
repositories/

investigation_repository.py

report_repository.py

knowledge_repository.py

user_repository.py

audit_repository.py
```

---

## Investigation Repository

Responsibilities

Create Investigation

Update Investigation

Load Investigation

Delete Investigation

Search Investigation

---

## Report Repository

Responsibilities

Store Report

Load Report

Update Report

Archive Report

---

## User Repository

Responsibilities

Authentication

Authorization

User Lookup

Role Lookup

---

## Audit Repository

Responsibilities

Store Logs

Search Logs

Export Logs

---

## Repository Benefits

- Decouples persistence
- Easier testing
- Swappable database
- Cleaner services

---

# 15 Service Layer

## Purpose

Services implement business logic.

Controllers never contain business rules.

---

## Service Structure

```
services/

planner_service.py

investigation_service.py

knowledge_service.py

report_service.py

dashboard_service.py

user_service.py
```

---

## Planner Service

Responsibilities

Start Planner

Pause Planner

Resume Planner

Assign Workers

Receive Results

Update Investigation

---

## Investigation Service

Responsibilities

CRUD

Evidence

Timeline

Hypothesis

Status

Confidence

---

## Knowledge Service

Responsibilities

Embedding

Retrieval

Ranking

Context Assembly

---

## Report Service

Responsibilities

Generate

Export

Archive

Version

---

## Dashboard Service

Responsibilities

Overview

Statistics

Planner Status

Worker Status

Reports

Notifications

---

# 16 Database Layer

## Purpose

The Database Layer manages persistence.

No business logic is permitted.

---

## Components

```
Database Layer

├── ORM Models

├── Repositories

├── Migrations

├── Transactions

├── Connection Pool

└── Backup Manager
```

---

## ORM

Recommended

SQLAlchemy

Responsibilities

Entity Mapping

Relationships

Transactions

Lazy Loading

---

## Migrations

Recommended

Alembic

Migration Strategy

Versioned

Reversible

Automated

---

## Transactions

Used for

Investigation Updates

Evidence Updates

Planner History

Worker History

Report Generation

---

## Connection Pool

Purpose

Efficient database utilization.

Configurable Pool Size.

---

## Backup Strategy

Daily

↓

Backup Database

↓

Verify Integrity

↓

Archive

Future

Point-in-Time Recovery

---

# 17 Dependency Injection

## Philosophy

Business logic should never instantiate dependencies directly.

Use dependency injection for

Repositories

Services

Knowledge Providers

Memory Providers

LLM Providers

Configuration

---

## Example

```python
PlannerService(

    repository,

    knowledge,

    memory,

    dispatcher,

    confidence_engine
)
```

This improves

- Testing
- Maintainability
- Replaceability

---

# 18 Module Dependency Rules

Allowed

```
API

↓

Services

↓

Planner

↓

Repositories

↓

Database
```

Forbidden

```
API

↓

Database
```

Forbidden

```
Worker

↓

Database
```

Forbidden

```
Planner

↓

Frontend
```

---

# 19 Technical Summary

The implementation follows

- Layered Architecture
- Repository Pattern
- Service Layer Pattern
- Dependency Injection
- Shared Investigation State
- Planner-Centric Orchestration
- Worker Isolation
- Interface-Based Design

This ensures that implementation remains modular, testable, maintainable, and extensible while preserving the agentic behavior defined in the AAD.

---

# End of TDD Part 2

Next Part

20 API Layer

21 State Management

22 Exception Handling

23 Logging

24 Configuration

25 Testing Strategy

26 CI/CD

27 Docker

28 Deployment

29 Performance

30 Security

31 Coding Checklist

32 Development Roadmap

33 Final Technical Summary


---

# 20 API Layer

## 20.1 Overview

The API Layer exposes all platform functionality through RESTful endpoints and WebSockets.

The API Layer is responsible only for communication.

Business logic remains inside the Service Layer.

```
Client

↓

REST API

↓

Service Layer

↓

Planner Runtime

↓

Repositories
```

---

## 20.2 API Principles

Every API shall

- be REST compliant
- return JSON
- be versioned
- support authentication
- provide standardized error responses
- validate all input

---

## 20.3 API Categories

```
API

├── Authentication

├── Dashboard

├── Investigations

├── Planner

├── Reports

├── Knowledge

├── Users

└── Administration
```

---

## 20.4 Request Lifecycle

```
Client

↓

Authentication

↓

Validation

↓

Controller

↓

Service

↓

Repository

↓

Response
```

---

## 20.5 Response Standard

Every response follows a common schema.

```json
{
    "success": true,
    "message": "Investigation updated",
    "data": {},
    "timestamp": "...",
    "request_id": "..."
}
```

---

# 21 State Management

## 21.1 Philosophy

The platform is **state-driven**.

The Investigation State represents the single source of truth.

Only the Planner modifies state.

Workers propose changes.

---

## 21.2 Investigation State

```
InvestigationState

├── Metadata

├── Goal

├── Status

├── Confidence

├── Evidence

├── Timeline

├── Hypotheses

├── Planner History

├── Worker Results

├── Reports

└── Recommendations
```

---

## 21.3 State Update Flow

```
Worker

↓

Result

↓

Planner

↓

Validate

↓

Merge

↓

Persist

↓

Dashboard Update
```

---

## 21.4 Versioning

Every investigation state contains

- Version Number
- Last Modified
- Modified By
- Checkpoint ID

This enables optimistic concurrency and rollback.

---

## 21.5 Checkpoint Strategy

Checkpoint when

- Planner completes cycle
- Confidence changes significantly
- Report generated
- Investigation closed

---

# 22 Exception Handling

## 22.1 Objectives

The platform shall

- Fail gracefully
- Preserve investigation state
- Produce actionable logs
- Avoid system crashes

---

## 22.2 Exception Categories

```
Exceptions

├── Validation

├── Business

├── Runtime

├── Infrastructure

├── AI

└── Security
```

---

## 22.3 Validation Exceptions

Examples

- Missing required fields
- Invalid JSON
- Unsupported event schema
- Invalid authentication token

Response

HTTP 400

---

## 22.4 Business Exceptions

Examples

- Investigation not found
- Worker unavailable
- Planner paused
- Invalid investigation state

Response

HTTP 409

---

## 22.5 Infrastructure Exceptions

Examples

- Database unavailable
- Redis unavailable
- ChromaDB unavailable
- Ollama unavailable

Recovery

Retry

↓

Circuit Breaker

↓

Fallback

↓

Escalate

---

## 22.6 AI Exceptions

Examples

- Invalid LLM output
- JSON parsing failure
- Prompt execution timeout
- Hallucination detection
- Confidence inconsistency

Planner Action

Discard Output

↓

Retry

↓

Alternative Prompt

↓

Analyst Escalation

---

# 23 Logging Architecture

## 23.1 Objectives

Every significant event shall be logged.

Logs support

- Debugging
- Auditing
- Explainability
- Performance Analysis

---

## 23.2 Log Categories

```
Logs

├── API

├── Planner

├── Worker

├── Database

├── Security

├── Dashboard

├── AI

└── Audit
```

---

## 23.3 Planner Log

Example

```json
{
    "planner_cycle": 23,
    "goal": "Validate Credential Theft",
    "selected_worker": "Investigation",
    "confidence": 0.82,
    "execution_time": "2.3s"
}
```

---

## 23.4 Worker Log

Stores

- Worker Name
- Task ID
- Duration
- Confidence
- Result Status

---

## 23.5 Audit Log

Stores

- Login
- Logout
- Investigation Updates
- Report Generation
- Analyst Approval
- Configuration Changes

Audit logs are immutable.

---

# 24 Configuration Management

## 24.1 Overview

All configuration is externalized.

No hard-coded values.

---

## Configuration Files

```
config/

├── app.yaml

├── ai.yaml

├── planner.yaml

├── security.yaml

├── database.yaml

├── logging.yaml

└── deployment.yaml
```

---

## Planner Configuration

Contains

- Confidence Thresholds
- Retry Count
- Task Timeout
- Planning Interval
- Goal Priorities

---

## AI Configuration

Contains

- Model Name
- Temperature
- Context Length
- Embedding Model
- Top-K Retrieval

---

## Environment Variables

Examples

```
DATABASE_URL

REDIS_URL

CHROMADB_URL

OLLAMA_URL

JWT_SECRET

LOG_LEVEL
```

---

# 25 Testing Strategy

## 25.1 Philosophy

Testing follows a layered approach.

```
Unit

↓

Integration

↓

System

↓

AI

↓

Performance

↓

Acceptance
```

---

## 25.2 Unit Testing

Target

- Services
- Repositories
- Planner Components
- Worker Components
- Utilities

---

## 25.3 Integration Testing

Verify

- Planner ↔ Worker
- Planner ↔ Database
- Planner ↔ Knowledge
- Dashboard ↔ Backend

---

## 25.4 AI Testing

Evaluate

- Prompt Quality
- Structured Output
- JSON Validity
- Confidence Consistency
- Hallucination Rate

---

## 25.5 Performance Testing

Metrics

- Planner Latency
- Worker Latency
- API Response Time
- Database Queries
- Knowledge Retrieval Time

---

## 25.6 Acceptance Testing

Validate

- End-to-end investigation
- Dynamic planning
- Human intervention
- Report generation
- Dashboard updates

---

# 26 Continuous Integration (CI)

## Objectives

Every commit shall

- Build
- Test
- Lint
- Validate

before merge.

---

## CI Pipeline

```
Commit

↓

GitHub Actions

↓

Lint

↓

Unit Tests

↓

Integration Tests

↓

Docker Build

↓

Artifact
```

---

## Quality Gates

- Tests Passed
- No Critical Lint Errors
- Build Successful
- Docker Image Created

---

# 27 Docker Implementation

## Containers

```
docker-compose

├── frontend

├── backend

├── planner

├── workers

├── postgres

├── redis

├── chromadb

└── ollama
```

---

## Health Checks

Every container exposes

- Health Endpoint
- Readiness Check
- Liveness Check

---

## Networking

Containers communicate through an internal Docker network.

No direct database exposure to external clients.

---

# 28 Deployment Strategy

## Development

```
Developer

↓

Docker Compose

↓

Local Stack
```

---

## Production (Future)

```
Load Balancer

↓

API Gateway

↓

Backend Cluster

↓

Planner

↓

Worker Pool

↓

Databases
```

---

## Deployment Principles

- Immutable containers
- Environment-specific configuration
- Zero code changes between environments

---

# 29 Performance Optimization

## Backend

- Async FastAPI endpoints
- Connection pooling
- Batch database operations
- Efficient indexing

---

## AI

- Cache embeddings
- Reuse retrieved context
- Limit prompt size
- Stream LLM responses where appropriate

---

## Database

- Indexed lookups
- Pagination
- Query optimization
- Archive old investigations

---

# 30 Security Implementation

## Authentication

JWT

Refresh Tokens

Password Hashing

---

## Authorization

Role-Based Access Control (RBAC)

- Analyst
- Manager
- Administrator

---

## Secure Coding

- Input validation
- Parameterized queries
- Output encoding
- Secret management
- Least privilege

---

## AI Security

- Prompt injection filtering
- Context validation
- Output schema validation
- Human approval for containment actions

---

# 31 Coding Checklist

Before merging code

- [ ] Feature implemented
- [ ] Unit tests added
- [ ] Integration tests pass
- [ ] Logging included
- [ ] Exceptions handled
- [ ] Documentation updated
- [ ] Code reviewed
- [ ] Lint passes
- [ ] No hard-coded secrets
- [ ] API documented

---

# 32 Development Roadmap

## Sprint 1

- Project setup
- Database
- Authentication
- Dashboard skeleton

---

## Sprint 2

- Planner Runtime
- Shared Investigation State
- Detection Worker

---

## Sprint 3

- Correlation Worker
- Investigation Worker
- Knowledge Layer
- RAG

---

## Sprint 4

- Reporting Worker
- Response Worker
- Planner Explainability
- Confidence Engine

---

## Sprint 5

- Dashboard Integration
- WebSockets
- Testing
- Performance Optimization

---

## Sprint 6

- Final Evaluation
- Documentation
- Deployment
- Demonstration

---

# 33 Final Technical Summary

The implementation follows modern software engineering practices while supporting an advanced Agentic AI architecture.

Key implementation characteristics include:

- Layered Architecture
- Planner-Centric Orchestration
- Shared Investigation State
- Repository Pattern
- Service Layer Pattern
- Dependency Injection
- Polyglot Persistence
- Retrieval-Augmented Generation
- Structured AI Outputs
- Comprehensive Testing
- Containerized Deployment
- Human-on-the-Loop Governance

The resulting system is modular, testable, extensible, and suitable for demonstrating enterprise-grade autonomous cybersecurity investigations while remaining achievable for a two-person engineering team.

---

# End of Technical Design Document (TDD)
