# Project Sentinel — Database & Persistence Design Specification

**Document Type:** Technical Design Specification  
**Version:** 1.0  
**Status:** Architecture Baseline  
**Primary Technologies:** PostgreSQL 15 and ChromaDB  
**Primary Focus:** Operational data persistence, entity relationships, evidence traceability, investigation state, auditability, indexing, and data lifecycle management.  
**Related Components:** PostgreSQL Relational Database, SQLAlchemy ORM, Alembic Migrations, ChromaDB Vector Store, State Manager, Audit Bus

---

# 1. Purpose

Project Sentinel processes security telemetry and transforms it into:
- Normalized events.
- Detection results.
- Alerts.
- Correlated evidence.
- Investigations.
- AI-generated investigation decisions.
- Analyst actions.

This information must be stored in a structured and traceable manner. The persistence architecture supports two fundamentally different data types:

```text
STRUCTURED OPERATIONAL DATA
            │
            ▼
        PostgreSQL


SEMANTIC KNOWLEDGE VECTORS
            │
            ▼
         ChromaDB
```

> **PostgreSQL stores what happened in Project Sentinel. ChromaDB stores knowledge that helps the system interpret what may have happened.**

---

# 2. Persistence Architecture

```text
                    PROJECT SENTINEL
                           │
          ┌────────────────┴────────────────┐
          │                                 │
          ▼                                 ▼
   OPERATIONAL DATA                  KNOWLEDGE DATA
          │                                 │
          ▼                                 ▼
     PostgreSQL                         ChromaDB
          │                                 │
          ├── Events                       ├── Chunks
          ├── Alerts                       ├── Embeddings
          ├── Investigations               └── Metadata
          ├── Evidence
          ├── Agent Runs
          ├── Actions
          └── Audit Records
```

The AI Planner accesses these stores through controlled services and registered capabilities rather than direct, uncontrolled database queries.

---

# 3. Database Design Principles

1. **Traceability**: Every conclusion or state mutation links backward through ancestral UUIDs to normalized events and raw files.
2. **Separation of Concerns**: Events $\neq$ Alerts $\neq$ Investigations $\neq$ Evidence $\neq$ Knowledge Context.
3. **Auditability**: All state mutations and analyst interventions generate append-only audit records.
4. **Controlled Transactions**: Database transactions are short and isolated; transactions must never remain open during external network calls or local LLM inference loops.

---

# 4. PostgreSQL Schema Domains

```text
sentinel
│
├── ingestion      (ingestion_runs)
├── telemetry      (events, entities, event_entities)
├── detection      (detection_rules, detection_results, alerts, alert_events)
├── investigation  (investigations, investigation_evidence, investigation_hypotheses)
├── orchestration  (agent_runs, investigation_actions)
└── audit          (audit_logs)
```

---

# 5. Core Relational Schemas

```text
INGESTION RUN
      │
      ▼
    EVENT
      │
      ▼
DETECTION RESULT
      │
      ▼
    ALERT
      │
      ▼
INVESTIGATION
      │
      ├──────────► EVIDENCE
      │
      ├──────────► AGENT RUN
      │
      ├──────────► ACTION
      │
      └──────────► AUDIT RECORD
```

---

## 6. Table: `ingestion_runs`

| Field | Type | Constraints | Purpose |
|---|---|---|---|
| `id` | UUID | PRIMARY KEY | Unique ingestion run identifier |
| `source_id` | VARCHAR(128) | NOT NULL | Dataset or source identifier |
| `mode` | VARCHAR(32) | NOT NULL | `batch` or `replay` |
| `status` | VARCHAR(32) | NOT NULL | `pending`, `running`, `completed`, `failed`, `paused` |
| `started_at` | TIMESTAMP WITH TZ | NOT NULL | Start timestamp |
| `completed_at` | TIMESTAMP WITH TZ | NULL | Completion timestamp |
| `records_processed` | BIGINT | DEFAULT 0 | Total records parsed |
| `records_accepted` | BIGINT | DEFAULT 0 | Valid canonical events stored |
| `records_rejected` | BIGINT | DEFAULT 0 | Quarantined / rejected records |
| `configuration` | JSONB | NOT NULL | Replay speed, batch size, file paths |

---

## 7. Table: `events`

| Field | Type | Constraints | Purpose |
|---|---|---|---|
| `id` | UUID | PRIMARY KEY | Internal canonical event UUID |
| `ingestion_run_id` | UUID | REFERENCES `ingestion_runs(id)` | Batch run provenance |
| `source_record_id` | VARCHAR(256) | NOT NULL | Original record identifier |
| `event_timestamp` | TIMESTAMP WITH TZ | NOT NULL | Observed telemetry timestamp |
| `event_type` | VARCHAR(64) | NOT NULL | `network_connection`, `auth`, `process`, `file` |
| `host_id` | VARCHAR(128) | NULL | Normalized host entity |
| `user_id` | VARCHAR(128) | NULL | Normalized user entity |
| `process_id` | VARCHAR(128) | NULL | Normalized process entity |
| `raw_reference` | JSONB | NOT NULL | Lineage pointer (`file_name`, `line_offset`) |
| `attributes` | JSONB | NULL | Source-specific extensible telemetry fields |
| `created_at` | TIMESTAMP WITH TZ | DEFAULT NOW() | System ingestion timestamp |

---

## 8. Table: `detection_results`

| Field | Type | Constraints | Purpose |
|---|---|---|---|
| `id` | UUID | PRIMARY KEY | Detection result UUID |
| `event_id` | UUID | REFERENCES `events(id)` | Triggering canonical event |
| `rule_id` | VARCHAR(64) | NOT NULL | Triggered detection rule ID |
| `score` | FLOAT | NOT NULL | Calculated detection confidence ($0.0 - 1.0$) |
| `severity` | VARCHAR(32) | NOT NULL | `low`, `medium`, `high`, `critical` |
| `result` | VARCHAR(32) | NOT NULL | `match`, `suppressed`, `error` |
| `metadata` | JSONB | NULL | Condition match details |
| `created_at` | TIMESTAMP WITH TZ | DEFAULT NOW() | Detection timestamp |

---

## 9. Table: `alerts`

| Field | Type | Constraints | Purpose |
|---|---|---|---|
| `id` | UUID | PRIMARY KEY | Alert UUID |
| `status` | VARCHAR(32) | NOT NULL | `new`, `triaged`, `investigating`, `resolved`, `dismissed` |
| `severity` | VARCHAR(32) | NOT NULL | Normalized alert severity |
| `confidence` | FLOAT | NOT NULL | Detection confidence score |
| `title` | VARCHAR(256) | NOT NULL | Human-readable alert summary |
| `summary` | TEXT | NULL | Detailed technical description |
| `created_at` | TIMESTAMP WITH TZ | DEFAULT NOW() | Alert creation timestamp |
| `updated_at` | TIMESTAMP WITH TZ | DEFAULT NOW() | Last alert update timestamp |

### Table: `alert_events` (Many-to-Many Relationship)
| Field | Type | Constraints | Purpose |
|---|---|---|---|
| `alert_id` | UUID | REFERENCES `alerts(id)` | Alert relationship |
| `event_id` | UUID | REFERENCES `events(id)` | Associated canonical event |
| `relationship_type` | VARCHAR(64) | NOT NULL | `trigger_event`, `supporting_event`, `correlated_event` |

---

## 10. Table: `investigations`

| Field | Type | Constraints | Purpose |
|---|---|---|---|
| `id` | UUID | PRIMARY KEY | Investigation UUID |
| `alert_id` | UUID | REFERENCES `alerts(id)` | Originating security alert |
| `status` | VARCHAR(32) | NOT NULL | `created`, `active`, `waiting`, `escalated`, `completed`, `failed` |
| `priority` | VARCHAR(32) | NOT NULL | Triage priority (`P1`, `P2`, `P3`) |
| `state_version` | INTEGER | DEFAULT 1 | Optimistic concurrency version counter |
| `confidence` | FLOAT | DEFAULT 0.0 | Overall investigation confidence ($I_c$) |
| `state_snapshot` | JSONB | NOT NULL | Compact current state snapshot for fast recovery |
| `created_at` | TIMESTAMP WITH TZ | DEFAULT NOW() | Start timestamp |
| `completed_at` | TIMESTAMP WITH TZ | NULL | Completion / termination timestamp |
| `analyst_id` | UUID | NULL | Assigned human investigator |

---

## 11. Table: `investigation_evidence`

| Field | Type | Constraints | Purpose |
|---|---|---|---|
| `id` | UUID | PRIMARY KEY | Evidence UUID |
| `investigation_id` | UUID | REFERENCES `investigations(id)` | Parent investigation |
| `event_id` | UUID | REFERENCES `events(id)` | Ancestral telemetry event |
| `evidence_type` | VARCHAR(64) | NOT NULL | `telemetry`, `correlation`, `detection`, `analyst_input` |
| `claim` | TEXT | NOT NULL | Supported factual claim |
| `source_reference` | JSONB | NOT NULL | Provenance details (file, offset, capability) |
| `confidence` | FLOAT | NOT NULL | Calculated evidence score ($E_s$) |
| `created_at` | TIMESTAMP WITH TZ | DEFAULT NOW() | Collection timestamp |

> **Constraint**: External knowledge retrieved via RAG is never stored in `investigation_evidence`. It is stored as contextual reference metadata.

---

## 12. Table: `investigation_hypotheses`

| Field | Type | Constraints | Purpose |
|---|---|---|---|
| `id` | UUID | PRIMARY KEY | Hypothesis UUID |
| `investigation_id` | UUID | REFERENCES `investigations(id)` | Parent investigation |
| `hypothesis` | TEXT | NOT NULL | Statement under evaluation |
| `status` | VARCHAR(32) | NOT NULL | `active`, `supported`, `rejected`, `inconclusive` |
| `confidence` | FLOAT | DEFAULT 0.0 | Calculated hypothesis confidence ($H_c$) |
| `supporting_references` | JSONB | NULL | Array of `evidence_id` references |
| `created_at` | TIMESTAMP WITH TZ | DEFAULT NOW() | Generation timestamp |

---

## 13. Table: `agent_runs` & `investigation_actions`

### Table: `agent_runs`
Records significant Planner and worker execution cycles: `id`, `investigation_id`, `agent_type`, `status`, `started_at`, `completed_at`, `input_reference`, `output_reference`, `error_code`.

### Table: `investigation_actions`
Tracks individual capability executions requested by the Planner:
| Field | Type | Constraints | Purpose |
|---|---|---|---|
| `id` | UUID | PRIMARY KEY | Action execution UUID |
| `investigation_id` | UUID | REFERENCES `investigations(id)` | Parent investigation |
| `capability_name` | VARCHAR(64) | NOT NULL | `event_query`, `event_correlation`, etc. |
| `parameters` | JSONB | NOT NULL | Validated input parameters |
| `status` | VARCHAR(32) | NOT NULL | `planned`, `approved`, `running`, `completed`, `failed`, `cancelled` |
| `requested_by` | VARCHAR(64) | NOT NULL | `planner` or `analyst` |
| `started_at` | TIMESTAMP WITH TZ | NOT NULL | Execution start time |
| `completed_at` | TIMESTAMP WITH TZ | NULL | Execution completion time |
| `result_reference` | JSONB | NULL | Execution summary / returned references |

---

## 14. Table: `audit_logs`

Strictly append-only audit trail:
| Field | Type | Constraints | Purpose |
|---|---|---|---|
| `id` | UUID | PRIMARY KEY | Audit event UUID |
| `timestamp` | TIMESTAMP WITH TZ | DEFAULT NOW() | Event timestamp |
| `actor_type` | VARCHAR(32) | NOT NULL | `planner`, `system`, `analyst` |
| `actor_id` | VARCHAR(128) | NOT NULL | Component or user ID |
| `action` | VARCHAR(64) | NOT NULL | `investigation_created`, `action_executed`, `analyst_override` |
| `resource_type` | VARCHAR(64) | NOT NULL | `investigation`, `action`, `alert` |
| `resource_id` | UUID | NOT NULL | Affected resource UUID |
| `previous_state` | JSONB | NULL | Pre-mutation snapshot |
| `new_state` | JSONB | NULL | Post-mutation snapshot |

---

# 15. Indexing & Transaction Boundaries

### Indexes for Investigative Query Patterns:
```sql
CREATE INDEX idx_events_host_time ON events (host_id, event_timestamp);
CREATE INDEX idx_events_user_time ON events (user_id, event_timestamp);
CREATE INDEX idx_events_type_time ON events (event_type, event_timestamp);
CREATE INDEX idx_alerts_status_severity ON alerts (status, severity);
CREATE INDEX idx_investigations_status ON investigations (status);
CREATE INDEX idx_audit_resource ON audit_logs (resource_type, resource_id);
```

### Transaction Boundary Rule:
$$\text{Short Atomic DB Write} \to \text{Commit} \to \text{Long LLM / Tool Execution} \to \text{Short Atomic DB Write} \to \text{Commit}$$
Database connections are never held open across network calls or model inference.

---

# 16. Repository Architecture & ORM Layout

```text
backend/app/
├── database/
│   ├── session.py          (Async SQLAlchemy sessionmaker, pooling)
│   ├── base.py             (Base declarative class)
│   ├── models/
│   │   ├── event.py        (events, alert_events)
│   │   ├── alert.py        (alerts, detection_results)
│   │   ├── investigation.py (investigations, evidence, hypotheses)
│   │   ├── action.py       (agent_runs, investigation_actions)
│   │   └── audit.py        (audit_logs)
│   └── repositories/
│       ├── event_repo.py
│       ├── alert_repo.py
│       └── investigation_repo.py
└── migrations/             (Alembic version control scripts)
```

The AI Planner accesses persistence strictly through repositories via registered capabilities; direct SQL construction by models is forbidden.

---

# 17. Final Persistence Principle

> **Every important conclusion should be traceable backward through the system to the evidence and source data that supported it.**
