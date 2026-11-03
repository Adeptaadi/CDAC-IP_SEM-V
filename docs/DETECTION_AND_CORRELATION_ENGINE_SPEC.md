# Project Sentinel
# Detection & Correlation Engine Technical Specification

**Document Type:** Technical Design Specification  
**Version:** 1.0  
**Status:** Proposed Architecture  
**Primary Focus:** Dataset ingestion, event normalization, detection, entity resolution, temporal correlation, and attack-chain construction

---

## 1. Purpose

This document defines the technical architecture of Project Sentinel's Detection and Correlation Engine.

The engine is responsible for converting raw cybersecurity telemetry into structured security findings that can be investigated by the Planner and specialized agents.

It performs two closely related functions:

1. **Detection:** Identify potentially malicious or suspicious activity from network and system telemetry.
2. **Correlation:** Identify relationships between events and organize them into meaningful sequences or incident candidates.

The engine must support the CSE-CIC-IDS2018 dataset as the primary proposed evaluation dataset, subject to inspection of the actual available files and fields.

The architecture should also preserve extensibility for other datasets, including KDD Cup.

**Core principle:** Detection and correlation produce evidence-backed findings. The Planner determines what investigation work should happen next.

## 2. Architectural Objectives

The engine must:

- Ingest selected dataset files through a replay mechanism.
- Preserve raw input and source provenance.
- Normalize supported telemetry into a canonical event representation.
- Validate and quarantine malformed records.
- Support rule-based and machine-learning detection.
- Preserve ground-truth labels separately from detection outputs.
- Correlate events using entity, temporal, and behavioral relationships.
- Generate structured detection findings.
- Construct incident candidates and timelines.
- Provide evidence references for downstream agents.
- Support incremental processing and replay.
- Measure detection and correlation performance.
- Avoid treating a dataset label as an operational detection result.

## 3. High-Level Architecture

```text
             CSE-CIC-IDS2018 DATASET
                       |
                       v
               DATASET REGISTRY
                       |
                       v
                REPLAY ENGINE
                       |
                       v
                INGESTION API
                       |
                       v
             RAW DATA PRESERVATION
                       |
                       v
              VALIDATION ENGINE
                       |
                       v
              NORMALIZATION ENGINE
                       |
                       v
               SECURITY EVENTS
                       |
             +---------+---------+
             |                   |
             v                   v
       RULE DETECTION       ML DETECTION
             |                   |
             +---------+---------+
                       |
                       v
               FINDING AGGREGATION
                       |
                       v
                CORRELATION ENGINE
                       |
                       v
              INCIDENT CANDIDATES
                       |
                       v
               PLANNER HANDOFF
                       |
                       v
             DYNAMIC INVESTIGATION
```

Detection and correlation should be independently testable.

The Planner should receive structured findings and incident candidates rather than raw dataset files.

## 4. Dataset and Telemetry Architecture

### 4.1 Primary dataset

The proposed primary dataset is **CSE-CIC-IDS2018**.

It is intended to support evaluation of network-based attack detection and selected investigation scenarios.

Potential attack categories include:

- Brute Force.
- Heartbleed.
- Botnet.
- DoS.
- DDoS.
- Web Attacks.
- Infiltration.

These categories must be mapped against the actual available files, labels, and fields before implementation.

Do not assume every category is represented in every file or that every category has sufficient examples for evaluation.

### 4.2 Dataset inspection requirements

Before building the canonical event schema, inspect:

1. Actual downloaded file inventory.
2. File formats.
3. Available columns.
4. Timestamp formats.
5. Source and destination identifiers.
6. Label fields.
7. Missing-value frequency.
8. Duplicate records.
9. Class distribution.
10. Whether selected files contain compatible telemetry.

The canonical schema must be derived from real source fields.

### 4.3 Dataset selection

The MVP should use a selected subset of dataset files.

Avoid loading the entire dataset unnecessarily.

Selection should be based on:

- Attack scenario coverage.
- Data quality.
- Available labels.
- Processing cost.
- Compatibility with the ingestion architecture.
- Ability to reproduce evaluation results.

PCAP processing should be added only if the selected implementation requires packet-level analysis.

### 4.4 Dataset registry

Every dataset should have a registration record.

```json
{
  "dataset_id": "DS-CICIDS2018",
  "dataset_name": "CSE-CIC-IDS2018",
  "dataset_version": "configured-version",
  "source": "official-dataset-source",
  "format": "csv",
  "status": "registered",
  "checksum": "sha256-value",
  "registered_at": "2026-08-01T10:00:00Z"
}
```

The values are illustrative placeholders.

The registry should also track individual files, scenario assignments, schema versions, and processing status.

## 5. Dataset Replay Engine

### 5.1 Purpose

The replay engine simulates telemetry arriving over time.

This allows Project Sentinel to evaluate continuous analysis behavior without requiring a live enterprise SIEM integration.

### 5.2 Replay architecture

```text
Dataset File
     |
     v
File Reader
     |
     v
Record Iterator
     |
     v
Timestamp Ordering
     |
     v
Replay Scheduler
     |
     v
Ingestion Endpoint
     |
     v
Event Processing
```

### 5.3 Replay modes

| Mode | Behavior |
|---|---|
| Instant replay | Processes records as quickly as possible |
| Timed replay | Emits records according to configured delays |
| Timestamp replay | Uses event timestamps to simulate relative arrival intervals |
| Scenario replay | Processes a selected attack scenario |
| Step replay | Allows controlled analyst-driven progression |

### 5.4 Replay configuration

```json
{
  "replay_id": "RP-001",
  "dataset_id": "DS-CICIDS2018",
  "file_id": "FILE-001",
  "mode": "timed",
  "speed_multiplier": 10,
  "batch_size": 500,
  "start_offset": 0,
  "end_offset": null,
  "scenario_id": "SC-BRUTEFORCE"
}
```

### 5.5 Replay controls

The replay engine should support:

- Start.
- Pause.
- Resume.
- Stop.
- Reset.
- Progress reporting.
- Processing-rate control.
- Error reporting.

Every replay must have a unique identifier.

### 5.6 Idempotency

Repeated ingestion must not silently duplicate records.

Use a stable event identifier where possible.

When the source does not provide one, generate a deterministic identifier from a documented combination of source file identity, row position, and source data.

A checksum-based strategy may also be used where appropriate.

## 6. Validation and Normalization

### 6.1 Validation

Every incoming record should pass validation before becoming a normalized security event.

Validation includes:

- Required field checks.
- Timestamp parsing.
- Numeric field validation.
- Address and port validation where applicable.
- Invalid encoding detection.
- Missing-value handling.
- Duplicate detection.
- Dataset schema compatibility.

Malformed records should be quarantined with failure reasons.

Do not silently discard invalid records.

### 6.2 Normalization

Different source formats may describe similar events using different field names.

Normalization maps these source-specific fields into a canonical event representation.

```text
Raw Dataset Record
        |
        v
Dataset-Specific Adapter
        |
        v
Field Mapping
        |
        v
Type Conversion
        |
        v
Timestamp Normalization
        |
        v
Canonical SecurityEvent
```

### 6.3 Dataset adapters

Use separate adapters for different datasets.

Suggested structure:

```text
backend/
└── app/
    └── ingestion/
        ├── registry.py
        ├── replay.py
        ├── service.py
        ├── validators.py
        ├── normalizers.py
        └── adapters/
            ├── base.py
            ├── cicids2018.py
            └── kddcup.py
```

This prevents dataset-specific assumptions from spreading into detection and correlation logic.

## 7. Canonical SecurityEvent Model

The canonical event model is the normalized representation used by downstream components.

It must be finalized after inspecting the actual source files.

The following is a proposed logical model, not a claim that every field exists in CSE-CIC-IDS2018.

```json
{
  "event_id": "EVT-001",
  "dataset_id": "DS-CICIDS2018",
  "source_file_id": "FILE-001",
  "source_row": 1001,
  "event_timestamp": "2026-08-01T10:00:00Z",
  "ingestion_timestamp": "2026-08-01T10:00:02Z",
  "event_type": "network_flow",
  "source": {
    "ip": "192.0.2.10",
    "port": 443
  },
  "destination": {
    "ip": "198.51.100.20",
    "port": 50000
  },
  "protocol": "TCP",
  "attributes": {},
  "ground_truth": {
    "label": "attack",
    "scenario": "configured-scenario"
  },
  "schema_version": "1.0"
}
```

### 7.1 Important field groups

| Group | Purpose |
|---|---|
| Identity | Stable event identifier |
| Provenance | Dataset, file, and row reference |
| Time | Event time and ingestion time |
| Classification | Event type |
| Network entities | Source and destination information |
| Attributes | Dataset-specific telemetry |
| Ground truth | Evaluation labels |
| Version | Canonical schema version |

### 7.2 Ground-truth separation

Ground-truth labels must not be passed to production-style detection logic.

They are available to the evaluation framework for calculating performance.

If the detection model receives ground-truth labels as input, the experiment may suffer from label leakage and become invalid.

### 7.3 Schema versioning

When the canonical schema changes:

- Introduce a new schema version.
- Update adapters.
- Validate backward compatibility.
- Preserve existing event provenance.
- Re-run relevant regression tests.

## 8. Detection Engine Architecture

### 8.1 Detection strategy

Use a hybrid detection architecture.

```text
                 SECURITY EVENTS
                        |
             +----------+----------+
             |                     |
             v                     v
       RULE ENGINE             ML ENGINE
             |                     |
             v                     v
       Rule Findings          ML Findings
             |                     |
             +----------+----------+
                        |
                        v
                FINDING AGGREGATOR
                        |
                        v
                DETECTION FINDINGS
```

Rules and ML models should be independently measurable.

The LLM may interpret findings and explain suspicious behavior, but it should not be the only mechanism responsible for detecting attacks.

### 8.2 Rule-based detection

Rules identify predefined conditions or patterns.

Potential rule categories:

- Repeated authentication failures.
- Suspicious connection patterns.
- Known attack signatures.
- Abnormal flow characteristics.
- Unusual traffic volume.
- Known malicious indicators, where available.

Rules should have:

- Unique rule identifier.
- Version.
- Description.
- Severity.
- Input requirements.
- Matching logic.
- Thresholds.
- Reference information.
- Test cases.

Example:

```yaml
rule_id: AUTH-001
name: Repeated Authentication Failures
description: Detects repeated authentication failures within a configured window.
severity: medium

conditions:
  event_type: authentication
  failure_count_threshold: 10
  time_window_seconds: 300

enabled: true
version: "1.0"
```

This is an illustrative rule. Its applicability depends on whether the selected telemetry contains authentication events.

### 8.3 Machine-learning detection

The ML engine should identify suspicious patterns using selected telemetry features.

Potential model families include:

- Logistic Regression.
- Random Forest.
- Gradient Boosting.
- Isolation Forest.
- Other suitable supervised or unsupervised methods.

The final selection must be based on dataset characteristics and measured performance.

### 8.4 Feature engineering

Feature extraction should be explicit and reproducible.

Potential network-flow features, subject to source availability:

- Flow duration.
- Forward and backward packet counts.
- Forward and backward byte counts.
- Packet length statistics.
- Flow rate.
- Inter-arrival-time statistics.
- Protocol.
- Source and destination ports.

Feature engineering must not use ground-truth labels as model inputs.

### 8.5 Training and inference separation

```text
TRAINING
Dataset
   |
   v
Feature Engineering
   |
   v
Train / Validation Split
   |
   v
Model Training
   |
   v
Model Evaluation
   |
   v
Approved Model Artifact

INFERENCE
SecurityEvent
   |
   v
Feature Transformation
   |
   v
Approved Model
   |
   v
Prediction
   |
   v
Detection Finding
```

The inference service should load an approved model artifact.

It should not retrain automatically during an investigation.

### 8.6 Model output

Example:

```json
{
  "finding_id": "FIND-001",
  "detector_type": "machine_learning",
  "detector_id": "RF-001",
  "prediction": "suspicious",
  "score": 0.91,
  "threshold": 0.75,
  "model_version": "1.0",
  "event_refs": [
    "EVT-001"
  ]
}
```

The score must be interpreted according to the model's scoring semantics.

A model score is not automatically a calibrated probability.

## 9. Detection Finding Model

A detection finding is the structured result of a rule or ML detector.

Suggested structure:

```json
{
  "finding_id": "FIND-001",
  "finding_type": "suspicious_activity",
  "classification": "credential_attack",
  "severity": "high",
  "detector": {
    "type": "rule",
    "id": "AUTH-001",
    "version": "1.0"
  },
  "event_refs": [
    "EVT-001",
    "EVT-002"
  ],
  "reason": "Repeated authentication failures exceeded the configured threshold.",
  "score": null,
  "created_at": "2026-08-01T10:05:00Z"
}
```

### 9.1 Finding aggregation

Multiple detectors may identify related activity.

The aggregator should:

- Preserve original findings.
- Identify overlapping event references.
- Avoid unnecessary duplicate alerts.
- Preserve detector provenance.
- Apply configurable severity rules.
- Produce a consolidated finding where justified.

Aggregation must not erase disagreements between detectors.

## 10. Detection Severity and Confidence

Severity and confidence are separate concepts.

| Attribute | Meaning |
|---|---|
| Severity | Potential impact or urgency |
| Confidence | Strength of support for the finding |

For example, a potentially critical activity may have low confidence if evidence is incomplete.

Do not calculate severity from confidence alone.

The mapping from detection outputs to severity should be configurable and documented.

## 11. Correlation Engine Architecture

### 11.1 Purpose

Detection identifies suspicious activity.

Correlation identifies relationships between events and findings.

It answers questions such as:

- Did multiple events involve the same entity?
- Did activity occur within a meaningful time window?
- Are several findings part of one possible incident?
- Do events form a plausible sequence?
- Is there evidence of movement between systems?
- Are multiple alerts duplicates of the same underlying activity?

### 11.2 Correlation workflow

```text
Security Events
      |
      v
Detection Findings
      |
      v
Entity Extraction
      |
      v
Entity Resolution
      |
      v
Temporal Analysis
      |
      v
Relationship Generation
      |
      v
Correlation Scoring
      |
      v
Incident Candidate
      |
      v
Planner
```

### 11.3 Correlation dimensions

The engine should initially support:

1. Entity-based correlation.
2. Temporal correlation.
3. Attribute-based correlation.
4. Finding-based correlation.
5. Rule-based relationship generation.

Graph-based representations may be introduced when they provide measurable benefits.

## 12. Entity Resolution

### 12.1 Entity types

Potential entity types include:

- IP address.
- Host.
- Account.
- Port.
- Network flow.
- Process.
- File hash.
- Domain.
- Vulnerability identifier.

The available entity types depend on the dataset and telemetry source.

### 12.2 Entity identity

Entities should have normalized identifiers.

Example:

```json
{
  "entity_id": "ENT-001",
  "entity_type": "ip_address",
  "normalized_value": "192.0.2.10",
  "source_refs": [
    "EVT-001",
    "EVT-002"
  ]
}
```

### 12.3 Entity resolution rules

Examples:

- Equivalent IP representations should normalize to the same address.
- Hostnames should follow a documented normalization policy.
- Account identifiers should preserve source-specific identity.
- Missing identifiers must not be guessed.
- Ambiguous entity matches should be marked uncertain.

### 12.4 Entity resolution confidence

If multiple identifiers may refer to the same entity, record the basis for the match.

Do not silently merge unrelated entities.

## 13. Temporal Correlation

### 13.1 Purpose

Temporal correlation identifies events that occur within meaningful time relationships.

Example:

```text
10:00:00  Authentication failure
10:00:05  Authentication failure
10:00:12  Authentication failure
10:01:03  Successful authentication
10:02:20  Suspicious follow-up activity
```

The sequence may warrant investigation.

However, temporal proximity alone does not prove causality.

### 13.2 Time-window correlation

A basic correlation rule may use:

- Event type.
- Shared entity.
- Time difference.
- Configured time window.

Example:

```python
def within_window(event_a, event_b, window_seconds):
    delta = abs(
        (event_a.timestamp - event_b.timestamp).total_seconds()
    )
    return delta <= window_seconds
```

### 13.3 Time handling

Store timestamps consistently.

Retain:

- Original source timestamp.
- Normalized UTC timestamp.
- Ingestion timestamp.
- Timestamp parsing status.

Do not assume that all dataset timestamps are already in UTC.

The dataset adapter must document timezone assumptions.

## 14. Relationship Model

Correlation results should represent relationships explicitly.

Example:

```json
{
  "relationship_id": "REL-001",
  "source_event_id": "EVT-001",
  "target_event_id": "EVT-002",
  "relationship_type": "same_source_ip",
  "relationship_basis": [
    "shared_source_ip"
  ],
  "time_difference_seconds": 15,
  "confidence": 0.95
}
```

Relationship confidence should reflect the strength of the relationship rule.

A shared IP address is evidence of a shared network identifier, not proof that the same person or host generated both events.

## 15. Correlation Scoring

A configurable correlation score may combine multiple signals.

Illustrative formula:

\[
C = w_eE + w_tT + w_aA + w_fF
\]

Where:

- \(E\): entity relationship strength.
- \(T\): temporal proximity score.
- \(A\): attribute similarity.
- \(F\): finding relationship strength.
- \(w_e,w_t,w_a,w_f\): configured weights.

Weights must be calibrated using the evaluation dataset.

This score is a ranking or grouping signal, not a probability of common malicious origin.

The engine should preserve individual relationship features so analysts can understand why two events were grouped.

## 16. Incident Candidate Construction

### 16.1 Purpose

An incident candidate is a collection of related findings and events that may represent one security incident.

It is not necessarily a confirmed incident.

### 16.2 Construction

```text
Detection Findings
       |
       v
Correlation Relationships
       |
       v
Connected Event Groups
       |
       v
Incident Candidate Creation
       |
       v
Candidate Validation
       |
       v
Planner Handoff
```

### 16.3 Candidate structure

```json
{
  "candidate_id": "INC-CAND-001",
  "status": "candidate",
  "classification": "suspicious_authentication",
  "severity": "high",
  "finding_refs": [
    "FIND-001",
    "FIND-002"
  ],
  "event_refs": [
    "EVT-001",
    "EVT-002",
    "EVT-003"
  ],
  "entity_refs": [
    "ENT-001"
  ],
  "relationships": [
    "REL-001"
  ],
  "first_seen": "2026-08-01T10:00:00Z",
  "last_seen": "2026-08-01T10:05:00Z",
  "correlation_version": "1.0"
}
```

### 16.4 Candidate lifecycle

Possible states:

- `candidate`
- `under_investigation`
- `confirmed`
- `benign`
- `inconclusive`
- `closed`

The Planner and analyst workflow determine subsequent status changes.

The correlation engine should not automatically classify every candidate as a confirmed incident.

## 17. Attack Timeline Construction

The engine should support a chronological timeline of relevant events.

Each timeline entry should retain:

- Timestamp.
- Event reference.
- Finding reference.
- Entity references.
- Event description.
- Relationship references.
- Source provenance.

Example:

| Time | Event | Significance |
|---|---|---|
| 10:00:00 | Authentication failure | Initial suspicious activity |
| 10:00:12 | Repeated authentication failure | Repetition |
| 10:01:03 | Successful authentication | Potentially significant transition |
| 10:02:20 | Follow-up activity | Requires investigation |

The table is illustrative.

The timeline should preserve source event timestamps and avoid inferring missing events.

## 18. LLM Integration

LLMs may assist with:

- Explaining detection findings.
- Interpreting correlation relationships.
- Identifying possible investigation hypotheses.
- Summarizing incident candidates.
- Recommending missing evidence.
- Mapping findings to relevant security knowledge.

LLMs should not replace deterministic operations such as:

- Timestamp comparison.
- Entity normalization.
- Exact identifier matching.
- Database retrieval.
- Rule evaluation.
- Model inference.
- Relationship persistence.

### 18.1 Structured LLM output

Example:

```json
{
  "summary": "The events may represent suspicious authentication activity.",
  "hypotheses": [
    {
      "description": "Potential credential compromise",
      "supporting_findings": [
        "FIND-001"
      ],
      "missing_evidence": [
        "Subsequent account activity"
      ]
    }
  ],
  "recommended_investigation": [
    "Search for activity associated with the account after successful authentication"
  ]
}
```

Every finding reference must be validated.

The LLM may recommend an investigation objective, but the Planner remains responsible for scheduling and coordinating tasks.

## 19. Planner Handoff Contract

The Detection and Correlation Engine should hand structured incident candidates to the orchestration layer.

Example:

```json
{
  "handoff_id": "HANDOFF-001",
  "candidate_id": "INC-CAND-001",
  "trigger_type": "new_incident_candidate",
  "summary": "Multiple related suspicious authentication findings",
  "finding_refs": [
    "FIND-001",
    "FIND-002"
  ],
  "event_refs": [
    "EVT-001",
    "EVT-002"
  ],
  "correlation_summary": {
    "entity_relationships": 2,
    "temporal_relationships": 1
  },
  "available_capabilities": [
    "event_search",
    "investigation",
    "knowledge_retrieval",
    "reporting"
  ]
}
```

The handoff should be idempotent.

The same candidate should not trigger unlimited duplicate investigations.

### 19.1 Planner responsibilities after handoff

The Planner may:

- Request additional event search.
- Request deeper correlation.
- Retrieve relevant knowledge.
- Assign investigation tasks.
- Revisit earlier findings.
- Request human review.
- Determine when the investigation is complete.

The handoff does not impose a fixed investigation sequence.

## 20. Persistence Model

Suggested tables:

```text
datasets
dataset_files
dataset_replays
ingestion_batches
raw_records
security_events
detection_rules
detection_models
detection_findings
correlation_runs
entities
event_relationships
incident_candidates
incident_candidate_events
incident_timelines
detection_handoffs
```

The final schema must be reconciled with the existing database design.

Avoid duplicating existing investigation, evidence, or task entities.

### 20.1 Provenance requirements

Every finding must retain:

- Source event references.
- Dataset and file references.
- Detector identifier.
- Detector version.
- Rule or model version.
- Processing timestamp.
- Schema version.

Every correlation result must retain:

- Correlation run identifier.
- Input references.
- Relationship basis.
- Scoring configuration.
- Algorithm version.

## 21. Detection and Correlation Evaluation

### 21.1 Detection metrics

For binary classification:

\[
Precision = \frac{TP}{TP+FP}
\]

\[
Recall = \frac{TP}{TP+FN}
\]

\[
F1 = 2 \times \frac{Precision \times Recall}{Precision+Recall}
\]

\[
FPR = \frac{FP}{FP+TN}
\]

Also measure:

- Macro F1.
- Weighted F1.
- Balanced accuracy.
- False negative rate.
- Detection latency.

### 21.2 Correlation metrics

Measure:

- Event-link precision.
- Event-link recall.
- Event-link F1.
- Entity resolution accuracy.
- Incident grouping quality.
- Timeline ordering accuracy.
- Correlation latency.

### 21.3 Incident candidate metrics

Measure:

- Candidate precision.
- Candidate recall.
- Duplicate candidate rate.
- Incident grouping accuracy.
- Candidate generation latency.

### 21.4 Ground-truth considerations

Dataset labels may identify attack categories at the flow or record level.

They do not necessarily provide a complete ground-truth incident graph.

Do not claim event-correlation accuracy using labels alone unless a defensible event-link ground truth exists.

Where required, construct a manually reviewed correlation test set or define a documented approximation.

### 21.5 Data leakage prevention

The evaluation design must ensure:

- Ground-truth labels are not detection features.
- Preprocessing is fitted only on training data.
- Related records do not leak across partitions.
- Dataset-specific duplicate patterns are considered.
- Scenario and time-based splits are used where appropriate.
- Test labels are not used to tune thresholds.

### 21.6 Provisional acceptance targets

These are proposed engineering targets, not measured results or established industry benchmarks.

| Metric | Initial target |
|---|---:|
| Detection macro F1 | ≥ 0.85 |
| Detection recall | ≥ 0.90 |
| False positive rate | ≤ 0.05 |
| Valid finding provenance | 100% |
| Correlation relationship precision | ≥ 0.85 |
| Event-link recall | ≥ 0.80 |
| Duplicate candidate rate | ≤ 0.05 |
| Replay reproducibility | 100% under fixed configuration |

Final targets must be calibrated against actual dataset quality and scenario difficulty.

## 22. Observability

The engine should emit structured logs and metrics.

Important identifiers:

- `dataset_id`
- `file_id`
- `replay_id`
- `ingestion_batch_id`
- `event_id`
- `finding_id`
- `correlation_run_id`
- `candidate_id`
- `investigation_id`

Suggested metrics:

```text
sentinel_ingestion_records_total
sentinel_ingestion_failures_total
sentinel_normalization_failures_total
sentinel_detection_findings_total
sentinel_detection_latency_seconds
sentinel_model_inference_seconds
sentinel_correlation_runs_total
sentinel_correlation_latency_seconds
sentinel_incident_candidates_total
sentinel_duplicate_candidates_total
sentinel_replay_records_per_second
```

Metrics should be broken down by detector, dataset, scenario, and processing stage where practical.

## 23. Failure Handling

### 23.1 Invalid records

- Quarantine invalid records.
- Preserve source location.
- Record validation errors.
- Continue processing valid records when possible.

### 23.2 Detector unavailable

- Preserve validated security events.
- Record detector failure.
- Continue with other eligible detectors.
- Mark detection coverage as incomplete.

### 23.3 Correlation failure

- Preserve detection findings.
- Record failed correlation run.
- Allow correlation retry.
- Do not silently discard candidate relationships.

### 23.4 Duplicate replay

- Use idempotency controls.
- Detect repeated records.
- Preserve replay provenance.
- Avoid generating duplicate candidates unnecessarily.

### 23.5 Planner unavailable

- Persist candidate and handoff state.
- Retry handoff according to policy.
- Do not lose findings because the orchestration layer is temporarily unavailable.

## 24. Implementation Roadmap

### Phase 1 — Dataset inspection

- Inspect actual CSE-CIC-IDS2018 files.
- Identify selected attack scenarios.
- Document available fields.
- Analyze class distributions.
- Identify missing and duplicate data.
- Define dataset splits.

### Phase 2 — Ingestion and normalization

- Implement dataset registry.
- Implement replay engine.
- Implement dataset adapters.
- Add validation and quarantine.
- Finalize canonical SecurityEvent schema.
- Add provenance and idempotency.

### Phase 3 — Detection

- Implement baseline rules.
- Build feature extraction.
- Train baseline ML models.
- Create inference interface.
- Implement detection finding schema.
- Add threshold configuration.

### Phase 4 — Correlation

- Implement entity extraction.
- Implement entity normalization.
- Implement temporal correlation.
- Implement relationship persistence.
- Construct incident candidates.
- Generate timelines.

### Phase 5 — Orchestration integration

- Implement detection handoff.
- Add idempotent candidate dispatch.
- Integrate with Planner.
- Support dynamic investigation task selection.
- Preserve investigation and evidence references.

### Phase 6 — Evaluation and optimization

- Run detection benchmarks.
- Evaluate correlation quality.
- Analyze false positives.
- Measure processing throughput.
- Run replay reproducibility tests.
- Perform failure and load testing.

## 25. Acceptance Criteria

| ID | Acceptance criterion |
|---|---|
| DET-01 | Selected dataset files are registered and versioned |
| DET-02 | Dataset replay supports controlled execution |
| DET-03 | Replay operations are identifiable and reproducible |
| DET-04 | Raw source provenance is preserved |
| DET-05 | Invalid records are quarantined |
| DET-06 | Canonical event schema is based on inspected source fields |
| DET-07 | Ground-truth labels are isolated from detection features |
| DET-08 | Rule-based detection operates independently |
| DET-09 | ML detection operates through a versioned inference interface |
| DET-10 | Detection findings retain source references |
| DET-11 | Entity resolution produces explicit relationships |
| DET-12 | Temporal correlation is configurable |
| DET-13 | Correlation results retain their relationship basis |
| DET-14 | Incident candidates preserve constituent findings |
| DET-15 | Timeline construction preserves event timestamps |
| DET-16 | Candidate handoff to Planner is idempotent |
| DET-17 | Detection and correlation metrics are measurable |
| DET-18 | Detector and correlation failures do not destroy persisted findings |

## 26. Key Architectural Decisions

| Decision | MVP position |
|---|---|
| Primary evaluation dataset | CSE-CIC-IDS2018, subject to inspection |
| Data delivery | Dataset replay |
| Normalization | Dataset-specific adapters |
| Canonical event model | Derived from actual source fields |
| Detection | Hybrid rules and ML |
| LLM role | Interpretation and investigation assistance |
| Correlation | Entity-based and temporal initially |
| Graph architecture | Optional extension after baseline |
| Incident representation | Structured incident candidates |
| Ground truth | Evaluation-only |
| Handoff | Structured, persistent, idempotent |
| Orchestration | Planner-controlled and non-linear |

## 27. Final Architectural Position

The Detection and Correlation Engine is the entry point for Project Sentinel's investigation lifecycle.

Its responsibility is to transform raw telemetry into reliable, structured, and traceable findings.

The detection layer identifies suspicious activity through measurable rule-based and ML mechanisms.

The correlation layer establishes relationships between events, entities, and findings.

The Planner then uses these outputs to decide which specialist capabilities should be executed, what additional evidence is required, and whether investigation should continue or conclude.

The engine must not become a fixed incident workflow. It supplies evidence and incident candidates to the orchestration system, which dynamically determines the next investigation objective.

The central architectural differentiator remains the Planner's ability to coordinate specialized capabilities based on evolving evidence—not simply the presence of multiple detection algorithms or agents.
