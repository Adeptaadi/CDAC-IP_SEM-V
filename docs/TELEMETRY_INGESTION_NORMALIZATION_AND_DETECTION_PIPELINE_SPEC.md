# Project Sentinel — Telemetry Ingestion, Normalization & Detection Pipeline Implementation Specification (TINDPIS)

**Document Type:** Technical Design and Implementation Specification  
**Version:** 1.0  
**Status:** Architecture Baseline  
**Primary Focus:** Dataset ingestion, telemetry normalization, event validation, replay processing, detection, alert generation, and detection evaluation.  
**Related Components:** Ingestion Pipeline, Dataset Adapters, Canonical Normalizer, Detection Engine, Alert Generator, AI Orchestrator

---

# 1. Purpose

The telemetry pipeline provides the operational foundation for Project Sentinel.

Before AI agents can investigate an incident, the system must:
1. Receive security telemetry from files or replay buffers.
2. Parse source data across varying formats.
3. Validate incoming records against structural schemas.
4. Convert source-specific records into canonical `NormalizedEvent` structures.
5. Store normalized events in PostgreSQL.
6. Detect suspicious activity patterns deterministically.
7. Generate traceable, auditable alerts.
8. Dispatch alerts into the investigation orchestration queue.

```text
SECURITY DATASET
      │
      ▼
DATASET ADAPTER
      │
      ▼
RAW EVENT PARSER
      │
      ▼
SCHEMA VALIDATION
      │
      ▼
NORMALIZATION
      │
      ▼
DEDUPLICATION
      │
      ▼
NORMALIZED EVENT STORE
      │
      ├──────────────► CORRELATION
      │
      ▼
DETECTION ENGINE
      │
      ▼
ALERT GENERATION
      │
      ▼
AI INVESTIGATION
```

---

# 2. Design Principles

1. **Dataset Adapters Are Isolated**: Source-specific parsing is quarantined behind adapter contracts so downstream systems remain decoupled.
2. **Raw Data Is Preserved**: Normalization retains pointers back to original files and line offsets (`raw_reference`).
3. **Detection Is Deterministic & Explainable**: Rules are explicit logical expressions; LLMs are forbidden from performing basic pattern detection.
4. **Processing Is Reproducible**: Deterministic replays across identical configurations yield identical detection sequences and alerts.

---

# 3. Dataset Adapter Architecture

```text
DatasetAdapter (Abstract Base Class)
│
├── validate_source()
├── discover_files()
├── read_events()
├── extract_metadata()
└── get_source_schema()
```

### Raw Event Ingestion Contract:
```json
{
  "source_id": "SRC-001",
  "source_type": "dataset",
  "source_event_id": "original-event-id",
  "raw_timestamp": "2026-11-02 10:15:30",
  "raw_data": {
    "src_ip": "192.168.1.10",
    "dst_ip": "10.0.0.25",
    "dst_port": 4444
  },
  "source_metadata": {
    "filename": "Friday-02-03-2018_TrafficForML_CICFlowMeter.csv",
    "row_index": 1042
  }
}
```

---

# 4. Ingestion Modes: Batch & Replay

1. **Batch Ingestion**: Reads chunks of historical CSV/JSONL records into memory/database; ideal for high-throughput model benchmarking.
2. **Simulated Stream Replay**: Paces event release according to historical inter-event time deltas ($\Delta t$):
   $$\text{Emitted Time} = \text{Start Time} + \frac{\text{Event Time} - \text{First Event Time}}{\text{Speed Multiplier}}$$

### Replay Configuration (`config/replay.yaml`):
```yaml
replay:
  enabled: true
  speed_multiplier: 10
  preserve_event_order: true
  timestamp_strategy: original_relative
```

---

# 5. Canonical Event Schema

```json
{
  "event_id": "EVT-001",

  "source": {
    "source_id": "SRC-001",
    "source_event_id": "original-id",
    "source_type": "dataset"
  },

  "event_type": "network_connection",

  "occurred_at": "2026-11-02T10:15:30Z",

  "entities": {
    "host": ["host-01"],
    "user": ["admin"],
    "process": ["powershell.exe"],
    "ip": ["192.168.1.10", "10.0.0.25"],
    "file": []
  },

  "attributes": {
    "protocol": "TCP",
    "bytes_sent": 2048,
    "bytes_received": 4096
  },

  "normalization": {
    "schema_version": "1.0",
    "adapter_name": "cic_ids_2018_adapter"
  }
}
```

---

# 6. Event Categorization & Entity Normalization

Standard event categories: `Process`, `Network`, `Authentication`, `File`, `System`, `Security`.

### Entity Extraction & Case Normalization:
$$\text{Raw: } \texttt{HOST-01} \quad \implies \quad \text{Normalized: } \texttt{host-01}$$
$$\text{Raw: } \texttt{192.168.1.10:4444} \quad \implies \quad \text{IP: } \texttt{192.168.1.10}, \text{ Port: } 4444$$

---

# 7. Validation, Quarantine & Deduplication

### Quarantine Error Handling:
Records failing schema, timestamp, or type validation are routed to quarantine logs rather than aborting batch runs:
```text
INVALID RECORD ──► QUARANTINE LOG (record_id, error_reason, timestamp) ──► CONTINUE PROCESSING
```

### Idempotency & Deduplication Hash:
$$D = H(\text{source\_id} + \text{source\_event\_id} + \text{occurred\_at} + \text{event\_type})$$
Where $H$ is SHA-256. Existing hashes in PostgreSQL trigger an immediate deduplication skip.

---

# 8. Detection Engine Architecture

```text
NORMALIZED EVENT
        │
        ▼
DETECTION ENGINE
        │
        ├── Single-Event Rules
        ├── Multi-Event Sequence Rules
        └── Threshold Aggregations
                │
                ▼
          DETECTION RESULT
```

### 8.1 Single-Event Detection Rule
```yaml
rule_id: DET-001
name: Suspicious Reverse Shell Port
enabled: true
event_type: network_connection
conditions:
  - field: entities.destination_port
    operator: equals
    value: 4444
severity: high
confidence: 0.85
```

### 8.2 Multi-Event Sequence Detection Rule
```yaml
rule_id: DET-002
name: Brute Force Followed by Outbound Connection
sequence:
  - event_type: authentication
    conditions:
      - field: attributes.status
        operator: equals
        value: failure
    min_count: 5
  - event_type: network_connection
    conditions:
      - field: attributes.direction
        operator: equals
        value: outbound
correlation:
  shared_entity: host
time_window_minutes: 10
severity: critical
confidence: 0.90
```

---

# 9. Detection Confidence & Alert Policy

### Detection Confidence Formula:
$$C_d = w_1 R + w_2 E + w_3 Q$$
Where $w_1 = 0.40$ (rule specificity), $w_2 = 0.40$ (evidence completeness), $w_3 = 0.20$ (data quality).

$$\text{Severity (Impact)} \neq \text{Confidence (Certainty)}$$

### Alert Dispatch Envelope:
```json
{
  "alert_id": "ALT-001",
  "detection_result_id": "DETRES-001",
  "title": "Suspicious Port 4444 Connection",
  "severity": "high",
  "confidence": 0.85,
  "status": "new",
  "triggering_event_ids": [
    "EVT-001"
  ]
}
```

---

# 10. Attack Scenario Mapping (CSE-CIC-IDS2018)

| Scenario ID | Attack Type | Triggering Signature | Detection Rule | Target Telemetry |
|---|---|---|---|---|
| **SCN-001** | Infiltration & C2 | Outbound connection to abnormal high port | `DET-001` | Network Flow (Friday 02-03) |
| **SCN-002** | SSH/FTP Brute Force | $\ge 20$ failed auth attempts within 60s | `DET-002` | Network Flow (Wednesday 14-02) |
| **SCN-003** | Web SQL Injection | Anomalous payload length / error responses | `DET-003` | Network Flow (Thursday 15-02) |

---

# 11. Detection Evaluation Metrics

$$\text{Precision} = \frac{TP}{TP + FP}$$

$$\text{Recall} = \frac{TP}{TP + FN}$$

$$F_1 = 2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}$$

### Root Cause Analysis:
- **False Positives (FP)**: Analyzed for overly broad thresholds or missing contextual preconditions.
- **False Negatives (FN)**: Analyzed for uncaptured telemetry, feature drift, or window expiry.

---

# 12. Pipeline Acceptance Criteria

1. **Adapter Boundary**: Source data converts to `NormalizedEvent` preserving `raw_reference`.
2. **Determinism**: Rule engine evaluates without non-deterministic LLM variance.
3. **Fault Tolerance**: Malformed events are quarantined without crashing the ingestion worker.
4. **Traceability**: Every generated alert contains UUIDs of triggering normalized events.
5. **Replayability**: Batch and simulated streaming yield identical detection outputs.

---

# 13. Final Architecture Principle

> **Source-specific complexity ends at the normalization boundary. From that point onward, detection, correlation, investigation, and AI orchestration operate strictly on traceable canonical events.**
