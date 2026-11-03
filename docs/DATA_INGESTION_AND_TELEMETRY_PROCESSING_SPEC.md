# Project Sentinel — Data Ingestion & Telemetry Processing Specification

**Document Type:** Technical Design Specification  
**Version:** 1.0  
**Status:** Architecture Baseline  
**Primary Focus:** Dataset ingestion, telemetry processing, event normalization, validation, batch/replay processing, canonical event schemas, data quality, and integration with detection and investigation.  
**Related Components:** Ingestion Engine, `TelemetryAdapter` Interface, Canonical Normalizer, Quarantine Store, Replay Controller, PostgreSQL

---

# 1. Purpose

Project Sentinel depends on telemetry as the primary source of incident evidence.

Before the AI Planner can investigate an alert, the system must reliably answer:
- Where did the event come from?
- What type of event is it?
- When did it occur?
- Which host, user, process, or network entity is involved?
- Is the event valid?
- Can events from different sources be represented consistently?
- Can the original source data still be traced?

The Data Ingestion & Telemetry Processing Layer is responsible for transforming raw dataset records into a **canonical internal event format**.

```text
RAW DATASET / TELEMETRY
          │
          ▼
    SOURCE ADAPTER
          │
          ▼
    DATA VALIDATION
          │
          ▼
  EVENT NORMALIZATION
          │
          ▼
  CANONICAL EVENT
          │
          ├───────────────► RAW DATA REFERENCE
          │
          ▼
    EVENT STORAGE
          │
          ▼
 DETECTION & CORRELATION
          │
          ▼
 INVESTIGATION SYSTEM
```

> **AI agents investigate normalized evidence. They do not parse arbitrary raw dataset files during an investigation.**

---

# 2. Architectural Role

```text
┌──────────────────────────────────────────┐
│              DATA SOURCES                │
│ Dataset Files / Replay Data / Telemetry  │
└────────────────────┬─────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────┐
│           INGESTION LAYER                │
│ Read → Validate → Normalize → Store      │
└────────────────────┬─────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────┐
│         EVENT PROCESSING LAYER           │
│ Detection → Correlation → Alerting       │
└────────────────────┬─────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────┐
│        INVESTIGATION ORCHESTRATION       │
│ Evidence → Planning → Actions            │
└──────────────────────────────────────────┘
```

This separation makes the system modular: data sources can change without redesigning the AI orchestration.

---

# 3. Processing Modes: Batch & Replay

1. **Batch Mode**: Reads chunks of historical CSV/JSONL records into storage; suitable for bulk benchmarking and training.
2. **Replay Mode**: Emits historical records preserving relative temporal pacing ($\Delta t$):
   $$\text{Emitted Time} = \text{Start Time} + \frac{\text{Event Time} - \text{First Event Time}}{\text{Speed Multiplier}}$$
   Allows reproducible simulation of live cyber attacks.

---

# 4. Source Adapter Architecture & Interface

```python
class TelemetryAdapter:
    def validate_source(self, record: dict) -> bool:
        """Validate raw input structural integrity."""
        pass

    def parse(self, record: dict) -> dict:
        """Parse source-specific fields."""
        pass

    def normalize(self, parsed_record: dict) -> dict:
        """Transform fields into canonical schema format."""
        pass

    def create_event(self, normalized_record: dict) -> "NormalizedEvent":
        """Instantiate validated Pydantic NormalizedEvent model."""
        pass
```

---

# 5. Canonical Event Schema

```json
{
  "event_id": "EVT-001",

  "timestamp": "2026-11-02T10:30:00Z",

  "event_type": "process_event",

  "source": {
    "source_id": "dataset-001",
    "source_type": "replay",
    "adapter_version": "1.0"
  },

  "host": {
    "host_id": "HOST-001",
    "hostname": "example-host"
  },

  "user": {
    "user_id": "USER-001",
    "username": "example-user"
  },

  "process": {
    "process_id": "PROC-001",
    "parent_process_id": "PROC-000",
    "image": "example-process"
  },

  "network": {
    "source_ip": null,
    "destination_ip": null,
    "destination_port": null
  },

  "attributes": {},

  "raw_reference": {
    "source_record_id": "RAW-001"
  },

  "ingestion_metadata": {
    "ingested_at": "2026-11-02T10:31:00Z",
    "schema_version": "1.0"
  }
}
```

---

# 6. Entity & Timestamp Normalization

- **Timestamps**: Normalized to ISO 8601 UTC (`occurred_at` vs. `ingested_at`).
- **Entity Case Normalization**: `HOST-01` $\to$ `host-01`, `User-Admin` $\to$ `admin`.
- **Pivot Entities**: Host, User, Process, IP Address, File, Session.

---

# 7. Validation Pipeline & Quarantine Store

```text
RAW RECORD ──► FIELD CHECK ──► FORMAT CHECK ──► TIMESTAMP CHECK ──┬──► ACCEPT ──► NORMALIZATION
                                                                  │
                                                                  └──► REJECT ──► QUARANTINE STORE
```

### Quarantine Entry Schema:
```json
{
  "record_id": "RAW-001",
  "source_id": "dataset-001",
  "error_reason": "Failed to parse ISO-8601 timestamp: 'invalid-time-val'",
  "quarantined_at": "2026-11-02T10:31:00Z",
  "raw_payload": "{...}"
}
```

---

# 8. Event Deduplication Fingerprint

To prevent duplicate records from inflating event frequency:

$$F = \text{SHA256}(\text{timestamp} + \text{event\_type} + \text{primary\_entity} + \text{source\_record\_identifier})$$

Duplicate fingerprints are discarded idempotently without raising errors.

---

# 9. Ingestion Job State Tracking

```json
{
  "run_id": "INGEST-RUN-001",
  "source_id": "cse-cic-ids2018",
  "current_position": 15400,
  "records_processed": 15400,
  "records_accepted": 15392,
  "records_rejected": 8,
  "status": "running",
  "started_at": "2026-11-02T10:00:00Z",
  "updated_at": "2026-11-02T10:15:00Z"
}
```

---

# 10. Data Quality Metrics

$$\text{Acceptance Rate} = \frac{\text{Accepted Records}}{\text{Total Records}}$$

$$\text{Rejection Rate} = \frac{\text{Rejected Records}}{\text{Total Records}}$$

$$\text{Completeness} = \frac{\text{Available Required Fields}}{\text{Expected Required Fields}}$$

---

# 11. Error Categorization Hierarchy

1. **Recoverable Errors** (e.g. temporary database lock): Exponential backoff retry.
2. **Record-Level Errors** (e.g. malformed IP address string): Quarantine individual record, continue batch.
3. **Source-Level Errors** (e.g. corrupt CSV header / missing file): Mark job `FAILED`, abort batch safely.

---

# 12. Final Design Principle

> **If the incoming data is inconsistent, the downstream intelligence cannot be trusted.**

Project Sentinel treats data ingestion as an evidence engineering discipline: raw data is normalized, validated, fingerprinted, and traceable before any detection or AI investigation takes place.
