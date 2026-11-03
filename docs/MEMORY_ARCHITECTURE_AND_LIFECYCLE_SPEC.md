# Project Sentinel
# Memory Architecture & Lifecycle Specification

**Document Type:** Technical Design Specification  
**Version:** 1.0  
**Status:** Proposed Architecture  
**Primary Focus:** Investigation memory, working memory, long-term memory, retrieval, persistence, and lifecycle management

---

## 1. Purpose

This document defines the memory architecture for Project Sentinel.

The system uses multiple AI agents coordinated by a central Planner. These agents need access to relevant investigation context, previous task results, historical incidents, and security knowledge.

Without a dedicated memory architecture, agents may:

- Lose important context between tasks.
- Repeat previously completed investigation work.
- Produce inconsistent conclusions.
- Fail to recognize recurring attack patterns.
- Retrieve irrelevant historical information.
- Treat outdated or unverified conclusions as facts.

The memory subsystem addresses these problems by maintaining structured, persistent, and retrievable context.

Its purpose is not to replace the primary database, evidence store, or knowledge base.

**Core principle:** Memory provides context to the orchestration system. It does not become an independent source of truth.

## 2. Architectural Objectives

The memory subsystem must:

1. Preserve the current investigation context.
2. Maintain a history of agent tasks and results.
3. Support dynamic Planner decisions.
4. Prevent unnecessary repetition of completed tasks.
5. Support retrieval of relevant historical incidents.
6. Preserve relationships between investigations and evidence.
7. Maintain provenance and confidence information.
8. Separate operational state from reusable knowledge.
9. Support memory expiration and archival.
10. Prevent cross-investigation data leakage.
11. Support deterministic evaluation and debugging.
12. Allow future memory optimization without changing the orchestration architecture.

## 3. Memory Architecture Overview

Project Sentinel should use a layered memory architecture.

```text
                  PROJECT SENTINEL
                         |
                         v
                ORCHESTRATION ENGINE
                         |
                         v
                       PLANNER
                         |
                         v
                  MEMORY SERVICE
                         |
       +-----------------+------------------+
       |                 |                  |
       v                 v                  v
  Working Memory   Episodic Memory    Semantic Memory
       |                 |                  |
       v                 v                  v
 Current State      Past Incidents     Reusable Knowledge
       |                 |                  |
       +-----------------+------------------+
                         |
                         v
                 Retrieval Interface
                         |
                         v
                Context Construction
                         |
                         v
                 Planner / Workers
```

The architecture contains three primary memory categories:

| Memory type | Purpose | Typical lifetime |
|---|---|---|
| Working memory | Current investigation context and active task state | Investigation lifetime |
| Episodic memory | Historical investigations and previous task experiences | Long-term, subject to retention |
| Semantic memory | Reusable security knowledge and validated patterns | Long-term, versioned |

These memory categories have different ownership, update, and retention rules.

## 4. Memory Type Definitions

### 4.1 Working Memory

Working memory stores information required to perform the current investigation.

It includes:

- Investigation objective.
- Current investigation status.
- Active hypotheses.
- Confirmed findings.
- Unresolved questions.
- Evidence references.
- Completed tasks.
- Active tasks.
- Failed tasks.
- Planner decisions.
- Investigation constraints.
- Current confidence assessments.

Example:

```json
{
  "investigation_id": "INV-2026-001",
  "objective": "Investigate suspected credential compromise",
  "status": "investigating",
  "confirmed_facts": [
    "Multiple failed authentication attempts",
    "Successful authentication followed the failures"
  ],
  "hypotheses": [
    {
      "hypothesis_id": "HYP-001",
      "description": "The account may have been compromised",
      "status": "under_investigation",
      "confidence": 0.78
    }
  ],
  "unresolved_questions": [
    "Was the successful login associated with the same source?",
    "Was the account used for subsequent suspicious activity?"
  ],
  "completed_tasks": [
    "TASK-1001"
  ],
  "active_tasks": [
    "TASK-1002"
  ],
  "evidence_refs": [
    "EV-001",
    "EV-002"
  ]
}
```

Working memory must be updated after meaningful task completion or investigation-state changes.

It must not rely solely on conversational history or an LLM's context window.

### 4.2 Episodic Memory

Episodic memory stores historical investigation experiences.

It answers questions such as:

- Have we investigated a similar incident before?
- What evidence was useful in previous investigations?
- Which investigation patterns were observed?
- What actions were recommended?
- What was the final analyst-approved conclusion?
- Did a previous investigation produce a false positive?

An episodic memory record should contain:

```json
{
  "episode_id": "EP-001",
  "investigation_id": "INV-2026-001",
  "incident_type": "credential_compromise",
  "summary": "Repeated failed authentication followed by a successful login",
  "entities": {
    "accounts": ["account-reference-1"],
    "source_ips": ["192.0.2.10"]
  },
  "findings": [
    "Authentication failures preceded a successful login"
  ],
  "outcome": "analyst_confirmed_suspicious",
  "evidence_refs": [
    "EV-001",
    "EV-002"
  ],
  "created_at": "2026-08-01T10:00:00Z"
}
```

The identifiers and addresses above are illustrative.

Episodic memory should retain references to original evidence rather than duplicating all raw events.

### 4.3 Semantic Memory

Semantic memory stores reusable knowledge that is not restricted to a single investigation.

Examples:

- Security concepts.
- Attack-pattern descriptions.
- Validated investigation procedures.
- Approved response playbooks.
- Known relationships between techniques and indicators.
- Lessons learned from reviewed incidents.
- Organizational detection knowledge.

Potential sources include:

- MITRE ATT&CK.
- Sigma rules.
- CVE descriptions.
- CAPEC.
- Approved incident response playbooks.
- Analyst-approved internal knowledge.

Semantic memory is distinct from episodic memory.

An ATT&CK technique description is reusable security knowledge. A specific incident involving that technique is an episode.

### 4.4 Memory boundaries

| Information | Authoritative location | Memory representation |
|---|---|---|
| Raw dataset events | Dataset storage | References and summaries |
| Normalized security events | Event database | Relevant event references |
| Investigation status | Investigation database | Working context |
| Task execution records | Task database | Task history and summaries |
| Evidence | Evidence database | Evidence references and selected summaries |
| Historical incident | Investigation records | Episodic representation |
| ATT&CK and Sigma knowledge | Knowledge repository | Semantic representation |
| Analyst-approved lessons | Knowledge repository | Validated semantic memory |

Memory should never become the only storage location for critical operational records.

## 5. Storage Architecture

### 5.1 Technology allocation

The proposed storage allocation is:

| Technology | Responsibility |
|---|---|
| PostgreSQL | Structured memory metadata and authoritative state |
| Redis | Temporary cache and short-lived execution context |
| ChromaDB | Vector representations for semantic and episodic retrieval |
| Ollama embedding model | Vector generation |
| FastAPI Memory Service | Controlled access to memory operations |

### 5.2 PostgreSQL

PostgreSQL should store structured memory records.

Recommended tables:

```text
investigations
investigation_state
investigation_hypotheses
investigation_memory
agent_tasks
agent_task_results
memory_records
memory_entities
memory_relationships
memory_feedback
memory_versions
```

The existing investigation and task tables should remain the authoritative records for operational state.

The memory tables should store reusable representations and retrieval metadata.

### 5.3 Redis

Redis may cache:

- Current investigation summaries.
- Recently accessed evidence references.
- Frequently accessed knowledge metadata.
- Temporary Planner context.
- Short-lived retrieval results.

Redis must not be the only persistence mechanism for investigation state.

If Redis becomes unavailable, the system must be able to reconstruct necessary working context from PostgreSQL.

### 5.4 ChromaDB

ChromaDB stores vector embeddings for:

- Semantic knowledge chunks.
- Episodic investigation summaries.
- Analyst-approved lessons.
- Selected investigation notes, where justified.

Vector records must contain metadata that supports filtering and provenance.

Example:

```json
{
  "id": "MEM-001",
  "document": "Repeated failed logins followed by a successful login may warrant investigation of account compromise.",
  "metadata": {
    "memory_type": "episodic",
    "source_id": "INV-2026-001",
    "source_type": "investigation",
    "approval_status": "analyst_reviewed",
    "tenant_id": "default",
    "created_at": "2026-08-01T10:00:00Z",
    "version": 1
  }
}
```

The text and metadata are illustrative.

### 5.5 Storage consistency

PostgreSQL is the authoritative metadata store.

ChromaDB is a derived retrieval index.

If vector indexing fails after a PostgreSQL memory record is committed:

1. Preserve the PostgreSQL record.
2. Mark the vector index operation as pending.
3. Retry indexing through a background job.
4. Record the indexing outcome.
5. Avoid treating an unindexed record as deleted.

This prevents vector database availability from determining whether memory exists.

## 6. Memory Service Architecture

All memory access should pass through a dedicated service.

Agents must not directly query PostgreSQL or ChromaDB.

### 6.1 Proposed package structure

```text
backend/
└── app/
    └── memory/
        ├── service.py
        ├── manager.py
        ├── models.py
        ├── schemas.py
        ├── repository.py
        ├── retriever.py
        ├── context_builder.py
        ├── summarizer.py
        ├── lifecycle.py
        ├── policies.py
        ├── permissions.py
        ├── embeddings.py
        └── stores/
            ├── postgres.py
            ├── redis.py
            └── chroma.py
```

### 6.2 Memory service responsibilities

The service should expose operations for:

- Creating memory records.
- Updating working context.
- Retrieving investigation state.
- Searching episodic memory.
- Searching semantic memory.
- Linking evidence references.
- Updating memory confidence and approval status.
- Archiving expired records.
- Invalidating stale cache entries.
- Managing vector indexing.

### 6.3 Service interface

Example:

```python
class MemoryService:

    async def get_working_memory(
        self,
        investigation_id: str
    ):
        ...

    async def update_working_memory(
        self,
        investigation_id: str,
        update: dict
    ):
        ...

    async def search_episodic_memory(
        self,
        query: str,
        filters: dict
    ):
        ...

    async def search_semantic_memory(
        self,
        query: str,
        filters: dict
    ):
        ...

    async def store_memory(
        self,
        memory_record: dict
    ):
        ...

    async def archive_memory(
        self,
        memory_id: str
    ):
        ...
```

The implementation must enforce authorization, validation, and provenance checks.

## 7. Working Memory Lifecycle

Working memory is continuously updated during an investigation.

### 7.1 Lifecycle

```text
Investigation Created
        |
        v
Initialize Working Memory
        |
        v
Planner Reads Context
        |
        v
Specialist Task Executed
        |
        v
Task Result Validated
        |
        v
Update Investigation State
        |
        v
Update Working Memory
        |
        v
Planner Re-evaluates
        |
        +------> More Tasks
        |
        +------> Human Review
        |
        +------> Investigation Completion
                         |
                         v
                 Final Memory Snapshot
                         |
                         v
                  Episodic Extraction
```

### 7.2 Update rules

Working memory should be updated when:

- A task completes.
- New evidence is attached.
- A hypothesis changes status.
- A contradiction is discovered.
- A Planner decision is accepted.
- An analyst provides feedback.
- Investigation status changes.

### 7.3 Avoiding state conflicts

Concurrent specialist tasks may attempt to update the same investigation.

Use controlled state updates with versioning or optimistic concurrency.

Example:

```json
{
  "investigation_id": "INV-2026-001",
  "state_version": 12,
  "update_type": "task_result",
  "source_task_id": "TASK-1002",
  "changes": {
    "unresolved_questions": [
      "Was the account used for subsequent suspicious activity?"
    ]
  }
}
```

An update based on an outdated state version should be rejected or reconciled.

Do not allow concurrent workers to overwrite each other's findings silently.

## 8. Episodic Memory Creation

### 8.1 Creation trigger

Episodic memory should normally be generated when an investigation reaches a terminal state.

Terminal states may include:

- Completed.
- Closed as benign.
- Escalated.
- Closed as inconclusive.

A partial episode may be created earlier if useful, but it must be marked as provisional.

### 8.2 Extraction process

```text
Completed Investigation
        |
        v
Load Investigation Record
        |
        v
Load Validated Evidence
        |
        v
Load Analyst Feedback
        |
        v
Generate Episode Summary
        |
        v
Validate References and Claims
        |
        v
Assign Review Status
        |
        v
Persist Episodic Record
        |
        v
Generate Embedding
        |
        v
Index in ChromaDB
```

### 8.3 Episode quality requirements

An episode must preserve:

- Investigation identifier.
- Incident classification.
- Summary.
- Relevant entities.
- Evidence references.
- Findings.
- Final disposition.
- Analyst review status.
- Creation timestamp.
- Source versions.

### 8.4 Provisional and approved episodes

Use explicit approval states:

| Status | Meaning |
|---|---|
| `provisional` | Generated but not reviewed |
| `analyst_reviewed` | Reviewed by an analyst |
| `approved` | Approved for reusable knowledge extraction |
| `rejected` | Not suitable for reuse |
| `archived` | Retained but not actively retrieved |

The system should not treat every generated episode as trusted knowledge.

## 9. Semantic Memory Lifecycle

Semantic memory should be created from trusted knowledge sources or validated internal knowledge.

### 9.1 External knowledge ingestion

```text
Knowledge Source
       |
       v
Source Validation
       |
       v
Document Parsing
       |
       v
Chunking
       |
       v
Metadata Assignment
       |
       v
Embedding Generation
       |
       v
Vector Indexing
       |
       v
Retrieval Availability
```

### 9.2 Source metadata

Every semantic memory record should retain:

- Source name.
- Source identifier.
- Source URL or document reference.
- Source version.
- Publication or update date, where available.
- Ingestion timestamp.
- Chunk identifier.
- Approval or trust status.
- Applicable knowledge category.

### 9.3 Version updates

When an external knowledge source changes:

1. Detect the source version change.
2. Identify affected chunks.
3. Mark outdated records.
4. Reprocess changed content.
5. Generate new embeddings.
6. Update the vector index.
7. Preserve version history where required.

An outdated record should not remain silently active.

## 10. Memory Retrieval Architecture

### 10.1 Retrieval objectives

Memory retrieval should provide relevant information to the Planner and specialist agents without overwhelming their context windows.

Retrieval must consider:

- Semantic similarity.
- Investigation relevance.
- Source authority.
- Approval status.
- Recency.
- Entity overlap.
- Tenant and access boundaries.
- Knowledge version.

### 10.2 Retrieval workflow

```text
Planner / Agent Query
         |
         v
Query Classification
         |
         v
Select Memory Types
         |
         +----------+-----------+
         |          |           |
         v          v           v
     Working    Episodic    Semantic
     Memory     Retrieval   Retrieval
         |          |           |
         +----------+-----------+
                    |
                    v
             Candidate Results
                    |
                    v
             Metadata Filtering
                    |
                    v
             Optional Reranking
                    |
                    v
              Relevance Scoring
                    |
                    v
             Context Construction
                    |
                    v
              Planner / Agent
```

### 10.3 Query classification

The retrieval layer should identify what kind of information is required.

Examples:

| Query | Memory source |
|---|---|
| What tasks are still running? | Working memory |
| Which hypotheses remain unresolved? | Working memory |
| Have we seen a similar incident? | Episodic memory |
| What does this ATT&CK technique describe? | Semantic memory |
| What did the analyst approve previously? | Reviewed episodic memory |
| Which response playbook applies? | Semantic memory |

Query classification may initially use deterministic rules and metadata rather than an additional LLM.

### 10.4 Retrieval filtering

Retrieval must exclude:

- Records outside the caller's access scope.
- Rejected memories.
- Expired records.
- Superseded knowledge versions.
- Provisional records where the query requires approved knowledge.
- Records with invalid source references.

### 10.5 Hybrid retrieval

A future retrieval implementation may combine:

1. Vector similarity.
2. PostgreSQL metadata filtering.
3. Keyword or exact identifier search.
4. Optional reranking.

This is useful because security investigations often contain exact identifiers such as:

- IP addresses.
- Account identifiers.
- File hashes.
- CVE identifiers.
- ATT&CK technique identifiers.
- Hostnames.

Pure semantic search may not reliably retrieve exact matches.

## 11. Context Construction

Retrieval results should not be passed directly into the LLM without processing.

The Context Builder selects and formats information for the specific task.

### 11.1 Context structure

Example:

```json
{
  "investigation_context": {
    "investigation_id": "INV-2026-001",
    "objective": "Investigate suspected credential compromise",
    "status": "investigating"
  },
  "working_memory": {
    "confirmed_facts": [
      "Repeated failed authentication attempts"
    ],
    "unresolved_questions": [
      "Determine subsequent account activity"
    ]
  },
  "episodic_context": [
    {
      "episode_id": "EP-004",
      "summary": "Previously reviewed suspicious authentication sequence",
      "approval_status": "analyst_reviewed"
    }
  ],
  "semantic_context": [
    {
      "source": "MITRE ATT&CK",
      "reference": "source-reference",
      "summary": "Relevant technique description"
    }
  ],
  "evidence_references": [
    "EV-001",
    "EV-002"
  ]
}
```

### 11.2 Context prioritization

When the context budget is limited, prioritize:

1. Current investigation objective.
2. Current state and constraints.
3. Confirmed facts.
4. Relevant evidence references.
5. Unresolved questions.
6. Recent task results.
7. Relevant approved historical episodes.
8. Relevant semantic knowledge.

The system must not remove contradictory evidence merely to simplify the prompt.

### 11.3 Memory summaries

Summaries should retain references to original records.

A summary is a convenience representation, not a replacement for the source evidence.

The agent must be able to request underlying evidence when necessary.

## 12. Memory and Planner Integration

Memory directly supports the Planner's ability to make dynamic decisions.

The Planner should receive a compact investigation snapshot containing:

- Current objective.
- Investigation status.
- Confirmed findings.
- Active hypotheses.
- Unresolved questions.
- Completed and failed tasks.
- Available evidence references.
- Relevant historical context.
- Relevant security knowledge.
- Remaining execution budget.

### 12.1 Planner use cases

Memory enables the Planner to:

- Avoid repeating completed tasks.
- Recognize previously investigated patterns.
- Identify missing evidence.
- Revisit an earlier hypothesis when new evidence appears.
- Compare current findings with reviewed historical incidents.
- Use relevant playbooks when selecting capabilities.
- Recognize when investigation is sufficiently complete.

### 12.2 Planner decision example

Suppose the investigation has:

- Multiple failed authentication events.
- A successful authentication event.
- No evidence yet of subsequent account activity.
- A previous task that already correlated source addresses.

The Planner should not repeat the same correlation task without a reason.

It may instead request an event search for subsequent account activity.

Memory therefore improves planning efficiency.

### 12.3 Memory is not an authority

Historical memory must not override current evidence.

If a previous incident resembles the current incident, that similarity is a reason to investigate—not proof that the incidents share the same cause.

The Planner must distinguish:

- Current observed evidence.
- Historical observations.
- Reusable security knowledge.
- Model-generated hypotheses.

## 13. Memory Confidence and Trust

Each memory record should have explicit provenance and trust metadata.

Suggested fields:

```json
{
  "memory_id": "MEM-1001",
  "memory_type": "episodic",
  "source_type": "investigation",
  "source_id": "INV-2026-001",
  "approval_status": "analyst_reviewed",
  "confidence": 0.91,
  "created_at": "2026-08-01T10:00:00Z",
  "last_verified_at": "2026-08-01T10:00:00Z",
  "version": 1
}
```

Confidence must not be treated as equivalent to truth.

For example:

- A high-confidence LLM summary is still model-generated.
- An analyst-reviewed finding has a different trust status.
- An authoritative external knowledge source may have a higher source-authority level.
- A provisional memory should remain provisional even if its similarity score is high.

Trust status and relevance score must be stored separately.

## 14. Memory Isolation and Security

Memory may contain sensitive investigation details.

Access must be scoped by:

- User permissions.
- Investigation permissions.
- Tenant or organization.
- Data classification.
- Source restrictions.

### 14.1 Isolation requirements

- One investigation must not retrieve another investigation's restricted working memory.
- Episodic retrieval must respect access controls.
- Semantic knowledge may have different visibility from incident records.
- Cached records must retain authorization context.
- Vector search results must be checked against authoritative metadata permissions.
- Deleting or archiving a record must propagate to retrieval indexes according to policy.

### 14.2 Prompt injection

Memory records may contain attacker-controlled content copied from logs, emails, files, or other evidence.

Treat retrieved memory as untrusted data unless its provenance and approval status establish otherwise.

The system must:

- Separate retrieved content from instructions.
- Prevent memory content from changing tool permissions.
- Validate generated plans.
- Retain source references.
- Avoid executing instructions found inside historical records.

### 14.3 Audit

Record:

- Memory creation.
- Memory update.
- Memory retrieval.
- Memory approval or rejection.
- Memory archival.
- Memory deletion.
- Access denial.

Audit records should include actor, timestamp, memory identifier, and operation.

## 15. Memory Lifecycle and Retention

### 15.1 Lifecycle states

```text
Created
   |
   v
Validated
   |
   v
Active
   |
   +------> Updated
   |           |
   |           v
   |        Revalidated
   |
   v
Archived
   |
   v
Deleted / Retained According to Policy
```

### 15.2 Retention categories

| Memory category | Proposed retention approach |
|---|---|
| Working memory | Retain throughout active investigation |
| Completed investigation snapshot | Retain according to investigation policy |
| Episodic memory | Retain according to organizational retention policy |
| Semantic memory | Retain while source/version remains valid |
| Temporary Redis cache | Short TTL, configurable |
| Rejected memory | Retain for audit or delete under policy |

Exact retention periods must be decided according to project deployment requirements and applicable organizational policy. They should not be hardcoded into application logic.

### 15.3 Archival

Archived memory should:

- Remain available for audit if policy requires.
- Be excluded from normal retrieval by default.
- Retain provenance and version metadata.
- Be recoverable only through authorized operations.

### 15.4 Deletion

Deletion should cover all representations:

1. PostgreSQL memory record.
2. ChromaDB vector entry.
3. Redis cache entry.
4. Derived summaries where applicable.
5. Search indexes or secondary copies.

The operation should be auditable.

Where regulatory or operational requirements demand retention, use controlled archival rather than deletion.

## 16. Memory Data Model

### 16.1 Core memory record

Suggested relational structure:

```sql
CREATE TABLE memory_records (
    id UUID PRIMARY KEY,
    memory_type VARCHAR(30) NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    source_id VARCHAR(255) NOT NULL,
    title TEXT,
    summary TEXT NOT NULL,
    content JSONB,
    approval_status VARCHAR(30) NOT NULL,
    confidence NUMERIC(4,3),
    tenant_id VARCHAR(100) NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_verified_at TIMESTAMPTZ,
    archived_at TIMESTAMPTZ
);
```

### 16.2 Memory relationships

A memory record may reference:

- An investigation.
- One or more evidence records.
- A task.
- A knowledge source.
- An entity.
- Another memory record.

Suggested relationship table:

```sql
CREATE TABLE memory_relationships (
    id UUID PRIMARY KEY,
    source_memory_id UUID NOT NULL
        REFERENCES memory_records(id),
    target_type VARCHAR(50) NOT NULL,
    target_id VARCHAR(255) NOT NULL,
    relationship_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

The database schema should be reconciled with the existing project schema before implementation to avoid duplicating investigation or evidence tables.

### 16.3 Memory feedback

Analyst feedback can improve memory quality.

Suggested structure:

```sql
CREATE TABLE memory_feedback (
    id UUID PRIMARY KEY,
    memory_id UUID NOT NULL
        REFERENCES memory_records(id),
    analyst_id VARCHAR(255) NOT NULL,
    feedback_type VARCHAR(30) NOT NULL,
    comments TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Feedback types may include:

- `approve`
- `reject`
- `correct`
- `outdated`
- `irrelevant`

## 17. Memory Evaluation

Memory must be evaluated independently and as part of end-to-end orchestration.

### 17.1 Retrieval quality

| Metric | Purpose |
|---|---|
| Recall@K | Measures whether relevant memories are retrieved |
| Precision@K | Measures relevance among retrieved memories |
| MRR | Measures rank of the first relevant result |
| nDCG@K | Measures ranking quality |
| Retrieval latency | Measures retrieval overhead |

### 17.2 Memory utility

| Metric | Purpose |
|---|---|
| Repeated task rate | Measures unnecessary repetition |
| Context completeness | Measures whether required investigation context is supplied |
| Historical relevance | Measures usefulness of retrieved episodes |
| Stale memory rate | Measures retrieval of outdated records |
| Unsupported memory claim rate | Measures conclusions based on unsupported memories |
| Memory-assisted task success | Measures task performance with memory |
| Memory retrieval overhead | Measures time added by memory operations |

### 17.3 Planner improvement

Compare:

- Planner without episodic memory.
- Planner with episodic memory.
- Planner with semantic memory.
- Planner with both episodic and semantic memory.

Measure:

- Task selection quality.
- Repeated task reduction.
- Investigation completion.
- Evidence completeness.
- Planning latency.
- Unsupported conclusions.

Memory should only be considered beneficial if the improvement is measurable without unacceptable increases in latency or false assumptions.

### 17.4 Ablation testing

Recommended experiments:

| Experiment | Comparison |
|---|---|
| Working memory | Persisted state vs limited conversational context |
| Episodic memory | No historical episodes vs historical retrieval |
| Semantic memory | No knowledge retrieval vs semantic retrieval |
| Approval filtering | All episodes vs approved-only episodes |
| Context construction | Raw retrieval results vs prioritized context |
| Hybrid retrieval | Vector-only vs vector plus metadata/keyword filtering |

### 17.5 Proposed acceptance targets

These are provisional project targets, not measured results or universal industry standards.

| Metric | Initial target |
|---|---:|
| Working memory recovery after restart | 100% for persisted state |
| Unauthorized cross-investigation retrieval | 0 |
| Memory record provenance completeness | 100% |
| Valid memory schema rate | ≥ 98% |
| Retrieval Recall@K | ≥ 0.85 |
| Stale memory retrieval rate | ≤ 0.05 |
| Repeated task reduction | Demonstrable improvement over baseline |

Targets should be recalibrated after the evaluation dataset and workload are finalized.

## 18. Observability and Diagnostics

Memory operations must be observable.

Record:

- `investigation_id`
- `task_id`
- `memory_id`
- `memory_type`
- `retrieval_query_id`
- `retrieval_latency_ms`
- `results_count`
- `filtered_results_count`
- `embedding_model_version`
- `index_version`
- `approval_filter`
- `cache_hit`
- `operation_status`

Sensitive memory content should not be copied into routine operational logs.

### 18.1 Suggested metrics

```text
sentinel_memory_reads_total
sentinel_memory_writes_total
sentinel_memory_retrieval_latency_seconds
sentinel_memory_retrieval_results
sentinel_memory_indexing_failures_total
sentinel_memory_cache_hits_total
sentinel_memory_stale_records_total
sentinel_memory_access_denied_total
```

These metrics should be integrated into the existing observability architecture.

## 19. Failure Handling

### 19.1 ChromaDB unavailable

- Continue using PostgreSQL-backed working memory.
- Disable vector retrieval temporarily.
- Preserve pending indexing operations.
- Retry indexing after recovery.
- Do not discard completed investigation state.

### 19.2 Redis unavailable

- Read working state from PostgreSQL.
- Continue without cache.
- Restore cache gradually after recovery.

### 19.3 Embedding model unavailable

- Preserve memory records in PostgreSQL.
- Queue embedding operations.
- Avoid marking the memory record as fully indexed.
- Resume indexing when the model is available.

### 19.4 Invalid or contradictory memory

- Preserve the original source.
- Mark the affected memory for review.
- Avoid treating it as approved knowledge.
- Notify the relevant investigation workflow where appropriate.

### 19.5 Memory retrieval failure

The Planner should be able to continue using authoritative current investigation state.

Historical memory retrieval is an enhancement, not a prerequisite for safe execution.

## 20. Implementation Roadmap

### Phase 1 — Working memory

- Define working-memory schemas.
- Integrate investigation state with PostgreSQL.
- Add versioned updates.
- Implement Memory Service.
- Add restart recovery tests.

### Phase 2 — Episodic memory

- Define episode schema.
- Generate investigation summaries.
- Preserve evidence references.
- Implement approval states.
- Add episodic retrieval.

### Phase 3 — Semantic memory

- Integrate approved security knowledge sources.
- Implement document parsing and chunking.
- Generate embeddings.
- Store vectors in ChromaDB.
- Add metadata filtering and source versioning.

### Phase 4 — Context construction

- Implement query classification.
- Build context prioritization.
- Integrate memory with Planner.
- Integrate selected retrieval with specialist agents.
- Add context budget controls.

### Phase 5 — Lifecycle and security

- Implement retention policies.
- Add archival and deletion.
- Enforce investigation and tenant isolation.
- Add audit records.
- Test prompt-injection handling.

### Phase 6 — Evaluation and optimization

- Create memory retrieval test sets.
- Measure retrieval quality.
- Run memory ablation experiments.
- Measure repeated task reduction.
- Optimize indexing and retrieval.
- Establish production retention and monitoring policies.

## 21. Acceptance Criteria

| ID | Acceptance criterion |
|---|---|
| MEM-01 | Working memory is persisted independently of the LLM context window |
| MEM-02 | Working memory can be reconstructed after application restart |
| MEM-03 | Investigation state updates support version control or concurrency protection |
| MEM-04 | Episodic memory preserves investigation provenance |
| MEM-05 | Semantic memory preserves source and version metadata |
| MEM-06 | Memory access is mediated by Memory Service |
| MEM-07 | Agents cannot bypass memory access permissions |
| MEM-08 | Retrieval supports memory-type and metadata filtering |
| MEM-09 | Provisional and rejected memories can be excluded |
| MEM-10 | Context construction preserves evidence references |
| MEM-11 | Historical memory cannot override current evidence |
| MEM-12 | ChromaDB failure does not destroy authoritative memory |
| MEM-13 | Embedding model and index versions are tracked |
| MEM-14 | Memory operations are observable and auditable |
| MEM-15 | Memory retrieval respects investigation and tenant boundaries |
| MEM-16 | Retention and deletion policies cover derived representations |
| MEM-17 | Memory utility is measured through controlled evaluation |

## 22. Key Architectural Decisions

| Decision | MVP position |
|---|---|
| Memory architecture | Working, episodic, and semantic |
| Authoritative operational storage | PostgreSQL |
| Temporary cache | Redis |
| Vector retrieval | ChromaDB |
| Embedding generation | Dedicated embedding model |
| Working memory updates | Controlled orchestration state updates |
| Episodic creation | At investigation completion |
| Episode approval | Explicit analyst review status |
| Semantic knowledge | Trusted, versioned sources |
| Memory retrieval | Hybrid architecture, introduced incrementally |
| Context construction | Dedicated Memory Context Builder |
| Memory access | Through Memory Service |
| Historical memory authority | Advisory, never overriding current evidence |
| Retention | Policy-driven and configurable |

## 23. Final Architectural Position

Project Sentinel's memory system should be treated as a controlled context and knowledge subsystem.

Its most important responsibility is to help the Planner make better decisions using current investigation state and relevant historical experience.

The three memory categories serve distinct purposes:

- **Working memory** maintains the current investigation.
- **Episodic memory** preserves previous investigation experiences.
- **Semantic memory** provides reusable security knowledge.

PostgreSQL remains authoritative for structured state, while Redis and ChromaDB provide supporting cache and retrieval capabilities.

The system must preserve provenance, enforce access boundaries, distinguish provisional from approved information, and prevent historical similarity from being mistaken for current evidence.

The goal is not to give agents unlimited memory. It is to give them the right information, at the right time, with enough provenance to use it safely.
