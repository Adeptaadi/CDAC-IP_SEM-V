# Project Sentinel
# Deployment, Environment & DevOps Specification

**Document Type:** Deployment and Operational Architecture Specification  
**Version:** 1.0  
**Status:** Architecture Baseline  
**Primary Focus:** Docker environment, service architecture, configuration, local development, service dependencies, startup sequencing, health checks, database migrations, and deployment readiness.

---

# 1. Purpose

Project Sentinel consists of multiple components that must work together:

- Frontend application.
- FastAPI backend.
- PostgreSQL database.
- Redis cache and background-processing support.
- ChromaDB vector store.
- AI model service.
- Agent orchestration layer.
- Telemetry processing pipeline.

A developer should not need to manually configure each dependency differently on every machine.

The deployment objective is therefore:

```text
ONE CONSISTENT ENVIRONMENT
          │
          ▼
REPRODUCIBLE DEVELOPMENT
          │
          ▼
RELIABLE INTEGRATION
          │
          ▼
CONSISTENT DEMONSTRATION
```

Docker and Docker Compose provide the baseline environment strategy.

---

# 2. Deployment Architecture Overview

The recommended local environment is:

```text
                         USER
                           │
                           ▼
                    ┌──────────────┐
                    │   FRONTEND   │
                    │ React / Vite │
                    └──────┬───────┘
                           │
                        HTTP/API
                           │
                           ▼
                    ┌──────────────┐
                    │   BACKEND    │
                    │   FastAPI    │
                    └───┬─────┬────┘
                        │     │
             ┌──────────┘     └───────────┐
             ▼                            ▼
      ┌──────────────┐              ┌──────────────┐
      │ PostgreSQL   │              │    Redis     │
      │ Durable Data │              │ Cache/Tasks  │
      └──────────────┘              └──────────────┘
             │
             │
             ▼
      ┌──────────────┐
      │   ChromaDB   │
      │ Vector Store │
      └──────────────┘

                    BACKEND
                       │
                       ▼
                 AI MODEL SERVICE
                    (Ollama)
```

The backend remains the central application boundary.

The frontend should not directly communicate with PostgreSQL, Redis, ChromaDB, or the AI service.

---

# 3. Environment Strategy

Project Sentinel should use separate configurations for different purposes.

## 3.1 Development Environment

Used for active implementation.

Characteristics:

- Hot reload enabled.
- Local Docker Compose.
- Development database.
- Debugging support.

---

## 3.2 Test Environment

Used for automated testing and evaluation.

Characteristics:

- Isolated test data.
- Repeatable configuration.
- Controlled dataset versions.
- Automated test execution.

---

## 3.3 Demonstration Environment

Used for the final project demonstration.

Characteristics:

- Stable configuration.
- Fixed model configuration.
- Prepared dataset.
- Verified service versions.

The conceptual flow is:

```text
DEVELOPMENT
     │
     ▼
TEST / EVALUATION
     │
     ▼
DEMONSTRATION
```

---

# 4. Docker Compose Service Architecture

The initial Docker Compose environment should contain the following services.

| Service | Primary Responsibility |
|---|---|
| frontend | User interface |
| backend | API and application logic |
| db | PostgreSQL persistence |
| cache | Redis caching and task support |
| vector-db | ChromaDB vector storage |

The AI model service may initially run outside Docker.

---

# 5. Ollama Deployment Strategy

For local development, the recommended baseline is:

```text
HOST MACHINE
    │
    ├── Docker Services
    │      │
    │      └── Backend
    │
    └── Ollama
          │
          ▼
      Local AI Model
```

The backend connects to the host AI service.

This approach simplifies:

- GPU utilization.
- Local model management.
- Model testing.
- Development configuration.

The architecture should maintain an abstraction layer so that the AI provider can be changed later.

---

# 6. AI Service Configuration

The backend should not hardcode a specific model endpoint.

Use configuration such as:

```text
LLM_PROVIDER=ollama
OLLAMA_HOST=http://host.docker.internal:11434
LLM_MODEL=<configured-model>
LLM_TIMEOUT=<configured-timeout>
```

The orchestration layer should communicate with a model adapter rather than embedding connection details throughout the codebase.

```text
ORCHESTRATOR
      │
      ▼
MODEL ADAPTER
      │
      ▼
AI SERVICE
```

This improves portability and testability.

---

# 7. PostgreSQL Service

PostgreSQL stores durable application state.

Recommended persistent data includes:

```text
Users
Alerts
Investigations
Evidence Metadata
Agent Execution Records
Audit Events
System Configuration
```

The database service should use a persistent Docker volume.

```text
POSTGRESQL CONTAINER
        │
        ▼
PERSISTENT VOLUME
```

This prevents normal container recreation from automatically destroying development data.

---

# 8. Redis Service

Redis should support lightweight transient operations.

Potential uses include:

- Caching.
- Temporary workflow state.
- Background task support.
- Rate limiting.

Redis should not become the sole durable source for critical investigation records.

The durability principle is:

```text
TEMPORARY / FAST DATA → REDIS

DURABLE SYSTEM STATE → POSTGRESQL
```

---

# 9. ChromaDB Service

ChromaDB supports vector-based retrieval.

Its primary use is:

```text
KNOWLEDGE DOCUMENT
       │
       ▼
CHUNKING
       │
       ▼
EMBEDDING
       │
       ▼
CHROMADB
       │
       ▼
RETRIEVAL
       │
       ▼
AGENT CONTEXT
```

For the Project Sentinel architecture, a standalone service provides clearer separation and easier inspection during development.

The service should use persistent storage.

---

# 10. Network Architecture

Docker Compose should create an internal application network.

The basic communication model is:

```text
FRONTEND
    │
    ▼
BACKEND
 ┌──┼───────┬───────────┐
 ▼  ▼       ▼           ▼
DB Redis Vector DB  AI Service
```

Only services requiring external access should expose ports to the host.

A recommended principle is:

> Expose the minimum number of services necessary for development and demonstration.

---

# 11. Port Configuration

A typical development configuration may use:

| Service | Example Port |
|---|---:|
| Frontend | 3000 |
| Backend | 8000 |
| PostgreSQL | Internal unless debugging |
| Redis | Internal unless debugging |
| ChromaDB | Internal unless debugging |
| Ollama | Host service port |

The exact configuration should remain environment-controlled.

---

# 12. Environment Variables

Configuration should be externalized.

The system should use:

```text
.env.example
```

as a documented template.

A local:

```text
.env
```

contains actual development values and should not contain production secrets.

Typical configuration groups are:

### Database

```text
POSTGRES_USER
POSTGRES_PASSWORD
POSTGRES_DB
DATABASE_URL
```

### Cache

```text
REDIS_URL
```

### Authentication

```text
JWT_SECRET
JWT_EXPIRATION
```

### AI

```text
LLM_PROVIDER
OLLAMA_HOST
LLM_MODEL
LLM_TIMEOUT
```

### Application

```text
APP_ENV
LOG_LEVEL
API_HOST
API_PORT
```

---

# 13. Configuration Architecture

The application should load configuration centrally.

```text
ENVIRONMENT
     │
     ▼
CONFIGURATION LAYER
     │
     ├── Database Config
     ├── AI Config
     ├── Security Config
     └── Application Config
```

Business logic should not repeatedly read environment variables directly.

This improves:

- Testability.
- Validation.
- Configuration consistency.

---

# 14. Backend Container

The backend container should contain:

- Python runtime.
- Application dependencies.
- Application source code.

Development execution may use:

```text
uvicorn app.main:app
```

Development mode can enable reload functionality.

Production-style execution should avoid development reload behavior.

---

# 15. Backend Startup Sequence

The backend should not assume that dependent services are immediately ready.

The logical startup sequence is:

```text
DATABASE AVAILABLE
       │
       ▼
DATABASE MIGRATED
       │
       ▼
BACKEND STARTS
       │
       ▼
DEPENDENCY HEALTH CHECK
       │
       ▼
API READY
```

Docker container startup does not guarantee application readiness.

This distinction is important.

---

# 16. Database Migration Strategy

Schema changes should be version-controlled.

Recommended flow:

```text
DATABASE MODEL CHANGE
        │
        ▼
CREATE MIGRATION
        │
        ▼
VERSION-CONTROL MIGRATION
        │
        ▼
APPLY TO ENVIRONMENT
```

Alembic is suitable for managing PostgreSQL schema migrations.

Database schema should not depend solely on manually executed SQL commands.

---

# 17. Health Checks

Each critical service should expose or support a health check.

Conceptually:

```text
SERVICE
   │
   ▼
HEALTH CHECK
   │
 ┌─┴──────┐
 │        │
READY   NOT READY
```

The backend health endpoint should distinguish, where practical, between:

- Application running.
- Critical dependencies available.

Example conceptual endpoints:

```text
/health
/ready
```

The exact API design can be finalized during implementation.

---

# 18. Dependency Health Model

A Project Sentinel investigation depends on multiple services.

```text
BACKEND
   │
   ├── PostgreSQL
   ├── Redis
   ├── ChromaDB
   └── AI Service
```

Not every dependency failure requires the same response.

For example:

| Dependency | Failure Impact |
|---|---|
| PostgreSQL | Critical persistence impact |
| Redis | Degraded caching or task support |
| ChromaDB | Knowledge retrieval unavailable |
| AI Service | Agent investigation unavailable |

The orchestration layer must handle degraded dependencies according to the fallback strategy.

---

# 19. Service Startup Order

A logical startup dependency sequence is:

```text
POSTGRESQL
REDIS
CHROMADB
    │
    ▼
BACKEND
    │
    ▼
FRONTEND
```

The AI service may operate independently when hosted on the local machine.

The backend should validate AI connectivity rather than assuming the service is available.

---

# 20. Local Development Workflow

A typical developer workflow is:

```text
1. Clone repository
        │
        ▼
2. Create local .env
        │
        ▼
3. Start infrastructure
        │
        ▼
4. Run database migrations
        │
        ▼
5. Start backend
        │
        ▼
6. Start frontend
        │
        ▼
7. Verify health
```

Docker Compose can automate most of the infrastructure startup.

---

# 21. Recommended Repository Structure

A structured project layout is:

```text
project-sentinel/
│
├── docker-compose.yml
├── .env.example
├── README.md
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic/
│   └── app/
│       ├── api/
│       ├── core/
│       ├── models/
│       ├── services/
│       ├── orchestration/
│       ├── agents/
│       ├── capabilities/
│       └── main.py
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   └── src/
│
├── infrastructure/
│   └── scripts/
│
└── docs/
```

The exact structure may evolve, but orchestration and agent logic should remain clearly separated from API and infrastructure concerns.

---

# 22. Development Data Strategy

Development data should not be mixed carelessly with evaluation data.

Recommended separation:

```text
DEVELOPMENT DATA
       │
       ├── Manual testing
       │
       ▼
EVALUATION DATA
       │
       ├── Controlled scenarios
       │
       ▼
DEMONSTRATION DATA
       └── Stable prepared cases
```

This improves reproducibility.

---

# 23. Dataset Volume Management

Large telemetry datasets should not necessarily be copied into Docker images.

A better approach is:

```text
HOST DATASET
     │
     ▼
MOUNT / CONFIGURED DATA PATH
     │
     ▼
INGESTION PIPELINE
```

This prevents unnecessarily large application images.

Dataset ingestion should remain explicit and controllable.

---

# 24. Logging in Containers

Containerized applications should emit operational logs in a consistent manner.

The logical flow is:

```text
APPLICATION
     │
     ▼
STRUCTURED LOG OUTPUT
     │
     ▼
CONTAINER LOG STREAM
```

Logs should contain correlation identifiers where appropriate.

Development teams can then inspect:

- Backend logs.
- Database startup logs.
- Dependency failures.

---

# 25. Build Strategy

Each application component should have a repeatable build definition.

```text
SOURCE CODE
    │
    ▼
DOCKERFILE
    │
    ▼
CONTAINER IMAGE
    │
    ▼
RUNNING SERVICE
```

The frontend and backend should be independently buildable.

This reduces coupling between application layers.

---

# 26. Development Verification

After starting the environment, verify:

### Frontend

```text
Frontend service reachable
```

### Backend

```text
API health endpoint responds
```

### Database

```text
Database connection succeeds
Migrations are applied
```

### AI Service

```text
Configured model service is reachable
```

### Vector Store

```text
Vector service is available
```

A single failed dependency should produce a clear diagnostic result.

---

# 27. CI/CD Readiness

A full production CI/CD pipeline is not mandatory for the MVP, but the repository should be structured to support automation.

A future pipeline could perform:

```text
CODE CHANGE
    │
    ▼
LINTING
    │
    ▼
UNIT TESTS
    │
    ▼
INTEGRATION TESTS
    │
    ▼
BUILD IMAGES
    │
    ▼
DEPLOY
```

The MVP should at minimum support repeatable automated testing.

---

# 28. Deployment Failure Handling

Deployment and runtime failures should be distinguishable.

Example:

```text
CONTAINER FAILED TO START
        │
        ▼
INFRASTRUCTURE / CONFIGURATION ISSUE
```

versus:

```text
APPLICATION STARTED
        │
        ▼
AI SERVICE UNAVAILABLE
        │
        ▼
DEGRADED AGENT FUNCTIONALITY
```

The observability layer should provide enough information to identify which category occurred.

---

# 29. Backup and Recovery Considerations

For the academic MVP, backup requirements can remain simple.

However, durable data should be treated differently from temporary data.

```text
POSTGRESQL
     │
     ▼
IMPORTANT SYSTEM STATE
```

Redis and transient cache data can generally be recreated depending on the implemented workflow.

The demonstration environment should have a reproducible method for restoring required data.

---

# 30. Deployment Security Baseline

The deployment environment should follow the security architecture.

Important rules include:

- Do not commit secrets.
- Use environment configuration.
- Limit exposed ports.
- Keep infrastructure services internal where possible.
- Use separate development and demonstration configuration.
- Do not expose database credentials through the frontend.

The deployment architecture supports security; it does not replace application-level security controls.

---

# 31. Deployment Acceptance Criteria

The deployment baseline is complete when:

### Environment

- A new developer can create a working environment using documented steps.
- Required services start consistently.
- Configuration is externalized.

### Backend

- The API starts successfully.
- Database migrations are reproducible.
- Dependency failures are identifiable.

### AI

- The backend can verify AI service connectivity.
- Model configuration is environment-controlled.
- AI service failure does not crash unrelated services.

### Data

- PostgreSQL data persists appropriately.
- Development datasets are not unnecessarily embedded in application images.
- Evaluation data can be reproduced.

### Demonstration

- The complete system can be started using a documented procedure.
- Service health can be verified before demonstration.
- A stable configuration is maintained.

---

# 32. Complete Deployment Workflow

The complete environment lifecycle is:

```text
SOURCE CODE
    │
    ▼
ENVIRONMENT CONFIGURATION
    │
    ▼
DOCKER BUILD
    │
    ▼
START INFRASTRUCTURE
    │
    ├── PostgreSQL
    ├── Redis
    └── ChromaDB
           │
           ▼
      START BACKEND
           │
           ▼
    CHECK DEPENDENCIES
           │
           ▼
     START FRONTEND
           │
           ▼
      VERIFY HEALTH
           │
           ▼
    PROJECT SENTINEL READY
```

---

# 33. Final Design Principle

The deployment architecture should make the system easier to develop and demonstrate, not unnecessarily complex.

The core philosophy is:

```text
REPRODUCIBLE ENVIRONMENT
          +
CLEAR SERVICE BOUNDARIES
          +
EXTERNALIZED CONFIGURATION
          +
HEALTH VISIBILITY
          +
CONTROLLED DEPENDENCIES
          =
RELIABLE PROJECT EXECUTION
```

For Project Sentinel, this is especially important because the AI agent orchestration layer depends on several supporting services. A stable deployment foundation ensures that development effort is focused on the project's core intelligence and investigation capabilities rather than repeated environment problems.

---

# Next Document

The next recommended document is:

## Data Management, Dataset Governance & Telemetry Lifecycle Specification

This document will define the complete lifecycle of security telemetry in Project Sentinel, including dataset selection, source organization, raw-data handling, schema validation, normalization, storage, dataset versioning, scenario extraction, ground-truth management, retention, reproducibility, and the flow of data from raw telemetry to investigation evidence.
