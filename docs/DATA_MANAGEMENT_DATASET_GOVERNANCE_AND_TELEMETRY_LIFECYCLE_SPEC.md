# Project Sentinel
# Data Management, Dataset Governance & Telemetry Lifecycle Specification

**Document Type:** Data Architecture and Governance Specification  
**Version:** 1.0  
**Status:** Architecture Baseline  
**Primary Focus:** Dataset management, telemetry lifecycle, data schemas, normalization, storage, provenance, ground truth, reproducibility, and evidence traceability.

---

# 1. Purpose

Project Sentinel is an AI-assisted security investigation platform. Every major capability depends on data:

- Detection requires telemetry.
- Alerts are derived from telemetry.
- Agents investigate alerts using evidence.
- Retrieval systems provide contextual knowledge.
- Evaluation requires known scenarios and expected outcomes.

Therefore, the data architecture must answer a fundamental question:

> **Where did this information come from, how was it transformed, and how did it influence the final investigation outcome?**

The complete data lifecycle is:

```text
RAW DATASET
    │
    ▼
DATASET REGISTRATION
    │
    ▼
VALIDATION
    │
    ▼
INGESTION
    │
    ▼
NORMALIZATION
    │
    ▼
DETECTION
    │
    ▼
ALERT
    │
    ▼
INVESTIGATION
    │
    ▼
EVIDENCE
    │
    ▼
FINAL OUTCOME
    │
    ▼
EVALUATION
```

The objective is not merely to store security logs. The objective is to maintain a **traceable and reproducible chain of information**.

---

# 2. Data Architecture Principles

The Project Sentinel data layer should follow the following principles.

## 2.1 Preserve Source Data

Raw source data should remain unchanged.

```text
RAW DATA
   │
   ├── Preserved
   │
   ▼
TRANSFORMATION PIPELINE
```

The system should not overwrite the original dataset during normalization.

---

## 2.2 Maintain Provenance

Every important derived record should be traceable to its source.

For example:

```text
RAW EVENT
    │
    ▼
NORMALIZED EVENT
    │
    ▼
DETECTION RESULT
    │
    ▼
ALERT
    │
    ▼
EVIDENCE
```

Each stage should preserve relevant identifiers.

---

## 2.3 Separate Data Types

The system handles different categories of data.

| Data Category | Purpose |
|---|---|
| Raw Telemetry | Original source events |
| Normalized Telemetry | Standardized events |
| Detection Data | Detection outputs |
| Investigation Data | Workflow and agent state |
| Evidence | Supporting investigation artifacts |
| Knowledge Data | Documents used for retrieval |
| Evaluation Data | Ground truth and expected outcomes |

These categories should not be treated as one undifferentiated data store.

---

## 2.4 Reproducibility

A previous evaluation should be reproducible.

The following information should be recorded where practical:

```text
Dataset Version
Normalization Version
Detection Version
Scenario Version
Model Configuration
Evaluation Configuration
```

This prevents ambiguous results.

---

# 3. Complete Telemetry Lifecycle

The complete lifecycle has eight major stages.

```text
┌───────────────────┐
│ 1. SOURCE DATA    │
└─────────┬─────────┘
          ▼
┌───────────────────┐
│ 2. REGISTRATION   │
└─────────┬─────────┘
          ▼
┌───────────────────┐
│ 3. VALIDATION     │
└─────────┬─────────┘
          ▼
┌───────────────────┐
│ 4. NORMALIZATION  │
└─────────┬─────────┘
          ▼
┌───────────────────┐
│ 5. DETECTION      │
└─────────┬─────────┘
          ▼
┌───────────────────┐
│ 6. INVESTIGATION  │
└─────────┬─────────┘
          ▼
┌───────────────────┐
│ 7. EVIDENCE       │
└─────────┬─────────┘
          ▼
┌───────────────────┐
│ 8. EVALUATION     │
└───────────────────┘
```

Each stage has a defined responsibility.

---

# 4. Dataset Registration

Before a dataset enters the system, it should be registered.

The registration record provides basic metadata.

## 4.1 Dataset Metadata Schema

```text
dataset_id
dataset_name
dataset_source
dataset_version
format
description
acquired_at
registered_at
checksum
```

### Purpose of Important Fields

| Field | Purpose |
|---|---|
| dataset_id | Internal unique identifier |
| dataset_source | Origin of the data |
| dataset_version | Reproducibility |
| format | Parser selection |
| checksum | Integrity verification |

---

# 5. Raw Dataset Storage

Raw datasets should be preserved separately from application data.

Recommended conceptual structure:

```text
data/
│
├── raw/
│   └── <dataset-version>/
│
├── processed/
│   └── <normalization-version>/
│
└── evaluation/
    └── <scenario-version>/
```

The exact physical implementation can vary.

The important principle is:

> **Raw source data should not be silently modified by downstream processing.**

---

# 6. Raw Telemetry Ingestion

The ingestion layer reads data from the selected source.

For the MVP, ingestion should primarily support **batch or replay-based processing**.

The flow is:

```text
DATASET FILE
     │
     ▼
INGESTION READER
     │
     ▼
RAW EVENT
     │
     ▼
VALIDATION
```

This approach is recommended for the initial implementation because it provides:

- Repeatable experiments.
- Controlled testing.
- Easier debugging.
- Deterministic scenario replay.

A streaming architecture can remain a future extension.

---

# 7. Input Validation

Every incoming event should be validated before entering the normalized pipeline.

Validation should check:

- Required structure.
- Valid data types.
- Timestamp format where available.
- Source identifiers.
- Parser compatibility.

The validation flow is:

```text
RAW EVENT
    │
    ▼
SCHEMA CHECK
    │
 ┌──┴───────┐
 │          │
VALID      INVALID
 │          │
 ▼          ▼
NORMALIZE   REJECT / QUARANTINE
```

Invalid events should not silently enter the investigation pipeline.

---

# 8. Invalid Event Handling

Invalid telemetry should be recorded for diagnostic purposes.

A conceptual invalid-event record may contain:

```text
invalid_event_id
dataset_id
source_reference
validation_error
received_at
```

The raw event may be retained according to the dataset and storage policy.

The objective is to distinguish:

```text
DATA QUALITY FAILURE
```

from:

```text
APPLICATION PROCESSING FAILURE
```

---

# 9. Canonical Event Model

Different telemetry sources can have different field structures.

Project Sentinel should use a canonical internal event representation.

The conceptual transformation is:

```text
SOURCE FORMAT A ──┐
                 │
SOURCE FORMAT B ──┼──► NORMALIZATION ──► CANONICAL EVENT
                 │
SOURCE FORMAT C ──┘
```

The MVP does not need to support every telemetry format.

It should establish one reliable canonical model that can be extended later.

---

# 10. Canonical Event Schema

A recommended baseline schema is:

```text
event_id
source_event_id
dataset_id

timestamp
event_type
event_category

host_id
host_name

user_id
user_name

process_id
process_name
parent_process_id
parent_process_name

network_source_ip
network_destination_ip
network_destination_port

command_line

raw_event_reference

normalized_at
normalization_version
```

Not every event will contain every field.

Missing fields should be represented consistently rather than fabricated.

---

# 11. Event Categories

The canonical model should classify events broadly.

Recommended categories include:

```text
PROCESS
NETWORK
AUTHENTICATION
FILE
SYSTEM
OTHER
```

Example:

```text
event_type = PROCESS_CREATE
event_category = PROCESS
```

This helps detection and agent reasoning operate on consistent concepts.

---

# 12. Normalization Pipeline

Normalization transforms source telemetry into the canonical representation.

```text
RAW EVENT
    │
    ▼
SOURCE PARSER
    │
    ▼
FIELD EXTRACTION
    │
    ▼
FIELD MAPPING
    │
    ▼
CANONICAL EVENT
```

The normalizer should not contain detection logic.

Its responsibility is to answer:

> **What happened according to this telemetry source?**

Detection answers a separate question:

> **Is this behavior suspicious?**

This separation improves maintainability.

---

# 13. Normalization Versioning

Normalization logic may change as the project evolves.

Therefore, processed data should record:

```text
normalization_version
normalized_at
```

This allows evaluation results to identify which transformation logic was used.

---

# 14. Normalized Event Storage

Normalized events can be stored according to access requirements.

The logical relationship is:

```text
RAW DATA
   │
   ▼
NORMALIZED EVENTS
   │
   ├── Detection Access
   ├── Investigation Access
   └── Evaluation Access
```

The implementation should avoid unnecessary duplication while maintaining source traceability.

---

# 15. Detection Data Lifecycle

Detection consumes normalized events.

```text
NORMALIZED EVENT
       │
       ▼
DETECTION ENGINE
       │
       ▼
DETECTION RESULT
```

A detection result should preserve references to the event or events that produced it.

---

# 16. Detection Result Schema

A conceptual detection result contains:

```text
detection_id
event_references
detector_id
detector_version

detection_type
severity
confidence

created_at
```

### Important Principle

The detection result should identify:

1. **What generated the result?**
2. **Which events contributed to it?**
3. **Which detector version was used?**

This supports debugging and evaluation.

---

# 17. Alert Creation

Not every detection result necessarily requires the same response.

The alerting layer creates an investigation-relevant object.

```text
DETECTION RESULT
       │
       ▼
ALERT DECISION
       │
   ┌───┴────┐
   │        │
IGNORE    CREATE ALERT
            │
            ▼
      INVESTIGATION
```

The alert represents the point where the security investigation workflow begins.

---

# 18. Alert Schema

A baseline alert structure may include:

```text
alert_id
detection_id
title
description
severity
confidence
status

created_at
updated_at

source_event_references
```

The alert should preserve links to the detection result rather than copying all telemetry unnecessarily.

---

# 19. Investigation Data Lifecycle

When an alert starts an investigation:

```text
ALERT
   │
   ▼
INVESTIGATION CREATED
   │
   ▼
ORCHESTRATION STATE
   │
   ▼
AGENT TASKS
   │
   ▼
EVIDENCE
   │
   ▼
OUTCOME
```

Investigation state is application data and should be stored separately from raw telemetry.

---

# 20. Investigation Record

A conceptual investigation schema is:

```text
investigation_id
alert_id

status
priority

started_at
completed_at

orchestration_version
configuration_version
```

The investigation record represents the parent object for all investigation activity.

---

# 21. Evidence Lifecycle

Evidence is a critical architectural concept.

Evidence should not simply be unstructured text generated by an AI model.

The preferred flow is:

```text
TELEMETRY
    │
    ▼
AGENT / CAPABILITY
    │
    ▼
EVIDENCE ARTIFACT
    │
    ▼
VALIDATION
    │
    ▼
INVESTIGATION CONTEXT
```

Each evidence artifact should have a source.

---

# 22. Evidence Schema

A recommended evidence model includes:

```text
evidence_id
investigation_id

evidence_type
content_reference
summary

source_type
source_reference

collected_by
collected_at

relevance_score
confidence
```

The `source_reference` is particularly important.

It should allow the system to trace the evidence back to:

- A telemetry event.
- A database query.
- A retrieval result.
- A capability execution.

---

# 23. Evidence Provenance

The provenance chain should be visible.

Example:

```text
RAW EVENT #1042
      │
      ▼
NORMALIZED EVENT #NE-1042
      │
      ▼
DETECTION #D-45
      │
      ▼
ALERT #A-19
      │
      ▼
EVIDENCE #E-88
```

An analyst should be able to understand why evidence exists.

AI-generated summaries should not replace the original source reference.

---

# 24. Agent Data Access

Agents should not receive unrestricted database access.

The preferred model is:

```text
AGENT
  │
  ▼
CAPABILITY REQUEST
  │
  ▼
CONTROLLED DATA ACCESS
  │
  ▼
RESULT
```

This provides:

- Access control.
- Validation.
- Auditability.
- Consistent data interfaces.

---

# 25. Agent Context Data

An agent investigation context may contain:

```text
investigation_id
alert_summary
relevant_evidence
current_hypotheses
previous_agent_results
allowed_capabilities
```

The context should be constructed deliberately.

Sending all raw telemetry directly to an AI model is inefficient and difficult to control.

---

# 26. Knowledge Data Lifecycle

Project Sentinel may use retrieval-augmented generation for security knowledge.

The knowledge lifecycle is:

```text
KNOWLEDGE DOCUMENT
       │
       ▼
DOCUMENT VALIDATION
       │
       ▼
CHUNKING
       │
       ▼
EMBEDDING
       │
       ▼
VECTOR STORAGE
       │
       ▼
RETRIEVAL
       │
       ▼
AGENT CONTEXT
```

Knowledge data should remain logically separate from security telemetry.

---

# 27. Knowledge Document Metadata

Each indexed document should maintain metadata.

Recommended fields include:

```text
document_id
document_name
source
version

indexed_at
chunking_version
embedding_model
```

This allows retrieval behavior to be understood and reproduced.

---

# 28. Vector Data Governance

The vector store should contain information necessary for retrieval.

However, ChromaDB should not automatically become the system of record for all application data.

The recommended separation is:

```text
POSTGRESQL
    │
    ├── System Records
    ├── Investigations
    └── Metadata

CHROMADB
    │
    └── Retrieval Embeddings
```

This gives each database a clear responsibility.

---

# 29. Ground Truth Management

Evaluation requires known expected results.

Ground truth should be managed explicitly.

A scenario record may contain:

```text
scenario_id
scenario_name
dataset_version

event_references
expected_detection
expected_evidence
expected_outcome
```

The expected result should be defined independently of the final system output.

---

# 30. Scenario Extraction

A large dataset should be converted into manageable evaluation scenarios.

The process is:

```text
FULL DATASET
     │
     ▼
SELECT RELEVANT TIME RANGE
     │
     ▼
IDENTIFY SCENARIO EVENTS
     │
     ▼
CREATE SCENARIO DEFINITION
     │
     ▼
REPLAY SCENARIO
```

This makes the project manageable while preserving a connection to the original dataset.

---

# 31. Evaluation Dataset Structure

A recommended logical structure is:

```text
evaluation/
│
├── scenarios/
│   ├── scenario_01/
│   ├── scenario_02/
│   └── scenario_03/
│
└── ground_truth/
    ├── scenario_01.json
    ├── scenario_02.json
    └── scenario_03.json
```

Each scenario should be independently reproducible.

---

# 32. Dataset Versioning

Every evaluation should identify the exact data version used.

The evaluation record should contain:

```text
dataset_id
dataset_version
scenario_id
normalization_version
detection_version
```

This prevents confusion when data processing logic changes.

---

# 33. Data Reproducibility Model

A complete result should be traceable through:

```text
RESULT
  │
  ▼
INVESTIGATION VERSION
  │
  ▼
DETECTION VERSION
  │
  ▼
NORMALIZATION VERSION
  │
  ▼
DATASET VERSION
```

This is essential for technically defensible evaluation.

---

# 34. Data Retention Principles

For the MVP, data retention can remain simple.

The conceptual policy is:

| Data Type | Retention Priority |
|---|---|
| Raw Dataset | Preserve source copy |
| Evaluation Data | Preserve |
| Investigation Records | Preserve |
| Evidence | Preserve |
| Temporary Cache | Re-creatable |

The actual retention duration depends on storage constraints and project requirements.

---

# 35. Sensitive Data Considerations

Security telemetry may contain:

- User identifiers.
- Host information.
- IP addresses.
- Command-line values.

The project should avoid exposing unnecessary raw telemetry through the frontend or AI context.

The principle is:

```text
DATA ACCESS
    │
    ▼
ONLY WHAT IS REQUIRED
```

This supports both security and efficient agent operation.

---

# 36. Data Access Boundaries

The recommended access architecture is:

```text
                     FRONTEND
                         │
                         ▼
                        API
                         │
              ┌──────────┼──────────┐
              │          │          │
              ▼          ▼          ▼
        APPLICATION   ORCHESTRATOR  RETRIEVAL
              │          │          │
              ▼          ▼          ▼
          POSTGRES    CAPABILITIES CHROMADB
```

Direct frontend access to infrastructure databases should be avoided.

---

# 37. Data Quality Metrics

The data pipeline should track basic quality indicators.

Examples include:

### Validation Success Rate

\[
ValidationSuccessRate =
\frac{ValidEvents}{TotalEvents}
\]

### Normalization Success Rate

\[
NormalizationSuccessRate =
\frac{SuccessfullyNormalizedEvents}{ValidEvents}
\]

These metrics help distinguish poor input data from processing problems.

---

# 38. Data Pipeline Failure Handling

A failed event should not necessarily stop the entire dataset replay.

Recommended behavior:

```text
EVENT
  │
  ▼
PROCESSING
  │
 ┌┴──────────┐
 │           │
SUCCESS     FAILURE
 │           │
 ▼           ▼
CONTINUE   QUARANTINE
             │
             ▼
       RECORD ERROR
```

The failure policy should depend on the severity of the data issue.

---

# 39. Auditability

Important data transformations should be observable.

The system should be able to answer:

- Which dataset was used?
- Which event produced this alert?
- Which evidence supported this conclusion?
- Which agent collected the evidence?
- Which system version performed the evaluation?

This is the core auditability chain:

```text
DATA
 │
 ▼
PROCESSING
 │
 ▼
DECISION
 │
 ▼
OUTCOME
```

---

# 40. Data Management Acceptance Criteria

The data architecture baseline is complete when:

### Dataset Management

- Datasets are registered with metadata.
- Source versions can be identified.
- Raw data remains separate from derived data.

### Telemetry Processing

- Events are validated.
- A canonical event model exists.
- Normalization is versioned.
- Invalid events are handled safely.

### Detection

- Detection results reference source events.
- Detector versions can be identified.

### Investigation

- Alerts initiate traceable investigations.
- Evidence maintains source provenance.
- Investigation data remains separate from raw telemetry.

### Agent Orchestration

- Agents receive controlled context.
- Data access occurs through defined capabilities.
- Agent results can be traced.

### Evaluation

- Scenarios have defined ground truth.
- Dataset versions are recorded.
- Evaluations are reproducible.

---

# 41. Complete Data Architecture

The complete Project Sentinel data architecture is:

```text
                         ┌─────────────────┐
                         │  RAW DATASET    │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ DATA REGISTRY   │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ VALIDATION      │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ NORMALIZATION   │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ DETECTION       │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ ALERT           │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ ORCHESTRATION   │
                         └────────┬────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
                 AGENTS      CAPABILITIES   KNOWLEDGE
                    │             │             │
                    └─────────────┼─────────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ EVIDENCE        │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ FINAL OUTCOME   │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ EVALUATION      │
                         └─────────────────┘
```

---

# 42. Final Design Principle

The data architecture should support the core intelligence of Project Sentinel rather than becoming an isolated storage layer.

The central principle is:

```text
TRUSTED SOURCE DATA
        +
CONTROLLED TRANSFORMATION
        +
CLEAR PROVENANCE
        +
AGENT-READY CONTEXT
        +
REPRODUCIBLE EVALUATION
        =
TRUSTWORTHY INVESTIGATION RESULTS
```

For Project Sentinel, the most important outcome is a complete chain of traceability:

> **Dataset → Event → Detection → Alert → Investigation → Evidence → Decision → Evaluation**

This chain ensures that the AI agent orchestration layer operates on controlled information and that every significant conclusion can be connected back to supporting evidence.

---

# Next Recommended Document

## Frontend, Analyst Experience & Human-in-the-Loop Specification

This document should define the user-facing side of Project Sentinel in detail, including:

- User roles.
- Analyst workflows.
- Dashboard architecture.
- Alert and investigation views.
- Evidence visualization.
- Agent activity visibility.
- Human approval and review points.
- Escalation workflows.
- API-to-frontend data flow.
- UI state management.
- Security and usability requirements.

This is the next logical document because the backend, orchestration, deployment, testing, and data architecture are now defined. The analyst interface must expose those capabilities in a way that makes the AI investigation process understandable, controllable, and useful.
