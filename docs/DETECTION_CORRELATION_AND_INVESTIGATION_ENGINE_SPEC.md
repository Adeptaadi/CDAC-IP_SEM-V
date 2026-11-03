# Project Sentinel — Detection, Correlation & Investigation Engine
## Concrete Schemas, Formulas and Decision Rules

**Version:** 1.1  
**Document Type:** Engine Specification & Data Contracts  
**Status:** Proposed Architecture Upgrade  
**Primary Focus:** Concrete data contracts, deterministic detection rules, entity extraction, correlation algorithms, mathematical scoring formulas, and policy termination rules.  
**Related Components:** Ingestion Engine, Normalizer, Detection Engine, Correlation Capability, Investigation State Manager, Policy Controller

---

# 1. Design Principles for Concrete Models

All core investigation data follows four fundamental rules:
1. **Traceability** — Every finding must reference its source record or ancestral event UUID.
2. **Explainability** — Important scores must be mathematically reproducible and auditable.
3. **Validation** — Data exchanged between components must follow strict Pydantic schemas.
4. **Separation of Concerns** — Detection confidence, correlation strength, evidence strength, and investigation confidence must remain separate mathematical concepts:

```text
Detection Confidence
        │
        ▼
    Alert Created
        │
        ▼
Correlation Strength ──► Related Evidence
        │                      │
        └──────────────────────┤
                               ▼
                        Evidence Strength
                               │
                               ▼
                    Investigation Confidence
                               │
                               ▼
                     Policy Decision / Outcome
```

> **Important:** These values must never be added together without normalization and explicit defined semantics.

---

# 2. Canonical Normalized Event Schema

Every event entering the detection and investigation pipeline is converted into a canonical structure.

## 2.1 JSON Schema

```json
{
  "event_id": "evt_01JXYZ001",
  "source_event_id": "original-source-id",
  "source_type": "dataset",
  "event_type": "network_connection",

  "occurred_at": "2026-11-02T10:15:30Z",
  "ingested_at": "2026-11-02T10:15:35Z",

  "entities": {
    "source_ip": "192.168.1.10",
    "destination_ip": "10.0.0.25",
    "source_port": 49152,
    "destination_port": 443,
    "host": "host-01",
    "user": null,
    "process": null
  },

  "attributes": {
    "protocol": "TCP",
    "bytes_sent": 2048,
    "bytes_received": 4096
  },

  "raw_event_reference": "raw://dataset/file-01/record-1024",
  "schema_version": "1.0"
}
```

## 2.2 Required Fields

| Field | Type | Required | Purpose |
|---|---|---|---|
| `event_id` | UUID/String | Yes | Internal unique identifier |
| `source_type` | String | Yes | Origin of telemetry (e.g. `ids2018`, `sysmon`) |
| `event_type` | String | Yes | Canonical classification (`network_connection`, `auth`, `process`) |
| `occurred_at` | Datetime | Yes | Time observed in target system telemetry |
| `ingested_at` | Datetime | Yes | Time Sentinel ingested the record |
| `entities` | Object | Yes | Normalized pivot entities for correlation |
| `attributes` | Object | No | Source-specific metadata dictionary |
| `raw_event_reference` | String | Yes | Lineage pointer to raw dataset line/file |

---

# 3. Detection Rule Schema

Detection rules are data-driven JSON/YAML definitions rather than hardcoded logic:

```json
{
  "rule_id": "DET-001",
  "version": "1.0",

  "name": "Suspicious Connection Pattern",
  "description": "Detects defined suspicious connection condition",

  "enabled": true,
  "severity": "high",

  "event_type": "network_connection",

  "conditions": [
    {
      "field": "entities.destination_port",
      "operator": "equals",
      "value": 4444
    }
  ],

  "logic": "AND",

  "detection_confidence": 0.85,

  "deduplication_window_seconds": 300,

  "created_at": "2026-11-02T00:00:00Z"
}
```

---

# 4. Detection Confidence Formula

Detection confidence answers: *How confidently did deterministic detection identify a meaningful suspicious pattern?*

$$D_c = w_r R + w_s S + w_c C$$

Where $w_r + w_s + w_c = 1.0$. Recommended initial configuration:

$$D_c = 0.50R + 0.30S + 0.20C$$

### Component Definitions:
1. **Rule Condition Coverage ($R$)**:
   $$R = \frac{\text{Satisfied Conditions}}{\text{Total Required Conditions}} \quad \text{or} \quad R \in \{0, 1\} \text{ (binary matching)}$$
2. **Source Reliability ($S$)**:
   - Trusted structured telemetry: $1.00$
   - Partially structured source: $0.75$
   - Incomplete / heuristic source: $0.50$
3. **Contextual Consistency ($C$)**:
   $$C = \frac{\text{Supporting Contextual Signals}}{\text{Total Evaluated Contextual Signals}}$$

---

# 5. Alert Schema

```json
{
  "alert_id": "ALT-001",

  "detection_id": "DETRES-001",
  "rule_id": "DET-001",
  "rule_version": "1.0",

  "triggering_event_ids": [
    "evt_01JXYZ001"
  ],

  "severity": "high",
  "detection_confidence": 0.89,

  "status": "new",

  "created_at": "2026-11-02T10:16:00Z",

  "entity_refs": [
    {
      "entity_type": "host",
      "entity_value": "host-01"
    }
  ]
}
```

---

# 6. Alert Severity Score

Severity represents potential organizational impact and triage priority:

$$S_a = 0.50I + 0.30E + 0.20P$$

Where:
- $I$ = Estimated impact (0–1)
- $E$ = Exposure / asset scope (0–1)
- $P$ = Persistence / frequency of occurrence (0–1)

### Severity Mapping:
- **0.00 – 0.24**: Low
- **0.25 – 0.49**: Medium
- **0.50 – 0.74**: High
- **0.75 – 1.00**: Critical

---

# 7. Entity Schema

Entities are first-class objects for graph pivots:

```json
{
  "entity_id": "ENT-001",

  "entity_type": "host",
  "normalized_value": "host-01",

  "attributes": {
    "ip_addresses": [
      "192.168.1.10"
    ]
  },

  "first_seen": "2026-11-02T09:00:00Z",
  "last_seen": "2026-11-02T10:15:30Z"
}
```

Supported types: `host`, `user`, `source_ip`, `destination_ip`, `process`, `file`, `session`.

---

# 8. Correlation Request Schema

```json
{
  "investigation_id": "INV-001",

  "seed_event_ids": [
    "evt_01JXYZ001"
  ],

  "entity_filters": [
    {
      "entity_type": "host",
      "entity_value": "host-01"
    }
  ],

  "time_window": {
    "start": "2026-11-02T09:45:00Z",
    "end": "2026-11-02T10:45:00Z"
  },

  "correlation_types": [
    "entity",
    "temporal"
  ],

  "max_results": 100
}
```

---

# 9. Correlation Result Schema

```json
{
  "correlation_id": "COR-001",

  "investigation_id": "INV-001",

  "source_event_id": "evt_01JXYZ001",
  "related_event_id": "evt_01JXYZ002",

  "correlation_type": "entity_temporal",

  "shared_entities": [
    {
      "entity_type": "host",
      "entity_value": "host-01"
    }
  ],

  "time_difference_seconds": 120,

  "correlation_score": 0.82,

  "explanation": "Events share the same host and occurred within the configured correlation window."
}
```

---

# 10. Correlation Score Formula

Measures the analytical strength of an event relationship:

$$C_s = 0.50E + 0.30T + 0.20A$$

1. **Entity Similarity ($E$)**:
   $$E = \frac{\text{Weighted Matched Entities}}{\text{Maximum Possible Entity Weight}}$$
   Default entity weights: Host ($0.35$), User ($0.30$), IP Address ($0.20$), Process ($0.15$).
2. **Temporal Proximity ($T$)**:
   For maximum correlation window $W$:
   $$T = \max\left(0, 1 - \frac{\Delta t}{W}\right)$$
   Example: If $W = 600\text{s}$ and $\Delta t = 120\text{s}$, $T = 1 - \frac{120}{600} = 0.80$.
3. **Attribute Relationship ($A$)**:
   $$A = \frac{\text{Matched Relevant Attributes}}{\text{Evaluated Relevant Attributes}}$$

### Correlation Thresholds:
- **0.80 – 1.00**: Strong
- **0.60 – 0.79**: Moderate
- **0.40 – 0.59**: Weak
- **< 0.40**: Discarded

---

# 11. Evidence Schema

```json
{
  "evidence_id": "EVD-001",

  "investigation_id": "INV-001",

  "evidence_type": "direct_telemetry",

  "source_type": "normalized_event",
  "source_id": "evt_01JXYZ001",

  "claim": "A connection to the identified destination was observed.",

  "support_level": "direct",

  "directness_score": 1.0,
  "source_reliability_score": 1.0,
  "corroboration_score": 0.70,
  "relevance_score": 0.95,

  "evidence_score": 0.93,

  "created_at": "2026-11-02T10:20:00Z"
}
```

---

# 12. Evidence Strength Formula

$$E_s = 0.35D + 0.25R + 0.20C + 0.20L$$

- $D$ = Directness (Direct Telemetry: $1.00$, Deterministic Correlation: $0.85$, Retrieved Knowledge: $0.60$, AI Interpretation: $0.40$)
- $R$ = Source Reliability ($1.00$ for structured canonical telemetry)
- $C$ = Corroboration ($C = 1 - e^{-k(n-1)}$, with $k = 0.5$ and $n = \text{independent sources}$)
- $L$ = Investigation Relevance (0.0 to 1.0)

$$\begin{array}{|c|c|}
\hline
\textbf{Independent Sources } (n) & \textbf{Corroboration Score } (C) \\
\hline
1 & 0.00 \\
2 & 0.39 \\
3 & 0.63 \\
4 & 0.78 \\
\hline
\end{array}$$

---

# 13. Investigation State Schema

```json
{
  "investigation_id": "INV-001",

  "status": "investigating",
  "state_version": 5,

  "alert_id": "ALT-001",

  "objective": "Determine whether the detected activity represents the defined attack scenario.",

  "facts": [
    {
      "fact_id": "FACT-001",
      "statement": "The triggering network event occurred.",
      "evidence_ids": [
        "EVD-001"
      ]
    }
  ],

  "hypotheses": [
    {
      "hypothesis_id": "HYP-001",
      "statement": "The observed activity may be related to the investigated scenario.",
      "supporting_evidence_ids": [
        "EVD-001"
      ],
      "conflicting_evidence_ids": [],
      "confidence": 0.65
    }
  ],

  "evidence_gaps": [
    {
      "gap_id": "GAP-001",
      "question": "Are related events present on the same host?",
      "priority": "high"
    }
  ],

  "actions": [],

  "budget": {
    "max_actions": 10,
    "actions_used": 2,

    "max_model_calls": 8,
    "model_calls_used": 2,

    "max_duration_seconds": 600
  },

  "created_at": "2026-11-02T10:16:00Z",
  "updated_at": "2026-11-02T10:22:00Z"
}
```

---

# 14. Investigation Action Schema

```json
{
  "action_id": "ACT-001",

  "investigation_id": "INV-001",

  "capability": "event_query",

  "reason": "Retrieve events associated with the triggering host.",

  "input": {
    "host": "host-01",
    "time_window_minutes": 30
  },

  "status": "completed",

  "started_at": "2026-11-02T10:20:00Z",
  "completed_at": "2026-11-02T10:20:02Z",

  "result_references": [
    "evt_01JXYZ002",
    "evt_01JXYZ003"
  ]
}
```

---

# 15. Confidence Formulas

### 15.1 Hypothesis Confidence ($H_c$)
$$H_c = \operatorname{clamp}(0, 1, 0.50S + 0.25C - 0.15X - 0.10G)$$
Where:
- $S$ = Average supporting evidence strength
- $C$ = Corroboration strength
- $X$ = Conflicting evidence penalty
- $G$ = Unresolved gap penalty

### 15.2 Overall Investigation Confidence ($I_c$)
$$I_c = \operatorname{clamp}(0, 1, 0.35E + 0.25H + 0.20V - 0.10G - 0.10X)$$
- $E$ = Weighted evidence quality ($35\%$)
- $H$ = Strongest validated hypothesis confidence ($25\%$)
- $V$ = Validation success score ($20\%$)
- $G$ = Unresolved evidence gap penalty ($-10\%$)
- $X$ = Conflicting evidence penalty ($-10\%$)

### 15.3 Evidence Coverage
$$\text{Coverage} = \frac{G_r}{G_t} = \frac{\text{Resolved Evidence Gaps}}{\text{Total Relevant Evidence Gaps}}$$

---

# 16. Auto-Resolution and Escalation Policy

```text
                    INVESTIGATION
                         │
                         ▼
                 CONFIDENCE SCORE
                         │
            ┌────────────┼─────────────┐
            ▼            ▼             ▼
         ≥ 0.85       0.60–0.84       < 0.60
            │            │             │
            ▼            ▼             ▼
      AUTO-RESOLVE    ANALYST       ESCALATE /
                      REVIEW       INCONCLUSIVE
```

### Strict Auto-Resolution Criteria:
$$\text{Investigation Confidence } \ge 0.85 \quad \land \quad \text{Evidence Coverage } \ge 0.80 \quad \land \quad \text{Zero Conflicting Evidence} \quad \land \quad \text{Validation Completed}$$

---

# 17. Termination Logic

$$\text{Terminate} = \text{SufficientEvidence} \lor \text{NoUsefulActions} \lor \text{BudgetExhausted} \lor \text{HumanReviewRequired}$$

```python
if sufficient_evidence:
    resolve()
elif human_review_required:
    escalate()
elif budget_exhausted:
    mark_inconclusive_or_escalate()
elif no_useful_actions:
    mark_inconclusive()
else:
    continue_investigation()
```

---

# 18. Action Utility & Information Gain

$$U_a = \frac{\text{Expected Information Gain} \times \text{Success Probability} \times \text{Policy Priority}}{\text{Estimated Cost}}$$

$$\text{Information Gain } (IG) = \frac{\text{High-Priority Gaps Addressed by Action}}{\text{Total Unresolved High-Priority Gaps}}$$

---

# 19. State Transition & Audit Schemas

### State Transition (Optimistic Locking)
```json
{
  "transition_id": "TRN-001",
  "investigation_id": "INV-001",
  "previous_status": "initialized",
  "new_status": "investigating",
  "trigger": "planner_started",
  "state_version_before": 4,
  "state_version_after": 5,
  "timestamp": "2026-11-02T10:20:00Z"
}
```

### Audit Log Record
```json
{
  "audit_id": "AUD-001",
  "investigation_id": "INV-001",
  "component": "planner",
  "event_type": "action_selected",
  "timestamp": "2026-11-02T10:20:00Z",
  "input_state_version": 5,
  "decision": {
    "selected_capability": "event_query",
    "reason": "Resolve high-priority host activity evidence gap."
  },
  "result_reference": "ACT-001"
}
```

---

# 20. Declarative Configuration Blueprint (`config/engine.yaml`)

```yaml
scoring:
  detection:
    rule_coverage_weight: 0.50
    source_reliability_weight: 0.30
    contextual_consistency_weight: 0.20

  correlation:
    entity_weight: 0.50
    temporal_weight: 0.30
    attribute_weight: 0.20

  evidence:
    directness_weight: 0.35
    reliability_weight: 0.25
    corroboration_weight: 0.20
    relevance_weight: 0.20

investigation:
  auto_resolve_threshold: 0.85
  analyst_review_threshold: 0.60
  minimum_evidence_coverage: 0.80

budget:
  max_actions: 10
  max_model_calls: 8
  max_duration_seconds: 600
```

---

# 21. Summary of Concrete Mathematical Formulas

| Metric | Formula / Method | Range |
|---|---|---|
| **Detection Confidence** | $0.50R + 0.30S + 0.20C$ | $0.00 - 1.00$ |
| **Alert Severity** | $0.50I + 0.30E + 0.20P$ | $0.00 - 1.00$ |
| **Correlation Score** | $0.50E + 0.30T + 0.20A$ | $0.00 - 1.00$ |
| **Evidence Strength** | $0.35D + 0.25R + 0.20C + 0.20L$ | $0.00 - 1.00$ |
| **Hypothesis Confidence** | $\operatorname{clamp}(0, 1, 0.50S + 0.25C - 0.15X - 0.10G)$ | $0.00 - 1.00$ |
| **Investigation Confidence** | $\operatorname{clamp}(0, 1, 0.35E + 0.25H + 0.20V - 0.10G - 0.10X)$ | $0.00 - 1.00$ |
| **Evidence Coverage** | $G_r / G_t$ | $0.00 - 1.00$ |
| **Action Utility** | $(IG \times P_s \times \text{Priority}) / \text{Cost}$ | Normalized relative |
| **Corroboration Score** | $1 - e^{-0.5(n-1)}$ | $0.00 - 1.00$ |

---

# 22. Calibration & Evaluation Loop

$$\text{Initial Weights} \to \text{Run Scenarios} \to \text{Measure F1 / Coverage / Utility} \to \text{Analyze FP / FN / Escalations} \to \text{Calibrate Configuration} \to \text{Re-Evaluate}$$
