# Project Sentinel
# Deployment Security Hardening & Production Readiness Specification

**Document Type:** Technical Architecture and Implementation Specification  
**System:** Project Sentinel — Multi-Agent Cyber Threat Detection and Investigation Platform  
**Version:** 1.0  
**Status:** Proposed Implementation Baseline

---

## 1. Purpose

This document defines the security hardening and production-readiness requirements for deploying Project Sentinel.

Project Sentinel combines:

- FastAPI backend services.
- React/Vite frontend.
- PostgreSQL persistence.
- Redis-based task coordination.
- ChromaDB vector retrieval.
- Ollama-hosted local LLMs.
- LangGraph-based agent orchestration.
- Dataset replay and cybersecurity analysis workloads.

The combination of conventional application components and autonomous AI capabilities introduces additional security concerns.

The deployment must protect against:

1. Unauthorized access to application resources.
2. Exposure of sensitive investigation data.
3. Compromise of agent execution capabilities.
4. Prompt injection and malicious retrieved content.
5. Unauthorized response actions.
6. Container and dependency vulnerabilities.
7. Database and credential exposure.
8. Resource exhaustion from dataset replay or agent execution.
9. Loss or corruption of investigation state.
10. Insecure configuration changes.

The goal is to make the system deployable and recoverable without granting agents unrestricted access to the infrastructure.

## 2. Deployment Security Objectives

| Objective | Requirement |
|---|---|
| Confidentiality | Protect telemetry, evidence, credentials and investigation data |
| Integrity | Prevent unauthorized changes to investigation state and audit history |
| Availability | Prevent uncontrolled agent execution and resource exhaustion |
| Authentication | Require authenticated access to protected application functions |
| Authorization | Enforce role and capability-level permissions |
| Isolation | Separate application services and execution responsibilities |
| Recoverability | Preserve durable investigation state |
| Auditability | Record security-sensitive actions |
| AI safety | Treat LLM output as untrusted input |
| Human oversight | Require approval for sensitive response operations |

### 2.1 MVP deployment security boundary

The MVP is a controlled demonstration and evaluation environment.

It is not automatically a production-ready enterprise SOC deployment.

The following limitations must remain explicit:

- Dataset replay is the primary telemetry ingestion mechanism.
- Real production SIEM connectivity is outside the MVP.
- Response actions are simulated.
- Ollama is initially deployed locally.
- Multi-tenancy is not required.
- Human-on-the-loop oversight remains mandatory for sensitive actions.

---

## 3. Security Architecture

### 3.1 Logical deployment topology

```text
                  Analyst Browser
                        |
                        | HTTPS
                        v
                 Reverse Proxy
                        |
             +----------+----------+
             |                     |
             v                     v
        React Frontend        FastAPI Backend
                                   |
                    +--------------+--------------+
                    |              |              |
                    v              v              v
               PostgreSQL        Redis         ChromaDB
                    |              |              |
                    +--------------+--------------+
                                   |
                                   v
                         Orchestration Runtime
                                   |
                          Planner + Workers
                                   |
                      Capability Execution Layer
                                   |
                      +------------+------------+
                      |            |            |
                      v            v            v
                  Detection   Investigation   Reporting
                      |
                      v
                 Ollama LLM
```

This is a logical topology. The actual container and network layout should be defined in Docker Compose and subsequently adapted if a different deployment platform is selected.

### 3.2 Trust boundaries

| Boundary | Protected assets | Main risks |
|---|---|---|
| Browser to API | Authentication tokens, requests | Unauthorized access, CSRF, XSS |
| API to database | Investigation and telemetry data | SQL injection, excessive privileges |
| API to Redis | Task coordination | Unauthorized task manipulation |
| API to ChromaDB | Knowledge retrieval | Malicious document retrieval |
| Orchestrator to workers | Task inputs and outputs | Capability misuse |
| Worker to LLM | Prompts and context | Prompt injection, data leakage |
| Worker to response layer | Proposed actions | Unauthorized containment |
| Container host to services | Runtime and secrets | Container escape, host compromise |

### 3.3 Core security rule

No AI component should receive unrestricted infrastructure privileges.

The Planner proposes work. The capability registry defines available operations. Policy validation controls execution. The executor invokes authorized capabilities. The persistence layer records outcomes.

---

## 4. Environment Separation

Project Sentinel should distinguish three environments.

| Environment | Purpose | Security posture |
|---|---|---|
| Development | Feature development and debugging | Controlled developer access |
| Testing | Automated testing and evaluation | Isolated test data and credentials |
| Demonstration | Stable project demonstration | Hardened configuration and restricted access |

Production deployment, if introduced later, requires a separate operational and security review.

### 4.1 Environment-specific controls

**Development**
- Debug logging permitted.
- Local test datasets permitted.
- Developer-only service exposure.
- Test credentials only.
- No real containment operations.

**Testing**
- Automated test identities.
- Isolated database.
- Reproducible dataset versions.
- Controlled mock external services.
- No access to demonstration data unless explicitly required.

**Demonstration**
- Debug mode disabled.
- Strong authentication.
- Restricted service ports.
- Persistent PostgreSQL storage.
- Controlled dataset access.
- Audit logging enabled.
- Response simulation only.

### 4.2 Configuration isolation

Use separate environment files:

```text
.env.development
.env.testing
.env.demo
```

These files must not be committed with secrets.

Provide `.env.example` containing variable names and safe placeholder values.

---

## 5. Secrets Management

### 5.1 Secrets inventory

| Secret | Used by | Protection requirement |
|---|---|---|
| PostgreSQL password | Backend, migrations | Never expose to frontend |
| Redis credentials | Backend, workers | Restrict network access |
| JWT signing secret | Authentication service | Strong random value |
| LLM configuration | Backend | Avoid embedding credentials in prompts |
| External API keys | Relevant integrations | Store outside source code |
| Encryption keys | Sensitive data encryption, if enabled | Separate from encrypted data |

### 5.2 Secret handling requirements

- Never hardcode credentials in Python or frontend source.
- Never commit `.env` files containing real credentials.
- Do not log passwords, tokens or API keys.
- Do not include secrets in error responses.
- Restrict filesystem permissions on secret files.
- Rotate compromised credentials immediately.
- Use different credentials for separate environments.
- Keep database credentials out of browser-visible configuration.

### 5.3 Configuration example

```env
APP_ENV=demo
DEBUG=false

DATABASE_URL=postgresql+psycopg://sentinel_app:<secret>@postgres:5432/sentinel

REDIS_URL=redis://redis:6379/0

JWT_SECRET_KEY=<strong-random-secret>

OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=<configured-model>

CHROMA_HOST=chromadb
CHROMA_PORT=8000
```

The example is illustrative. Actual variable names must match the implemented configuration module.

The application must fail safely when mandatory secrets are absent or invalid.

### 5.4 Secret validation

At startup, validate:

- Required environment variables.
- Secret length and format.
- Database connectivity.
- Redis connectivity.
- Required model configuration.
- Allowed CORS origins.
- Debug mode restrictions.

Do not silently replace missing production secrets with insecure defaults.

---

## 6. Container Security Hardening

### 6.1 Image security

All application containers should:

- Use maintained base images.
- Pin dependencies and image versions.
- Avoid unnecessary packages.
- Use non-root users.
- Exclude development tooling from runtime images.
- Avoid copying `.env` files into images.
- Use `.dockerignore`.
- Be scanned for known vulnerabilities.

Avoid floating production tags such as `latest` where reproducibility matters.

### 6.2 Non-root execution

Illustrative Dockerfile pattern:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN groupadd --system sentinel \
    && useradd --system --gid sentinel sentinel

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

RUN chown -R sentinel:sentinel /app

USER sentinel

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

This example must be adapted to the actual repository and build process.

### 6.3 Container privileges

Where supported:

- Set `read_only: true` for containers that do not require filesystem writes.
- Drop unnecessary Linux capabilities.
- Set `no-new-privileges`.
- Apply CPU and memory limits.
- Avoid privileged containers.
- Avoid Docker socket mounts.
- Restrict writable volumes.
- Use dedicated service accounts where applicable.

### 6.4 Docker Compose network isolation

Recommended logical networks:

```text
frontend_network
       |
       v
api_network
       |
       +------ PostgreSQL
       |
       +------ Redis
       |
       +------ ChromaDB
       |
       +------ Ollama
```

The database, Redis, ChromaDB and Ollama ports should not be exposed publicly.

Only the reverse proxy or explicitly required application entry point should be exposed outside the deployment network.

---

## 7. Network Security

### 7.1 External exposure

| Service | Public exposure |
|---|---|
| React frontend | Through reverse proxy |
| FastAPI | Through reverse proxy |
| PostgreSQL | No |
| Redis | No |
| ChromaDB | No |
| Ollama | No |
| Internal worker services | No |

Development access may expose additional ports locally, but this must not carry over into the demonstration configuration.

### 7.2 TLS

For any network-accessible demonstration environment:

- Terminate HTTPS at a reverse proxy.
- Redirect HTTP to HTTPS.
- Use valid TLS certificates.
- Disable obsolete TLS protocols.
- Apply appropriate security headers.
- Protect authentication cookies when cookie-based sessions are used.

For purely local development, HTTP may be used within the local machine.

### 7.3 CORS

Configure an explicit frontend origin allowlist.

Do not use unrestricted wildcard origins with credentialed requests.

Example:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_ORIGIN
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

The exact allowed methods should be reduced to the endpoints actually required.

### 7.4 Rate limiting

Apply rate limits to:

- Authentication attempts.
- Dataset upload or registration.
- Replay controls.
- Investigation creation.
- Manual Planner requests.
- Expensive AI-assisted endpoints.

Rate limits should be configurable and should distinguish normal analyst activity from expensive orchestration requests.

---

## 8. Backend Application Security

### 8.1 Authentication

The API must authenticate users before granting access to protected resources.

Authentication requirements:

- Secure password hashing if local password authentication is used.
- Token expiration.
- Token signature validation.
- Token revocation or session invalidation strategy.
- Login failure handling.
- Account activation and deactivation.
- Secure credential reset procedures if implemented.

JWTs should not contain sensitive investigation data.

### 8.2 Authorization

Use role-based access control.

| Role | Capabilities |
|---|---|
| Administrator | User management, configuration and system administration |
| SOC Analyst | View alerts, create and manage investigations, request AI analysis |
| Reviewer | Review investigations and approve or reject permitted actions |

Authorization must be enforced in the backend, not only in the React UI.

### 8.3 Resource-level authorization

For every protected endpoint, verify:

1. The user is authenticated.
2. The user has the required role or permission.
3. The requested resource exists.
4. The user is allowed to access that resource.
5. The requested state transition is valid.

An authenticated user must not automatically gain access to every investigation.

### 8.4 Input validation

Use Pydantic request schemas for:

- Dataset registration.
- Investigation creation.
- Analyst instructions.
- Task requests.
- Human-review decisions.
- Configuration changes.

Validate:

- String length.
- Numeric ranges.
- Enumerated values.
- UUID formats.
- File types and sizes.
- JSON structure.
- Nested payload depth where appropriate.

### 8.5 Error handling

Production responses must not expose:

- Database connection strings.
- Filesystem paths.
- Internal stack traces.
- Authentication secrets.
- Raw LLM prompts containing sensitive context.
- Internal service topology.

Use structured internal logs and sanitized external error messages.

---

## 9. AI and Agent Runtime Security

This is a critical area because Project Sentinel delegates analysis and execution to AI-driven components.

### 9.1 Planner privilege boundaries

The Planner must not:

- Execute arbitrary shell commands.
- Construct arbitrary SQL.
- Access Docker directly.
- Modify database schemas.
- Change security policies.
- Invoke unregistered capabilities.
- Approve its own sensitive actions.
- Bypass human review.

The Planner may propose structured tasks that pass through the capability registry and execution policy.

### 9.2 Capability authorization

Every capability should declare:

- Capability identifier.
- Version.
- Description.
- Input schema.
- Output schema.
- Risk classification.
- Required permissions.
- Allowed execution context.
- Human-approval requirement.
- Timeout.
- Retry policy.

Example:

```json
{
  "capability": "response.simulate_containment",
  "version": "1.0",
  "risk_level": "high",
  "requires_human_approval": true,
  "execution_mode": "simulation_only",
  "allowed_targets": [
    "dataset_entity"
  ]
}
```

This is an illustrative contract, not an existing registered capability.

### 9.3 Worker isolation

Workers should:

- Receive only the input needed for their task.
- Use narrowly scoped service interfaces.
- Have explicit execution timeouts.
- Have bounded memory and CPU.
- Avoid direct access to infrastructure credentials.
- Validate outputs before persistence.
- Return structured results.

A worker should not inherit the full permission set of the backend API.

### 9.4 LLM output validation

All model output must be treated as untrusted.

Before execution:

1. Parse structured output.
2. Validate against the capability input schema.
3. Check required fields.
4. Check value ranges.
5. Check resource references.
6. Apply authorization policy.
7. Check human-review requirements.
8. Persist the validated task.
9. Execute through the controlled executor.

Malformed or unauthorized model output must be rejected.

### 9.5 Prompt injection protection

Prompt injection may originate from:

- Dataset fields.
- Network payloads.
- System logs.
- Retrieved knowledge documents.
- Analyst-provided content.
- External threat intelligence.

Controls:

- Treat retrieved content as data, not instructions.
- Delimit untrusted content in prompts.
- Keep system instructions separate from retrieved context.
- Do not grant the LLM direct infrastructure access.
- Require deterministic policy validation.
- Validate all tool arguments.
- Track the source of retrieved evidence.
- Test with adversarial documents and telemetry.

### 9.6 RAG security

The knowledge retrieval subsystem must:

- Restrict ingestion to approved sources.
- Record source identity and document version.
- Track content hashes.
- Reject malformed documents.
- Detect duplicate content.
- Preserve source attribution.
- Validate retrieved content before adding it to prompts.
- Prevent untrusted documents from altering tool permissions.

A document retrieved from ChromaDB does not gain authority over the Planner or the execution policy.

---

## 10. Human Approval and Response Safety

### 10.1 MVP restriction

All response actions must remain simulated.

The response capability must not execute real:

- Firewall modifications.
- Endpoint isolation.
- Account disabling.
- Network blocking.
- Process termination.
- Production infrastructure changes.

### 10.2 Approval flow

```text
Planner proposes action
          |
          v
Capability validation
          |
          v
Risk classification
          |
          v
Human review required?
       /       \
     Yes        No
      |          |
      v          v
Review queue   Policy validation
      |
      v
Analyst decision
   /       \
Approve   Reject
   |        |
   v        v
Simulation  Record rejection
   |
   v
Persist result and audit event
```

The approval must apply to a specific action and target.

If the action changes after approval, the approval must be invalidated and a new review requested.

### 10.3 Fail-safe behavior

If the review service is unavailable:

- Do not assume approval.
- Do not execute the action.
- Preserve the proposed action.
- Mark the operation as blocked or awaiting review.
- Record the failure.

---

## 11. Database and Persistence Security

### 11.1 PostgreSQL

- Restrict database network access.
- Use parameterized queries.
- Use least-privilege credentials.
- Protect backups.
- Avoid sensitive information in JSONB metadata.
- Audit privileged changes.
- Validate migrations.
- Use short transactions.
- Apply retention policies.

### 11.2 Redis

- Keep Redis on an internal network.
- Require authentication where appropriate.
- Avoid public exposure.
- Use bounded key lifetimes for transient data.
- Avoid storing durable evidence exclusively in Redis.
- Restrict access to task and coordination keys.

### 11.3 ChromaDB

- Keep ChromaDB on an internal network.
- Restrict write operations to the ingestion service.
- Restrict collection access.
- Validate document metadata.
- Track index versions.
- Support index reconstruction.

### 11.4 Backup security

Backups should be:

- Access-controlled.
- Encrypted where appropriate.
- Stored separately from the application runtime.
- Periodically verified.
- Tested through actual restore operations.

A backup that has never been restored is not sufficient evidence of recoverability.

---

## 12. File and Dataset Security

Dataset ingestion introduces risks from malformed files, oversized inputs and hostile content.

### 12.1 File validation

Validate:

- File extension.
- Actual file format.
- File size.
- Encoding.
- Record structure.
- Column count.
- Header consistency.
- Unexpected nested data.
- Parser errors.

Do not trust the MIME type supplied by the client.

### 12.2 Storage controls

- Store uploaded files outside the public web root.
- Generate server-side storage identifiers.
- Prevent path traversal.
- Avoid executing uploaded files.
- Restrict read permissions.
- Record file checksums.
- Maintain original-file provenance.

### 12.3 Resource limits

Set limits for:

- Maximum upload size.
- Maximum number of files per dataset.
- Maximum records per ingestion batch.
- Maximum parser execution time.
- Maximum concurrent replay sessions.

The limits should be configurable according to available hardware.

---

## 13. Observability and Security Monitoring

Security monitoring must integrate with the existing observability architecture.

### 13.1 Security-relevant events

Log:

- Authentication failures.
- Authorization failures.
- Unusual request volume.
- Repeated invalid inputs.
- Dataset validation failures.
- Capability execution rejection.
- Invalid LLM output.
- Prompt-injection detection signals.
- Human approval and rejection.
- Response simulation failures.
- Database connection failures.
- Unexpected worker termination.
- Configuration changes.

### 13.2 Structured logging

Every relevant execution should carry:

- `request_id`
- `trace_id`
- `investigation_id`
- `task_id`
- `planner_run_id`

Where applicable, also include:

- `user_id`
- `capability_id`
- `model_version`
- `prompt_version`

Never include passwords, tokens or unnecessary sensitive telemetry in logs.

### 13.3 Operational metrics

Recommended metrics:

| Metric | Purpose |
|---|---|
| API request error rate | Backend health |
| Authentication failure rate | Access monitoring |
| Task queue depth | Orchestration pressure |
| Task execution failures | Worker reliability |
| Planner timeout rate | Planning reliability |
| LLM request latency | Model performance |
| Database connection usage | Persistence health |
| Redis availability | Coordination health |
| ChromaDB retrieval failures | RAG health |
| Pending human reviews | Analyst workload |
| Rejected capability executions | Policy enforcement |

Alert thresholds should be established after measuring representative workloads.

---

## 14. Dependency and Supply-Chain Security

### 14.1 Dependency management

- Pin Python dependencies.
- Use a lockfile for frontend dependencies.
- Review dependency updates.
- Remove unused libraries.
- Scan for known vulnerabilities.
- Avoid installing packages dynamically during runtime.
- Track dependency versions used in evaluation runs.

### 14.2 Image scanning

Scan Docker images for:

- Critical vulnerabilities.
- High-severity vulnerabilities.
- Outdated system packages.
- Known vulnerable application dependencies.

A finding should be assessed based on exploitability and deployment context. Do not automatically ignore a vulnerability merely because the image is used in a demonstration.

### 14.3 Software provenance

Where practical, record:

- Source commit.
- Build timestamp.
- Dependency lockfile hash.
- Container image digest.
- Model artifact checksum.
- Prompt version.
- Database migration version.

This improves reproducibility and incident investigation.

---

## 15. Secure Release Pipeline

Recommended CI/CD sequence:

```text
Source Commit
     |
     v
Static Analysis
     |
     v
Unit Tests
     |
     v
Integration Tests
     |
     v
Dependency Scan
     |
     v
Container Build
     |
     v
Container Scan
     |
     v
Migration Validation
     |
     v
Security Tests
     |
     v
Release Approval
     |
     v
Deployment
     |
     v
Health and Smoke Tests
```

### 15.1 Required checks

| Check | Release requirement |
|---|---|
| Unit tests | Pass |
| Integration tests | Pass |
| API authorization tests | Pass |
| Dependency scan | No unaccepted critical findings |
| Container scan | No unaccepted critical findings |
| Migration tests | Pass |
| Configuration validation | Pass |
| Response safety tests | Pass |
| Smoke tests | Pass |
| Backup validation | Demonstrated for the release environment |

The project may use a manual release process for the MVP, but these checks should still be run before demonstration deployment.

---

## 16. Production-Readiness Checklist

### Application security

- [ ] Debug mode disabled.
- [ ] Authentication enabled.
- [ ] Role and resource-level authorization enforced.
- [ ] CORS restricted.
- [ ] Input validation enabled.
- [ ] Error responses sanitized.
- [ ] Rate limits configured.

### Container security

- [ ] Non-root execution configured.
- [ ] Unnecessary ports removed.
- [ ] Privileged containers avoided.
- [ ] Resource limits configured.
- [ ] Images pinned.
- [ ] Container vulnerabilities scanned.
- [ ] Docker socket not mounted into application containers.

### Persistence security

- [ ] Database credentials protected.
- [ ] PostgreSQL not publicly exposed.
- [ ] Redis not publicly exposed.
- [ ] ChromaDB not publicly exposed.
- [ ] Backups created and tested.
- [ ] Migrations version-controlled.

### AI security

- [ ] Planner cannot execute arbitrary commands.
- [ ] Workers use registered capabilities.
- [ ] LLM outputs are schema-validated.
- [ ] Retrieved content is treated as untrusted.
- [ ] Prompt-injection tests pass.
- [ ] Capability permissions are enforced.
- [ ] Sensitive actions require human review.

### Response safety

- [ ] Real containment is disabled.
- [ ] Response actions are simulation-only.
- [ ] Approval is bound to the proposed action.
- [ ] Approval failure is fail-safe.
- [ ] Response decisions are audited.

### Operations

- [ ] Health checks configured.
- [ ] Structured logs enabled.
- [ ] Critical metrics exposed.
- [ ] Backup and restore tested.
- [ ] Resource limits measured.
- [ ] Failure recovery validated.

---

## 17. Security Verification Test Cases

| ID | Test | Expected result |
|---|---|---|
| SEC-01 | Access protected endpoint without authentication | Request rejected |
| SEC-02 | Analyst attempts administrator operation | Access denied |
| SEC-03 | User accesses unauthorized investigation | Access denied |
| SEC-04 | Upload malformed dataset file | Rejected safely |
| SEC-05 | Upload oversized file | Rejected or bounded |
| SEC-06 | Inject malicious instruction into dataset field | Treated as untrusted data |
| SEC-07 | LLM proposes unregistered capability | Execution rejected |
| SEC-08 | LLM returns malformed task payload | Schema validation fails |
| SEC-09 | Worker requests unauthorized operation | Policy rejects request |
| SEC-10 | Human review service unavailable | Sensitive operation remains blocked |
| SEC-11 | Attempt to invoke real containment | Not available in MVP |
| SEC-12 | Redis restarts during pending task | Task recoverable from durable state |
| SEC-13 | ChromaDB index becomes unavailable | System reports retrieval failure safely |
| SEC-14 | Database credentials missing | Application fails startup safely |
| SEC-15 | Unauthorized database port access | Connection unavailable |
| SEC-16 | Attempt to modify audit history through application role | Operation rejected |

---

## 18. Risk Register

| Risk | Impact | Mitigation |
|---|---|---|
| Prompt injection | Unauthorized or misleading agent behavior | Untrusted-context handling and policy enforcement |
| Excessive Planner authority | Unsafe execution | Capability registry and least privilege |
| Credential leakage | Infrastructure compromise | Secret management and log redaction |
| Container compromise | Host or service compromise | Non-root execution and image hardening |
| Dataset parser abuse | Resource exhaustion or application failure | Validation, limits and isolation |
| Database exposure | Data theft or tampering | Internal network and least privilege |
| Redis manipulation | Task corruption | Network restrictions and authenticated access |
| Vector poisoning | Incorrect investigation conclusions | Source validation and provenance |
| Unauthorized response | Operational disruption | Simulation-only MVP and human approval |
| Lost investigation state | Incomplete or inconsistent investigations | Durable state, checkpoints and recovery |
| Dependency vulnerability | Application compromise | Dependency scanning and controlled updates |

Risk severity should be reassessed after the actual deployment topology and threat model are finalized.

---

## 19. Implementation Roadmap

### Phase 1 — Configuration hardening

- Separate environment configurations.
- Remove hardcoded credentials.
- Validate mandatory environment variables.
- Disable debug mode in demonstration deployment.
- Restrict CORS.
- Sanitize error responses.

### Phase 2 — Container hardening

- Use non-root users.
- Pin base images.
- Remove unnecessary packages.
- Restrict service ports.
- Configure container health checks.
- Apply CPU and memory limits.

### Phase 3 — Application and access security

- Verify authentication.
- Implement resource-level authorization.
- Add rate limiting.
- Validate file uploads.
- Add security audit events.

### Phase 4 — AI execution security

- Enforce capability registry authorization.
- Validate Planner outputs.
- Restrict worker permissions.
- Implement prompt-injection tests.
- Enforce human approval for sensitive actions.

### Phase 5 — Operational readiness

- Configure structured security logs.
- Add service health checks.
- Verify database backups.
- Test Redis recovery.
- Test ChromaDB reconstruction.
- Run security verification tests.

### Phase 6 — Release validation

- Scan dependencies and images.
- Run automated tests.
- Validate migrations.
- Perform smoke tests.
- Review unresolved security findings.
- Approve demonstration deployment.

---

## 20. Definition of Done

Project Sentinel's demonstration deployment is considered security-hardened when:

1. Protected APIs require authentication.
2. Role and resource-level authorization are enforced.
3. Application secrets are externalized.
4. Infrastructure services are not publicly exposed.
5. Application containers run with restricted privileges.
6. Database writes preserve investigation integrity.
7. Planner and workers cannot bypass the capability execution layer.
8. All LLM outputs are validated before execution.
9. Untrusted dataset and RAG content cannot directly authorize operations.
10. Real response actions are disabled.
11. Sensitive actions require explicit human approval.
12. Security-relevant operations are auditable.
13. Database backups can be restored.
14. Orchestration can recover from transient service failures.
15. The release passes the security verification test suite.

---

## 21. Final Architectural Position

Project Sentinel must be treated as a security-sensitive application that happens to use autonomous AI components—not as an unrestricted AI agent with access to a cybersecurity environment.

Its security boundary must remain deterministic even when its investigation strategy is dynamic.

The governing execution model is:

**Planner proposes → Policy validates → Capability registry authorizes → Executor runs → Worker returns structured output → Persistence records → Human reviews when required.**

This separation is essential to preserving human oversight, preventing unauthorized operations, and maintaining the integrity of investigation results.

The MVP should prioritize a secure, reproducible demonstration environment over premature enterprise deployment complexity.
